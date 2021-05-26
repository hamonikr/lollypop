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

from locale import strxfrm

from lollypop.utils import noaccents

from lollypop.localized import index_of


class FastScroll(Gtk.ScrolledWindow):
    """
        Widget showing letter and allowing fast scroll on click
        Do not call show on widget, not needed
    """

    def __init__(self, listbox, scrolled):
        """
            Init widget
            @param listbox as Gtk.ListBox
            @param scrolled as Gtk.ScrolledWindow
        """
        Gtk.ScrolledWindow.__init__(self)
        self.__main_scrolled = scrolled
        self.__leave_timeout_id = None
        self.get_style_context().add_class("no-border")
        self.set_margin_end(15)
        self.set_vexpand(True)
        self.set_policy(Gtk.PolicyType.NEVER,
                        Gtk.PolicyType.NEVER)
        self.set_property("halign", Gtk.Align.END)
        self.__chars = []
        self.__listbox = listbox
        self.__scrolled = scrolled
        self.__grid = Gtk.Grid()
        self.__grid.set_orientation(Gtk.Orientation.VERTICAL)
        self.__grid.set_property("valign", Gtk.Align.START)
        self.__grid.show()
        eventbox = Gtk.EventBox()
        eventbox.add(self.__grid)
        eventbox.connect("button-press-event", self.__on_button_press_event)
        eventbox.show()
        self.add(eventbox)
        self.__main_scrolled.get_vadjustment().connect(
            "value_changed", self.__on_value_changed)
        self.connect("scroll-event", self.__on_scroll_event)

    def clear(self):
        """
            Clear values
        """
        for child in self.__grid.get_children():
            child.destroy()
        self.hide()

    def clear_chars(self):
        """
            Clear chars
        """
        self.__chars = []

    def add_char(self, c):
        """
            Add a char to widget, will not be shown
            @param c as char
        """
        if c:
            to_add = noaccents(index_of(c)).upper()
            if to_add not in self.__chars:
                self.__chars.append(to_add)

    def populate(self):
        """
            Populate widget based on current chars
        """
        if not self.__chars:
            return
        label = Gtk.Label.new()
        label.set_margin_start(10)
        label.set_markup('<span font="Monospace"><b>%s</b></span>' % "▲")
        label.show()
        self.__grid.add(label)
        for c in sorted(self.__chars, key=strxfrm):
            label = Gtk.Label.new()
            label.set_margin_start(10)
            label.set_markup('<span font="Monospace"><b>%s</b></span>' % c)
            label.set_opacity(0.4)
            label.show()
            self.__grid.add(label)
        label = Gtk.Label.new()
        label.set_margin_start(10)
        label.set_markup('<span font="Monospace"><b>%s</b></span>' % "▼")
        label.show()
        self.__grid.add(label)
        self.__on_value_changed()

#######################
# PRIVATE             #
#######################
    def __set_margin(self):
        """
            Get top non static entry and set margin based on it position
        """
        margin = 0
        for row in self.__listbox.get_children():
            if row.id >= 0:
                values = row.translate_coordinates(self.__main_scrolled, 0, 0)
                if values is not None:
                    margin = values[1] + 5
                if margin < 5:
                    margin = 5
                self.set_margin_top(margin)
                break

    def __check_value_to_mark(self):
        """
            Look at visible listbox range, and mark char as needed
        """
        start = self.__scrolled.get_vadjustment().get_value()
        end = start + self.__scrolled.get_allocated_height()
        start_value = None
        end_value = None
        for row in self.__listbox.get_children():
            if row.id < 0:
                continue
            values = row.translate_coordinates(self.__listbox, 0, 0)
            if values is not None:
                if row.sortname:
                    name = row.sortname
                else:
                    name = row.name
                if values[1] >= start and start_value is None:
                    start_value = name[0]
                elif values[1] <= end:
                    end_value = name[0]
                else:
                    break
        if start_value is not None and end_value is not None:
            self.__mark_values(start_value, end_value)

    def __mark_values(self, start, end):
        """
            Mark values
            @param start as char
            @param end as char
        """
        start = noaccents(index_of(start)).upper()
        end = noaccents(index_of(end)).upper()
        chars = sorted(self.__chars, key=strxfrm)
        start_idx = chars.index(start)
        end_idx = chars.index(end)
        selected = chars[start_idx:end_idx + 1] + ["▲", "▼"]
        for child in self.__grid.get_children():
            label = child.get_text()
            mark = True if label in selected else False
            if mark:
                child.set_opacity(0.9)
                if label == chars[start_idx]:
                    values = child.translate_coordinates(self.__grid, 0, 0)
                    if values is not None:
                        self.get_vadjustment().set_value(values[1])
            else:
                child.set_opacity(0.4)

    def __on_button_press_event(self, eventbox, event):
        """
            Scroll to activated child char
        """
        char = None
        row = None
        for child in self.__grid.get_children():
            allocation = child.get_allocation()
            if allocation.y <= event.y <= allocation.y + allocation.height:
                char = child.get_text()
                break
        if char is not None:
            if char == "▲":
                row = self.__listbox.get_children()[0]
            elif char == "▼":
                row = self.__listbox.get_children()[-1]
            else:
                for child in self.__listbox.get_children():
                    if child.id < 0:
                        continue
                    if noaccents(index_of(child.sortname))[0].upper() == char:
                        row = child
                        break
        if row is not None:
            values = row.translate_coordinates(self.__listbox,
                                               0, 0)
            if values is not None:
                adj = self.__scrolled.get_vadjustment()
                adj.set_value(values[1])

    def __on_scroll_event(self, scrolled, event):
        """
            Pass event to main scrolled
            @param scrolled as Gtk.ScrolledWindow
            @param event as Gdk.EventScroll
        """
        adj = self.__main_scrolled.get_vadjustment()
        adj.set_value(adj.get_value() + (event.delta_y * 50))
        return True

    def __on_value_changed(self, *ignore):
        """
            Show a popover with current letter
        """
        if self.__chars:
            self.show()
            GLib.idle_add(self.__check_value_to_mark)
            GLib.idle_add(self.__set_margin)
