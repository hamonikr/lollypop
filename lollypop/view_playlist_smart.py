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


from lollypop.widgets_playlist_smart import SmartPlaylistRow
from lollypop.view import View
from lollypop.logger import Logger
from lollypop.define import App, StorageType


class SmartPlaylistView(View):
    """
        Show a view allowing user to create a smart playlist
    """

    def __init__(self, playlist_id, view_type):
        """
            Init PlaylistView
            @param playlist_id as int
            @param view_type as ViewType
        """
        View.__init__(self, StorageType.ALL, view_type)
        self.__playlist_id = playlist_id
        self.__size_group = Gtk.SizeGroup()
        self.__size_group.set_mode(Gtk.SizeGroupMode.BOTH)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/SmartPlaylistView.ui")
        widget = builder.get_object("widget")
        self.connect("size-allocate", self.__on_size_allocate, widget)
        self.__listbox = builder.get_object("listbox")
        self.scrolled.set_property("expand", True)
        self.__match_toggle = builder.get_object("match_toggle")
        self.__operand_combobox = builder.get_object("operand_combobox")
        self.__select_combobox = builder.get_object("select_combobox")
        self.__limit_spin = builder.get_object("limit_spin")
        self.__add_rule_button = builder.get_object("add_rule_button")
        self.__up_box = builder.get_object("up_box")
        self.__bottom_box = builder.get_object("bottom_box")
        if App().playlists.get_smart(playlist_id):
            self.__match_toggle.set_active(True)
            self.__set_sensitive(True)
        self.add_widget(widget)
        builder.connect_signals(self)

    def populate(self):
        """
            Setup an initial widget based on current request
        """
        sql = App().playlists.get_smart_sql(self.__playlist_id)
        if sql is None:
            return
        try:
            if sql.find(" UNION ") != -1:
                operand = "OR"
            else:
                operand = "AND"
            self.__operand_combobox.set_active_id(operand)
        except Exception as e:
            self.__operand_combobox.set_active(0)
            Logger.warning("SmartPlaylistView::populate: %s", e)
        # Setup rows
        for line in sql.split("((")[1:]:
            widget = SmartPlaylistRow(self.__size_group)
            try:
                widget.set(line.split("))")[0])
            except Exception as e:
                Logger.error("SmartPlaylistView::populate: %s", e)
            widget.show()
            self.__listbox.add(widget)
        try:
            split_limit = sql.split("LIMIT")
            limit = int(split_limit[1].split(" ")[1])
            self.__limit_spin.set_value(limit)
        except Exception as e:
            Logger.warning("SmartPlaylistView::populate: %s", e)
        try:
            split_order = sql.split("ORDER BY")
            split_spaces = split_order[1].split(" ")
            orderby = split_spaces[1]
            if split_spaces[2] in ["ASC", "DESC"]:
                orderby += " %s" % split_spaces[2]
            self.__select_combobox.set_active_id(orderby)
        except Exception as e:
            self.__select_combobox.set_active(0)
            Logger.warning("SmartPlaylistView::populate: %s", e)

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"playlist_id": self.__playlist_id,
                "view_type": self.view_type}

