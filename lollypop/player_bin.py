# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gst, GstAudio, GstPbutils, GLib, Gio

from time import time
from gettext import gettext as _

from lollypop.tagreader import TagReader, Discoverer
from lollypop.player_plugins import PluginsPlayer
from lollypop.define import GstPlayFlags, App, StorageType, Repeat
from lollypop.codecs import Codecs
from lollypop.logger import Logger
from lollypop.objects_track import Track
from lollypop.utils import emit_signal, get_network_available


class BinPlayer:
    """
        Gstreamer bin player
    """

    def __init__(self):
        """
            Init playbin
        """
        # In the case of gapless playback, both 'about-to-finish'
        # and 'eos' can occur during the same stream.
        self.__track_in_pipe = False
        self.__cancellable = Gio.Cancellable()
        self.__codecs = Codecs()
        self._current_track = Track()
        self._next_track = Track()
        self._prev_track = Track()
        self._playbin = self._playbin1 = Gst.ElementFactory.make(
            "playbin", "player")
        self._playbin2 = Gst.ElementFactory.make("playbin", "player")
        self._plugins = self._plugins1 = PluginsPlayer(self._playbin1)
        self._plugins2 = PluginsPlayer(self._playbin2)
        for playbin in [self._playbin1, self._playbin2]:
            flags = playbin.get_property("flags")
            flags &= ~GstPlayFlags.GST_PLAY_FLAG_VIDEO
            playbin.set_property("flags", flags)
            playbin.set_property("buffer-size", 5 << 20)
            playbin.set_property("buffer-duration", 10 * Gst.SECOND)
            playbin.connect("notify::volume", self.__on_volume_changed)
            playbin.connect("about-to-finish",
                            self._on_stream_about_to_finish)
            bus = playbin.get_bus()
            bus.add_signal_watch()
            bus.connect("message::error", self._on_bus_error)
            bus.connect("message::eos", self._on_bus_eos)
            bus.connect("message::element", self._on_bus_element)
            bus.connect("message::stream-start", self._on_stream_start)
            bus.connect("message::tag", self._on_bus_message_tag)
        self._start_time = 0

    def load(self, track):
        """
            Load track and play it
            @param track as Track
        """
        self._playbin.set_state(Gst.State.NULL)
        if self._load_track(track):
            self.play()

    def play(self):
        """
            Change player state to PLAYING
        """
        # No current playback, song in queue
        if self._current_track.id is None:
            if self._next_track.id is not None:
                self.load(self._next_track)
        else:
            self._playbin.set_state(Gst.State.PLAYING)
            emit_signal(self, "status-changed")

    def pause(self):
        """
            Change player state to PAUSED
        """
        self._playbin.set_state(Gst.State.PAUSED)
        emit_signal(self, "status-changed")

    def stop(self):
        """
            Change player state to STOPPED
            @param force as bool
        """
        self._current_track = Track()
        self._current_track = Track()
        self._prev_track = Track()
        self._next_track = Track()
        emit_signal(self, "current-changed")
        emit_signal(self, "prev-changed")
        emit_signal(self, "next-changed")
        self._playbin.set_state(Gst.State.NULL)
        emit_signal(self, "status-changed")

    def stop_all(self):
        """
            Stop all bins, lollypop should quit now
        """
        # Stop
        self._playbin1.set_state(Gst.State.NULL)
        self._playbin2.set_state(Gst.State.NULL)

    def play_pause(self):
        """
            Set playing if paused
            Set paused if playing
        """
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def reload_track(self):
        """
            Reload track at current position
        """
        if self.current_track.id is None:
            return
        position = self.position
        self.load(self.current_track)
        GLib.timeout_add(100, self.seek, position)

    def seek(self, position):
        """
            Seek current track to position
            @param position as int (ms)
        """
        if self._current_track.id is None:
            return
        # Seems gstreamer doesn't like seeking to end, sometimes
        # doesn't go to next track
        if position >= self._current_track.duration:
            self.next()
        else:
            self._playbin.seek_simple(Gst.Format.TIME,
                                      Gst.SeekFlags.FLUSH |
                                      Gst.SeekFlags.KEY_UNIT,
                                      position * 1000000)
            emit_signal(self, "seeked", position)

    def get_status(self):
        """
            Playback status
            @return Gstreamer state
        """
        ok, state, pending = self._playbin.get_state(Gst.CLOCK_TIME_NONE)
        if ok == Gst.StateChangeReturn.ASYNC:
            state = pending
        elif (ok != Gst.StateChangeReturn.SUCCESS):
            state = Gst.State.NULL
        return state

    def set_volume(self, rate):
        """
            Set player volume rate
            @param rate as double
        """
        if rate < 0.0:
            rate = 0.0
        elif rate > 1.0:
            rate = 1.0
        self._playbin.set_volume(GstAudio.StreamVolumeFormat.CUBIC, rate)

    @property
    def plugins(self):
        """
            Get plugins
            @return [PluginsPlayer]
        """
        return [self._plugins1, self._plugins2]

    @property
    def is_playing(self):
        """
            True if player is playing
            @return bool
        """
        ok, state, pending = self._playbin.get_state(Gst.CLOCK_TIME_NONE)
        if ok == Gst.StateChangeReturn.ASYNC:
            return pending == Gst.State.PLAYING
        elif ok == Gst.StateChangeReturn.SUCCESS:
            return state == Gst.State.PLAYING
        else:
            return False

    @property
    def position(self):
        """
            Return bin playback position
            @HACK handle crossefade here, as we know we're going to be
            called every seconds
            @return position as int (ms)
        """
        return self.__get_bin_position(self._playbin)

    @property
    def remaining(self):
        """
            Return remaining duration
            @return duration as int (ms)
        """
        position = self._playbin.query_position(Gst.Format.TIME)[1] / 1000000
        duration = self._current_track.duration
        return int(duration - position)

    @property
    def current_track(self):
        """
            Current track
        """
        return self._current_track

    @property
    def volume(self):
        """
            Return player volume rate
            @return rate as double
        """
        return self._playbin.get_volume(GstAudio.StreamVolumeFormat.CUBIC)

