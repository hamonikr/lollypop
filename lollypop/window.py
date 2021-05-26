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

from gi.repository import Gtk, GLib, Handy

from lollypop.define import App, ScanType, ArtSize
from lollypop.container import Container
from lollypop.toolbar import Toolbar
from lollypop.utils import emit_signal
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.logger import Logger


class Window(Handy.ApplicationWindow, SignalsHelper):
    """
        Main window
    """

    @signals_map
    def __init__(self):
        """
            Init window
        """
        Handy.ApplicationWindow.__init__(self,
                                         application=App(),
                                         title="Lollypop",
                                         icon_name="org.gnome.Lollypop")
        self.__miniplayer = None
        self.__configure_timeout_id = None
        self.set_auto_startup_notification(False)
        self.connect("realize", self.__on_realize)
        # Does not work with a Gtk.Gesture in GTK3
        self.connect("button-release-event", self.__on_button_release_event)
        self.connect("window-state-event", self.__on_window_state_event)
        self.connect("configure-event", self.__on_configure_event)
        self.connect("destroy", self.__on_destroy)
        self.set_size_request(ArtSize.MINIPLAYER, ArtSize.MINIPLAYER)
        return [
            (App().player, "current-changed", "_on_current_changed")
        ]

    def setup(self):
        """
            Setup window content
        """
        self.__vgrid = Gtk.Grid()
        self.__vgrid.set_orientation(Gtk.Orientation.VERTICAL)
        self.__vgrid.show()
        self.__container = Container()
        self.__container.setup()
        self.__container.show()
        self.__toolbar = Toolbar(self)
        self.__toolbar.show()
        self.__vgrid.add(self.__toolbar)
        self.__toolbar.set_show_close_button(True)
        self.__vgrid.add(self.__container)
        self.add(self.__vgrid)
        self.__container.widget.connect("notify::folded",
                                        self.__on_container_folded)

    def show_miniplayer(self, show, reveal=False):
        """
            Show/hide subtoolbar
            @param show as bool
            @param reveal as bool
        """
        def show_buttons(show):
            if show:
                self.toolbar.end.show()
                self.toolbar.playback.show()
            else:
                self.toolbar.end.hide()
                self.toolbar.playback.hide()

        def on_revealed(miniplayer, revealed):
            miniplayer.set_vexpand(revealed)
            show_buttons(not revealed)
            if revealed:
                self.__toolbar.hide()
                self.__container.hide()
                emit_signal(self.__container, "can-go-back-changed", False)
            else:
                self.__toolbar.show()
                self.__container.show()
                emit_signal(self.__container, "can-go-back-changed",
                            self.__container.can_go_back)

        if show and self.__miniplayer is None:
            from lollypop.miniplayer import MiniPlayer
            self.__miniplayer = MiniPlayer()
            if App().player.current_track.id is not None:
                self.__miniplayer.show()
            self.__miniplayer.connect("revealed", on_revealed)
            self.__vgrid.add(self.__miniplayer)
            self.__miniplayer.set_vexpand(False)
        elif not show and self.__miniplayer is not None:
            if App().lookup_action("miniplayer").get_state():
                App().lookup_action("miniplayer").change_state(
                    GLib.Variant("b", False))
            else:
                self.__miniplayer.destroy()
                self.__miniplayer = None
                self.__container.show()
                show_buttons(True)
        if self.__miniplayer is not None:
            if reveal:
                self.__miniplayer.reveal(True)
            else:
                self.__miniplayer.update_artwork()

    @property
    def folded(self):
        """
            True if window is adaptive, ie widget folded
        """
        return App().window.container.widget.get_folded()

    @property
    def miniplayer(self):
        """
            @return MiniPlayer
        """
        return self.__miniplayer

    @property
    def toolbar(self):
        """
            @return Toolbar
        """
        return self.__toolbar

    @property
    def container(self):
        """
            @return Container
        """
        return self.__container

##############
# PROTECTED  #
##############
    def _on_current_changed(self, player):
        """
            Update toolbar
            @param player as Player
        """
        if App().player.current_track.id is None:
            self.set_title("Lollypop")
        else:
            artists = ", ".join(player.current_track.artists)
            self.set_title("%s - %s" % (artists, player.current_track.name))
            if self.__miniplayer is not None:
                self.__miniplayer.show()

    def _on_configure_event_timeout(self, width, height, x, y):
        """
            Setup content based on current size
            @param width as int
            @param height as int
            @param x as int
            @param y as int
        """
        self.__configure_timeout_id = None
        if App().lookup_action("miniplayer").get_state():
            return
        if not self.is_maximized():
            App().settings.set_value("window-size",
                                     GLib.Variant("ai", [width, height]))
        App().settings.set_value("window-position", GLib.Variant("ai", [x, y]))

############
# PRIVATE  #
############
    def __setup_size_and_position(self):
        """
            Setup window position and size, callbacks
        """
        try:
            size = App().settings.get_value("window-size")
            pos = App().settings.get_value("window-position")
            self.resize(size[0], size[1])
            self.move(pos[0], pos[1])
            if App().settings.get_value("window-maximized"):
                self.maximize()
        except Exception as e:
            Logger.error("Window::__setup_size_and_position(): %s", e)

    def __on_realize(self, window):
        """
            Init window content
            @param window as Gtk.Window
        """
        self.__setup_size_and_position()
        if App().settings.get_value("auto-update") or App().tracks.is_empty():
            App().scanner.update(ScanType.FULL)
        # FIXME: remove this later
        elif GLib.file_test("/app", GLib.FileTest.EXISTS) and\
                not App().settings.get_value("flatpak-access-migration"):
            App().scanner.update(ScanType.FULL)

    def __on_button_release_event(self, window, event):
        """
            Handle special mouse buttons
            @param window as Gtk.Window
            @param event as Gdk.EventButton
        """
        if event.button == 8:
            App().window.container.go_back()
            return True

    def __on_window_state_event(self, widget, event):
        """
            Save maximised state
        """
        if not App().lookup_action("miniplayer").get_state():
            App().settings.set_boolean("window-maximized",
                                       "GDK_WINDOW_STATE_MAXIMIZED" in
                                       event.new_window_state.value_names)

    def __on_container_folded(self, leaflet, folded):
        """
            show/hide miniplayer
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        emit_signal(self.__container,
                    "can-go-back-changed",
                    self.__container.can_go_back)
        self.show_miniplayer(App().window.folded)

    def __on_destroy(self, widget):
        """
            Remove ref cycle, just to prevent output on DEBUG_LEAK
            @param widget as Gtk.Widget
        """
        self.__toolbar = None

    def __on_configure_event(self, window, event):
        """
            Delay event
            @param window as Gtk.Window
            @param event as Gdk.EventConfigure
        """
        if self.__configure_timeout_id:
            GLib.source_remove(self.__configure_timeout_id)
        (width, height) = window.get_size()
        (x, y) = window.get_position()
        self.__configure_timeout_id = GLib.idle_add(
            self._on_configure_event_timeout,
            width, height, x, y, priority=GLib.PRIORITY_LOW)
