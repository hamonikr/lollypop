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

from gi.repository import Gio

from gettext import gettext as _

from lollypop.define import App, ViewType
from lollypop.utils import get_default_storage_type
from lollypop.objects_album import Album


class GenreMenu(Gio.Menu):
    """
        Contextual menu for a genres
    """
    def __init__(self, genre_id, view_type, header=False):
        """
            Init decade menu
            @param genre_id as int
            @param view_type as ViewType
            @param header as bool
        """
        Gio.Menu.__init__(self)
        if header:
            from lollypop.menu_header import RoundedMenuHeader
            name = App().genres.get_name(genre_id)
            artwork_name = "genre_%s" % name
            self.append_item(RoundedMenuHeader(name, artwork_name))
        if not view_type & ViewType.BANNER:
            from lollypop.menu_playback import GenrePlaybackMenu
            self.append_section(_("Playback"), GenrePlaybackMenu(genre_id))
        from lollypop.menu_sync import SyncAlbumsMenu
        section = Gio.Menu()
        self.append_section(_("Add to"), section)
        storage_type = get_default_storage_type()
        album_ids = App().albums.get_ids([genre_id], [],
                                         storage_type,
                                         False)
        album_ids += App().albums.get_compilation_ids([genre_id],
                                                      storage_type,
                                                      False)
        albums = [Album(album_id) for album_id in album_ids]
        section.append_submenu(_("Devices"), SyncAlbumsMenu(albums))
