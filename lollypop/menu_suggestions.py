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

from lollypop.define import App, StorageType
from lollypop.utils import get_network_available


class SuggestionsMenu(Gio.Menu):
    """
        Contextual menu for suggestions
    """
    def __init__(self, header=False):
        """
            Init search menu
            @param header as bool
        """
        Gio.Menu.__init__(self)
        section = Gio.Menu()
        if header:
            from lollypop.menu_header import MenuHeader
            self.append_item(MenuHeader(
                                 _("Suggestions"),
                                 "org.gnome.Lollypop-suggestions-symbolic"))
        mask = App().settings.get_value("suggestions-mask").get_int32()
        action = Gio.SimpleAction.new_stateful(
            "spotify_new_releases",
            None,
            GLib.Variant("b", mask & StorageType.SPOTIFY_NEW_RELEASES))
        action.connect("change-state",
                       self.__on_change_state,
                       StorageType.SPOTIFY_NEW_RELEASES)
        action.set_enabled(get_network_available("SPOTIFY"))
        App().add_action(action)
        menu_item = Gio.MenuItem.new(_("New releases on Spotify"),
                                     "app.spotify_new_releases")
        section.append_item(menu_item)
        action = Gio.SimpleAction.new_stateful(
            "spotify_similars",
            None,
            GLib.Variant("b", mask & StorageType.SPOTIFY_SIMILARS))
        action.connect("change-state",
                       self.__on_change_state,
                       StorageType.SPOTIFY_SIMILARS)
        action.set_enabled(get_network_available("SPOTIFY"))
        App().add_action(action)
        menu_item = Gio.MenuItem.new(_("Suggestions from Spotify"),
                                     "app.spotify_similars")
        section.append_item(menu_item)
        action = Gio.SimpleAction.new_stateful(
            "deezer_charts",
            None,
            GLib.Variant("b", mask & StorageType.DEEZER_CHARTS))
        action.connect("change-state",
                       self.__on_change_state,
                       StorageType.DEEZER_CHARTS)
        action.set_enabled(get_network_available("DEEZER"))
        App().add_action(action)
        menu_item = Gio.MenuItem.new(_("Top albums on Deezer"),
                                     "app.deezer_charts")
        section.append_item(menu_item)
        self.append_section(_("From the Web"), section)

#######################
# PRIVATE             #
#######################
    def __clean_storage_type(self, state, mask):
        """
            Clear storage type if state false
            @param state as bool
            @param mask as int
        """
        if state:
            return
        album_ids = App().albums.get_for_storage_type(mask)
        for album_id in album_ids:
            # EPHEMERAL with not tracks will be cleaned below
            App().albums.set_storage_type(album_id,
                                          StorageType.EPHEMERAL)
            App().tracks.remove_album(album_id)
        App().tracks.clean()
        App().albums.clean()
        App().artists.clean()

    def __handle_mask_change(self, state, mask):
        """
            Update mask value in settings
            @param state as bool
            @param mask as int
        """
        if App().ws_director.collection_ws is not None:
            if not App().ws_director.collection_ws.stop():
                GLib.timeout_add(500, self.__handle_mask_change, state, mask)
                return
        suggestion_mask = App().settings.get_value(
            "suggestions-mask").get_int32()
        if state:
            suggestion_mask |= mask
        else:
            suggestion_mask &= ~mask
        App().settings.set_value("suggestions-mask",
                                 GLib.Variant("i", suggestion_mask))
        self.__clean_storage_type(state, mask)
        if App().ws_director.collection_ws is not None:
            App().ws_director.collection_ws.start()

    def __on_change_state(self, action, state, mask):
        """
            Update settings value
            @param action as Gio.SimpleAction
            @param state as bool
            @param mask as int
        """
        action.set_state(state)
        self.__handle_mask_change(state, mask)
