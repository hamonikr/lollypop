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

from gi.repository import GObject, Gtk, Gdk

from lollypop.define import App
from lollypop.utils import emit_signal
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.helper_gestures import GesturesHelper


class TracksWidget(Gtk.ListBox, SignalsHelper, GesturesHelper):
    """
        Widget showing a track list
    """

    __gsignals__ = {
        "activated": (GObject.SignalFlags.RUN_FIRST,
                      None, (GObject.TYPE_PYOBJECT,)),
        "do-selection": (GObject.SignalFlags.RUN_FIRST,
                         None, (GObject.TYPE_PYOBJECT,)),
        "do-shift-selection": (GObject.SignalFlags.RUN_FIRST,
                               None, (GObject.TYPE_PYOBJECT,))
    }

    @signals_map
    def __init__(self, view_type):
        """
            Init track widget
            @param view_type as ViewType
        """
        Gtk.ListBox.__init__(self)
        GesturesHelper.__init__(self, self)
        self.__view_type = view_type
        self.get_style_context().add_class("trackswidget")
        self.set_property("hexpand", True)
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        return [
            (App().player, "queue-changed", "_on_queue_changed")
        ]

    def update_playing(self, track_id):
        """
            Update playing track
            @param track_id as int
        """
        for row in self.get_children():
            row.set_indicator()

    def update_duration(self, track_id):
        """
            Update duration for track id
            @param track_id as int
        """
        for row in self.get_children():
            if row.track.id == track_id:
                row.update_duration()

#######################
# PROTECTED           #
#######################
    def _on_queue_changed(self, *ignore):
        """
            Update all position labels
        """
        for row in self.get_children():
            row.update_number_label()

    def _on_primary_long_press_gesture(self, x, y):
        """
            Show row menu
            @param x as int
            @param y as int
        """
        row = self.get_row_at_y(y)
        if row is None:
            return
        emit_signal(self, "do-selection", row)

    def _on_primary_press_gesture(self, x, y, event):
        """
            Activate current row
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        row = self.get_row_at_y(y)
        if row is None:
            return
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            emit_signal(self, "do-shift-selection", row)
        elif event.state & Gdk.ModifierType.CONTROL_MASK:
            emit_signal(self, "do-selection", row)
        elif event.state & Gdk.ModifierType.MOD1_MASK:
            emit_signal(self, "do-selection", None)
            App().player.clear_albums()
            App().player.load(row.track)
        else:
            emit_signal(self, "activated", row.track)
            emit_signal(self, "do-selection", None)

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        row = self.get_row_at_y(y)
        if row is None:
            return
        row.popup_menu(self, x, y)

#######################
# PRIVATE             #
#######################
