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

from gi.repository import Gio, GLib

from gettext import gettext as _

from lollypop.define import App
from lollypop.utils import get_network_available


class SearchMenu(Gio.Menu):
    """
        Contextual menu for search
    """
    def __init__(self, header=False):
        """
            Init search menu
            @param header as bool
        """
        Gio.Menu.__init__(self)
        if header:
            from lollypop.menu_header import MenuHeader
            self.append_item(MenuHeader(_("Search"), "edit-find-symbolic"))
        search_action = Gio.SimpleAction.new_stateful(
            "web_search",
            GLib.VariantType.new("s"),
            GLib.Variant("s", "NONE"))
        App().add_action(search_action)
        section = Gio.Menu()
        self.append_section(_("Search on the Web"), section)
        menu_item = Gio.MenuItem.new(_("Disabled"),
                                     "app.web_search('NONE')")
        section.append_item(menu_item)

        if not get_network_available("YOUTUBE"):
            return

        web_search = App().settings.get_value("web-search")
        if web_search.get_string() != "NONE":
            if get_network_available(web_search.get_string()):
                search_action.set_state(web_search)
        search_action.connect("change-state",
                              self.__on_search_change_state)

        if get_network_available("DEEZER"):
            menu_item = Gio.MenuItem.new(_("Deezer"),
                                         "app.web_search('DEEZER')")
            section.append_item(menu_item)
        if get_network_available("LASTFM"):
            menu_item = Gio.MenuItem.new(_("Last.fm"),
                                         "app.web_search('LASTFM')")
            section.append_item(menu_item)
        if get_network_available("MUSICBRAINZ"):
            menu_item = Gio.MenuItem.new(_("MusicBrainz"),
                                         "app.web_search('MUSICBRAINZ')")
            section.append_item(menu_item)
        if get_network_available("SPOTIFY"):
            menu_item = Gio.MenuItem.new(_("Spotify"),
                                         "app.web_search('SPOTIFY')")
            section.append_item(menu_item)
        if get_network_available("JAMENDO"):
            menu_item = Gio.MenuItem.new(_("Jamendo"),
                                         "app.web_search('JAMENDO')")
            section.append_item(menu_item)

#######################
# PRIVATE             #
#######################
    def __on_search_change_state(self, action, value):
        """
            Update search setting
            @param action as Gio.SimpleAction
            @param value as bool
        """
        App().settings.set_value("web-search", value)
        action.set_state(value)
