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

from gi.repository import Gtk, GLib, Gdk, Handy

from gettext import gettext as _

from lollypop.define import App, ScanType, NetworkAccessACL
from lollypop.widgets_row_device import DeviceRow
from lollypop.helper_passwords import PasswordsHelper


class SettingsDialog:
    """
        Dialog showing lollypop settings
    """

    __BOOLEAN = ["dark-ui", "artist-artwork", "auto-update", "background-mode",
                 "save-state", "import-playlists", "save-to-tags",
                 "show-compilations", "transitions", "network-access",
                 "recent-youtube-dl", "import-advanced-artist-tags",
                 "force-single-column", "hd-artwork"]

    __RANGE = ["cover-size", "transitions-duration"]

    __COMBO = ["replay-gain", "orderby"]
    __ENTRY = ["invidious-server", "cs-api-key", "listenbrainz-user-token"]
    __LOCKED = ["data", "lyrics", "search", "playback"]

    def __init__(self):
        """
            Init dialog
        """
        self.__timeout_id = None
        self.__choosers = []
        self.__locked = []
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/SettingsDialog.ui")
        self.__settings_dialog = builder.get_object("settings_dialog")
        self.__progress = builder.get_object("progress")
        for setting in self.__BOOLEAN:
            button = builder.get_object("%s_boolean" % setting)
            value = App().settings.get_value(setting)
            button.set_state(value)
        for setting in self.__ENTRY:
            entry = builder.get_object("%s_entry" % setting)
            value = App().settings.get_value(setting).get_string()
            entry.set_text(value)
        for setting in self.__RANGE:
            widget = builder.get_object("%s_range" % setting)
            value = App().settings.get_value(setting).get_int32()
            widget.set_value(value)
        for setting in self.__COMBO:
            widget = builder.get_object("%s_combo" % setting)
            value = App().settings.get_enum(setting)
            widget.set_active(value)
        for locked in self.__LOCKED:
            widget = builder.get_object(locked)
            self.__locked.append(widget)
        self.__update_locked()
        self.__music_group = builder.get_object("music_group")
        for uri in App().settings.get_music_uris():
            button = self.__get_new_chooser(uri)
            self.__music_group.add(button)
        for device in App().settings.get_value("devices"):
            row = DeviceRow(device)
            builder.get_object("device_group").add(row)
        acl = App().settings.get_value("network-access-acl").get_int32()
        for key in NetworkAccessACL.keys():
            if acl & NetworkAccessACL[key]:
                builder.get_object("%s_button" % key).set_state(True)
        artists_count = App().artists.count()
        albums_count = App().albums.count()
        tracks_count = App().tracks.count()
        builder.get_object("stat_artists").set_title(
            _("Artists count: %s") % artists_count)
        builder.get_object("stat_albums").set_title(
            _("Albums count: %s") % albums_count)
        builder.get_object("stat_tracks").set_title(
            _("Tracks count: %s") % tracks_count)
        self.__settings_dialog.set_transient_for(App().window)
        self.__settings_dialog.connect("destroy", self.__on_destroy)
        passwords_helper = PasswordsHelper()
        passwords_helper.get("LASTFM", self.__on_get_password,
                             builder.get_object("lastfm_button"))
        passwords_helper.get("LIBREFM", self.__on_get_password,
                             builder.get_object("librefm_button"))
        builder.connect_signals(self)
        self.__controller = Gtk.EventControllerKey.new(self.__settings_dialog)
        self.__controller.connect("key-released", self.__on_key_released)

    def show(self):
        """
            Show dialog
        """
        self.__settings_dialog.show()

