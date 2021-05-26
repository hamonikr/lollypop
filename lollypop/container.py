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

from gi.repository import Gtk, GLib, GObject, Handy

from lollypop.define import App, Type
from lollypop.utils import emit_signal
from lollypop.view import View
from lollypop.container_stack import StackContainer
from lollypop.container_notification import NotificationContainer
from lollypop.container_scanner import ScannerContainer
from lollypop.container_playlists import PlaylistsContainer
from lollypop.container_lists import ListsContainer
from lollypop.container_views import ViewsContainer
from lollypop.container_filter import FilterContainer
from lollypop.progressbar import ProgressBar


class Grid(Gtk.Grid):
    def do_get_preferred_width(self):
        return 200, 700


class Container(Gtk.Overlay, NotificationContainer,
                ScannerContainer, PlaylistsContainer,
                ListsContainer, ViewsContainer, FilterContainer):
    """
        Main view management
    """

    __gsignals__ = {
        "can-go-back-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self):
        """
            Init container
            @param view_type as ViewType, will be appended to any created view
        """
        Gtk.Overlay.__init__(self)
        NotificationContainer.__init__(self)
        ScannerContainer.__init__(self)
        PlaylistsContainer.__init__(self)
        ViewsContainer.__init__(self)

    def setup(self):
        """
            Setup container
        """
        self.__widget = Handy.Leaflet()
        self.__widget.show()
        self.__widget.connect("notify::folded", self.__on_folded)
        self.__sub_widget = Handy.Leaflet()
        self.__sub_widget.show()
        self.__focused_view = None
        self._stack = StackContainer()
        self._stack.show()
        ListsContainer.__init__(self)
        self.__progress = ProgressBar()
        self.__progress.get_style_context().add_class("progress-bottom")
        self.__progress.set_property("valign", Gtk.Align.END)
        self.add_overlay(self.__progress)
        search_action = App().lookup_action("search")
        search_action.connect("activate", self.__on_search_activate)
        self.__widget.add(self.sidebar)
        self.__grid_view = Grid()
        self.__grid_view.set_orientation(Gtk.Orientation.VERTICAL)
        self.__grid_view.show()
        self.__sub_widget.add(self.left_list)
        self.__sub_widget.add(self.__grid_view)
        self.__grid_view.attach(self._stack, 0, 0, 1, 1)
        self.__widget.add(self.__sub_widget)
        self.__widget.set_visible_child(self.__sub_widget)
        self.__sub_widget.set_visible_child(self.__grid_view)
        self.add(self.__widget)
        FilterContainer.__init__(self)

    def stop(self):
        """
            Stop current view from processing
        """
        view = self._stack.get_visible_child()
        if view is not None:
            view.stop()

    def reload_view(self):
        """
            Reload current view
        """
        view = self._stack.get_visible_child()
        if view is not None and view.args is not None:
            cls = view.__class__
            new_view = cls(**view.args)
            new_view.populate()
            new_view.show()
            self._stack.add(new_view)
            self._stack.set_visible_child(new_view)
        else:
            App().lookup_action("reload").change_state(GLib.Variant("b", True))

    def set_focused_view(self, view):
        """
            Set focused view
            @param view as View
        """
        self.__focused_view = view

    def go_home(self):
        """
            Go back to first page
        """
        self.__widget.set_visible_child(self.sidebar)
        self._stack.clear()
        emit_signal(self, "can-go-back-changed", False)

    def go_back(self):
        """
            Go back in history
        """
        if self._stack.history.count > 0:
            self._stack.go_back()
            self.set_focused_view(self._stack.get_visible_child())
        elif self.__sub_widget.get_folded() and\
                self.__sub_widget.get_visible_child() != self.left_list:
            self.__sub_widget.set_visible_child(self.left_list)
            self._stack.clear()
        elif self.__widget.get_folded() and\
                self.__widget.get_visible_child() != self.sidebar:
            self.__widget.set_visible_child(self.sidebar)
            self._stack.clear()
        emit_signal(self, "can-go-back-changed", self.can_go_back)

    @property
    def can_go_back(self):
        """
            True if can go back
            @return bool
        """
        if self.__widget.get_folded():
            return self.__widget.get_visible_child() != self._sidebar
        else:
            return self._stack.history.count > 0

    @property
    def widget(self):
        """
            Get main widget
            @return Handy.Leaflet
        """
        return self.__widget

    @property
    def sub_widget(self):
        """
            Get sub widget
            @return Handy.Leaflet
        """
        return self.__sub_widget

    @property
    def grid_view(self):
        """
            Get grid view
            @return Gtk.Grid
        """
        return self.__grid_view

    @property
    def focused_view(self):
        """
            Get focused view
            @return View
        """
        return self.__focused_view

    @property
    def view(self):
        """
            Get current view
            @return View
        """
        view = self._stack.get_visible_child()
        if view is not None and isinstance(view, View):
            return view
        return None

    @property
    def stack(self):
        """
            Container stack
            @return stack as Gtk.Stack
        """
        return self._stack

    @property
    def progress(self):
        """
            Progress bar
            @return ProgressBar
        """
        return self.__progress

############
# PRIVATE  #
############
    def __on_folded(self, *ignore):
        """
            Reload main view if needed
        """
        if not App().window.folded and self.view is None:
            self.show_view(self.sidebar.selected_ids)

    def __on_search_activate(self, action, variant):
        """
            @param action as Gio.SimpleAction
            @param variant as GLib.Variant
        """
        if App().window.folded:
            search = variant.get_string()
            App().window.container.show_view([Type.SEARCH], search)
