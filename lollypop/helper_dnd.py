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

from gi.repository import Gdk, Gtk, GLib, GObject

from lollypop.objects_album import Album
from lollypop.define import App
from lollypop.utils import set_cursor_type
from lollypop.widgets_row_album import AlbumRow
from lollypop.widgets_row_track import TrackRow


class DNDHelper(GObject.Object):
    """
        Helper for DND of AlbumsListView
    """

    __gsignals__ = {
        "dnd-insert": (GObject.SignalFlags.RUN_FIRST, None,
                       (GObject.TYPE_PYOBJECT, int)),
        "dnd-finished": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, listbox, view_type):
        """
            Init helper
            @param listbox as Gtk.ListBox
            @params view_type as ViewType
        """
        GObject.Object.__init__(self)
        self.__listbox = listbox
        self.__view_type = view_type
        self.__drag_begin_rows = []
        self.__autoscroll_timeout_id = None
        self.__begin_scrolled_y = 0
        self.__gesture = Gtk.GestureDrag.new(listbox)
        self.__gesture.set_button(Gdk.BUTTON_PRIMARY)
        self.__gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.__gesture.connect("drag-begin", self.__on_drag_begin)
        self.__gesture.connect("drag-end", self.__on_drag_end)
        self.__gesture.connect("drag-update", self.__on_drag_update)

    @property
    def gesture(self):
        """
            Get gesture
            @return Gtk.GestureDrag
        """
        return self.__gesture

