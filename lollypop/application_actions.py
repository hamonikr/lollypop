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

from gi.repository import Gio, GLib, Gtk

from lollypop.define import App, ScanType, Type


class ApplicationActions:
    """
        Application actions
    """

    def __init__(self):
        """
            Init actions
        """
        self.__restore_mini_player = False
        self.__special_shortcuts_count = 0
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.__on_settings_activate)
        App().add_action(settings_action)

        update_action = Gio.SimpleAction.new("update_db", None)
        update_action.connect("activate", self.__on_update_db_activate)
        App().add_action(update_action)

        fullscreen_action = Gio.SimpleAction.new("fullscreen", None)
        fullscreen_action = Gio.SimpleAction.new_stateful(
                    "fullscreen",
                    None,
                    GLib.Variant.new_boolean(False))
        App().player.connect("status-changed",
                             self.__on_status_changed,
                             fullscreen_action)
        fullscreen_action.set_enabled(False)
        fullscreen_action.connect("change-state",
                                  self.__on_fullscreen_change_state)
        App().add_action(fullscreen_action)

        equalizer_action = Gio.SimpleAction.new("equalizer", None)
        equalizer_action.connect("activate", self.__on_equalizer_activate)
        App().set_accels_for_action("app.equalizer", ["<Shift><Alt>e"])
        App().add_action(equalizer_action)

        miniplayer_action = Gio.SimpleAction.new_stateful(
                    "miniplayer",
                    None,
                    GLib.Variant.new_boolean(False))
        App().player.connect("status-changed",
                             self.__on_status_changed,
                             miniplayer_action)
        miniplayer_action.set_enabled(False)
        miniplayer_action.connect("change-state",
                                  self.__on_miniplayer_change_state)
        App().set_accels_for_action("app.miniplayer", ["<Shift><Alt>m"])
        App().add_action(miniplayer_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.__on_about_activate)
        App().add_action(about_action)

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self.__on_shortcuts_activate)
        App().add_action(shortcuts_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda x, y: App().quit(True))
        App().add_action(quit_action)

        seek_action = Gio.SimpleAction.new("seek",
                                           GLib.VariantType.new("i"))
        seek_action.connect("activate", self.__on_seek_action)
        App().add_action(seek_action)
        player_action = Gio.SimpleAction.new("shortcut",
                                             GLib.VariantType.new("s"))
        player_action.connect("activate", self.__on_player_action)
        App().add_action(player_action)

        search_action = Gio.SimpleAction.new("search",
                                             GLib.VariantType.new("s"))
        App().add_action(search_action)
        App().set_accels_for_action("app.search('')", ["<Control>f"])
        search_action.connect("activate", self.__on_search_activate)

        # Special action to queue a view reload
        reload_action = Gio.SimpleAction.new_stateful(
                "reload",
                None,
                GLib.Variant.new_boolean(False))
        App().add_action(reload_action)

        self.__setup_global_shortcuts()
        self.enable_special_shortcuts(True)

    def enable_special_shortcuts(self, enable):
        """
            Enable special shortcuts
            @param enable as bool
        """
        if enable:
            if self.__special_shortcuts_count == 0:
                if Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL:
                    App().set_accels_for_action("app.seek(10000)", ["Left"])
                    App().set_accels_for_action("app.seek(-10000)", ["Right"])
                else:
                    App().set_accels_for_action("app.seek(10000)", ["Right"])
                    App().set_accels_for_action("app.seek(-10000)", ["Left"])
                App().set_accels_for_action("app.shortcut::play_pause",
                                            ["c", "space"])
                App().set_accels_for_action("app.shortcut::play", ["x"])
                App().set_accels_for_action("app.shortcut::stop", ["v"])
                App().set_accels_for_action("app.shortcut::next", ["n"])
                App().set_accels_for_action("app.shortcut::prev", ["p"])
            self.__special_shortcuts_count += 1
        else:
            self.__special_shortcuts_count -= 1
            if self.__special_shortcuts_count == 0:
                App().set_accels_for_action("app.seek(10000)", [])
                App().set_accels_for_action("app.seek(-10000)", [])
                App().set_accels_for_action("app.shortcut::play_pause", [])
                App().set_accels_for_action("app.shortcut::play", [])
                App().set_accels_for_action("app.shortcut::stop", [])
                App().set_accels_for_action("app.shortcut::next", [])
                App().set_accels_for_action("app.shortcut::prev", [])

