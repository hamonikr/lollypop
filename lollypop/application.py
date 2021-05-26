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

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstAudio", "1.0")
gi.require_version("GstPbutils", "1.0")
gi.require_version("TotemPlParser", "1.0")
gi.require_version("Handy", "1")
from gi.repository import Gtk, Gio, GLib, Gdk, Gst, GstPbutils, Handy
Gst.init(None)
GstPbutils.pb_utils_init()

from threading import current_thread
from pickle import dump
from signal import signal, SIGINT, SIGTERM

from lollypop.utils import init_proxy_from_gnome
from lollypop.application_actions import ApplicationActions
from lollypop.application_cmdline import ApplicationCmdline
from lollypop.utils_file import install_youtube_dl
from lollypop.define import LOLLYPOP_DATA_PATH, StorageType
from lollypop.database import Database
from lollypop.player import Player
from lollypop.inhibitor import Inhibitor
from lollypop.artwork import Artwork
from lollypop.artwork_album import AlbumArtwork
from lollypop.artwork_artist import ArtistArtwork
from lollypop.logger import Logger
from lollypop.ws_director import DirectorWebService
from lollypop.sqlcursor import SqlCursor
from lollypop.settings import Settings
from lollypop.database_cache import CacheDatabase
from lollypop.database_albums import AlbumsDatabase
from lollypop.database_artists import ArtistsDatabase
from lollypop.database_genres import GenresDatabase
from lollypop.database_tracks import TracksDatabase
from lollypop.notification import NotificationManager
from lollypop.playlists import Playlists
from lollypop.helper_task import TaskHelper
from lollypop.helper_art import ArtHelper
from lollypop.collection_scanner import CollectionScanner


