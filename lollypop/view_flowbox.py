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

from gi.repository import Gtk

from locale import strcoll

from lollypop.view_lazyloading import LazyLoadingView
from lollypop.helper_gestures import GesturesHelper
from lollypop.define import ViewType, App
from lollypop.utils import get_font_height, popup_widget, set_cursor_type


class FlowBoxView(LazyLoadingView, GesturesHelper):
    """
        Lazy loading FlowBox
    """

    def __init__(self, storage_type, view_type=ViewType.SCROLLED):
        """
            Init flowbox view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        LazyLoadingView.__init__(self, storage_type, view_type)
        self._items = []
        self.__hovered_child = None
        self.__font_height = get_font_height()
        self._box = Gtk.FlowBox()
        self._box.get_style_context().add_class("padding")
        # Allow lazy loading to not jump up and down
        self._box.set_homogeneous(True)
        self._box.set_vexpand(True)
        self._box.set_max_children_per_line(1000)
        self._box.set_property("valign", Gtk.Align.START)
        self._box.connect("child-activated", self._on_child_activated)
        self._box.show()
        if App().animations:
            self.__event_controller = Gtk.EventControllerMotion.new(self._box)
            self.__event_controller.connect("motion", self.__on_box_motion)
        GesturesHelper.__init__(self, self._box)

    def populate(self, items):
        """
            Populate items
            @param items
        """
        LazyLoadingView.populate(self, items)

    def add_value(self, value):
        """
            Append value
            @param value as object
        """
        self._box.set_sort_func(self._sort_func)
        self.add_value_unsorted(value)

    def add_value_unsorted(self, value):
        """
            Add value unsorted
            @param value as object
        """
        child = self._get_child(value)
        child.populate()

    def remove_value(self, value):
        """
            Remove value
            @param value as object
        """
        for child in self._box.get_children():
            if child.data == value:
                child.destroy()
                break

    def clear(self):
        """
            Clear flowbox
        """
        for child in self._box.get_children():
            child.destroy()

    def destroy(self):
        """
            Force destroying the box
            Help freeing memory, no idea why
        """
        self._box.destroy()
        LazyLoadingView.destroy(self)

    @property
    def font_height(self):
        """
            Get font height
            @return int
        """
        return self.__font_height

    @property
    def children(self):
        """
            Get box children
            @return [Gtk.Widget]
        """
        return self._box.get_children()

#######################
# PROTECTED           #
#######################
    def _get_menu_widget(self, child):
        """
            Get menu widget
            @param child as Gtk.FlowBoxChild
            @return Gtk.Widget
        """
        return None

    def _get_label_height(self):
        """
            Get wanted label height
            @return int
        """
        return 0

    def _sort_func(self, widget1, widget2):
        """
            Sort function
            @param widget1 as Gtk.Widget
            @param widget2 as Gtk.Widget
        """
        return strcoll(widget1.sortname, widget2.sortname)

    def _on_child_activated(self, flowbox, child):
        pass

    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        LazyLoadingView._on_container_folded(self, leaflet, folded)
        self.pause()
        children = self._box.get_children()
        for child in children:
            child.reset_artwork()
            self.queue_lazy_loading(child)
        self.lazy_loading()

    def _on_view_leave(self, event_controller):
        """
            Unselect selected child
            @param event_controller as Gtk.EventControllerMotion
        """
        self.__unselect_selected()

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Popup menu at position
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        self._on_primary_long_press_gesture(x, y)

    def _on_primary_long_press_gesture(self, x, y):
        """
            Popup menu at position
            @param x as int
            @param y as int
        """
        child = self._box.get_child_at_pos(x, y)
        if child is None or child.artwork is None:
            return
        self.__popup_menu(child)

    def _on_destroy(self, widget):
        """
            Clean up widget
            @param widget as Gtk.Widget
        """
        LazyLoadingView._on_destroy(self, widget)
        self.__event_controller = None

#######################
# PRIVATE             #
#######################
    def __popup_menu(self, child):
        """
            Popup album menu at position
            @param child ad RoundedArtistWidget
        """
        menu_widget = self._get_menu_widget(child)
        if menu_widget is not None:
            menu_widget.show()
            popup_widget(menu_widget, child.artwork, None, None, None)

    def __unselect_selected(self):
        """
            Unselect selected child
        """
        if self.__hovered_child is not None and\
                self.__hovered_child.artwork is not None:
            self.__hovered_child.artwork.unset_state_flags(
                Gtk.StateFlags.VISITED)
            set_cursor_type(self.__hovered_child, "left_ptr")
            self.__hovered_child = None

    def __on_box_motion(self, event_controller, x, y):
        """
            Update current selected child
            @param event_controller as Gtk.EventControllerMotion
            @param x as int
            @param y as int
        """
        child = self._box.get_child_at_pos(x, y)
        if child == self.__hovered_child:
            return
        elif child is not None and child.artwork is not None:
            child.artwork.set_state_flags(Gtk.StateFlags.VISITED, False)
            self.__unselect_selected()
            self.__hovered_child = child
            set_cursor_type(child)
        else:
            self.__unselect_selected()
