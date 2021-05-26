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

from lollypop.utils import popup_widget
from lollypop.view_lazyloading import LazyLoadingView
from lollypop.define import App, ViewType, MARGIN, StorageType
from lollypop.widgets_row_album import AlbumRow
from lollypop.widgets_listbox import ListBox
from lollypop.helper_gestures import GesturesHelper
from lollypop.helper_signals import SignalsHelper, signals_map


class AlbumsListView(LazyLoadingView, SignalsHelper, GesturesHelper):
    """
        View showing albums
    """

    @signals_map
    def __init__(self, genre_ids, artist_ids, view_type):
        """
            Init widget
            @param genre_ids as int
            @param artist_ids as int
            @param view_type as ViewType
        """
        LazyLoadingView.__init__(self, StorageType.ALL, view_type)
        self.__genre_ids = genre_ids
        self.__artist_ids = artist_ids
        self.__reveals = []
        # Calculate default album height based on current pango context
        # We may need to listen to screen changes
        self.__height = AlbumRow.get_best_height(self)
        self._box = ListBox()
        self._box.set_margin_bottom(MARGIN)
        self._box.set_margin_end(MARGIN)
        self._box.get_style_context().add_class("trackswidget")
        self._box.set_vexpand(True)
        self._box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._box.show()
        GesturesHelper.__init__(self, self._box)
        if view_type & ViewType.DND:
            from lollypop.helper_dnd import DNDHelper
            self.__dnd_helper = DNDHelper(self._box, view_type)
            self.__dnd_helper.connect("dnd-insert", self.__on_dnd_insert)
        return [
            (App().player, "current-changed", "_on_current_changed"),
            (App().album_art, "album-artwork-changed", "_on_artwork_changed")
        ]

    def add_reveal_albums(self, albums):
        """
            Add albums to reveal list
            @param albums as [Album]
        """
        self.__reveals += list(albums)

    def add_value(self, album):
        """
            Insert item
            @param album as Album
        """
        # Merge album if previous is same
        if self.children and self.children[-1].album.id == album.id:
            track_ids = self.children[-1].album.track_ids
            for track in album.tracks:
                if track.id not in track_ids:
                    self.children[-1].tracks_view.append_row(track)
        else:
            LazyLoadingView.populate(self, [album])

    def insert_row(self, row, index):
        """
            Insert row at index
            @param row as AlbumRow
            @param index as int
        """
        row.connect("activated", self._on_row_activated)
        row.connect("destroy", self._on_row_destroy)
        row.connect("track-removed", self._on_track_removed)
        row.show()
        self._box.insert(row, index)

    def populate(self, albums):
        """
            Populate widget with album rows
            @param albums as [Album]
        """
        for child in self._box.get_children():
            self._box.remove(child)
        LazyLoadingView.populate(self, albums)

    def clear(self):
        """
            Clear the view
        """
        self.stop()
        self.__reveals = []
        for child in self._box.get_children():
            self._box.remove(child)

    def jump_to_current(self):
        """
            Scroll to album
        """
        y = self.__get_current_ordinate()
        if y is not None:
            self.scrolled.get_vadjustment().set_value(y)

    def destroy(self):
        """
            Force destroying the box
            Help freeing memory, no idea why
        """
        self._box.destroy()
        LazyLoadingView.destroy(self)

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"genre_ids": self.__genre_ids,
                "artist_ids": self.__artist_ids,
                "view_type": self.view_type & ~ViewType.SMALL}

    @property
    def dnd_helper(self):
        """
            Get Drag & Drop helper
            @return DNDHelper
        """
        return self.__dnd_helper

    @property
    def box(self):
        """
            Get album list box
            @return Gtk.ListBox
        """
        return self._box

    @property
    def children(self):
        """
            Get view children
            @return [AlbumRow]
        """
        return self._box.get_children()

#######################
# PROTECTED           #
#######################
    def _get_child(self, album):
        """
            Get an album view widget
            @param album as Album
            @return AlbumRow
        """
        if self.destroyed:
            return None
        row = AlbumRow(album, self.__height, self.view_type)
        row.connect("activated", self._on_row_activated)
        row.connect("destroy", self._on_row_destroy)
        row.connect("track-removed", self._on_track_removed)
        row.show()
        self._box.add(row)
        return row

    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        for child in self._box.get_children():
            child.set_selection()

    def _on_artwork_changed(self, artwork, album_id):
        """
            Update children artwork if matching album id
            @param artwork as Artwork
            @param album_id as int
        """
        for child in self._box.get_children():
            if child.album.id == album_id:
                child.set_artwork()

    def _on_primary_long_press_gesture(self, x, y):
        """
            Show row menu
            @param x as int
            @param y as int
        """
        self.__popup_menu(x, y)

    def _on_primary_press_gesture(self, x, y, event):
        """
            Activate current row
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        row = self._box.get_row_at_y(y)
        if row is None:
            return
        self._box.set_selection_mode(Gtk.SelectionMode.NONE)
        row.reveal()

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        self._on_primary_long_press_gesture(x, y)

    def _on_populated(self, widget):
        """
            Add another album/disc
            @param widget as AlbumWidget/TracksView
        """
        if widget.album in self.__reveals:
            widget.reveal()
            self.__reveals.remove(widget.album)
        else:
            LazyLoadingView._on_populated(self, widget)

    def _on_row_activated(self, row, track):
        pass

    def _on_row_destroy(self, row):
        pass

    def _on_track_removed(self, row, track):
        pass

#######################
# PRIVATE             #
#######################
    def __get_current_ordinate(self):
        """
            If current track in widget, return it ordinate,
            @return y as int
        """
        y = None
        for child in self._box.get_children():
            if child.album == App().player.current_track.album:
                child.reveal(True)
                y = child.translate_coordinates(self._box, 0, 0)[1]
        return y

    def __popup_menu(self, x, y):
        """
            Popup menu for album
            @param x as int
            @param y as int
        """
        row = self._box.get_row_at_y(y)
        if row is None:
            return
        # First check it's not a track gesture
        if row.revealed:
            for track_row in row.listbox.get_children():
                coordinates = track_row.translate_coordinates(self._box, 0, 0)
                if coordinates is not None and\
                        coordinates[1] < y and\
                        coordinates[1] + track_row.get_allocated_height() > y:
                    track_row.popup_menu(self._box, x, y)
                    return
        # Then handle album gesture
        from lollypop.menu_objects import AlbumMenu
        from lollypop.widgets_menu import MenuBuilder
        menu = AlbumMenu(row.album, ViewType.ALBUM, self.view_type)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, self._box, x, y, row)

    def __reveal_row(self, row):
        """
            Reveal row if style always present
        """
        style_context = row.get_style_context()
        if style_context.has_class("drag-down"):
            row.reveal(True)

    def __on_dnd_insert(self, dnd_helper, row, index):
        """
            Insert row at index
            @param dnd_helper as DNDHelper
            @param row as AlbumRow
            @param index as int
        """
        self.insert_row(row, index)