#######################
# PROTECTED           #
#######################
    def __get_or_request(self):
        """
            Get request for AND operand
            @return str
        """
        request = ""
        orderby = self.__select_combobox.get_active_id()
        for child in self.__listbox.get_children():
            if child.sql is None:
                continue
            request += "SELECT DISTINCT(tracks.rowid)"
            if orderby != "random()":
                request += ", %s" % orderby
            request += " FROM tracks"
            subrequest = " WHERE %s" % child.sql
            if orderby.find("albums.name") != -1:
                subrequest += " AND tracks.album_id = albums.rowid"
            elif orderby.find("artists.name") != -1:
                subrequest += " AND track_artists.artist_id = artists.rowid\
                                AND track_artists.track_id = tracks.rowid"
            if subrequest.find(" genres."):
                request += ", %s" % "genres"
            if subrequest.find(" artists."):
                request += ", %s" % "artists"
            if subrequest.find(" albums.") != -1:
                request += ", %s" % "albums"
            if subrequest.find(" album_genres.") != -1:
                request += ", %s" % " album_genres"
            if subrequest.find(" track_artists.") != -1:
                request += ", %s" % " track_artists"
            request += subrequest + " UNION "
        request = request[:-7]  # " UNION "
        request += " ORDER BY %s" % orderby
        request += " LIMIT %s" % int(self.__limit_spin.get_value())
        return request

    def __get_and_request(self):
        """
            Get request for AND operand
            @return str
        """
        orderby = self.__select_combobox.get_active_id()
        request = "SELECT DISTINCT(tracks.rowid) FROM tracks"
        subrequest = " WHERE"
        for child in self.__listbox.get_children():
            if child.sql is not None:
                subrequest += " %s AND" % child.sql
        subrequest = subrequest[:-3]
        if orderby.find("albums.name") != -1:
            subrequest += " AND tracks.album_id = albums.rowid"
        elif orderby.find("artists.name") != -1:
            subrequest += " AND track_artists.artist_id = artists.rowid\
                            AND track_artists.track_id = tracks.rowid"
        if subrequest.find(" genres.") != -1:
            request += ", %s" % "genres"
        if subrequest.find(" artists.") != -1:
            request += ", %s" % "artists"
        if subrequest.find(" albums.") != -1:
            request += ", %s" % "albums"
        if subrequest.find(" album_genres.") != -1:
            request += ", %s" % "album_genres"
        if subrequest.find(" track_artists.") != -1:
            request += ", %s" % "track_artists"
        subrequest += " ORDER BY %s" % orderby
        subrequest += " LIMIT %s" % int(self.__limit_spin.get_value())
        return request + subrequest

    def _on_save_button_clicked(self, button):
        """
            Save SQL request
            @param button as Gtk.Button
        """
        operand = self.__operand_combobox.get_active_id()
        if len(self.__listbox.get_children()) == 0:
            request = ""
            App().playlists.set_smart(self.__playlist_id, False)
        elif operand == "AND":
            request = self.__get_and_request()
        else:
            request = self.__get_or_request()
        App().playlists.set_smart_sql(self.__playlist_id, request)
        App().window.container.go_back()

    def _on_add_rule_button_clicked(self, button):
        """
            Add a new rule
            @param button as Gtk.Button
        """
        self.__populate()

    def _on_match_check_button_toggled(self, button):
        """
            Enable/Disable smart playlist
            @param button as GtkButton
        """
        active = button.get_active()
        App().playlists.set_smart(self.__playlist_id, active)
        self.__set_sensitive(active)

    def _on_map(self, widget):
        """
            Disable global shortcuts and update toolbar
            @param widget as Gtk.Widget
        """
        View._on_map(self, widget)
        App().enable_special_shortcuts(False)

    def _on_unmap(self, widget):
        """
            Enable global shortcuts
            @param widget as Gtk.Widget
        """
        View._on_unmap(self, widget)
        App().enable_special_shortcuts(True)

#######################
# PRIVATE             #
#######################
    def __populate(self):
        """
            Setup an initial widget
        """
        widget = SmartPlaylistRow(self.__size_group)
        widget.show()
        self.__listbox.add(widget)

    def __set_sensitive(self, sensitive):
        """
            Set view sensitive
            @param sensitive as bool
        """
        if sensitive:
            self.__up_box.set_sensitive(True)
            self.__bottom_box.set_sensitive(True)
            self.__add_rule_button.set_sensitive(True)
            self.__listbox.set_sensitive(True)
        else:
            self.__up_box.set_sensitive(False)
            self.__bottom_box.set_sensitive(False)
            self.__add_rule_button.set_sensitive(False)
            self.__listbox.set_sensitive(False)

    def __on_size_allocate(self, widget, allocation, child_widget):
        """
            Set child widget size
            @param widget as Gtk.Widget
            @param allocation as Gtk.Allocation
            @param child_widget as Gtk.Widget
        """
        width = max(400, allocation.width / 2)
        child_widget.set_size_request(width, -1)
