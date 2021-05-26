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

from gi.repository import Gtk, GLib

from gettext import gettext as _

from lollypop.define import ViewType, App, MARGIN_SMALL, Type
from lollypop.helper_adaptive import AdaptiveHelper
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.helper_filtering import FilteringHelper


class View(Gtk.Grid, AdaptiveHelper, FilteringHelper, SignalsHelper):
    """
        Generic view
    """

    @signals_map
    def __init__(self, storage_type, view_type):
        """
            Init view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        Gtk.Grid.__init__(self)
        AdaptiveHelper.__init__(self)
        FilteringHelper.__init__(self)
        self.__storage_type = storage_type
        self.__view_type = view_type
        self.__scrolled_position = None
        self.__destroyed = False
        self.__banner = None
        self.__placeholder = None
        self.scrolled_value = 0
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_border_width(0)
        self.__new_ids = []
        self._empty_message = _("No items to show")
        self._empty_icon_name = "emblem-music-symbolic"

        if view_type & ViewType.SCROLLED:
            self.__scrolled = Gtk.ScrolledWindow.new()
            self.__event_controller = Gtk.EventControllerMotion.new(
                self.__scrolled)
            self.__event_controller.set_propagation_phase(
                Gtk.PropagationPhase.TARGET)
            self.__event_controller.connect("leave", self._on_view_leave)
            self.__scrolled.get_vadjustment().connect("value-changed",
                                                      self._on_value_changed)
            self.__scrolled.show()
            self.__scrolled.set_property("expand", True)

        # Stack for placeholder
        self.__stack = Gtk.Stack.new()
        self.__stack.show()
        self.__stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.connect("destroy", self._on_destroy)
        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)
        self.connect("realize", self._on_realize)
        return [
            (App().window.container.widget, "notify::folded",
             "_on_container_folded"),
        ]

    def add_widget(self, widget, banner=None):
        """
            Add widget to view
            Add banner if ViewType.OVERLAY
            @param widget as Gtk.Widget
        """
        self.__stack.add_named(widget, "main")
        if self.view_type & ViewType.OVERLAY:
            self.__overlay = Gtk.Overlay.new()
            self.__overlay.show()
            if self.view_type & ViewType.SCROLLED:
                self.__overlay.add(self.scrolled)
                self.__scrolled.add(self.__stack)
            else:
                self.__overlay.add(self.__stack)
            if banner is not None:
                self.__overlay.add_overlay(banner)
                self.__banner = banner
                self.__banner.connect("scroll", self.__on_banner_scroll)
            self.add(self.__overlay)
        elif self.view_type & ViewType.SCROLLED:
            self.__scrolled.add(self.__stack)
            if banner is not None:
                self.__banner = banner
                self.add(self.__banner)
            self.add(self.scrolled)
        else:
            if banner is not None:
                self.__banner = banner
                self.add(self.__banner)
            self.add(self.__stack)
        if banner is not None:
            banner.connect("height-changed", self.__on_banner_height_changed)

    def populate(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def show_placeholder(self, show, new_text=None):
        """
            Show placeholder
            @param show as bool
        """
        if show:
            if self.__placeholder is not None:
                GLib.timeout_add(200, self.__placeholder.destroy)
            message = new_text\
                if new_text is not None\
                else self._empty_message
            from lollypop.widgets_placeholder import Placeholder
            self.__placeholder = Placeholder(message, self._empty_icon_name)
            self.__placeholder.show()
            self.__stack.add(self.__placeholder)
            self.__stack.set_visible_child(self.__placeholder)
        else:
            self.__stack.set_visible_child_name("main")

    def set_scrolled(self, scrolled):
        """
            Add an external scrolled window
            @param scrolled as Gtk.ScrolledWindow
        """
        self.__scrolled = scrolled
        self.__view_type |= ViewType.SCROLLED

    def set_populated_scrolled_position(self, position):
        """
            Set scrolled position on populated
            @param position as int
        """
        if self.view_type & ViewType.SCROLLED:
            self.__scrolled_position = position

    @property
    def scrolled(self):
        """
            Get scrolled widget
            @return Gtk.ScrolledWindow
        """
        if self.view_type & ViewType.SCROLLED:
            return self.__scrolled
        else:
            return Gtk.ScrolledWindow.new()

    @property
    def banner(self):
        """
            Get view banner
            @return BannerWidget
        """
        return self.__banner

    @property
    def children(self):
        """
            Get view children
            @return [Gtk.Widget]
        """
        return []

    @property
    def storage_type(self):
        """
            Get storage type
            @return StorageType
        """
        return self.__storage_type

    @property
    def view_type(self):
        """
            View type less sizing
            @return ViewType
        """
        return self.__view_type

    @property
    def position(self):
        """
            Get scrolled position
            @return float
        """
        if self.view_type & ViewType.SCROLLED:
            position = self.scrolled.get_vadjustment().get_value()
        else:
            position = 0
        return position

    @property
    def destroyed(self):
        """
            True if widget has been destroyed
            @return bool
        """
        return self.__destroyed

#######################
# PROTECTED           #
#######################
    def _on_view_leave(self, event_controller):
        pass

    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        if self.__placeholder is not None and self.__placeholder.is_visible():
            self.__placeholder.set_folded(App().window.folded)

    def _on_value_changed(self, adj):
        """
            Reveal banner
            @param adj as Gtk.Adjustment
        """
        if self.__banner is not None:
            reveal = self.__should_reveal_header(adj)
            self.__banner.set_reveal_child(reveal)
            if reveal:
                main_widget = self.__stack.get_child_by_name("main")
                if main_widget is not None:
                    main_widget.set_margin_top(self.__banner.height +
                                               MARGIN_SMALL)
                if self.view_type & ViewType.SCROLLED:
                    self.scrolled.get_vscrollbar().set_margin_top(
                        self.__banner.height)
            elif self.view_type & ViewType.SCROLLED:
                self.scrolled.get_vscrollbar().set_margin_top(0)

    def _on_map(self, widget):
        """
            Set initial view state
            @param widget as GtK.Widget
        """
        # Set sidebar id
        if self.sidebar_id is None:
            ids = App().window.container.sidebar.selected_ids
            if ids:
                self.set_sidebar_id(ids[0])
                if self.sidebar_id == Type.GENRES_LIST:
                    self.selection_ids["left"] =\
                        App().window.container.left_list.selected_ids
                    self.selection_ids["right"] =\
                        App().window.container.right_list.selected_ids
                elif self.sidebar_id == Type.ARTISTS_LIST:
                    self.selection_ids["left"] =\
                        App().window.container.left_list.selected_ids

    def _on_unmap(self, widget):
        pass

    def _on_realize(self, widget):
        """
            Delayed adaptive mode
            Restore scroll position
            @param widget as Gtk.Widget
        """
        parent = widget.get_parent()
        if self.__banner is not None and parent is not None:
            width = parent.get_allocated_width()
            self.__banner.update_for_width(width)
            self.__on_banner_height_changed(self.__banner,
                                            self.__banner.height)
        # Wait for stack allocation to restore scrolled position
        if self.__scrolled_position is not None:
            self.__stack.connect("size-allocate",
                                 self.__on_stack_size_allocated)

    def _on_destroy(self, widget):
        """
            Clean up widget
            @param widget as Gtk.Widget
        """
        self.__destroyed = True
        self.__event_controller = None

#######################
# PRIVATE             #
#######################
    def __should_reveal_header(self, adj):
        """
            Check if we need to reveal header
            @param adj as Gtk.Adjustment
            @param delta as int
            @return int
        """
        value = adj.get_value()
        reveal = self.scrolled_value > value
        self.scrolled_value = value
        return reveal

    def __on_banner_height_changed(self, banner, height):
        """
            Update scroll margin
            @param banner as BannerWidget
            @param height as int
        """
        if self.view_type & ViewType.OVERLAY:
            main_widget = self.__stack.get_child_by_name("main")
            main_widget.set_margin_top(height + MARGIN_SMALL)
            if self.view_type & ViewType.SCROLLED:
                self.scrolled.get_vscrollbar().set_margin_top(height)

    def __on_banner_scroll(self, banner, x, y):
        """
            Pass to scrolled
            @param banner as BannerWidget
            @param x as float
            @param y as float
        """
        if y > 0:
            y = 100
        else:
            y = -100
        adj = self.scrolled.get_vadjustment()
        new_value = adj.get_value() + y
        lower = adj.get_lower()
        upper = adj.get_upper() - adj.get_page_size()
        if new_value != lower and new_value != upper:
            adj.set_value(new_value)

    def __on_stack_size_allocated(self, stack, allocation):
        """
            Restore scrolled position
            @param stack as Gtk.Stack
            @param allocation as Gdk.Rectangle
        """
        if self.__scrolled_position is not None and\
                allocation.height > self.__scrolled_position:
            stack.disconnect_by_func(self.__on_stack_size_allocated)
            self.scrolled.get_vadjustment().set_value(
                self.__scrolled_position)
            self.__scrolled_position = None
