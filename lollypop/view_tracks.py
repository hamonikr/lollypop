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

from gi.repository import Gtk, GObject, GLib


from lollypop.widgets_tracks import TracksWidget
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.define import App, ViewType, IndicatorType
from lollypop.define import Size
from lollypop.utils import emit_signal
from lollypop.helper_size_allocation import SizeAllocationHelper


class TracksView(Gtk.Bin, SignalsHelper, SizeAllocationHelper):
    """
        Responsive view showing tracks
    """

    __gsignals__ = {
        "activated": (GObject.SignalFlags.RUN_FIRST,
                      None, (GObject.TYPE_PYOBJECT,)),
        "selected": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "track-removed": (GObject.SignalFlags.RUN_FIRST, None,
                          (GObject.TYPE_PYOBJECT,)),
    }

    @signals_map
    def __init__(self, view_type):
        """
            Init view
            @param album as Album
            @param view_type as ViewType
        """
        Gtk.Bin.__init__(self)
        self._view_type = view_type
        self._tracks_widget_left = {}
        self._tracks_widget_right = {}
        self._responsive_widget = None
        self.__orientation = None
        self.connect("realize", self.__on_realize)
        return [
            (App().player, "loading-changed", "_on_loading_changed"),
            (App().player, "current-changed", "_on_current_changed"),
            (App().player, "duration-changed", "_on_duration_changed"),
        ]

    def get_current_ordinate(self, parent):
        """
            If current track in widget, return it ordinate,
            @param parent widget as Gtk.Widget
            @return y as int
        """
        for child in self.children:
            if child.id == App().player.current_track.id:
                return child.translate_coordinates(parent, 0, 0)[1]
        return None

    @property
    def children(self):
        """
            Return all rows
            @return [Gtk.ListBoxRow]
        """
        return []

    @property
    def boxes(self):
        """
            Get available list boxes
            @return [Gtk.ListBox]
        """
        return []

    @property
    def view_type(self):
        """
            Get view type
            @return ViewType
        """
        return self._view_type

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            Change columns disposition
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            if allocation.width >= Size.NORMAL:
                orientation = Gtk.Orientation.HORIZONTAL
            else:
                orientation = Gtk.Orientation.VERTICAL
            if self.__orientation != orientation:
                self._set_orientation(orientation)

    def _init(self):
        """
            Init main widget
            @return bool
        """
        if self._responsive_widget is None:
            self._responsive_widget = Gtk.Grid()
            self._responsive_widget.set_column_spacing(20)
            self._responsive_widget.set_column_homogeneous(True)
            self._responsive_widget.set_property("valign", Gtk.Align.START)
            self.add(self._responsive_widget)
            self._responsive_widget.show()
            return True
        return False

    def _add_disc_container(self, disc_number):
        """
            Add disc container to box
            @param disc_number as int
        """
        self._tracks_widget_left[disc_number] = TracksWidget(self._view_type)
        self._tracks_widget_right[disc_number] = TracksWidget(self._view_type)
        self._tracks_widget_left[disc_number].connect(
            "activated", self._on_activated)
        self._tracks_widget_right[disc_number].connect(
            "activated", self._on_activated)
        self._tracks_widget_left[disc_number].connect(
            "do-selection", self.__on_do_selection)
        self._tracks_widget_right[disc_number].connect(
            "do-selection", self.__on_do_selection)
        self._tracks_widget_left[disc_number].connect(
            "do-shift-selection", self.__on_do_shift_selection)
        self._tracks_widget_right[disc_number].connect(
            "do-shift-selection", self.__on_do_shift_selection)
        self._tracks_widget_left[disc_number].connect(
            "row-selected", self._on_row_selected)
        self._tracks_widget_right[disc_number].connect(
            "row-selected", self._on_row_selected)

    def _add_tracks(self, widget, tracks, position=0):
        """
            Add tracks to widget
            @param widget as Gtk.ListBox
            @param tracks as [Track]
        """
        pass

    def _set_orientation(self, orientation):
        """
            Set columns orientation
            @param orientation as Gtk.Orientation
            @return updated as bool
        """
        if self.__orientation == orientation or\
                self._responsive_widget is None:
            return False
        self.__orientation = orientation
        for child in self._responsive_widget.get_children():
            self._responsive_widget.remove(child)
        return True

    def _allow_selection(self):
        """
            Allow selection on boxes
        """
        emit_signal(self, "selected", True)
        for box in self.boxes:
            if box.get_selection_mode() == Gtk.SelectionMode.MULTIPLE:
                continue
            box.set_selection_mode(Gtk.SelectionMode.MULTIPLE)

    def _disallow_selection(self):
        """
            Disallow selection on boxes
        """
        emit_signal(self, "selected", False)
        for box in self.boxes:
            if box.get_selection_mode() == Gtk.SelectionMode.NONE:
                continue
            box.set_selection_mode(Gtk.SelectionMode.NONE)
            box.set_activate_on_single_click(True)

    def _on_loading_changed(self, player, status, track):
        """
            Update row loading status
            @param player as Player
            @param status as bool
            @param track as Track
        """
        for row in self.children:
            if row.track.id == track.id:
                row.set_indicator(IndicatorType.LOADING)
            else:
                row.set_indicator()

    def _on_row_selected(self, listbox, row):
        """
            Update selection state
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        for child in self.children:
            if child.is_selected():
                return
        self._disallow_selection()

    def _on_activated(self, widget, track):
        pass

    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        for key in self._tracks_widget_left.keys():
            self._tracks_widget_left[key].update_playing(
                    App().player.current_track.id)
        for key in self._tracks_widget_right.keys():
            self._tracks_widget_right[key].update_playing(
                    App().player.current_track.id)

    def _on_duration_changed(self, player, track_id):
        """
            Update track duration
            @param player as Player
            @param track_id as int
        """
        for key in self._tracks_widget_left.keys():
            self._tracks_widget_left[key].update_duration(track_id)
        for key in self._tracks_widget_right.keys():
            self._tracks_widget_right[key].update_duration(track_id)

#######################
# PRIVATE             #
#######################
    def __on_realize(self, widget):
        """
            Set initial orientation
            @param widget as Gtk.Widget
            @param orientation as Gtk.Orientation
        """
        if self._view_type & ViewType.SINGLE_COLUMN or\
                App().settings.get_value("force-single-column"):
            self._set_orientation(Gtk.Orientation.VERTICAL)
        elif self._view_type & ViewType.TWO_COLUMNS:
            self._set_orientation(Gtk.Orientation.HORIZONTAL)
        else:
            # We need to listen to parent allocation as currently, we have
            # no children
            SizeAllocationHelper.__init__(self, True)

    def __on_do_selection(self, listbox, row):
        """
            Do shift selection
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxrow
        """
        if row is None:
            self._disallow_selection()
        else:
            self._allow_selection()
            if row.is_selected():
                # Let current selection event terminate
                GLib.timeout_add(100, listbox.unselect_row, row)
            else:
                listbox.select_row(row)

    def __on_do_shift_selection(self, listbox, row):
        """
            Do shift selection
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxrow
        """
        self._allow_selection()
        is_selected = row.is_selected()
        start_idx = end_idx = -1
        idx = 0
        for children in self.children:
            if children.is_selected() and not is_selected:
                start_idx = idx
            elif not children.is_selected() and is_selected:
                start_idx = idx
            if children == row:
                end_idx = idx
                break
            idx += 1
        if start_idx == -1:
            start_idx = 0
        for child in self.children[start_idx:end_idx + 1]:
            if is_selected:
                GLib.timeout_add(100,
                                 children.get_parent().unselect_row, child)
            else:
                children.get_parent().select_row(child)
