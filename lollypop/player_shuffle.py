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

from random import shuffle, random

from lollypop.define import Repeat, App
from lollypop.objects_track import Track
from lollypop.objects_album import Album
from lollypop.list import LinkedList
from lollypop.utils import emit_signal, get_default_storage_type
from lollypop.logger import Logger


class ShufflePlayer:
    """
        Shuffle player
        Manage shuffle tracks and party mode
    """

    def __init__(self):
        """
            Init shuffle player
        """
        # Albums to play, different from _albums for a better shuffle
        self.__to_play_albums = []
        # Albums who never have been played
        self.__not_played_albums = []
        # Tracks already played
        self.__history = []
        # Tracks already played by albums
        self.__already_played_tracks = {}
        # Party mode
        self._is_party = False
        App().settings.connect("changed::shuffle", self.__set_shuffle)
        self.connect("playback-added", self.__on_playback_added)
        self.connect("playback-setted", self.__on_playback_setted)
        self.connect("playback-removed", self.__on_playback_removed)

    def next(self):
        """
            Next shuffle track
            @return Track
        """
        if self.shuffle_has_next:
            track = self.__history.next.value
        elif self._albums:
            track = self.__get_next()
        else:
            track = Track()
        return track

    def prev(self):
        """
            Prev track based on history
            @return Track
        """
        if self.shuffle_has_prev:
            track = self.__history.prev.value
        else:
            track = self._current_track
        return track

    def set_party(self, party):
        """
            Set party mode on if party is True
            Play a new random track if not already playing
            @param party as bool
        """
        def start_party(*ignore):
            if self._albums:
                # Start a new song if not playing
                if self._current_track.id is None:
                    track = self.__get_tracks_random()
                    self.load(track)
                elif not self.is_playing:
                    self.play()
                else:
                    self.set_next()
            emit_signal(self, "loading-changed", False, Track())

        if party == self._is_party:
            return
        self._is_party = party

        if party:
            App().task_helper.run(self.set_party_ids, callback=(start_party,))
        else:
            # We want current album to continue playback
            self._albums = [self._current_track.album]
            emit_signal(self, "playback-setted", [])
            emit_signal(self, "playback-added",
                        self._current_track.album)
        if self._current_track.id is not None:
            self.set_next()
            self.set_prev()

    def set_party_ids(self):
        """
            Set party mode ids
        """
        if not self._is_party:
            return
        party_ids = App().settings.get_value("party-ids")
        storage_type = get_default_storage_type()
        album_ids = App().albums.get_ids(party_ids, [], storage_type, False)
        emit_signal(self, "playback-setted", [])
        self._albums = []
        if album_ids:
            emit_signal(self, "loading-changed", True, Track())
        for album_id in album_ids:
            album = Album(album_id, [], [], False)
            self._albums.append(album)
        emit_signal(self, "playback-setted", list(self._albums))

    @property
    def is_party(self):
        """
            True if party mode on
            @return bool
        """
        return self._is_party

    @property
    def shuffle_has_next(self):
        """
            True if history provide a next track
            @return bool
        """
        return self.__history and self.__history.has_next

    @property
    def shuffle_has_prev(self):
        """
            True if history provide a prev track
            @return bool
        """
        return self.__history and self.__history.has_prev

#######################
# PROTECTED           #
#######################
    def _on_stream_start(self, bus, message):
        """
            On stream start add to shuffle history
        """
        if self._current_track.id is None or\
                self._current_track.id < 0:
            return
        # Add track to shuffle history if needed
        if App().settings.get_value("shuffle") or self._is_party:
            self.__add_to_shuffle_history(self._current_track)
            if self.__history:
                next = self.__history.next
                prev = self.__history.prev
                # Remove next track
                if next is not None and\
                        self._current_track == next.value:
                    next = self.__history.next
                    next.set_prev(self.__history)
                    self.__history = next
                # Remove previous track
                elif prev is not None and\
                        self._current_track == prev.value:
                    prev = self.__history.prev
                    prev.set_next(self.__history)
                    self.__history = prev
                # Add a new track
                elif self.__history.value != self._current_track:
                    new_list = LinkedList(self._current_track,
                                          None,
                                          self.__history)
                    self.__history = new_list
            else:
                # Initial history
                new_list = LinkedList(self._current_track)
                self.__history = new_list

