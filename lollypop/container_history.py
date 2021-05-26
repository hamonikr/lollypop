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

from pickle import dump, load

from lollypop.logger import Logger
from lollypop.define import LOLLYPOP_DATA_PATH


class HistoryContainer:
    """
        Navigation history
        Offload old items and reload them on the fly
    """

    __MAX_HISTORY_ITEMS = 4

    def __init__(self):
        """
            Init history
        """
        self.__items = []

    def add_view(self, view):
        """
            Add view to history
            @param view as View
        """
        if view.args is None:
            return
        view_class = view.__class__
        self.__items.append((view, view_class, view.args, view.sidebar_id,
                             view.selection_ids, view.position))
        # Offload history if too many items
        if self.count >= self.__MAX_HISTORY_ITEMS:
            (view, _class, args, sidebar_id,
             selection_ids, position) = self.__items[-self.__MAX_HISTORY_ITEMS]
            if view is not None:
                view.destroy()
                # This view can't be offloaded
                if args is None:
                    del self.__items[-self.__MAX_HISTORY_ITEMS]
                else:
                    self.__items[-self.__MAX_HISTORY_ITEMS] =\
                        (None, _class, args, sidebar_id,
                         selection_ids, position)

    def pop(self, index=-1):
        """
            Pop last view from history
            @param index as int
            @return View
        """
        try:
            if not self.__items:
                return None
            (view, _class, args, sidebar_id,
             selection_ids, position) = self.__items.pop(index)
            # View is offloaded, create a new one
            if view is None:
                view = self.__get_view_from_class(_class, args)
                view.set_sidebar_id(sidebar_id)
                view.set_selection_ids(selection_ids)
                view.set_populated_scrolled_position(position)
            return view
        except Exception as e:
            Logger.error("AdaptiveHistory::pop(): %s" % e)
            self.__items = []

    def remove(self, view):
        """
            Remove view from history
            @param view as View
        """
        for (_view, _class, args, sidebar_id,
             selection_ids, position) in self.__items:
            if _view == view:
                self.__items.remove((_view, _class, args, sidebar_id,
                                     selection_ids, position))
                break

    def clear(self):
        """
            Clear history
        """
        for (view, _class, args, sidebar_id,
             selection_ids, position) in self.__items:
            if view is not None:
                view.stop()
                view.destroy_later()
        self.__items = []

    def save(self):
        """
            Save history
        """
        try:
            history = []
            for (_view, _class, args, sidebar_id,
                 selection_ids, position) in self.__items[-50:]:
                history.append((None, _class, args, sidebar_id,
                                selection_ids, position))
            with open(LOLLYPOP_DATA_PATH + "/history.bin", "wb") as f:
                dump(history, f)
        except Exception as e:
            Logger.error("AdaptiveHistory::save(): %s" % e)

    def load(self):
        """
            Load history
        """
        try:
            self.__items = load(
                open(LOLLYPOP_DATA_PATH + "/history.bin", "rb"))
        except Exception as e:
            Logger.error("AdaptiveHistory::load(): %s" % e)

    def exists(self, view):
        """
            True if view exists in history
            @return bool
        """
        for (_view, _class, args, sidebar_id,
             selection_ids, position) in self.__items:
            if _view == view:
                return True
        return False

    @property
    def items(self):
        """
            Get history items
            @return [(View, class, {})]
        """
        return self.__items

    @property
    def count(self):
        """
            Get history item count
            @return int
        """
        return len(self.__items)

############
# PRIVATE  #
############
    def __get_view_from_class(self, _class, args):
        """
            Get view from history
            @param _class as class
            @param args as {}
            @return View
        """
        try:
            view = _class(**args)
            # Start populating the view
            if hasattr(view, "populate"):
                view.populate()
            view.show()
            return view
        except Exception as e:
            Logger.warning(
                "AdaptiveHistory::__get_view_from_class(): %s, %s",
                _class, e)
        return None
