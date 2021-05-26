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

from gi.repository import GLib, GObject

from time import time

from lollypop.define import LoadingState, App
from lollypop.logger import Logger
from lollypop.view import View
from lollypop.utils import emit_signal


class LazyLoadingView(View):
    """
        Lazy loading for view
    """

    __gsignals__ = {
        # View has been populated/depopulated, children are not populated
        "initialized": (GObject.SignalFlags.RUN_FIRST, None, ()),
        # All children are populated
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, storage_type, view_type):
        """
            Init lazy loading
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        View.__init__(self, storage_type, view_type)
        self.__loading_state = LoadingState.NONE
        self.__lazy_queue = []
        self.__priority_queue = []
        self.__scroll_timeout_id = None
        self.__start_time = time()

    def populate(self, values):
        """
            Populate view with values
            @param values as [object]
        """
        self.__add_values(values)

    def pause(self):
        """
            Pause loading
        """
        self.__loading_state = LoadingState.ABORTED
        if self.__scroll_timeout_id is not None:
            GLib.source_remove(self.__scroll_timeout_id)
            self.__scroll_timeout_id = None
        View.stop(self)

    def stop(self):
        """
            Stop loading and clear queue
        """
        self.__loading_state = LoadingState.FINISHED
        if self.__scroll_timeout_id is not None:
            GLib.source_remove(self.__scroll_timeout_id)
            self.__scroll_timeout_id = None
        self.__lazy_queue = []
        self.__priority_queue = []
        View.stop(self)

    def lazy_loading(self):
        """
            Load the view in a lazy way
        """
        self.__loading_state = LoadingState.RUNNING
        self.__lazy_loading()

    def queue_lazy_loading(self, widget):
        """
            Queue widget into lazy loading
            @param widget as Gtk.Widget
        """
        self.__lazy_queue.append(widget)

    def set_scrolled(self, scrolled):
        """
            Add an external scrolled window
            @param scrolled as Gtk.ScrolledWindow
        """
        View.set_scrolled(self, scrolled)
        scrolled.get_vadjustment().connect("value-changed",
                                           self._on_value_changed)

    @property
    def is_populated(self):
        """
            True if populated
            @return bool
        """
        return self.__loading_state == LoadingState.FINISHED

#######################
# PROTECTED           #
#######################
    def _get_child(self, value):
        """
            Get child for value
            @param value as object
            @return object
        """
        return None

    def _on_map(self, widget):
        """
            Restore backup and load
            @param widget as Gtk.Widget
        """
        View._on_map(self, widget)
        if self.__loading_state == LoadingState.ABORTED and self.__lazy_queue:
            self.lazy_loading()

    def _on_value_changed(self, adj):
        """
            Update scroll value and check for lazy queue
            @param adj as Gtk.Adjustment
        """
        View._on_value_changed(self, adj)
        if not self.__lazy_queue:
            return False
        if self.__scroll_timeout_id is not None:
            GLib.source_remove(self.__scroll_timeout_id)
        self.__scroll_timeout_id = GLib.timeout_add(200, self.__lazy_or_not)

    def _on_populated(self, widget):
        """
            Add another album/disc
            @param widget as AlbumWidget/TracksView
        """
        if self.__loading_state != LoadingState.RUNNING:
            return
        if not widget.is_populated:
            widget.populate()
        else:
            # Do not remove this idle_add()
            # RecursionError: maximum recursion depth exceeded
            GLib.idle_add(self.__lazy_loading)

#######################
# PRIVATE             #
#######################
    def __lazy_loading(self):
        """
            Load the view in a lazy way
        """
        widget = None
        if self.__priority_queue:
            widget = self.__priority_queue.pop(0)
            self.__lazy_queue.remove(widget)
        elif self.__lazy_queue:
            widget = self.__lazy_queue.pop(0)

        if widget is not None:
            widget.connect("populated", self._on_populated)
            widget.populate()
        else:
            self.__loading_state = LoadingState.FINISHED
            emit_signal(self, "populated")
            # Apply filtering
            if App().window.container.type_ahead.get_reveal_child():
                text = App().window.container.type_ahead.entry.get_text()
                if text:
                    self.search_for_child(text)
                else:
                    GLib.idle_add(
                        App().window.container.type_ahead.entry.grab_focus)
            Logger.debug("LazyLoadingView::lazy_loading(): %s",
                         time() - self.__start_time)

    def __add_values(self, values):
        """
            Add widget from values
            @param values as []
        """
        if values:
            value = values.pop(0)
            child = self._get_child(value)
            if child is not None:
                self.__lazy_queue.append(child)
            GLib.idle_add(self.__add_values, values)
        elif self.__loading_state != LoadingState.RUNNING:
            self.__loading_state = LoadingState.RUNNING
            emit_signal(self, "initialized")
            self.__lazy_loading()

    def __is_visible(self, widget):
        """
            Is widget visible in scrolled
            @param widget as Gtk.Widget
        """
        widget_alloc = widget.get_allocation()
        scrolled_alloc = self.scrolled.get_allocation()
        try:
            (x, y) = widget.translate_coordinates(self.scrolled, 0, 0)
            return (y > -widget_alloc.height or y >= 0) and\
                y < scrolled_alloc.height
        except:
            return True

    def __lazy_or_not(self):
        """
            Add visible widgets to lazy queue
        """
        self.__scroll_timeout_id = None
        if self.__loading_state == LoadingState.RUNNING:
            self.__priority_queue = []
            for child in self.__lazy_queue:
                if self.__is_visible(child):
                    self.__priority_queue.append(child)
