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

from gi.repository import Gio, GLib, Gtk, Gdk

from gettext import gettext as _

from lollypop.define import App, StorageType, CACHE_PATH
from lollypop.objects_track import Track
from lollypop.objects_album import Album
from lollypop.logger import Logger
from lollypop.dialog_apps import AppsDialog


class ActionsMenu(Gio.Menu):
    """
        ActionsMenu menu for album
    """

    def __init__(self, object):
        """
            Init edit menu
            @param object as Album/Track
        """
        Gio.Menu.__init__(self)
        # Ignore genre_ids/artist_ids
        if isinstance(object, Album):
            self.__object = Album(object.id)
        else:
            self.__object = Track(object.id)
        self.__set_save_action()
        if self.__object.storage_type & StorageType.COLLECTION and\
                not GLib.file_test("/app", GLib.FileTest.EXISTS):
            self.__set_open_action()

#######################
# PRIVATE             #
#######################
    def __set_save_action(self):
        """
            Set save action
        """
        if not self.__object.storage_type & (StorageType.SAVED |
                                             StorageType.COLLECTION):
            save_action = Gio.SimpleAction(name="save_album_action")
            App().add_action(save_action)
            save_action.connect("activate",
                                self.__on_save_action_activate,
                                True)
            menu_item = Gio.MenuItem.new(_("Save in collection"),
                                         "app.save_album_action")
            menu_item.set_attribute_value("close", GLib.Variant("b", True))
            self.append_item(menu_item)
        elif self.__object.storage_type & StorageType.SAVED:
            save_action = Gio.SimpleAction(name="remove_album_action")
            App().add_action(save_action)
            save_action.connect("activate",
                                self.__on_save_action_activate,
                                False)
            menu_item = Gio.MenuItem.new(_("Remove from collection"),
                                         "app.remove_album_action")
            menu_item.set_attribute_value("close", GLib.Variant("b", True))
            self.append_item(menu_item)
        if self.__object.is_web:
            clean_action = Gio.SimpleAction(name="clean_album_action")
            App().add_action(clean_action)
            clean_action.connect("activate",
                                 self.__on_clean_action_activate)
            menu_item = Gio.MenuItem.new(_("Clean cache"),
                                         "app.clean_album_action")
            menu_item.set_attribute_value("close", GLib.Variant("b", True))
            self.append_item(menu_item)
        if isinstance(self.__object, Album) and\
                not self.__object.storage_type & StorageType.COLLECTION:
            buy_action = Gio.SimpleAction(name="buy_album_action")
            App().add_action(buy_action)
            buy_action.connect("activate",
                               self.__on_buy_action_activate)
            menu_item = Gio.MenuItem.new(_("Buy this album"),
                                         "app.buy_album_action")
            menu_item.set_attribute_value("close", GLib.Variant("b", True))
            self.append_item(menu_item)

    def __set_open_action(self):
        """
            Set edit action
        """
        open_tag_action = Gio.SimpleAction(name="open_tag_action")
        App().add_action(open_tag_action)
        open_tag_action.connect("activate", self.__on_open_tag_action_activate)
        menu_item = Gio.MenuItem.new(_("Open with…"),
                                     "app.open_tag_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)

    def __on_buy_action_activate(self, action, variant):
        """
            Launch a browser for Qobuz
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        artists = " ".join(self.__object.artists)
        search = "%s %s" % (artists, self.__object.name)
        uri = "https://www.qobuz.com/search?q=%s" % (
            GLib.uri_escape_string(search, None, True))
        Gtk.show_uri_on_window(App().window,
                               uri,
                               Gdk.CURRENT_TIME)

    def __on_clean_action_activate(self, action, variant):
        """
            clean album cache
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        try:
            if isinstance(self.__object, Album):
                tracks = self.__object.tracks
            else:
                tracks = [self.__object]
            for track in tracks:
                escaped = GLib.uri_escape_string(track.uri, None, True)
                f = Gio.File.new_for_path("%s/web_%s" % (CACHE_PATH, escaped))
                if f.query_exists():
                    f.delete(None)
        except Exception as e:
            Logger.error("ActionsMenu::__on_clean_action_activate():", e)

    def __on_save_action_activate(self, action, variant, save):
        """
            Save album to collection
            @param Gio.SimpleAction
            @param GLib.Variant
            @param save as bool
        """
        if isinstance(self.__object, Album):
            self.__object.save(save)
        else:
            album = self.__object.album
            album.save_track(save, self.__object)
        if not save:
            App().tracks.del_non_persistent()
            App().tracks.clean()
            App().albums.clean()
            App().artists.clean()
            App().genres.clean()

    def __on_open_tag_action_activate(self, action, variant):
        """
            Run tag editor
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        try:
            def launch_app(commandline, f):
                if f.query_exists():
                    args = []
                    for item in commandline.split():
                        if item in ["%U", "%u"]:
                            args.append(f.get_uri())
                        elif item in ["%F", "%f"]:
                            args.append(f.get_path())
                        else:
                            args.append(item)
                    commands = [args,
                                ["flatpak-spawn", "--host"] + args]
                    for cmd in commands:
                        try:
                            (pid, stdin, stdout, stderr) = GLib.spawn_async(
                                cmd, flags=GLib.SpawnFlags.SEARCH_PATH |
                                GLib.SpawnFlags.STDOUT_TO_DEV_NULL,
                                standard_input=False,
                                standard_output=False,
                                standard_error=False
                            )
                            GLib.spawn_close_pid(pid)
                            break
                        except Exception as e:
                            Logger.error("ActionsMenu::launch_app(): %s", e)

            def on_response(dialog, response_id, f):
                if response_id == Gtk.ResponseType.OK:
                    if dialog.commandline is not None:
                        launch_app(dialog.commandline, f)
                dialog.destroy()

            f = Gio.File.new_for_uri(self.__object.uri)
            dialog = AppsDialog(f)
            dialog.connect("response", on_response, f)
            dialog.run()
        except Exception as e:
            Logger.error("ActionsMenu::__on_open_tag_action_activate(): %s", e)
