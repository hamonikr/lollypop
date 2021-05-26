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

from gi.repository import GObject, Gtk

from lollypop.logger import Logger
from lollypop.container_history import HistoryContainer
from lollypop.utils import emit_signal


class StackContainer(Gtk.Stack):
    """
        A Gtk.Stack handling navigation
    """

    __gsignals__ = {
        "history-changed":   (GObject.SignalFlags.RUN_FIRST, None, ()),
        "set-sidebar-id":    (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "set-selection-ids": (GObject.SignalFlags.RUN_FIRST, None,
                              (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        """
            Init stack
        """
        Gtk.Stack.__init__(self)
        self.get_style_context().add_class("view")
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.__history = HistoryContainer()

    def add(self, view):
        """
            Add view to stack
            @param view as View
        """
        if view not in self.get_children():
            Gtk.Stack.add(self, view)

    def set_visible_child(self, view):
        """
            Set visible child in stack
            @param view as View
        """
        visible_child = self.get_visible_child()
        if visible_child == view:
            return
        elif visible_child is not None:
            visible_child.pause()
            if visible_child.__class__ != view.__class__ or\
                    visible_child.args != view.args:
                self.__history.add_view(visible_child)
            else:
                visible_child.destroy_later()
            Gtk.Stack.set_visible_child(self, view)
            emit_signal(self, "history-changed")
        else:
            Gtk.Stack.set_visible_child(self, view)

    def go_back(self):
        """
            Go back in stack
        """
        if self.__history:
            visible_child = self.get_visible_child()
            view = self.__history.pop()
            if view is not None:
                if view not in self.get_children():
                    self.add(view)
                Gtk.Stack.set_visible_child(self, view)
                if view.sidebar_id is not None:
                    emit_signal(self, "set-sidebar-id", view.sidebar_id)
                    emit_signal(self, "set-selection-ids", view.selection_ids)
                if visible_child is not None:
                    visible_child.stop()
                    visible_child.destroy_later()

    def remove(self, view):
        """
            Remove from stack and history
            @param view as View
        """
        if self.__history.exists(view):
            self.__history.remove(view)
        Gtk.Stack.remove(self, view)

    def save_history(self):
        """
            Save history to disk
        """
        visible_child = self.get_visible_child()
        if visible_child is not None:
            self.__history.add_view(visible_child)
        self.__history.save()

    def load_history(self):
        """
            Load history from disk
        """
        try:
            self.__history.load()
            view = self.__history.pop()
            if view is not None:
                self.add(view)
                Gtk.Stack.set_visible_child(self, view)
                if view.sidebar_id is not None:
                    emit_signal(self, "set-sidebar-id", view.sidebar_id)
                    emit_signal(self, "set-selection-ids", view.selection_ids)
        except Exception as e:
            Logger.error("AdaptiveStack::load_history(): %s", e)

    def clear(self):
        """
            Clear stack
        """
        for child in self.get_children():
            child.destroy()
        self.__history.clear()

    @property
    def history(self):
        """
            Get stack history
            @return [AdaptiveView]
        """
        return self.__history
