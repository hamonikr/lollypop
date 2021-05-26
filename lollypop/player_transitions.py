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

from gi.repository import Gst, GLib, GstAudio

from time import sleep

from lollypop.define import App


class TransitionsPlayer:
    """
        Handle track transitions
    """
    __PADDING = 250

    def __init__(self):
        """
            Init playbin
        """
        self.__crossfading_id = None
        self.__crossfade_up = False
        self.__crossfade_down = False
        self.update_crossfading()

    def load(self, track):
        """
            Load track and play it with transitions
            @param track as Track
            @return bool: True if track has been loaded
        """
        if self.crossfading and\
           self._current_track.id is not None and\
           self.is_playing:
            transition_duration = App().settings.get_value(
                    "transitions-duration").get_int32()
            self.__do_crossfade(transition_duration, track)
            return True
        return False

    def set_crossfading(self, status):
        """
            Set crossfading on/off
            @param status as bool
        """
        if status and self.__crossfading_id is None:
            transition_duration = App().settings.get_value(
                "transitions-duration").get_int32()
            timemout = min(transition_duration, 500)
            self.__crossfading_id = GLib.timeout_add(
                timemout, self.__check_for_crossfading)
        elif not status and self.__crossfading_id is not None:
            GLib.source_remove(self.__crossfading_id)
            self.__crossfading_id = None

    def update_crossfading(self):
        """
            Calculate if crossfading is needed
        """
        transitions = App().settings.get_value("transitions")
        party_only = App().settings.get_value("transitions-party-only")
        self.set_crossfading((transitions and not party_only) or
                             (transitions and party_only and self.is_party))

    @property
    def crossfading(self):
        """
            True if crossfading is on
            @return bool
        """
        return self.__crossfading_id is not None

#######################
# PRIVATE             #
#######################
    def __check_for_crossfading(self):
        """
            Check if we need to do crossfading
        """
        if self._current_track.duration > 0:
            remaining = self.remaining
            transition_duration = App().settings.get_value(
                    "transitions-duration").get_int32()
            if remaining < transition_duration + self.__PADDING:
                self.__do_crossfade(transition_duration,
                                    self._next_track)
        return True

    def __volume_up(self, playbin, plugins, duration):
        """
            Make volume going up smoothly
            @param playbin as Gst.Bin
            @param plugins as PluginsPlayer
            @param duration as int
        """
        plugins.volume.props.volume = 0.0
        self.__crossfade_up = True
        # We add padding because user will not hear track around 0.2
        sleep_ms = (duration + self.__PADDING) / 10
        while plugins.volume.props.volume < 1.0:
            vol = round(plugins.volume.props.volume + 0.1, 1)
            plugins.volume.props.volume = vol
            sleep(sleep_ms / 1000)
        self.__crossfade_up = False

    def __volume_down(self, playbin, plugins, duration):
        """
            Make volume going down smoothly
            @param playbin as Gst.Bin
            @param plugins as PluginsPlayer
            @param duration as int
        """
        plugins.volume.props.volume = 1.0
        self.__crossfade_down = True
        # We add padding because user will not hear track around 0.2
        sleep_ms = (duration + self.__PADDING) / 10
        while plugins.volume.props.volume > 0:
            vol = round(plugins.volume.props.volume - 0.1, 1)
            plugins.volume.props.volume = vol
            sleep(sleep_ms / 1000)
        playbin.set_state(Gst.State.NULL)
        self.__crossfade_down = False

    def __do_crossfade(self, duration, track):
        """
            Crossfade tracks
            @param duration as int
            @param track as Track
        """
        self._on_track_finished(self._current_track)

        if track.id is None:
            return

        # If some crossfade already running, just switch to track
        if self.__crossfade_up or self.__crossfade_down:
            self._playbin.set_state(Gst.State.NULL)
            if self._load_track(track):
                self.play()
            return

        App().task_helper.run(self.__volume_down, self._playbin,
                              self._plugins, duration)
        if self._playbin == self._playbin2:
            self._playbin = self._playbin1
            self._plugins = self._plugins1
        else:
            self._playbin = self._playbin2
            self._plugins = self._plugins2
        rate = App().settings.get_value("volume-rate").get_double()
        self._playbin.set_volume(GstAudio.StreamVolumeFormat.CUBIC, rate)
        if track.id is not None:
            self._playbin.set_state(Gst.State.NULL)
            if self._load_track(track):
                self._playbin.set_state(Gst.State.PLAYING)
            App().task_helper.run(self.__volume_up, self._playbin,
                                  self._plugins, duration)