class Application(Gtk.Application, ApplicationActions, ApplicationCmdline):
    """
        Lollypop application:
            - Handle appmenu
            - Handle command line
            - Create main window
    """

    def __init__(self, version, data_dir, app_id):
        """
            Create application
            @param version as str
            @param data_dir as str
            @param app_id as str
        """
        Gtk.Application.__init__(
            self,
            application_id=app_id,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        ApplicationCmdline.__init__(self, version)
        self.__app_id = app_id
        self.__data_dir = data_dir
        self.set_property("register-session", True)
        signal(SIGINT, lambda a, b: self.quit())
        signal(SIGTERM, lambda a, b: self.quit())
        # Set main thread name
        # We force it to current python 3.6 name, to be sure in case of
        # change in python
        current_thread().setName("MainThread")
        (self.__proxy_host, self.__proxy_port) = init_proxy_from_gnome()
        GLib.setenv("PULSE_PROP_media.role", "music", True)
        GLib.setenv("PULSE_PROP_application.icon_name",
                    "org.gnome.Lollypop", True)
        # Flatpak hacks
        if GLib.file_test("/app", GLib.FileTest.EXISTS):
            # Set /tmp for GLib, /tmp not accessible in flatpak
            tmp = GLib.environ_getenv(GLib.get_environ(), "XDG_RUNTIME_DIR")
            GLib.setenv("TMPDIR", "%s/app/org.gnome.Lollypop" % tmp, True)
        self.cursors = {}
        self.shown_sidebar_tooltip = False
        self.__window = None
        self.__fs_window = None
        settings = Gio.Settings.new("org.gnome.desktop.interface")
        self.animations = settings.get_value("enable-animations").get_boolean()
        GLib.set_application_name("Lollypop")
        GLib.set_prgname("lollypop")
        self.connect("activate", self.__on_activate)
        self.connect("shutdown", lambda a: self.__save_state())
        if GLib.environ_getenv(GLib.get_environ(), "DEBUG_LEAK") is not None:
            import gc
            gc.set_debug(gc.DEBUG_LEAK)

    def init(self):
        """
            Init main application
        """
        self.settings = Settings.new()
        # Mount enclosing volume as soon as possible
        uris = self.settings.get_music_uris()
        try:
            for uri in uris:
                if uri.startswith("file:/"):
                    continue
                f = Gio.File.new_for_uri(uri)
                f.mount_enclosing_volume(Gio.MountMountFlags.NONE,
                                         None,
                                         None,
                                         None)
        except Exception as e:
            Logger.error("Application::init(): %s" % e)

        cssProviderFile = Gio.File.new_for_uri(
            "resource:///org/gnome/Lollypop/application.css")
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_file(cssProviderFile)
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
        # Devel version, load devel theme
        if self.__app_id is None:
            css = "*:selected{ background-color: red; }"
            cssProvider = Gtk.CssProvider()
            cssProvider.load_from_data(css.encode("utf-8"))
            screen = Gdk.Screen.get_default()
            styleContext = Gtk.StyleContext()
            styleContext.add_provider_for_screen(
                screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        self.db = Database()
        self.cache = CacheDatabase()
        self.playlists = Playlists()
        self.albums = AlbumsDatabase(self.db)
        self.artists = ArtistsDatabase(self.db)
        self.genres = GenresDatabase(self.db)
        self.tracks = TracksDatabase(self.db)
        self.player = Player()
        self.inhibitor = Inhibitor()
        self.scanner = CollectionScanner()
        self.notify = NotificationManager()
        self.task_helper = TaskHelper()
        self.art_helper = ArtHelper()
        self.art = Artwork()
        self.art.update_art_size()
        self.album_art = AlbumArtwork()
        self.artist_art = ArtistArtwork()
        self.ws_director = DirectorWebService()
        self.ws_director.start()
        if not self.settings.get_value("disable-mpris"):
            from lollypop.mpris import MPRIS
            MPRIS(self)

        settings = Gtk.Settings.get_default()
        self.__gtk_dark = settings.get_property(
            "gtk-application-prefer-dark-theme")
        if not self.__gtk_dark:
            dark = self.settings.get_value("dark-ui")
            settings.set_property("gtk-application-prefer-dark-theme", dark)
        ApplicationActions.__init__(self)
        monitor = Gio.NetworkMonitor.get_default()
        if monitor.get_network_available() and\
                not monitor.get_network_metered() and\
                self.settings.get_value("recent-youtube-dl"):
            self.task_helper.run(install_youtube_dl)

    def do_startup(self):
        """
            Init application
        """
        Gtk.Application.do_startup(self)
        Handy.init()
        if self.__window is None:
            from lollypop.window import Window
            self.init()
            self.__window = Window()
            self.__window.connect("delete-event", self.__hide_on_delete)
            self.__window.setup()
            self.__window.show()
            self.player.restore_state()

    def quit(self, vacuum=False, wait=100):
        """
            Quit Lollypop
            @param vacuum as bool
            @param wait as int
        """
        self.__window.container.stop()
        self.__window.hide()
        # Force stop after some tries
        if wait < 1000 and not self.ws_director.stop():
            GLib.timeout_add(wait, self.quit, vacuum, wait + 100)
            return
        self.album_art.cancellable.cancel()
        self.artist_art.cancellable.cancel()
        if self.settings.get_value("save-state"):
            self.__window.container.stack.save_history()
        # Then vacuum db
        if vacuum:
            self.__vacuum()
            self.art.clean_artwork()
        Gio.Application.quit(self)
        if GLib.environ_getenv(GLib.get_environ(), "DEBUG_LEAK") is not None:
            import gc
            gc.collect()
            for x in gc.garbage:
                s = str(x)
                print(type(x), "\n  ", s)

    def fullscreen(self):
        """
            Go fullscreen
        """
        def on_destroy(window):
            self.__fs_window = None
            self.__window.show()

        if self.__fs_window is None:
            from lollypop.fullscreen import FullScreen
            self.__fs_window = FullScreen()
            self.__fs_window.delayed_init()
            self.__fs_window.show()
            self.__fs_window.connect("destroy", on_destroy)
            self.__window.hide()
        else:
            self.__fs_window.destroy()

    @property
    def proxy_host(self):
        """
            Get proxy host
            @return str
        """
        return self.__proxy_host

    @property
    def proxy_port(self):
        """
            Get proxy port
            @return int
        """
        return self.__proxy_port

    @property
    def devices(self):
        """
            Get available devices
            Merge connected and known
            @return [str]
        """
        devices = self.__window.toolbar.end.devices_popover.devices
        devices += list(self.settings.get_value("devices"))
        result = []
        # Do not use set() + filter() because we want to keep order
        for device in devices:
            if device not in result and device != "":
                result.append(device)
        return result

    @property
    def is_fullscreen(self):
        """
            Return True if application is fullscreen
        """
        return self.__fs_window is not None

    @property
    def main_window(self):
        """
            Get main window
        """
        return self.__window

    @property
    def window(self):
        """
            Get current application window
            @return Gtk.Window
        """
        if self.__fs_window is not None:
            return self.__fs_window
        else:
            return self.__window

    @property
    def data_dir(self):
        """
            Get data dir
            @return str
        """
        return self.__data_dir

    @property
    def gtk_application_prefer_dark_theme(self):
        """
            Return default gtk value
            @return bool
        """
        return self.__gtk_dark

#######################
# PRIVATE             #
#######################
    def __save_state(self):
        """
            Save player state
        """
        if self.settings.get_value("save-state"):
            if self.player.current_track.id is None or\
                    self.player.current_track.storage_type &\
                    StorageType.EPHEMERAL:
                track_id = None
            else:
                track_id = self.player.current_track.id
                # Save albums context
                try:
                    with open(LOLLYPOP_DATA_PATH + "/Albums.bin", "wb") as f:
                        dump(self.player.albums, f)
                except Exception as e:
                    Logger.error("Application::__save_state(): %s" % e)
            dump(track_id, open(LOLLYPOP_DATA_PATH + "/track_id.bin", "wb"))
            dump([self.player.is_playing, self.player.is_party],
                 open(LOLLYPOP_DATA_PATH + "/player.bin", "wb"))
            dump(self.player.queue,
                 open(LOLLYPOP_DATA_PATH + "/queue.bin", "wb"))
            if self.player.current_track.id is not None:
                position = self.player.position
            else:
                position = 0
            dump(position, open(LOLLYPOP_DATA_PATH + "/position.bin", "wb"))
        self.player.stop_all()

    def __vacuum(self):
        """
            VACUUM DB
        """
        try:
            if self.scanner.is_locked():
                self.scanner.stop()
                GLib.idle_add(self.__vacuum)
                return
            SqlCursor.add(self.db)
            self.tracks.del_non_persistent(False)
            self.tracks.clean(False)
            self.albums.clean(False)
            self.artists.clean(False)
            self.genres.clean(False)
            SqlCursor.remove(self.db)
            self.cache.clean(True)

            with SqlCursor(self.db) as sql:
                sql.isolation_level = None
                sql.execute("VACUUM")
                sql.isolation_level = ""
            with SqlCursor(self.playlists) as sql:
                sql.isolation_level = None
                sql.execute("VACUUM")
                sql.isolation_level = ""
        except Exception as e:
            Logger.error("Application::__vacuum(): %s" % e)

    def __hide_on_delete(self, widget, event):
        """
            Hide window
            @param widget as Gtk.Widget
            @param event as Gdk.Event
        """
        # Quit if background mode is on but player is off
        if not self.settings.get_value("background-mode") or\
                not self.player.is_playing:
            GLib.idle_add(self.quit, True)
        return widget.hide_on_delete()

    def __on_activate(self, application):
        """
            Call default handler
            @param application as Gio.Application
        """
        self.__window.present()
