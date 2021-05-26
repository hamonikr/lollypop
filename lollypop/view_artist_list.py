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

from lollypop.define import ViewType, MARGIN, App
from lollypop.utils import set_cursor_type
from lollypop.widgets_banner_artist import ArtistBannerWidget
from lollypop.widgets_album import AlbumWidget
from lollypop.objects_album import Album
from lollypop.view_lazyloading import LazyLoadingView
from lollypop.helper_size_allocation import SizeAllocationHelper
from lollypop.helper_signals import SignalsHelper, signals_map


class ArtistViewList(LazyLoadingView, SignalsHelper, SizeAllocationHelper):
    """
        Show artist albums in a list with tracks
    """

    @signals_map
    def __init__(self, genre_ids, artist_ids, storage_type, view_type):
        """
            Init ArtistView
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        LazyLoadingView.__init__(self, storage_type,
                                 view_type |
                                 ViewType.OVERLAY |
                                 ViewType.ARTIST)
        self.__boxes = []
        self.__others_boxes = []
        self.__width = 0
        self.__boxes_count = 0
        self.__current_box = 0
        self.__albums_count = 0
        self.__hovered_child = None
        self.__genre_ids = genre_ids
        self.__artist_ids = artist_ids
        self.__storage_type = storage_type
        self.__banner = ArtistBannerWidget(genre_ids, artist_ids,
                                           storage_type, self.view_type)
        self.__banner.show()
        self.__main_grid = Gtk.Grid.new()
        self.__main_grid.show()
        self.__main_grid.set_orientation(Gtk.Orientation.VERTICAL)
        self.__boxes_grid = Gtk.Grid.new()
        self.__boxes_grid.show()
        self.__boxes_grid.set_valign(Gtk.Align.START)
        self.__boxes_grid.set_halign(Gtk.Align.CENTER)
        self.__main_grid.add(self.__boxes_grid)
        self.add_widget(self.__main_grid, self.__banner)
        self.connect("populated", self.__on_populated)
        if App().settings.get_value("force-single-column"):
            self.__column_width = 1200
        else:
            self.__column_width = 600
        if App().animations:
            self.__event_controller = Gtk.EventControllerMotion.new(self)
            self.__event_controller.connect("motion", self.__on_motion)
        SizeAllocationHelper.__init__(self)
        return [
            (App().player, "current-changed", "_on_current_changed"),
        ]

    def populate(self):
        pass

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"genre_ids": self.__genre_ids,
                "artist_ids": self.__artist_ids,
                "storage_type": self.storage_type,
                "view_type": self.view_type}

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        filtered = []
        boxes_count = len(self.__boxes)
        for i in range(0, boxes_count):
            for child in self.__boxes[i].get_children():
                if isinstance(child, AlbumWidget):
                    filtered.append(child)
                    filtered += child.filtered
                else:
                    filtered += child.children
        return filtered

    @property
    def scroll_shift(self):
        """
            Get scroll shift for y axes
            @return int
        """
        return self.__banner.height + MARGIN

#######################
# PROTECTED           #
#######################
    def _get_child(self, album_id):
        """
            Get an album view widget
            @param album_id as int
            @return AlbumView
        """
        if self.destroyed:
            return None
        album = Album(album_id, self.__genre_ids, self.__artist_ids)
        widget = AlbumWidget(album,
                             self.storage_type,
                             ViewType.ARTIST)
        widget.show()
        widget.set_property("valign", Gtk.Align.START)
        box = self.__get_box_at_index(self.__current_box)
        box.add(widget)
        box.show()
        self.__current_box += 1
        if self.__current_box == self.__boxes_count:
            self.__current_box = 0
        return widget

    def _handle_width_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
            @return bool
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            if allocation.width != self.__width:
                self.__width = allocation.width
                boxes_count = self.__width // self.__column_width
                if boxes_count < 1:
                    boxes_count = 1
                if self.__boxes_count == boxes_count:
                    return
                self.__boxes_count = boxes_count
                # Rework content
                if self.is_populated:
                    children = self.__get_children_sorted()
                    self.__remove_children()
                    self.__populate(children)
                else:
                    album_ids = App().albums.get_ids(self.__genre_ids,
                                                     self.__artist_ids,
                                                     self.storage_type,
                                                     True)
                    self.__albums_count = len(album_ids)
                    LazyLoadingView.populate(self, album_ids)
                return True
        return False

    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        boxes_count = len(self.__boxes)
        for i in range(0, boxes_count):
            for child in self.__boxes[i].get_children():
                child.set_selection()

#######################
# PRIVATE             #
#######################
    def __get_box_at_index(self, index):
        """
            Get album box at index, add new ones if index out of range
            @param index as int
            @return Gtk.Box
        """
        while len(self.__boxes) <= index:
            box = Gtk.Box.new(Gtk.Orientation.VERTICAL, MARGIN)
            box.set_valign(Gtk.Align.START)
            box.set_property("margin", MARGIN)
            self.__boxes.append(box)
            self.__boxes_grid.add(box)
        return self.__boxes[index]

    def __populate(self, children):
        """
            Populate children
            @param children as [AlbumWidget]
        """
        self.__current_box = 0
        for child in children:
            box = self.__get_box_at_index(self.__current_box)
            box.show()
            box.add(child)
            self.__current_box += 1
            if self.__current_box == self.__boxes_count:
                self.__current_box = 0

    def __get_children_sorted(self):
        """
            Get children sorted (insert order)
            @return [Gtk.Widget]
        """
        boxes_count = len(self.__boxes)
        children = {}
        for i in range(0, boxes_count):
            children[i] = self.__boxes[i].get_children()
        sorted_children = []
        not_found = 0
        while not_found != boxes_count:
            not_found = 0
            for i in range(0, boxes_count):
                if children[i]:
                    child = children[i].pop(0)
                    sorted_children.append(child)
                else:
                    not_found += 1
        return sorted_children

    def __remove_children(self):
        """
            Remove children from boxes
        """
        boxes_count = len(self.__boxes)
        for i in range(0, boxes_count):
            self.__boxes[i].hide()
            children = self.__boxes[i].get_children()
            for child in children:
                self.__boxes[i].remove(child)

    def __unselect_selected(self):
        """
            Unselect selected child
        """
        if self.__hovered_child is not None:
            self.__hovered_child.unset_state_flags(
                Gtk.StateFlags.VISITED)
            set_cursor_type(self.__hovered_child.banner, "left_ptr")
            self.__hovered_child = None

    def __on_populated(self, view):
        """
            Add appears on albums
            @param view as ArtistViewBox
        """
        if self.__albums_count == 1:
            self.__boxes[0].get_children()[0].reveal_child()
        from lollypop.view_albums_line import AlbumsArtistAppearsOnLineView
        others_box = AlbumsArtistAppearsOnLineView(self.__artist_ids,
                                                   self.__genre_ids,
                                                   self.storage_type,
                                                   ViewType.SMALL |
                                                   ViewType.SCROLLED)
        others_box.set_margin_start(MARGIN)
        others_box.set_margin_end(MARGIN)
        others_box.populate()
        self.__main_grid.add(others_box)
        self.__others_boxes.append(others_box)

    def __on_motion(self, event_controller, x, y):
        """
            Update current selected child
            @param event_controller as Gtk.EventControllerMotion
            @param x as int
            @param y as int
        """
        hovered_child = None
        for i in range(0, len(self.__boxes)):
            for child in self.__boxes[i].get_children():
                (tx, ty) = child.translate_coordinates(self, 0, 0)
                width = child.get_allocated_width()
                height = child.get_allocated_height()
                if x > tx and x < tx + width and y > ty and y < ty + height:
                    hovered_child = child
                    break
        if hovered_child == self.__hovered_child:
            return
        elif hovered_child is not None:
            hovered_child.set_state_flags(Gtk.StateFlags.VISITED, False)
            self.__unselect_selected()
            self.__hovered_child = hovered_child
            set_cursor_type(hovered_child.banner)
        else:
            self.__unselect_selected()
