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


class SmartPlaylistRow(Gtk.ListBoxRow):
    """
        A smart playlist widget (WHERE SQL subrequest)
    """
    __TEXT = ["genre", "album", "artist"]
    __INT = ["rating", "popularity", "year", "bpm"]

    def __init__(self, size_group):
        """
            Init widget
            @param size_group as Gtk.SizeGroup
        """
        Gtk.ListBoxRow.__init__(self)
        self.__operand = None
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/SmartPlaylistWidget.ui")
        builder.connect_signals(self)
        self.__stack = builder.get_object("stack")
        self.__type_combobox = builder.get_object("type_combobox")
        self.__operand_combobox = builder.get_object("operand_combobox")
        size_group.add_widget(self.__operand_combobox)
        self.__entry = builder.get_object("entry")
        self.__spin_button = builder.get_object("spin_button")
        self.__rate = 0
        self._stars = []
        self._stars.append(builder.get_object("star0"))
        self._stars.append(builder.get_object("star1"))
        self._stars.append(builder.get_object("star2"))
        self._stars.append(builder.get_object("star3"))
        self._stars.append(builder.get_object("star4"))
        self._on_leave_notify_event(None, None)
        self.add(builder.get_object("widget"))

    def set(self, item):
        """
            Try to set widget from item
            @param item as str
        """
        item = item.replace(" COLLATE NOCASE", "")
        # Sucks, search for a better way to handle this in Lollypop2
        if item.find("NOT LIKE") != -1:
            self.__operand = "NOT LIKE"
            (t, *args) = item.split(" NOT LIKE ")
        else:
            (t, self.__operand, *args) = item.split(" ")
        value = " ".join(list(args))
        # Unquote value
        if value[0] == "'":
            value = value[1:]
        if value[-1] == "'":
            value = value[:-1]
        # Remove %
        if value[0] == "%":
            value = value[1:]
        if value[-1] == "%":
            value = value[:-1]
        if t == "tracks.year":
            self.__type_combobox.set_active_id("year")
            self.__spin_button.set_value(int(value))
        elif t == "tracks.bpm":
            self.__type_combobox.set_active_id("bpm")
            self.__spin_button.set_value(int(value))
        elif t == "genres.name":
            self.__type_combobox.set_active_id("genre")
            self.__entry.set_text(value)
        elif t == "albums.name":
            self.__type_combobox.set_active_id("album")
            self.__entry.set_text(value)
        elif t == "artists.name":
            self.__type_combobox.set_active_id("artist")
            self.__entry.set_text(value)
        elif t == "tracks.rate":
            self.__type_combobox.set_active_id("rating")
            self.__rate = int(value)
            self._on_leave_notify_event(None, None)
        elif t == "tracks.popularity":
            self.__type_combobox.set_active_id("popularity")
            self.__rate = int(value)
            self._on_leave_notify_event(None, None)
        else:
            self.destroy()

    @property
    def sql(self):
        """
            Get SQL subrequest
            @return str
        """
        request_type = self.__type_combobox.get_active_id()
        request_check = self.__operand_combobox.get_active_id()
        sql = None
        if request_type == "rating":
            sql = "( ((tracks.rate %s '%s')) )"
            sql = sql % (request_check, self.__rate)
        elif request_type == "popularity":
            sql = "( ((tracks.popularity %s '%s')) )"
            sql = sql % (request_check, self.__rate)
        elif request_type == "year":
            value = int(self.__spin_button.get_value())
            sql = "( ((tracks.year %s '%s')) )"
            sql = sql % (request_check, value)
        elif request_type == "bpm":
            value = int(self.__spin_button.get_value())
            sql = "( ((tracks.bpm %s '%s')) )"
            sql = sql % (request_check, value)
        elif request_type == "genre":
            request_value = self.__entry.get_text().replace("'", "''")
            if request_check.find("LIKE") != -1:
                value = "%" + request_value + "%"
            else:
                value = request_value
            sql = "(album_genres.genre_id = genres.rowid" +\
                  " AND tracks.album_id = album_genres.album_id" +\
                  " AND ((genres.name %s '%s' COLLATE NOCASE)) )"
            sql = sql % (request_check, value)
        elif request_type == "album":
            request_value = self.__entry.get_text().replace("'", "''")
            if request_check.find("LIKE") != -1:
                value = "%" + request_value + "%"
            else:
                value = request_value
            sql = "(tracks.album_id = albums.rowid" +\
                  " AND ((albums.name %s '%s' COLLATE NOCASE)) )"
            sql = sql % (request_check, value)
        elif request_type == "artist":
            request_value = self.__entry.get_text().replace("'", "''")
            if request_check.find("LIKE") != -1:
                value = "%" + request_value + "%"
            else:
                value = request_value
            sql = "(track_artists.artist_id = artists.rowid" +\
                  " AND tracks.rowid = track_artists.track_id" +\
                  " AND ((artists.name %s '%s' COLLATE NOCASE)) )"
            sql = sql % (request_check, value)
        return sql

