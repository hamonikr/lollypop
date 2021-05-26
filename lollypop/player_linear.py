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

from itertools import chain

from lollypop.define import Repeat, App
from lollypop.objects_track import Track
from lollypop.logger import Logger


class LinearPlayer:
    """
        Manage normal playback
    """

    def __init__(self):
        """
            Init linear player
        """
        pass

    def next(self):
        """
            Next track for current album or next album
            @return track as Track
        """
        # No album in playback
        if not self.albums:
            return Track()
        album = self._current_track.album
        track = self.__fallback_track_if_album_missing(album)
        # Current album missing, go to fallback track
        if track is not None:
            return track
        new_track_position = self._current_track.position + 1
        # next album
        if new_track_position >= len(album.track_ids):
            try:
                pos = self.albums.index(album)
                albums_count = len(self._albums)
                new_pos = 0
                # Search for a next album
                for idx in chain(range(pos + 1, albums_count),
                                 range(0, pos)):
                    if self._albums[idx].tracks:
                        new_pos = idx
                        break
                if new_pos == 0:
                    repeat = App().settings.get_enum("repeat")
                    if repeat == Repeat.ALL:
                        pos = 0
                    else:
                        return Track()
                else:
                    pos = new_pos
            except Exception as e:
                Logger.error("LinearPlayer::next(): %s", e)
                pos = 0  # Happens if current album has been removed
            track = self._albums[pos].tracks[0]
        # next track
        else:
            track = album.tracks[new_track_position]
        return track

    def prev(self):
        """
            Prev track base on.current_track context
            @return track as Track
        """
        # No album in playback
        if not self._albums:
            return Track()
        album = self._current_track.album
        track = self.__fallback_track_if_album_missing(album)
        # Current album missing, go to fallback track
        if track is not None:
            return track
        new_track_position = self._current_track.position - 1
        # Previous album
        if new_track_position < 0:
            try:
                pos = self.albums.index(album)
                albums_count = len(self._albums)
                new_pos = 0
                # Search for a prev album
                for idx in chain(reversed(range(0, pos)),
                                 reversed(range(pos, albums_count))):
                    if self._albums[idx].tracks:
                        new_pos = idx
                        break
                if new_pos == albums_count - 1:
                    repeat = App().settings.get_enum("repeat")
                    if repeat == Repeat.ALL:
                        pos = new_pos
                    else:
                        return Track()
                else:
                    pos = new_pos
            except Exception as e:
                Logger.error("LinearPlayer::prev(): %s", e)
                pos = 0  # Happens if current album has been removed
            track = self._albums[pos].tracks[-1]
        # Previous track
        else:
            track = album.tracks[new_track_position]
        return track

    def __fallback_track_if_album_missing(self, album):
        """
            Get a fallback track if album not in player
            @param album as Album
            @return Track/None
        """
        if album not in self._albums:
            album = self._albums[0]
            if album.tracks:
                return album.tracks[0]
            else:
                return Track()
        return None