#######################
# PROTECTED           #
#######################
    def _load_track(self, track):
        """
            Load track
            @param track as Track
            @return False if track not loaded
        """
        self.__track_in_pipe = True
        Logger.debug("BinPlayer::_load_track(): %s" % track.uri)
        try:
            emit_signal(self, "loading-changed", False, self._current_track)
            self._current_track = track
            if track.is_web and not track.uri_loaded:
                emit_signal(self, "loading-changed", True, track)
                self.__load_from_web(track)
                return False
            else:
                self._playbin.set_property("uri", track.uri)
        except Exception as e:  # Gstreamer error
            Logger.error("BinPlayer::_load_track(): %s" % e)
            return False
        return True

    def _on_stream_start(self, bus, message):
        """
            On stream start
            Handle stream start: scrobbling, notify, ...
            @param bus as Gst.Bus
            @param message as Gst.Message
        """
        self.__track_in_pipe = False
        emit_signal(self, "loading-changed", False, self._current_track)
        self._start_time = time()
        Logger.debug("Player::_on_stream_start(): %s" %
                     self._current_track.uri)
        emit_signal(self, "current-changed")
        for scrobbler in App().ws_director.scrobblers:
            scrobbler.playing_now(self._current_track)

    def _on_bus_message_tag(self, bus, message):
        """
            Read tags from stream
            @param bus as Gst.Bus
            @param message as Gst.Message
        """
        if self._current_track.storage_type != StorageType.EXTERNAL:
            return
        Logger.debug("Player::__on_bus_message_tag(): %s" %
                     self._current_track.uri)
        reader = TagReader()
        tags = message.parse_tag()
        title = reader.get_title(tags, "")
        if len(title) > 1 and self._current_track.title != title:
            self._current_track.set_name(title)
            emit_signal(self, "current-changed")

    def _on_bus_element(self, bus, message):
        """
            Set elements for missings plugins
            @param bus as Gst.Bus
            @param message as Gst.Message
        """
        if GstPbutils.is_missing_plugin_message(message):
            self.__codecs.append(message)

    def _on_bus_error(self, bus, message):
        """
            Try a codec install and update current track
            @param bus as Gst.Bus
            @param message as Gst.Message
        """
        if self._current_track.is_web:
            emit_signal(self, "loading-changed", False,
                        self._current_track)
        Logger.info("Player::_on_bus_error(): %s" % message.parse_error()[1])
        if self.current_track.id is not None and self.current_track.id >= 0:
            if self.__codecs.is_missing_codec(message):
                self.__codecs.install()
                App().scanner.stop()
                self.stop()
            else:
                (error, parsed) = message.parse_error()
                App().notify.send("Lollypop", parsed)
                self.stop()

    def _on_bus_eos(self, bus, message):
        """
            If we are current bus, try to restart playback
            Else stop playback
        """
        if self.__track_in_pipe:
            return
        if self._playbin.get_bus() == bus:
            if self._next_track.id is None:
                self.stop()
            else:
                self._load_track(self._next_track)
                self.next()

    def _on_stream_about_to_finish(self, playbin):
        """
            When stream is about to finish, switch to next track without gap
            @param playbin as Gst.Bin
        """
        try:
            Logger.debug("Player::__on_stream_about_to_finish(): %s" % playbin)
            # Don't do anything if crossfade on, track already scrobbled
            # See TransitionsPlayer
            if not self.crossfading:
                self._on_track_finished(self.current_track)
                repeat = App().settings.get_enum("repeat")
                if repeat == Repeat.TRACK:
                    self._load_track(self.current_track)
                elif self._next_track.id is not None:
                    self._load_track(self._next_track)
        except Exception as e:
            Logger.error("BinPlayer::_on_stream_about_to_finish(): %s", e)

