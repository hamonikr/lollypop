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

from lollypop.logger import Logger
from lollypop.selectionlist import SelectionList
from lollypop.define import App, Type, SelectionListMask, StorageType, ViewType
from lollypop.shown import ShownLists
from lollypop.helper_gestures import GesturesHelper
from lollypop.view import View
from lollypop.utils import emit_signal, get_default_storage_type


class NoneView(View):
    """
        A view that do nothing
    """

    def __init__(self):
        View.__init__(self, StorageType.COLLECTION, ViewType.DEFAULT)

    @property
    def args(self):
        return None


class ListsContainer:
    """
        Selections lists management for main view
    """

    def __init__(self):
        """
            Init container
        """
        self.__left_list = None
        self.__right_list = None
        self._sidebar = SelectionList(SelectionListMask.SIDEBAR)
        self._sidebar.show()
        self._sidebar.listbox.connect("row-activated",
                                      self.__on_sidebar_activated)
        self._sidebar.connect("populated", self.__on_sidebar_populated)
        items = ShownLists.get(SelectionListMask.SIDEBAR)
        self._sidebar.populate(items)
        self._stack.connect("set-sidebar-id", self.__on_set_sidebar_id)
        self._stack.connect("set-selection-ids", self.__on_set_selection_ids)

    @property
    def sidebar(self):
        """
            Get first SelectionList
            @return SelectionList
        """
        return self._sidebar

    @property
    def left_list(self):
        """
            Get left selection list
            @return SelectionList
        """
        if self.__left_list is None:
            self.__left_list = SelectionList(SelectionListMask.FASTSCROLL)
            self.__left_list.listbox.connect("row-activated",
                                             self.__on_left_list_activated)
            self.__left_list.scrolled.set_size_request(300, -1)
        return self.__left_list

    @property
    def right_list(self):
        """
            Get right selection list
            @return SelectionList
        """
        def on_unmap(widget):
            """
                Hide right list on left list hidden
            """
            if not App().window.folded:
                self._hide_right_list()

        if self.__right_list is None:
            eventbox = Gtk.EventBox.new()
            eventbox.set_size_request(50, -1)
            eventbox.show()
            self.__right_list_grid = Gtk.Grid()
            style_context = self.__right_list_grid.get_style_context()
            style_context.add_class("left-gradient")
            style_context.add_class("opacity-transition-fast")
            self.__right_list = SelectionList(SelectionListMask.FASTSCROLL)
            self.__right_list.show()
            self.__right_list.scrolled.set_size_request(250, -1)
            self.__gesture = GesturesHelper(
                eventbox, primary_press_callback=self._hide_right_list)
            self.__right_list.listbox.connect("row-activated",
                                              self.__on_right_list_activated)
            self.__right_list_grid.add(eventbox)
            self.__right_list_grid.add(self.__right_list)
            self.__left_list.overlay.add_overlay(self.__right_list_grid)
            self.__left_list.connect("unmap", on_unmap)
            self.__left_list.connect("populated", self.__on_list_populated)
            self.__right_list.connect("populated", self.__on_list_populated)
        return self.__right_list

    @property
    def sidebar_id(self):
        """
            Get sidebar id for current state
            @return int
        """
        if self.right_list.selected_ids:
            ids = self.right_list.selected_ids
        elif self.left_list.selected_ids:
            ids = self.left_list.selected_ids
        else:
            ids = self.sidebar.selected_ids
        return ids[0] if ids else Type.NONE

##############
# PROTECTED  #
##############
    def _show_genres_list(self, selection_list):
        """
            Setup list for genres
            @param list as SelectionList
        """
        def load():
            genres = App().genres.get()
            return genres
        selection_list.set_mask(SelectionListMask.GENRES)
        App().task_helper.run(load, callback=(selection_list.populate,))

    def _show_artists_list(self, selection_list, genre_ids=[]):
        """
            Setup list for artists
            @param list as SelectionList
            @param genre_ids as [int]
        """
        def load():
            storage_type = get_default_storage_type()
            artists = App().artists.get(genre_ids, storage_type)
            return artists
        selection_list.set_mask(SelectionListMask.ARTISTS)
        App().task_helper.run(load, callback=(selection_list.populate,))

    def _show_right_list(self):
        """
            Show right list
        """
        if self.__right_list is not None:
            self.__right_list_grid.show()
            self.__right_list_grid.set_state_flags(Gtk.StateFlags.VISITED,
                                                   False)
            self.set_focused_view(self.right_list)

    def _hide_right_list(self, *ignore):
        """
            Hide right list
        """
        if self.__right_list is not None:
            self.__right_list_grid.unset_state_flags(Gtk.StateFlags.VISITED)
            GLib.timeout_add(200, self.__right_list_grid.hide)
            self.__right_list.clear()
            self.set_focused_view(self.left_list)

