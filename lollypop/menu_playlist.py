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

from gi.repository import Gio, Gtk

from gettext import gettext as _

from lollypop.define import App, MARGIN_SMALL, Type


class PlaylistMenu(Gio.Menu):
    """
        A playlist menu
    """

    def __init__(self, playlist_id, view_type, header=False):
        """
            Init variable
            @param playlist_id as int
            @param view_type as ViewType
            @param header as bool
        """
        Gio.Menu.__init__(self)
        self.__playlist_id = playlist_id
        name = App().playlists.get_name(playlist_id)
        if header:
            from lollypop.menu_header import RoundedMenuHeader
            artwork_name = "playlist_%s" % name
            self.append_item(RoundedMenuHeader(name, artwork_name))
        menu = Gio.Menu()
        save_action = Gio.SimpleAction(name="save_pl_action")
        App().add_action(save_action)
        save_action.connect("activate", self.__on_save_action_activate)
        menu.append(_("Save playlist"), "app.save_pl_action")
        if App().ws_director.lastfm_ws is not None and\
                playlist_id == Type.LOVED:
            lastfm_action = Gio.SimpleAction(name="lastfm_action")
            App().add_action(lastfm_action)
            lastfm_action.connect("activate",
                                  self.__on_lastfm_action_activate)
            menu.append(_("Sync from Last.FM"), "app.lastfm_action")
        if playlist_id >= 0:
            if not App().playlists.get_track_uris(playlist_id):
                smart_action = Gio.SimpleAction(name="smart_action")
                App().add_action(smart_action)
                smart_action.connect("activate",
                                     self.__on_smart_action_activate)
                menu.append(_("Manage smart playlist"), "app.smart_action")
            remove_action = Gio.SimpleAction(name="remove_pl_action")
            App().add_action(remove_action)
            remove_action.connect("activate", self.__on_remove_action_activate)
            menu.append(_("Remove playlist"), "app.remove_pl_action")
        from lollypop.menu_playback import PlaylistPlaybackMenu
        playback_menu = PlaylistPlaybackMenu(playlist_id)
        self.append_section(_("Playlist"), playback_menu)
        section = Gio.Menu()
        self.append_section(_("Add to"), section)
        from lollypop.menu_sync import SyncPlaylistsMenu
        section.append_submenu(_("Devices"),
                               SyncPlaylistsMenu(playlist_id))
        self.append_section(_("Edit"), menu)

#######################
# PRIVATE             #
#######################
    def __on_smart_action_activate(self, action, variant):
        """
            Show smart playlist editor
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        App().window.container.show_smart_playlist_editor(self.__playlist_id)

    def __on_lastfm_action_activate(self, action, variant):
        """
            Sync playlist with Last.FM
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        App().ws_director.lastfm_ws.sync_loved_tracks()

    def __on_remove_action_activate(self, action, variant):
        """
            Remove playlist
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        def remove_playlist():
            App().playlists.remove(self.__playlist_id)
        from lollypop.app_notification import AppNotification
        notification = AppNotification(_("Remove this playlist?"),
                                       [_("Confirm")],
                                       [remove_playlist])
        notification.show()
        App().window.container.add_overlay(notification)
        notification.set_reveal_child(True)

    def __on_save_action_activate(self, action, variant):
        """
            Save playlist to file
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        filechooser = Gtk.FileChooserNative.new(_("Save playlist"),
                                                App().window,
                                                Gtk.FileChooserAction.SAVE,
                                                _("Save"),
                                                _("Cancel"))
        filter = Gtk.FileFilter.new()
        filter.set_name("audio/x-mpegurl")
        filter.add_mime_type("audio/x-mpegurl")
        filechooser.add_filter(filter)
        filechooser.set_do_overwrite_confirmation(True)
        name = App().playlists.get_name(self.__playlist_id)
        filechooser.set_current_name("%s.m3u" % name)
        filechooser.connect("response", self.__on_save_response)
        filechooser.run()

    def __on_save_response(self, dialog, response_id):
        """
            Save playlist
            @param dialog as Gtk.NativeDialog
            @param response_id as int
        """
        if response_id == Gtk.ResponseType.ACCEPT:
            uri = dialog.get_file().get_uri()
            App().playlists.set_sync_uri(self.__playlist_id, uri)
            App().playlists.sync_to_disk(self.__playlist_id, True)


class PlaylistMenuExt(Gtk.Grid):
    """
        Additional widgets for playlist menu
    """

    def __init__(self, playlist_id):
        """
            Init widget
            @param playlist_id as int
        """
        Gtk.Grid.__init__(self)
        self.set_margin_top(MARGIN_SMALL)
        self.set_row_spacing(MARGIN_SMALL)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        entry = Gtk.Entry()
        entry.set_margin_top(MARGIN_SMALL)
        entry.set_margin_start(MARGIN_SMALL)
        entry.set_margin_end(MARGIN_SMALL)
        entry.set_margin_bottom(MARGIN_SMALL)
        entry.set_property("hexpand", True)
        entry.set_text(App().playlists.get_name(playlist_id))
        entry.connect("changed", self.__on_entry_changed, playlist_id)
        entry.show()
        self.add(entry)

    @property
    def section(self):
        return None

    @property
    def submenu_name(self):
        return None

#######################
# PRIVATE             #
#######################
    def __on_entry_changed(self, entry, playlist_id):
        """
            Update playlist name
            @param entry as Gtk.Entry
            @param playlist_id as int
        """
        new_name = entry.get_text()
        App().playlists.rename(playlist_id, new_name)