#######################
# PROTECTED           #
#######################
    def _on_boolean_state_set(self, widget, state):
        """
            Save setting
            @param widget as Gtk.Switch
            @param state as bool
        """
        setting = widget.get_name()
        App().settings.set_value(setting,
                                 GLib.Variant("b", state))
        if setting == "dark-ui":
            if not App().player.is_party:
                settings = Gtk.Settings.get_default()
                settings.set_property("gtk-application-prefer-dark-theme",
                                      state)
        elif setting == "artist-artwork":
            App().window.container.reload_view()
        elif setting == "network-access":
            self.__update_locked()

    def _on_range_changed(self, widget):
        """
            Save value
            @param widget as Gtk.Range
        """
        setting = widget.get_name()
        value = widget.get_value()
        App().settings.set_value(setting, GLib.Variant("i", value))
        if setting == "cover-size":
            if self.__timeout_id is not None:
                GLib.source_remove(self.__timeout_id)
            self.__timeout_id = GLib.timeout_add(500,
                                                 self.__update_coversize,
                                                 widget)

    def _on_combo_changed(self, widget):
        """
            Save value
            @param widget as Gtk.ComboBoxText
        """
        setting = widget.get_name()
        value = widget.get_active()
        App().settings.set_enum(setting, value)
        if setting == "replay-gain":
            for plugin in App().player.plugins:
                plugin.build_audiofilter()
            App().player.reload_track()

    def _on_clean_artwork_cache_clicked(self, button):
        """
            Clean artwork cache
            @param button as Gtk.Button
        """
        App().task_helper.run(App().art.clean_all_cache)
        button.set_sensitive(False)

    def _on_google_api_key_changed(self, entry):
        """
            Save Key
            @param entry as Gtk.Entry
        """
        value = entry.get_text().strip()
        App().settings.set_value("cs-api-key", GLib.Variant("s", value))

    def _on_musicbrainz_api_key_changed(self, entry):
        """
            Save Key
            @param entry as Gtk.Entry
        """
        value = entry.get_text().strip()
        App().settings.set_value("listenbrainz-user-token",
                                 GLib.Variant("s", value))

    def _on_connect_button_clicked(self, button):
        """
            Connect to API
            @param button as Gtk.Button
        """
        def on_destroy(assistant):
            self.__settings_dialog.show()

        name = button.get_name()
        if button.get_tooltip_text():
            button.set_tooltip_text("")
            button.set_label(_("Connect"))
            App().ws_director.token_ws.clear_token(button.get_name(), True)
        else:
            if name == "GOOGLE":
                from lollypop.assistant_google import GoogleAssistant
                assistant = GoogleAssistant()
            elif name in ["LASTFM", "LIBREFM"]:
                from lollypop.assistant_lastfm import LastfmAssistant
                assistant = LastfmAssistant(name)
            else:
                from lollypop.assistant_musicbrainz import MusicbrainzAssistant
                assistant = MusicbrainzAssistant()
            assistant.set_transient_for(App().window)
            assistant.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            assistant.show()
            assistant.connect("destroy", on_destroy)
            self.__settings_dialog.hide()
            button.set_label(_("Disconnect"))

    def _on_invidious_entry_changed(self, entry):
        """
            Update invidious server setting
            @param entry as Gtk.entry
        """
        uri = entry.get_text()
        App().settings.set_value("invidious-server", GLib.Variant("s", uri))

    def _on_acl_state_set(self, widget, state):
        """
            Save network acl state
            @param widget as Gtk.Switch
            @param state as bool
        """
        key = widget.get_name()
        acl = App().settings.get_value("network-access-acl").get_int32()
        if state:
            acl |= NetworkAccessACL[key]
        else:
            acl &= ~NetworkAccessACL[key]
        acl = App().settings.set_value("network-access-acl",
                                       GLib.Variant("i", acl))

    def _on_add_button_clicked(self, button):
        """
            Add a new chooser
            @param button as Gtk.Button
        """
        button = self.__get_new_chooser(None)
        self.__music_group.add(button)

    def _on_reset_button_clicked(self, button):
        """
            Reset database
            @param button as Gtk.Button
        """
        if button.get_style_context().has_class("red"):
            button.set_label(_("Reset collection"))
            button.set_sensitive(False)
            button.get_style_context().remove_class("red")
            App().scanner.reset_database()
        else:
            button.get_style_context().add_class("red")
            button.set_label(_("Are you sure?"))

#######################
# PRIVATE             #
#######################
    def __update_locked(self):
        """
            Update locked widgets
        """
        network_access = App().settings.get_value("network-access")
        for widget in self.__locked:
            widget.set_sensitive(network_access)

    def __get_new_chooser(self, uri):
        """
            Get a new chooser
            @param uri as str
            @return Handy.ActionRow
        """
        chooser = Gtk.FileChooserButton()
        chooser.show()
        chooser.set_local_only(False)
        chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        chooser.set_valign(Gtk.Align.CENTER)
        chooser.set_hexpand(True)
        self.__choosers.append(chooser)
        if uri is not None:
            chooser.set_uri(uri)
        button = Gtk.Button.new_from_icon_name("list-remove-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.show()
        button.set_valign(Gtk.Align.CENTER)
        row = Handy.ActionRow()
        row.show()
        row.add(chooser)
        row.add(button)
        button.connect("clicked", lambda x: self.__choosers.remove(chooser))
        button.connect("clicked", lambda x: row.destroy())
        return row

    def __update_coversize(self, widget):
        """
            Update cover size
            @param widget as Gtk.Range
        """
        self.__timeout_id = None
        App().task_helper.run(App().art.clean_all_cache)
        App().art.update_art_size()
        App().window.container.reload_view()

    def __on_destroy(self, widget):
        """
            Save settings and update if needed
            @param widget as Gtk.Window
        """
        # Music uris
        uris = []
        default = GLib.get_user_special_dir(
            GLib.UserDirectory.DIRECTORY_MUSIC)
        if default is not None:
            default = GLib.filename_to_uri(default)
        else:
            default = None
        for chooser in self.__choosers:
            uri = chooser.get_uri()
            if uri is not None and uri not in uris:
                uris.append(uri)
        if not uris:
            uris.append(default)

        previous = App().settings.get_value("music-uris")
        App().settings.set_value("music-uris", GLib.Variant("as", uris))

        if set(previous) != set(uris):
            to_delete = [uri for uri in previous if uri not in uris]
            to_scan = [uri for uri in uris if uri not in previous]
            if to_delete:
                App().scanner.update(ScanType.FULL)
            elif to_scan:
                App().scanner.update(ScanType.NEW_FILES, to_scan)

    def __on_get_password(self, attributes, password, service, button):
        """
            Set button state
            @param attributes as {}
            @param password as str
            @param service as str
            @param button as Gtk.Button
        """
        if attributes is not None:
            button.set_label(_("Disconnect"))
            button.set_tooltip_text("%s:%s" % (attributes["login"], password))

    def __on_key_released(self, event_controller, keyval, keycode, state):
        """
            Quit on escape
            @param event_controller as Gtk.EventController
            @param keyval as int
            @param keycode as int
            @param state as Gdk.ModifierType
        """
        if keyval == Gdk.KEY_Escape:
            self.__settings_dialog.destroy()
