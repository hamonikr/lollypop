# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2020 David Mandelberg
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

from lollypop.define import App, Repeat
from lollypop.objects_album import Album
from lollypop.utils import get_default_storage_type


class AutoRandomPlayer:
    """
        Manage playback for AUTO_RANDOM when going to the end
    """

    def __init__(self):
        """
            Init player
        """
        self.connect("next-changed", self.__on_next_changed)

    def next_album(self):
        """
            Get next album to add
            @return Album
        """
        storage_type = get_default_storage_type()
        for album_id in App().albums.get_randoms(storage_type, None, False, 2):
            if album_id != self.current_track.album.id:
                return Album(album_id)
        return None

#######################
# PRIVATE             #
#######################
    def __on_next_changed(self, player):
        """
            Add a new album if playback finished and wanted by user
        """
        if not self._albums:
            return
        if App().settings.get_enum("repeat") != Repeat.AUTO_RANDOM or\
                player.next_track.id is not None:
            return
        album = self.next_album()
        if album:
            self.add_album(album)