############
# PRIVATE  #
############
    def __on_sidebar_activated(self, listbox, row):
        """
            Update view based on selected object
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        Logger.debug("Container::__on_sidebar_activated()")
        self.sub_widget.set_visible_child(self.grid_view)
        view = None
        focus_set = False
        selected_id = self._sidebar.selected_id
        if selected_id is None:
            return
        # Update lists
        if selected_id in [Type.ARTISTS_LIST, Type.GENRES_LIST] and\
                self.type_ahead.get_reveal_child() and\
                self.left_list.get_visible():
            self.set_focused_view(self.left_list)
            focus_set = True
        elif selected_id == Type.ARTISTS_LIST:
            self._show_artists_list(self.left_list)
            self._hide_right_list()
            self.left_list.show()
            self.widget.set_visible_child(self.sub_widget)
            self.sub_widget.set_visible_child(self.left_list)
            self.set_focused_view(self.left_list)
            focus_set = True
        elif selected_id == Type.GENRES_LIST:
            self._show_genres_list(self.left_list)
            self._hide_right_list()
            self.left_list.show()
            self.widget.set_visible_child(self.sub_widget)
            self.sub_widget.set_visible_child(self.left_list)
            self.set_focused_view(self.left_list)
            focus_set = True
        else:
            self.left_list.hide()
            self.left_list.clear()
            if self.widget.get_folded():
                self.widget.set_visible_child(self.sub_widget)
                self.sub_widget.set_visible_child(self.grid_view)

        storage_type = get_default_storage_type()
        if selected_id in [Type.ARTISTS_LIST, Type.GENRES_LIST] and not\
                App().window.folded:
            view = NoneView()
            view.show()
        elif selected_id == Type.PLAYLISTS:
            view = self._get_view_playlists()
        elif selected_id == Type.LYRICS:
            view = self._get_view_lyrics()
        elif selected_id == Type.CURRENT:
            view = self.get_view_current()
        elif selected_id == Type.SEARCH:
            view = self.get_view_search()
        elif selected_id == Type.INFO:
            view = self._get_view_info()
        elif selected_id == Type.SUGGESTIONS:
            view = self._get_view_suggestions(storage_type)
        elif selected_id in [Type.POPULARS,
                             Type.LOVED,
                             Type.RECENTS,
                             Type.LITTLE,
                             Type.RANDOMS]:
            view = self._get_view_albums([selected_id], [], storage_type)
        elif selected_id == Type.WEB:
            view = self._get_view_albums([selected_id], [], StorageType.SAVED)
        elif selected_id == Type.YEARS:
            view = self._get_view_albums_decades(storage_type)
        elif selected_id == Type.GENRES:
            view = self._get_view_genres(storage_type)
        elif selected_id == Type.ARTISTS:
            view = self._get_view_artists_rounded(storage_type)
        elif selected_id == Type.ALL:
            view = self._get_view_albums([selected_id], [], storage_type)
        elif selected_id == Type.COMPILATIONS:
            view = self._get_view_albums([selected_id], [], storage_type)
        if view is not None and view not in self._stack.get_children():
            view.show()
            self._stack.add(view)
        if view is not None:
            self._stack.set_visible_child(view)
            if not focus_set:
                self.set_focused_view(view)
        emit_signal(self, "can-go-back-changed", self.can_go_back)

    def __on_sidebar_populated(self, selection_list):
        """
            @param selection_list as SelectionList
        """
        if App().settings.get_value("save-state"):
            self._stack.load_history()
            emit_signal(self, "can-go-back-changed", self.can_go_back)
        else:
            startup_id = App().settings.get_value("startup-id").get_int32()
            if startup_id == -1:
                selection_list.select_first()
            else:
                selection_list.select_ids([startup_id], True)

    def __on_left_list_activated(self, listbox, row):
        """
            Update view based on selected object
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        Logger.debug("Container::__on_left_list_activated()")
        selected_ids = self.left_list.selected_ids
        view = None
        storage_type = get_default_storage_type()
        if self.left_list.mask & SelectionListMask.GENRES:
            if not App().window.folded:
                view = self._get_view_albums(selected_ids, [], storage_type)
            self._show_artists_list(self.right_list, selected_ids)
            self._show_right_list()
        else:
            view = self._get_view_artists([], selected_ids, storage_type)
            self.set_focused_view(view)
            self.sub_widget.set_visible_child(self.grid_view)
        if view is not None:
            view.show()
            self._stack.add(view)
            self._stack.set_visible_child(view)

    def __on_right_list_activated(self, listbox, row):
        """
            Update view based on selected object
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        storage_type = get_default_storage_type()
        genre_ids = self.left_list.selected_ids
        artist_ids = self.right_list.selected_ids
        view = self._get_view_artists(genre_ids, artist_ids, storage_type)
        view.show()
        self._stack.add(view)
        self._stack.set_visible_child(view)
        self.set_focused_view(view)
        self.sub_widget.set_visible_child(self.grid_view)

    def __on_list_populated(self, selection_list):
        """
            Select pending ids
            @param selection_list as SelectionList
        """
        selection_list.select_pending_ids()

    def __on_set_sidebar_id(self, stack, sidebar_id):
        """
            Set sidebar id on container
            @param stack as ContainerStack
            @param sidebar_id as int
        """
        self._sidebar.select_ids([sidebar_id], False)

    def __on_set_selection_ids(self, stack, selection_ids):
        """
            Set sidebar id and left/right list ids
            @param stack as ContainerStack
            @param selection_ids as {"left": [int], "right": [int])
        """
        # Restore left list
        if selection_ids["left"]:
            if self.left_list.selected_ids != selection_ids["left"]:
                self.left_list.show()
                if self.left_list.count == 0:
                    self.left_list.set_selection_pending_ids(
                        selection_ids["left"])
                    if App().window.container.sidebar.selected_ids[0] ==\
                            Type.GENRES_LIST:
                        self._show_genres_list(self.left_list)
                    else:
                        self._show_artists_list(self.left_list)
                else:
                    self.left_list.select_ids(selection_ids["left"], False)
                    self.left_list.show()
        else:
            self.left_list.hide()
            self.left_list.clear()
        # Restore right list
        if selection_ids["right"]:
            if self.right_list.selected_ids != selection_ids["right"]:
                self.right_list.set_selection_pending_ids(
                                        selection_ids["right"])
                self._show_artists_list(self.right_list,
                                        selection_ids["left"])
                self._show_right_list()
        else:
            self._hide_right_list()
