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

from gettext import gettext as _

from lollypop.widgets_row_track import TrackRow
from lollypop.widgets_listbox import ListBox
from lollypop.define import App, ViewType, Size, MARGIN
from lollypop.objects_track import Track
from lollypop.helper_signals import SignalsHelper, signals
from lollypop.helper_gestures import GesturesHelper


class QueueTracksView(Gtk.Bin, GesturesHelper, SignalsHelper):
    """
        Responsive view showing queued tracks
    """

    @signals
    def __init__(self):
        """
            Init view
        """
        Gtk.Bin.__init__(self)
        label = Gtk.Label.new(_("Currently in queue"))
        label.show()
        label.get_style_context().add_class("dim-label")
        label.get_style_context().add_class("large")
        self.__box = ListBox()
        self.__box.show()
        self.__box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.__box.set_width(Size.SMALL)
        self.__box.connect("row-activated", self.__on_row_activated)
        self.__grid = Gtk.Grid()
        self.__grid.set_orientation(Gtk.Orientation.VERTICAL)
        self.__grid.set_halign(Gtk.Align.CENTER)
        self.__grid.add(label)
        self.__grid.add(self.__box)
        self.__grid.set_margin_bottom(MARGIN)
        self.__grid.get_style_context().add_class("borders")
        self.add(self.__grid)
        GesturesHelper.__init__(self, self.__box)
        return [
            (App().player, "queue-changed", "_on_queue_changed"),
            (App().player, "current-changed", "_on_current_changed"),
        ]

    def populate(self):
        """
            Populate with current queue
        """
        self.allow_duplicate("_on_queue_changed")
        tracks = [Track(track_id) for track_id in App().player.queue]
        self.__add_tracks(tracks)

#######################
# PROTECTED           #
#######################
    def _on_queue_changed(self, *ignore):
        """
            Clean view and reload if empty
        """
        queue = App().player.queue
        track_ids = [row.track.id for row in self.__box.get_children()]
        for track_id in queue:
            if track_id not in track_ids:
                self.__add_tracks([Track(track_id)])
        for row in self.__box.get_children():
            if row.track.id not in queue:
                row.destroy()
        if not self.__box.get_children():
            self.__grid.hide()

    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        for child in self.__box.get_children():
            child.update_number_label()

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        row = self.__box.get_row_at_y(y)
        if row is None:
            return
        row.popup_menu(self.__box, x, y)

#######################
# PRIVATE             #
#######################
    def __add_tracks(self, tracks):
        """
            Add tracks to widget
            @param tracks as [Track]
        """
        for track in tracks:
            row = TrackRow(track, [], ViewType.QUEUE)
            row.show()
            row.connect("removed", self.__on_track_removed)
            self.__box.add(row)
            self.__grid.show()

    def __on_row_activated(self, listbox, row):
        """
            Play track
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        App().player.load(row.track)

    def __on_track_removed(self, row):
        """
            Remove track from queue
            @param row as TrackRow
        """
        if row.track.id in App().player.queue:
            App().player.remove_from_queue(row.track.id)