#######################
# PRIVATE             #
#######################
    def __update_album_rows(self, start_index, end_index):
        """
            Merge album rows and update track position for indexes
        """
        def merge_if_possible(row1, row2):
            if row1 is None or row2 is None:
                return False
            if row1.album.id == row2.album.id:
                row1.tracks_view.append_rows(row2.album.tracks)
                row1.reveal(True)
                return True
            return False

        children = self.__listbox.get_children()[start_index:end_index]
        while children:
            row = children[0]
            index = row.get_index()
            next = self.__listbox.get_row_at_index(index + 1)
            if merge_if_possible(row, next):
                if next in children:
                    children.remove(next)
                self.__listbox.remove(next)
            else:
                children.pop(0)
        for album_row in self.__listbox.get_children():
            if album_row.album.id == App().player.current_track.album.id:
                for track_row in album_row.children:
                    if track_row.track.id == App().player.current_track.id:
                        App().player._current_track = track_row.track
        GLib.timeout_add(100, self.emit, "dnd-finished")

    def __do_drag_and_drop(self, src_rows, dest_row, direction):
        """
            Drag source rows at destination row with direction
            @param src_rows as [Row]
            @param dest_row as Row
            @param direction as Gtk.DirectionType
        """
        indexes = []
        # Build new rows
        new_rows = self.__get_rows_from_rows(
            src_rows, AlbumRow.get_best_height(dest_row))
        # Insert new rows
        if isinstance(dest_row, TrackRow):
            album_row = dest_row.get_ancestor(AlbumRow)
            if album_row is None:
                return
            # Destroy src_rows from album before split
            for row in src_rows:
                if isinstance(row, TrackRow):
                    if row.get_ancestor(AlbumRow) == album_row:
                        album_row.tracks_view.remove_row(row.track)
            indexes.append(album_row.get_index())
            split_album_row = self.__split_album_row(album_row,
                                                     dest_row,
                                                     direction)
            index = album_row.get_index()
            if split_album_row is not None:
                self.emit("dnd-insert", split_album_row, index)
                index += 1
            elif direction == Gtk.DirectionType.DOWN:
                index += 1
            for row in new_rows:
                self.emit("dnd-insert", row, index)
                index += 1
        else:
            index = dest_row.get_index()
            indexes.append(index)
            if direction == Gtk.DirectionType.DOWN:
                index += 1
            for row in new_rows:
                self.emit("dnd-insert", row, index)
                index += 1
        # Calculate update range
        for row in src_rows:
            if isinstance(row, TrackRow):
                album_row = row.get_ancestor(AlbumRow)
                if album_row is not None:
                    indexes.append(album_row.get_index())
            else:
                indexes.append(row.get_index())
        self.__destroy_rows(src_rows)
        self.__update_album_rows(max(0, min(indexes) - 1), max(indexes) + 1)

    def __split_album_row(self, album_row, track_row, direction):
        """
            Split album row at track row with direction
            @param album_row as AlbumRow
            @param track_row as TrackRow
            @param direction as Gtk.DirectionType
            @return AlbumRow
        """
        height = AlbumRow.get_best_height(album_row)
        children = album_row.children
        index = children.index(track_row)
        if direction == Gtk.DirectionType.DOWN:
            index += 1
            if index + 1 > len(children):
                return None
        elif index - 1 < 0:
            return None
        rows = album_row.children[:index]
        split_album = Album(album_row.album.id)
        split_album.set_tracks([row.track for row in rows])
        split_album_row = AlbumRow(split_album, height, self.__view_type)
        split_album_row.reveal()
        split_album_row.show()
        for row in rows:
            empty = album_row.album.remove_track(row.track)
            if empty:
                album_row.destroy()
            row.destroy()
        return split_album_row

    def __get_rows_from_rows(self, rows, height):
        """
            Build news rows from rows
            @param rows as [TrackRow/AlbumRow]
            @param height as int
            @return [AlbumRow]
        """
        new_rows = []
        for row in rows:
            if isinstance(row, TrackRow):
                # Merge with previous
                if new_rows and new_rows[-1].album.id == row.track.album.id:
                    new_rows[-1].tracks_view.append_row(row.track)
                # Create a new album
                else:
                    new_album = Album(row.track.album.id)
                    new_album.set_tracks([row.track])
                    new_album_row = AlbumRow(new_album, height,
                                             self.__view_type)
                    new_album_row.show()
                    new_album_row.reveal()
                    new_rows.append(new_album_row)
            else:
                # Merge with previous
                if new_rows and new_rows[-1].album.id == row.album.id:
                    new_rows[-1].tracks_view.append_rows(row.album.tracks)
                # Create a new album
                else:
                    new_album = Album(row.album.id)
                    new_album.set_tracks(row.album.tracks)
                    new_album_row = AlbumRow(new_album, height,
                                             self.__view_type)
                    new_album_row.populate()
                    new_album_row.show()
                    new_rows.append(new_album_row)
        return new_rows

    def __destroy_rows(self, rows):
        """
            Destroy rows and parent if needed
            @param rows as [Row]
        """
        for row in rows:
            if isinstance(row, TrackRow):
                album_row = row.get_ancestor(AlbumRow)
                if album_row is not None:
                    album_row.album.remove_track(row.track)
                    if album_row.album.id is None:
                        album_row.destroy()
            row.destroy()

    def __unmark_all_rows(self):
        """
            Undrag all rows
        """
        for row in self.__listbox.get_children():
            context = row.get_style_context()
            context.remove_class("drag-up")
            context.remove_class("drag-down")
            if row.revealed:
                for subrow in row.children:
                    context = subrow.get_style_context()
                    context.remove_class("drag-up")
                    context.remove_class("drag-down")

    def __get_row_at_y(self, y):
        """
            Get row at position
            @param y as int
            @return (Gtk.ListBox, Row)
        """
        row = self.__listbox.get_row_at_y(y)
        if row is not None and row.revealed:
            (listbox, subrow) = self.__get_subrow_at_y(row, y)
            if subrow is not None:
                return (listbox, subrow)
        return (self.__listbox, row)

    def __get_subrow_at_y(self, album_row, y):
        """
            Get subrow as position
            @param album_row as AlbumRow
            @param y as int
            @return (Gtk.ListBox, Row)
        """
        if album_row is not None:
            listbox = album_row.listbox
            t = listbox.translate_coordinates(self.__listbox, 0, 0)
            if t is not None:
                track_row = listbox.get_row_at_y(y - t[1])
                if track_row is not None:
                    return (listbox, track_row)
        return (None, None)

    def __autoscroll(self, scrolled, y):
        """
            Auto scroll up/down
            @param scrolled as Gtk.ScrolledWindow
            @param y as int
        """
        adj = scrolled.get_vadjustment()
        value = adj.get_value()
        adj_value = value + y
        adj.set_value(adj_value)
        if adj.get_value() <= adj.get_lower() or\
                adj.get_value() >= adj.get_upper() - adj.get_page_size():
            self.__autoscroll_timeout_id = None
            return False
        return True

    def __on_drag_begin(self, gesture, x, y):
        """
            @param gesture as Gtk.GestureDrag
            @param x as int
            @param y as int
        """
        self.__drag_begin_rows = []
        (listbox, row) = self.__get_row_at_y(y)
        if row is not None:
            self.__drag_begin_rows += [row]
        for row in listbox.get_selected_rows():
            if row not in self.__drag_begin_rows:
                self.__drag_begin_rows.append(row)
        scrolled = self.__listbox.get_ancestor(Gtk.ScrolledWindow)
        if scrolled is not None and row is not None:
            (scrolled_x,
             self.__begin_scrolled_y) = row.translate_coordinates(scrolled,
                                                                  0, 0)

    def __on_drag_end(self, gesture, x, y):
        """
            @param gesture as Gtk.GestureDrag
            @param x as int
            @param y as int
        """
        set_cursor_type(self.__listbox, "default")
        self.__unmark_all_rows()
        if self.__autoscroll_timeout_id is not None:
            GLib.source_remove(self.__autoscroll_timeout_id)
            self.__autoscroll_timeout_id = None
        if x == 0 or y == 0:
            return
        (active, start_x, start_y) = gesture.get_start_point()
        if not active:
            return
        y += start_y
        (listbox, row) = self.__get_row_at_y(y)
        if row is None or row in self.__drag_begin_rows:
            return
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        if self.__drag_begin_rows:
            row_height = row.get_allocated_height()
            (row_x, row_y) = row.translate_coordinates(self.__listbox,
                                                       0, 0)
            if y < row_y + row_height / 2:
                direction = Gtk.DirectionType.UP
            elif y > row_y - row_height / 2:
                direction = Gtk.DirectionType.DOWN
            GLib.idle_add(self.__do_drag_and_drop,
                          self.__drag_begin_rows,
                          row, direction)

    def __on_drag_update(self, gesture, x, y):
        """
            Add style
            @param gesture as Gtk.GestureDrag
            @param x as int
            @param y as int
        """
        if self.__autoscroll_timeout_id is not None:
            GLib.source_remove(self.__autoscroll_timeout_id)
            self.__autoscroll_timeout_id = None
        self.__unmark_all_rows()
        set_cursor_type(self.__listbox, "dnd-move")
        (active, start_x, start_y) = gesture.get_start_point()
        if not active:
            return
        current_y = y + start_y
        (ignore, row) = self.__get_row_at_y(current_y)
        if row is None:
            return
        row_height = row.get_allocated_height()
        (row_x, row_y) = row.translate_coordinates(self.__listbox, 0, 0)
        if current_y < row_y + 20:
            row.get_style_context().add_class("drag-up")
        elif current_y > row_y + row_height - 20:
            row.get_style_context().add_class("drag-down")
        scrolled = self.__listbox.get_ancestor(Gtk.ScrolledWindow)
        if scrolled is None:
            return
        (scrolled_x, scrolled_y) = row.translate_coordinates(scrolled, 0, 0)
        diff = self.__begin_scrolled_y - scrolled_y
        if abs(diff) < 100:
            return
        self.__autoscroll_timeout_id = GLib.idle_add(self.__autoscroll,
                                                     scrolled,
                                                     -diff / 10000)
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