#######################
# PRIVATE             #
#######################
    def __load_from_web(self, track):
        """
            Load track from web
            @param track as Track
        """
        if get_network_available():
            self.__cancellable.cancel()
            self.__cancellable = Gio.Cancellable.new()
            from lollypop.helper_web import WebHelper
            helper = WebHelper(track, self.__cancellable)
            helper.connect("loaded", self.__on_web_helper_loaded,
                           track, self.__cancellable)
            helper.load()
        else:
            self.skip_album()

    def __get_bin_position(self, playbin):
        """
            Get position for playbin
            @param playbin as Gst.Bin
            @return position as int (ms)
        """
        return playbin.query_position(Gst.Format.TIME)[1] / 1000000

    def __update_current_duration(self, track):
        """
            Update current track duration
            @param track as Track
        """
        try:
            discoverer = Discoverer()
            duration = discoverer.get_info(track.uri).get_duration() / 1000000
            if duration != track.duration and duration > 0:
                App().tracks.set_duration(track.id, int(duration))
                track.reset("duration")
                emit_signal(self, "duration-changed", track.id)
        except Exception as e:
            Logger.error("BinPlayer::__update_current_duration(): %s" % e)

    def __on_volume_changed(self, playbin, sink):
        """
            Emit volume-changed signal
            @param playbin as Gst.Bin
            @param sink as Gst.Sink
        """
        App().settings.set_value("volume-rate", GLib.Variant("d", self.volume))
        emit_signal(self, "volume-changed")

    def __on_web_helper_loaded(self, helper, uri, track, cancellable):
        """
            Play track URI
            @param helper as WebHelper
            @param uri as str
            @param track as Track
            @param cancellable as Gio.Cancellable
        """
        if cancellable.is_cancelled():
            return
        if uri:
            track.set_uri(uri)
            track.set_preloaded()
            self.load(track)
            App().task_helper.run(self.__update_current_duration, track)
        else:
            GLib.idle_add(
                App().notify.send,
                "Lollypop",
                _("Can't find this track on YouTube"))
            self.next()
