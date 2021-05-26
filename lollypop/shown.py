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

from gettext import gettext as _

from lollypop.define import Type, App


class ShownLists:
    """
        Handle shown lists
    """

    IDS = {
        Type.SUGGESTIONS: _("Suggestions"),
        Type.POPULARS: _("Popular albums"),
        Type.RANDOMS: _("Random albums"),
        Type.LOVED: _("Loved albums"),
        Type.RECENTS: _("Recently added albums"),
        Type.LITTLE: _("Seldomly played albums"),
        Type.PLAYLISTS: _("Playlists"),
        Type.YEARS: _("Years"),
        Type.GENRES: _("Genres"),
        Type.GENRES_LIST: _("Genres (list)"),
        Type.WEB: _("Web"),
        Type.LYRICS: _("Lyrics"),
        Type.ALL: _("Albums"),
        Type.ARTISTS: _("Artists"),
        Type.ARTISTS_LIST: _("Artists (list)"),
        Type.SEARCH: _("Search"),
        Type.CURRENT: _("Playing albums"),
        Type.INFO: _("Information"),
        Type.COMPILATIONS: _("Compilations"),
    }

    def get(mask, get_all=False):
        """
            Get list
            @param mask as bit mask
            @param get_all as bool
            @return [(,)]
        """
        wanted = list(App().settings.get_value("shown-album-lists"))
        lists = []
        for key in ShownLists.IDS.keys():
            string = ShownLists.IDS[key]
            if get_all or key in wanted:
                lists.append((key, string, ""))
        lists.append((Type.SEPARATOR, "", ""))
        lists.sort(key=lambda tup: tup[0], reverse=True)
        return lists


class ShownPlaylists(ShownLists):
    """
        Handle shown playlists
    """
    IDS = {
        Type.POPULARS: _("Popular tracks"),
        Type.RANDOMS: _("Random tracks"),
        Type.LOVED: _("Loved tracks"),
        Type.RECENTS: _("Recently played tracks"),
        Type.LITTLE: _("Seldomly played tracks"),
        Type.SKIPPED: _("Skipped tracks"),
        Type.ALL: _("All tracks")
    }

    def get(get_all=False):
        """
            Get list
            @return [(,)]
        """
        wanted = App().settings.get_value("shown-playlists")
        lists = []
        for key in ShownPlaylists.IDS.keys():
            string = ShownPlaylists.IDS[key]
            if get_all or key in wanted:
                lists.append((key, string, ""))
        lists.sort(key=lambda tup: tup[0], reverse=True)
        return lists
