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

from gi.repository import Gtk, Gdk, GObject

from lollypop.define import ArtSize, ViewType, MARGIN, App
from lollypop.utils import emit_signal
from lollypop.helper_size_allocation import SizeAllocationHelper


class Overlay(Gtk.Overlay):
    """
        Overlay with constraint size
    """
    def __init__(self):
        """
            Init overlay
            @param banner as BannerWidget
        """
        Gtk.Overlay.__init__(self)

    def do_get_preferred_width(self):
        """
            Force preferred width
        """
        (min, nat) = Gtk.Bin.do_get_preferred_width(self)
        # Allow resizing
        return (1, 1)


class BannerWidget(Gtk.Revealer, SizeAllocationHelper):
    """
        Default banner widget
    """

    gsignals = {
        "scroll": (GObject.SignalFlags.RUN_FIRST, None, (float, float)),
        "height-changed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    for signal in gsignals:
        args = gsignals[signal]
        GObject.signal_new(signal, Gtk.Revealer,
                           args[0], args[1], args[2])

    def __init__(self, view_type):
        """
            Init bannner
            @param view_type as ViewType
        """
        Gtk.Revealer.__init__(self)
        self._artwork = None
        self.__view_type = view_type | ViewType.BANNER
        self.__width = 1
        self.set_property("valign", Gtk.Align.START)
        if view_type & ViewType.OVERLAY:
            self._overlay = Overlay()
            self._overlay.show()
            self._artwork = Gtk.Image()
            self._artwork.show()
            if App().animations:
                self._artwork.set_opacity(0.99)
            self.get_style_context().add_class("default-banner")
            self._artwork.get_style_context().add_class("default-banner")
            eventbox = Gtk.EventBox.new()
            eventbox.show()
            eventbox.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
            eventbox.add(self._artwork)
            self._overlay.add(eventbox)
            self.__event_controller = Gtk.EventControllerScroll.new(
                eventbox, Gtk.EventControllerScrollFlags.BOTH_AXES)
            self.__event_controller.set_propagation_phase(
                Gtk.PropagationPhase.TARGET)
            self.__event_controller.connect("scroll", self.__on_scroll)
            self.add(self._overlay)
        self.set_reveal_child(True)
        self.set_transition_duration(250)
        self.connect("destroy", self.__on_destroy)
        SizeAllocationHelper.__init__(self)

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        self.__width = width
        if self._artwork is not None:
            self._artwork.set_size_request(-1, self.height)

    @property
    def width(self):
        """
            Get current width
            @return int
        """
        # If not SMALL, we add sidebar width because we want banners
        # to calculate sizing with sidebar included. Allows to prevent
        # glitch when sidebar is auto shown
        if not App().window.folded:
            sidebar_width = App().window.container.sidebar.\
                get_allocated_width()
            return self.__width + sidebar_width
        else:
            return self.__width

    @property
    def height(self):
        """
            Get wanted height
            @return int
        """
        if App().window.folded:
            height = ArtSize.MEDIUM + MARGIN * 2
        else:
            height = ArtSize.BANNER + MARGIN * 2
        return height

    @property
    def view_type(self):
        """
            Get view type
            @return ViewType
        """
        return self.__view_type

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
            @return bool
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            if allocation.width != self.__width:
                self.__width = allocation.width
                height = self.height
                if self._artwork is not None:
                    self._artwork.set_size_request(-1, height)
                emit_signal(self, "height-changed", height)
                return True
        return False

    def _on_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        banner_context = self.get_style_context()
        artwork_context = self._artwork.get_style_context()
        self._artwork.set_from_surface(surface)
        if surface is None:
            banner_context.add_class("default-banner")
            banner_context.remove_class("black")
            artwork_context.add_class("default-banner")
        else:
            self.emit("populated")
            banner_context.remove_class("default-banner")
            banner_context.add_class("black")
            artwork_context.remove_class("default-banner")

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, widget):
        """
            Remove ref cycle
            @param widget as Gtk.Widget
        """
        self.__event_controller = None

    def __on_scroll(self, event_controller, x, y):
        """
            Pass scroll
            @param event_controller as Gtk.EventControllerScroll
            @param x as int
            @param y as int
        """
        emit_signal(self, "scroll", x, y)
