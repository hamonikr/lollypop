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

from gi.repository import Gtk, Gdk, GLib, Gio, Gst

from datetime import datetime
from gettext import gettext as _

from lollypop.define import App, ArtSize, ArtBehaviour
from lollypop.define import MARGIN_BIG
from lollypop.widgets_player_progress import ProgressPlayerWidget
from lollypop.widgets_player_buttons import ButtonsPlayerWidget
from lollypop.widgets_player_artwork import ArtworkPlayerWidget
from lollypop.widgets_player_label import LabelPlayerWidget
from lollypop.container import Container
from lollypop.logger import Logger
from lollypop.helper_signals import SignalsHelper, signals_map


class FullScreen(Gtk.Window, SignalsHelper):
    """
        Show a fullscreen window showing current track context
    """

    @signals_map
    def __init__(self):
        """
            Init window
        """
        Gtk.Window.__init__(self)
        return [
                (App().player, "current-changed", "_on_current_changed")
        ]

    def delayed_init(self):
        """
            Delay real init to get App().window == self
        """
        self.get_style_context().add_class("black")
        self.set_title("Lollypop")
        self.__allocation = Gdk.Rectangle()
        self.set_application(App())
        self.__timeout_id = None
        self.__signal1_id = self.__signal2_id = None
        self.__background_id = None
        self.set_decorated(False)
        art_size = ArtSize.FULLSCREEN
        font_size = 30
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/FullScreen.ui")
        builder.connect_signals(self)
        self.__progress_widget = ProgressPlayerWidget()
        self.__progress_widget.show()
        self.__progress_widget.set_property("halign", Gtk.Align.CENTER)
        self.__progress_widget.set_size_request(500, -1)
        self.__buttons_widget = ButtonsPlayerWidget(["banner-button"])
        self.__buttons_widget.show()
        self.__buttons_widget.set_size_request(500, -1)
        self.__buttons_widget.set_property("valign", Gtk.Align.CENTER)
        self.__buttons_widget.set_property("halign", Gtk.Align.CENTER)
        self.__artwork_widget = ArtworkPlayerWidget(
            ArtBehaviour.CACHE | ArtBehaviour.CROP_SQUARE)
        self.__artwork_widget.show()
        self.__artwork_widget.set_vexpand(True)
        self.__artwork_widget.set_art_size(art_size, art_size)
        self.__artwork_widget.set_property("valign", Gtk.Align.CENTER)
        self.__artwork_widget.set_property("halign", Gtk.Align.CENTER)
        self.__label_widget = LabelPlayerWidget(True, font_size)
        self.__label_widget.show()
        self.__label_widget.set_hexpand(True)
        self.__label_widget.set_vexpand(True)
        self.__label_widget.set_justify(Gtk.Justification.CENTER)
        eventbox = Gtk.EventBox.new()
        eventbox.show()
        eventbox.connect("button-release-event",
                         self.__on_image_button_release_event)
        eventbox.connect("realize", self.__on_image_realize)
        eventbox.add(self.__artwork_widget)
        self.__revealer = builder.get_object("revealer")
        self.__datetime = builder.get_object("datetime")
        self.__overlay_grid = builder.get_object("overlay_grid")
        widget = builder.get_object("widget")
        if App().settings.get_value("artist-artwork"):
            self.__overlay_grid.attach(self.__buttons_widget, 0, 4, 2, 1)
            self.__overlay_grid.attach(self.__label_widget, 0, 2, 2, 1)
            self.__overlay_grid.attach(self.__progress_widget, 0, 3, 2, 1)
            self.__overlay_grid.attach(eventbox, 2, 2, 1, 3)
            eventbox.set_margin_end(MARGIN_BIG)
            eventbox.set_property("valign", Gtk.Align.END)
            eventbox.set_property("halign", Gtk.Align.END)
            self.__artwork_widget.set_margin_end(MARGIN_BIG)
            self.__artwork_widget.set_margin_bottom(MARGIN_BIG)
            self.__label_widget.set_property("valign", Gtk.Align.END)
            self.__artwork_widget.set_property("valign", Gtk.Align.END)
        else:
            self.__overlay_grid.attach(self.__buttons_widget, 0, 4, 3, 1)
            self.__overlay_grid.attach(self.__label_widget, 0, 2, 3, 1)
            self.__overlay_grid.attach(self.__progress_widget, 0, 3, 3, 1)
            self.__overlay_grid.attach(eventbox, 0, 1, 3, 1)
            eventbox.set_vexpand(True)
        close_btn = builder.get_object("close_btn")
        preferences = Gio.Settings.new("org.gnome.desktop.wm.preferences")
        layout = preferences.get_value("button-layout").get_string()
        if layout.split(":")[0] == "close":
            self.__overlay_grid.attach(close_btn, 0, 0, 1, 1)
            close_btn.set_property("halign", Gtk.Align.START)
        else:
            self.__overlay_grid.attach(close_btn, 2, 0, 1, 1)
            close_btn.set_property("halign", Gtk.Align.END)
        self._artwork = builder.get_object("cover")
        self.connect("key-release-event", self.__on_key_release_event)
        # Add a navigation widget on the right
        self.__back_button = Gtk.Button.new_from_icon_name(
            "go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.__back_button.set_sensitive(False)
        self.__back_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__back_button.set_property("valign", Gtk.Align.START)
        self.__back_button.set_property("halign", Gtk.Align.START)
        self.__back_button.connect("clicked", self.__on_back_button_clicked)
        self.__back_button.set_margin_start(5)
        self.__back_button.set_margin_end(5)
        self.__back_button.set_margin_top(5)
        self.__back_button.set_margin_bottom(5)
        self.__back_button.show()
        self.__background_artwork = builder.get_object("background_artwork")
        self.__container = Container()
        self.__container.show()
        self.__container.setup()
        self.__sidebar = Gtk.Grid()
        self.__sidebar.set_size_request(400, -1)
        self.__sidebar.set_orientation(Gtk.Orientation.VERTICAL)
        self.__sidebar.get_style_context().add_class("borders-left-top")
        self.__sidebar.show()
        self.__sidebar.add(self.__back_button)
        self.__sidebar.add(self.__container)
        self.__sidebar.set_size_request(450, -1)
        self.__sidebar.get_style_context().add_class("background-opacity")
        self.__container.connect("can-go-back-changed",
                                 self.__on_can_go_back_changed)
        self.connect("size-allocate", self.__on_size_allocate)
        self.__revealer.add(self.__sidebar)
        self.add(widget)

    def do_show(self):
        """
            Setup window for current screen
        """
        Gtk.Window.do_show(self)
        self.__buttons_widget.update()
        self.__label_widget.update()
        self.__progress_widget.update()
        self.__update_progress_visibility()
        self.__setup_artwork_type()
        if self.__timeout_id is None:
            try:
                interface = Gio.Settings.new("org.gnome.desktop.interface")
                show_seconds = interface.get_value("clock-show-seconds")
            except:
                show_seconds = False
            self.__update_datetime(show_seconds)
            self.__timeout_id = GLib.timeout_add(1000,
                                                 self.__update_datetime,
                                                 show_seconds)
        self.__progress_widget.update_position(
            App().player.position / Gst.SECOND)
        screen = Gdk.Screen.get_default()
        monitor = screen.get_monitor_at_window(App().main_window.get_window())
        self.fullscreen_on_monitor(screen, monitor)
        # Disable screensaver (idle)
        App().inhibitor.manual_inhibit(
                Gtk.ApplicationInhibitFlags.IDLE |
                Gtk.ApplicationInhibitFlags.SUSPEND)

    def do_hide(self):
        """
            Clean window
        """
        Gtk.Window.do_hide(self)
        if self.__timeout_id is not None:
            GLib.source_remove(self.__timeout_id)
            self.__timeout_id = None
        App().inhibitor.manual_uninhibit()

    @property
    def miniplayer(self):
        return App().main_window.miniplayer

    @property
    def folded(self):
        return False

    @property
    def toolbar(self):
        return App().main_window.toolbar

    @property
    def container(self):
        """
            Get container
            @return Container
        """
        return self.__container

#######################
# PROTECTED           #
#######################
    def _on_close_button_clicked(self, button):
        """
            Destroy self
            @param button as Gtk.Button
        """
        self.destroy()

    def _on_reveal_button_clicked(self, button):
        """
            Reveal widget
            @param button as Gtk.Button
        """
        if self.__revealer.get_reveal_child():
            self.__revealer.set_reveal_child(False)
            button.get_image().set_from_icon_name("pan-start-symbolic",
                                                  Gtk.IconSize.BUTTON)
        else:
            self.__revealer.set_reveal_child(True)
            button.get_image().set_from_icon_name("pan-end-symbolic",
                                                  Gtk.IconSize.BUTTON)

    def _on_current_changed(self, player):
        """
            Update background
            @param player as Player
        """
        self.__update_background()
        self.__update_progress_visibility()

#######################
# PRIVATE             #
#######################
    def __setup_artwork_type(self):
        """
            Setup artwork type
        """
        fs_type = App().settings.get_value("fullscreen-type").get_int32()
        context = self.__artwork_widget.get_style_context()
        behaviour = ArtBehaviour.CROP_SQUARE
        if fs_type & ArtBehaviour.ROUNDED:
            context.add_class("image-rotate")
            context.remove_class("small-cover-frame")
            behaviour |= ArtBehaviour.ROUNDED
        else:
            context.remove_class("image-rotate")
            context.add_class("small-cover-frame")
        self.__artwork_widget.set_behaviour(behaviour)
        self.__artwork_widget.update()

    def __update_progress_visibility(self):
        """
            Update progress bar visibility
        """
        if App().player.current_track.id is not None:
            self.__progress_widget.show()
        else:
            self.__progress_widget.hide()

    def __update_background(self, album_artwork=False):
        """
            Update window background
            @param album_artwork as bool
        """
        try:
            if App().player.current_track.id is None:
                return
            allocation = self.get_allocation()
            if allocation.width <= 1 or allocation.height <= 1:
                return
            behaviour = App().settings.get_value("fullscreen-type").get_int32()
            behaviour |= (ArtBehaviour.CROP |
                          ArtBehaviour.DARKER)
            # We don't want this for background, stored for album cover
            behaviour &= ~ArtBehaviour.ROUNDED
            if not album_artwork and\
                    App().settings.get_value("artist-artwork"):
                if App().player.current_track.album.artists:
                    artist = App().player.current_track.album.artists[0]
                else:
                    artist = App().player.current_track.artists[0]
                if self.__background_id == artist:
                    return
                App().art_helper.set_artist_artwork(
                                    artist,
                                    allocation.width,
                                    allocation.height,
                                    self.get_scale_factor(),
                                    behaviour,
                                    self.__on_artwork,
                                    False)
            else:
                if self.__background_id == App().player.current_track.album.id:
                    return
                App().art_helper.set_album_artwork(
                                    App().player.current_track.album,
                                    allocation.width,
                                    allocation.height,
                                    self.get_scale_factor(),
                                    ArtBehaviour.BLUR_MAX |
                                    ArtBehaviour.CROP |
                                    ArtBehaviour.DARKER,
                                    self.__on_artwork,
                                    True)
        except Exception as e:
            Logger.error("Fullscreen::__update_background(): %s", e)

    def __update_datetime(self, show_seconds=False):
        """
            Update datetime in headerbar
            @param show_seconds as bool
        """
        now = datetime.now()
        if show_seconds:
            self.__datetime.set_label(now.strftime("%a %d %b %X"))
        else:
            self.__datetime.set_label(now.strftime("%a %d %b %X")[:-3])
        if self.__timeout_id is None:
            self.__timeout_id = GLib.timeout_add(60000, self.__update_datetime)
            return False
        return True

    def __on_image_realize(self, eventbox):
        """
            Set cursor
            @param eventbox as Gtk.EventBox
        """
        try:
            eventbox.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))
        except:
            Logger.warning(_("You are using a broken cursor theme!"))

    def __on_image_button_release_event(self, widget, event):
        """
            Change artwork type
            @param widget as Gtk.Widget
            @param event as Gdk.Event
        """
        fs_type = App().settings.get_value("fullscreen-type").get_int32()
        if fs_type & ArtBehaviour.BLUR_HARD and\
                fs_type & ArtBehaviour.ROUNDED:
            fs_type = ArtBehaviour.NONE
        elif fs_type & ArtBehaviour.NONE:
            fs_type = ArtBehaviour.BLUR_HARD
        elif fs_type & ArtBehaviour.BLUR_HARD:
            fs_type |= ArtBehaviour.ROUNDED
            fs_type &= ~ArtBehaviour.BLUR_HARD
        elif fs_type & ArtBehaviour.ROUNDED:
            fs_type |= ArtBehaviour.BLUR_HARD
        else:
            fs_type = ArtBehaviour.NONE
        App().settings.set_value("fullscreen-type",
                                 GLib.Variant("i", fs_type))
        self.__setup_artwork_type()
        self.__update_background()

    def __on_artwork(self, surface, album_artwork):
        """
            Set background artwork
            @param surface as str
            @param album_artwork as bool
        """
        if surface is None and not album_artwork:
            self.__update_background(True)
        else:
            self.__background_artwork.set_from_surface(surface)
            del surface

    def __on_key_release_event(self, widget, event):
        """
            Destroy window if Esc
            @param widget as Gtk.Widget
            @param event as Gdk.event
        """
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def __on_back_button_clicked(self, button):
        """
            Go back in container stack
            @param button as Gtk.Button
        """
        self.__container.go_back()

    def __on_can_go_back_changed(self, window, back):
        """
            Make button sensitive
            @param window as Gtk.Window
            @param back as bool
        """
        if back:
            self.__back_button.set_sensitive(True)
        else:
            self.__back_button.set_sensitive(False)

    def __on_size_allocate(self, widget, allocation):
        """
            Update background if needed
            @param widget as Gtk.Widget
            @param allocation as Gtk.Allocation
        """
        if allocation.width <= 1 or\
                allocation.height <= 1 or\
                allocation.width == self.__allocation.width or\
                allocation.height == self.__allocation.height:
            return
        self.__allocation = allocation
        self.__update_background()