#######################
# PROTECTED           #
#######################
    def _on_destroy_button_clicked(self, button):
        """
            Destroy self
            @param button as Gtk.Button
        """
        self.destroy()

    def _on_type_combobox_changed(self, combobox):
        """
            Update check combobox
            @param combobox as Gtk.ComboBoxText
        """
        self.__operand_combobox.remove_all()
        self.__operand_combobox.append("=", _("is equal to"))
        self.__operand_combobox.append("!=", _("is not equal to"))
        if combobox.get_active_id() in self.__TEXT:
            self.__operand_combobox.append("LIKE", _("contains "))
            self.__operand_combobox.append("NOT LIKE", _("does not contain"))
        elif combobox.get_active_id() in self.__INT:
            self.__operand_combobox.append(">", _("is greater than"))
            self.__operand_combobox.append("<", _("is less than"))
        if self.__operand is None:
            self.__operand_combobox.set_active(0)
        else:
            self.__operand_combobox.set_active_id(self.__operand)

        active_id = combobox.get_active_id()
        if active_id in ["year", "bpm"]:
            self.__stack.set_visible_child_name("int")
            if active_id == "year":
                self.__spin_button.set_value(1960)
            else:
                self.__spin_button.set_value(130)
        elif combobox.get_active_id() in ["rating", "popularity"]:
            self.__stack.set_visible_child_name("rating")
        else:
            self.__stack.set_visible_child_name("text")

    def _on_enter_notify_event(self, widget, event):
        """
            Update star opacity
            @param widget as Gtk.EventBox
            @param event as Gdk.Event
        """
        event_star = widget.get_children()[0]
        # First star is hidden (used to clear score)
        if event_star.get_opacity() == 0.0:
            found = True
        else:
            found = False
        for star in self._stars:
            if found:
                star.set_opacity(0.2)
                star.get_style_context().remove_class("selected")
            else:
                star.get_style_context().add_class("selected")
                star.set_opacity(0.8)
            if star == event_star:
                found = True

    def _on_leave_notify_event(self, widget, event):
        """
            Update star opacity
            @param widget as Gtk.EventBox (can be None)
            @param event as Gdk.Event (can be None)
        """
        if self.__rate < 1:
            for i in range(5):
                self._stars[i].set_opacity(0.2)
                self._stars[i].get_style_context().remove_class("selected")
        else:
            star = self.__star_from_rate(self.__rate)
            # Select wanted star
            for idx in range(0, star):
                widget = self._stars[idx]
                widget.get_style_context().add_class("selected")
                widget.set_opacity(0.8)
            # Unselect others
            for idx in range(star, 5):
                self._stars[idx].set_opacity(0.2)
                self._stars[idx].get_style_context().remove_class("selected")

    def _on_button_release_event(self, widget, event):
        """
            Set album popularity
            @param widget as Gtk.EventBox
            @param event as Gdk.Event
        """
        event_star = widget.get_children()[0]
        if event_star in self._stars:
            position = self._stars.index(event_star)
        else:
            position = -1
        self.__rate = position + 1
        self._on_leave_notify_event(None, None)
        return True

#######################
# PRIVATE             #
#######################
    def __star_from_rate(self, rate):
        """
            Calculate stars from rate
            @param rate as double
            @return int
        """
        star = min(5, int(rate))
        return star