#######################
# PRIVATE             #
#######################
    def __setup_global_shortcuts(self):
        """
            Setup global shortcuts
        """
        if Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL:
            App().set_accels_for_action("app.shortcut::go_back",
                                        ["<Alt>Right", "Back"])
        else:
            App().set_accels_for_action("app.shortcut::go_back",
                                        ["<Alt>Left", "Back"])
        App().set_accels_for_action("app.shortcut::filter", ["<Control>i"])
        App().set_accels_for_action("app.shortcut::volume",
                                    ["<Shift><Alt>v"])
        App().set_accels_for_action("app.shortcut::lyrics",
                                    ["<Shift><Alt>l"])
        App().set_accels_for_action("app.shortcut::next_album", ["<Control>n"])
        App().set_accels_for_action("app.update_db", ["<Control>u"])
        App().set_accels_for_action("app.settings", ["<Control>comma"])
        App().set_accels_for_action("app.fullscreen", ["F11", "F7"])
        App().set_accels_for_action("app.mini", ["<Control>m"])
        App().set_accels_for_action("app.about", ["F3"])
        App().set_accels_for_action("app.shortcuts", ["F2"])
        App().set_accels_for_action("app.help", ["F1"])
        App().set_accels_for_action("app.quit", ["<Control>q"])
        App().set_accels_for_action("app.shortcut::loved", ["<Alt>l"])
        App().set_accels_for_action("app.shortcut::reload", ["<Control>r"])
        App().set_accels_for_action("app.shortcut::volume_up",
                                    ["<Shift><Alt>Up"])
        App().set_accels_for_action("app.shortcut::volume_down",
                                    ["<Shift><Alt>Down"])

    def __on_update_db_activate(self, *ignore):
        """
            Search for new music
        """
        if App().window:
            App().scanner.update(ScanType.FULL)

    def __on_about_activate_response(self, dialog, response_id):
        """
            Destroy about dialog when closed
            @param dialog as Gtk.Dialog
            @param response id as int
        """
        dialog.destroy()

    def __on_search_activate(self, action, value):
        """
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        search = value.get_string()
        App().window.container.show_view([Type.SEARCH], search)

    def __on_fullscreen_change_state(self, action, value):
        """
            Show a fullscreen window with cover and artist information
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        action.set_state(value)
        App().fullscreen()

    def __on_equalizer_activate(self, action, value):
        """
            Show equalizer view
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        App().window.container.show_view([Type.EQUALIZER])

    def __on_miniplayer_change_state(self, action, value):
        """
            Show miniplayer view
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        def replace_window():
            App().window.hide()
            App().window.show()
            App().window.set_opacity(1)

        App().window.set_opacity(0)
        action.set_state(value)
        if value:
            self.__restore_mini_player = App().window.miniplayer is not None
            App().window.show_miniplayer(True, True)
            App().window.toolbar.hide_info_and_buttons(True)
            App().window.unmaximize()
            App().window.resize(1, 1)
        else:
            if self.__restore_mini_player:
                App().window.miniplayer.reveal(False)
            else:
                App().window.miniplayer.reveal(False)
                App().window.show_miniplayer(False)
                App().window.toolbar.hide_info_and_buttons(False)
            size = App().settings.get_value("window-size")
            maximized = App().settings.get_value("window-maximized")
            App().window.resize(size[0], size[1])
            if maximized:
                GLib.idle_add(App().window.maximize)
        # Big hack, wait unmaximize/maximize to finish
        GLib.timeout_add(250, replace_window)

    def __on_settings_activate(self, action, value):
        """
            Show settings dialog
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        def do():
            from lollypop.dialog_settings import SettingsDialog
            dialog = SettingsDialog()
            dialog.show()
        # Settings dialog is heavy to load, let action close
        GLib.idle_add(do)

    def __on_about_activate(self, action, value):
        """
            Setup about dialog
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        def get_instance(children, instance):
            for child in children:
                if isinstance(child, instance):
                    return child
            return None
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/AboutDialog.ui")
        about = builder.get_object("about_dialog")
        about.set_transient_for(App().window)
        about.connect("response", self.__on_about_activate_response)
        about.show()

    def __on_shortcuts_activate(self, action, value):
        """
            Show shorctus
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/Shortcuts.ui")
        builder.get_object("shortcuts").set_transient_for(App().window)
        builder.get_object("shortcuts").show()

    def __on_status_changed(self, player, action):
        """
            Activate action if wanted
            @param player as Player
            @param action as Gio.SimpleAction
        """
        action.set_enabled(player.current_track.id is not None)

    def __on_seek_action(self, action, value):
        """
            Seek in stream
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        ms = value.get_int32()
        position = App().player.position
        seek = position + ms
        if seek < 0:
            seek = 0
        if seek > App().player.current_track.duration:
            seek = App().player.current_track.duration - 2
        App().player.seek(seek)

    def __on_player_action(self, action, value):
        """
            Change player state
            @param action as Gio.SimpleAction
            @param value as GLib.Variant
        """
        string = value.get_string()
        if string == "play_pause":
            App().player.play_pause()
        elif string == "play":
            App().player.play()
        elif string == "stop":
            App().player.stop()
        elif string == "next":
            App().player.next()
        elif string == "next_album":
            App().player.skip_album()
        elif string == "prev":
            App().player.prev()
        elif string == "go_back":
            if App().window.toolbar.playback.back_button.get_sensitive():
                App().window.container.go_back()
        elif string == "reload":
            App().window.container.reload_view()
        elif string == "volume_up":
            App().player.set_volume(App().player.volume + 0.1)
        elif string == "volume_down":
            App().player.set_volume(App().player.volume - 0.1)
        elif string == "filter":
            App().window.container.show_filter()
        elif string == "loved":
            track = App().player.current_track
            if track.id is not None and track.id >= 0:
                if track.loved < 1:
                    loved = track.loved + 1
                else:
                    loved = Type.NONE
                track.set_loved(loved)
                if track.loved == 1:
                    heart = "❤"
                elif track.loved == -1:
                    heart = "⏭"
                else:
                    heart = "♡"
                App().notify.send("Lollypop", "%s - %s: %s" %
                                  (", ".join(track.artists),
                                   track.name,
                                   heart))
