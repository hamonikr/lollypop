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

from gi.repository import Gtk, Pango, GLib

from gettext import gettext as _

from lollypop.widgets_row_track import TrackRow
from lollypop.define import App, ViewType
from lollypop.view_tracks import TracksView
from lollypop.helper_signals import SignalsHelper, signals_map


class SearchTracksView(TracksView, SignalsHelper):
    """
        Responsive view showing searched tracks
    """

    @signals_map
    def __init__(self):
        """
            Init view
        """
        TracksView.__init__(self, ViewType.SEARCH)
        self.__track_ids = []
        self._add_disc_container(0)
        self._tracks_widget_left[0].show()
        self._tracks_widget_right[0].show()
        return [
            (App().window, "notify::folded", "_on_container_folded"),
        ]

    def append_row(self, track):
        """
            Append a track
            ONE COLUMN ONLY
            @param track as Track
            @param position as int
        """
        self._init()
        if track.id in self.__track_ids:
            return
        self.__track_ids.append(track.id)
        left_len = len(self._tracks_widget_left[0].get_children())
        right_len = len(self._tracks_widget_right[0].get_children())
        if left_len > right_len:
            self._add_tracks(self._tracks_widget_right[0], [track])
        else:
            self._add_tracks(self._tracks_widget_left[0], [track])

    def clear(self):
        """
            Clear and hide the view
        """
        self.__track_ids = []
        for child in self._tracks_widget_left[0].get_children() +\
                self._tracks_widget_right[0].get_children():
            child.destroy()
        GLib.idle_add(self.hide)

    @property
    def children(self):
        """
            Return all rows
            @return [Gtk.ListBoxRow]
        """
        return self._tracks_widget_left[0].get_children() +\
            self._tracks_widget_right[0].get_children()

#######################
# PROTECTED           #
#######################
    def _add_tracks(self, widget, tracks, position=0):
        """
            Add tracks to widget
            @param widget as Gtk.ListBox
            @param tracks as [Track]
        """
        for track in tracks:
            track.set_number(position + 1)
            row = TrackRow(track, [], self.view_type)
            row.show()
            widget.add(row)
            position += 1

    def _set_orientation(self, orientation):
        """
            Set columns orientation
            @param orientation as Gtk.Orientation
        """
        if not TracksView._set_orientation(self, orientation):
            return
        self._responsive_widget.insert_row(0)
        self.__label = Gtk.Label.new(_("Tracks"))
        self.__label.show()
        self.__label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__label.get_style_context().add_class("dim-label")
        self.__update_label(App().window.folded)
        self.__label.set_hexpand(True)
        self.__label.set_property("halign", Gtk.Align.START)
        idx = 1
        # Vertical
        ##########################
        #  --------Label-------- #
        #  |     Column 1      | #
        #  |     Column 2      | #
        ##########################
        # Horizontal
        ###########################
        # ---------Label--------- #
        # | Column 1 | Column 2 | #
        ###########################
        if orientation == Gtk.Orientation.VERTICAL:
            self._responsive_widget.attach(self.__label, 0, 0, 1, 1)
            self._responsive_widget.attach(
                      self._tracks_widget_left[0],
                      0, idx, 2, 1)
            idx += 1
        else:
            self._responsive_widget.attach(self.__label, 0, 0, 2, 1)
            self._responsive_widget.attach(
                      self._tracks_widget_left[0],
                      0, idx, 1, 1)
        if not self.view_type & ViewType.SINGLE_COLUMN:
            if orientation == Gtk.Orientation.VERTICAL:
                self._responsive_widget.attach(
                           self._tracks_widget_right[0],
                           0, idx, 2, 1)
            else:
                self._responsive_widget.attach(
                           self._tracks_widget_right[0],
                           1, idx, 1, 1)
        idx += 1

    def _on_loading_changed(self, player, status, track):
        """
            Update row loading status
            @param player as Player
            @param status as bool
            @param track as Track
        """
        if track.is_web:
            TracksView._on_loading_changed(self, player, status, track)

    def _on_activated(self, widget, track):
        """
            Handle playback if album or pass signal
            @param widget as TracksWidget
            @param track as Track
        """
        track.album.set_tracks([track])
        App().player.add_album(track.album)
        App().player.load(track.album.get_track(track.id))

    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        self.__update_label(App().window.folded)

#######################
# PRIVATE             #
#######################
    def __update_label(self, is_adaptive):
        """
            Update label style based on current adaptive state
            @param is_adaptive as bool
        """
        style_context = self.__label.get_style_context()
        if is_adaptive:
            style_context.remove_class("text-x-large")
        else:
            style_context.add_class("text-x-large")