#######################
# PRIVATE             #
#######################
    def __set_shuffle(self, settings, value):
        """
            Update next track
            @param settings as Gio.Settings
            @param value as GLib.Variant
        """
        self.__on_playback_setted(self, self.albums)
        if self._current_track.id is not None:
            self.set_next()

    def __get_next(self):
        """
            Next track in shuffle mode
            @return track as Track
        """
        try:
            if App().settings.get_value("shuffle") or self._is_party:
                if self._albums:
                    track = self.__get_tracks_random()
                    # All tracks done
                    # Try to get another one track after reseting history
                    if track.id is None:
                        self.__to_play_albums = list(self._albums)
                        shuffle(self.__to_play_albums)
                        repeat = App().settings.get_enum("repeat")
                        # Do not reset history if a new album is going to
                        # be added
                        if repeat not in [Repeat.AUTO_SIMILAR,
                                          Repeat.AUTO_RANDOM]:
                            self.__history = []
                            self.__already_played_tracks = {}
                        if repeat == Repeat.ALL:
                            return self.__get_next()
                    return track
        except Exception as e:
            Logger.error("ShufflePLayer::__get_next(): %s", e)
        return Track()

    def __get_tracks_random(self):
        """
            Return a random track and make sure it has never been played
            @return Track
        """
        # True if all albums have been played on time
        if not self.__not_played_albums:
            self.__not_played_albums = list(self.__to_play_albums)
        while self.__not_played_albums:
            album = self.__not_played_albums.pop(0)
            if not album.tracks:
                continue
            for track in sorted(album.tracks,
                                key=lambda *args: random()):
                if not self.__in_shuffle_history(track):
                    return track
            self.__to_play_albums.remove(album)
        if self.__to_play_albums:
            return self.__get_tracks_random()
        else:
            return Track()

    def __in_shuffle_history(self, track):
        """
            True if track in shuffle history
            @param track as Track
            @return bool
        """
        return track.album.id in self.__already_played_tracks.keys() and\
            track.id in self.__already_played_tracks[track.album.id]

    def __add_to_shuffle_history(self, track):
        """
            Add a track to shuffle history
            @param track as Track
        """
        if track.album.id not in self.__already_played_tracks.keys():
            self.__already_played_tracks[track.album.id] = []
        if track not in self.__already_played_tracks[track.album.id]:
            self.__already_played_tracks[track.album.id].append(track.id)

    def __on_playback_added(self, player, album):
        """
            Update shuffle for album
            @param player as Player
            @param album as Album
        """
        if App().settings.get_value("shuffle") or self._is_party:
            if album not in self.__to_play_albums:
                self.__to_play_albums.append(album)
                shuffle(self.__to_play_albums)
            if album not in self.__not_played_albums:
                self.__not_played_albums.append(album)
            # If album already playing or
            # if current track was last one
            if App().player.current_track.album == album or\
                    not self.__already_played_tracks:
                self.__add_to_shuffle_history(App().player.current_track)

    def __on_playback_setted(self, player, albums):
        """
            Update shuffle for album
            @param player as Player
            @param albums as [Album]
        """
        if App().settings.get_value("shuffle") or self._is_party:
            self.__to_play_albums = albums
            if albums:
                shuffle(self.__to_play_albums)
            self.__not_played_albums = []
            self.__already_played_tracks = {}
            if App().player.current_track.album in albums:
                self.__add_to_shuffle_history(App().player.current_track)

    def __on_playback_removed(self, player, album):
        """
            Update shuffle for album
            @param player as Player
            @param album as Album
        """
        if App().settings.get_value("shuffle") or self._is_party:
            if album in self.__to_play_albums:
                self.__to_play_albums.remove(album)
            if album in self.__not_played_albums:
                self.__not_played_albums.remove(album)
