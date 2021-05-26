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

from random import sample

from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.define import App, Type
from lollypop.objects_track import Track
from lollypop.widgets_albums_rounded import RoundedAlbumsWidget


class PlaylistRoundedWidget(RoundedAlbumsWidget, SignalsHelper):
    """
        Playlist widget showing cover for 4 albums
    """

    @signals_map
    def __init__(self, playlist_id, view_type, font_height):
        """
            Init widget
            @param playlist_id as playlist_id
            @param view_type as ViewType
            @param font_height as int
        """
        name = sortname = App().playlists.get_name(playlist_id)
        RoundedAlbumsWidget.__init__(self, playlist_id, name,
                                     sortname, view_type, font_height)
        self._track_ids = []
        self._genre = Type.PLAYLISTS
        return [
            (App().art, "artwork-cleared", "_on_artwork_cleared")
        ]

    def populate(self):
        """
            Populate widget content
        """
        if self._artwork is None:
            RoundedAlbumsWidget.populate(self)
        else:
            self.set_artwork()

    @property
    def track_ids(self):
        """
            Get current track ids
            @return [int]
        """
        return self._track_ids

    @property
    def artwork_name(self):
        """
            Get artwork name
            return str
        """
        return "playlist_" + self.name

#######################
# PROTECTED           #
#######################
    def _get_album_ids(self):
        """
            Get album ids
            @return [int]
        """
        album_ids = []
        if self._data > 0 and App().playlists.get_smart(self._data):
            request = App().playlists.get_smart_sql(self._data)
            if request is not None:
                self._track_ids = App().db.execute(request)
        else:
            self._track_ids = App().playlists.get_track_ids(self._data)
        sample(self._track_ids, len(self._track_ids))
        for track_id in self._track_ids:
            track = Track(track_id)
            if track.album.id not in album_ids:
                album_ids.append(track.album.id)
            if len(album_ids) == self._ALBUMS_COUNT:
                break
        return album_ids

    def _on_artwork_cleared(self, art, name, prefix):
        """
            Update artwork
            @param art as Art
            @param name as str
            @param prefix as str
        """
        if self._artwork is not None:
            self.set_artwork()

#######################
# PRIVATE             #
#######################
