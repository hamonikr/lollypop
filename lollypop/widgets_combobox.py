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

from lollypop.utils import emit_signal
from lollypop.define import App


class ComboRow(Gtk.ListBoxRow):
    """
        A Row for combobox
    """

    def __init__(self, title):
        """
            Init widget
            @param title as str
        """
        Gtk.ListBoxRow.__init__(self)
        if title == "Separator":
            self.__label = None
            separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
            separator.show()
            self.add(separator)
            self.set_sensitive(False)
        else:
            self.get_style_context().add_class("big-padding")
            self.__label = Gtk.Label.new(title)
            self.__label.show()
            self.__label.set_property("halign", Gtk.Align.START)
            self.add(self.__label)

    @property
    def title(self):
        """
            Get row title
            @return str
        """
        return self.__label.get_text() if self.__label is not None else None


class ComboBox(Gtk.MenuButton):
    """
        Implement one combobox to prevent this GTK bug:
        https://gitlab.gnome.org/World/lollypop/issues/2253
    """
    # Same signal than MenuWidget
    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        """
            Init widget
        """
        Gtk.MenuButton.__init__(self)
        grid = Gtk.Grid.new()
        grid.show()
        self.__label = Gtk.Label.new()
        self.__label.show()
        image = Gtk.Image.new_from_icon_name("pan-down-symbolic",
                                             Gtk.IconSize.BUTTON)
        image.show()
        grid.add(self.__label)
        grid.add(image)
        self.set_image(grid)
        self.__popover = Gtk.Popover.new()
        self.__popover.set_relative_to(self)
        height = max(250, App().window.get_allocated_height() / 2)
        self.__popover.set_size_request(250, height)
        self.__scrolled = Gtk.ScrolledWindow.new()
        self.__scrolled.show()
        self.__scrolled.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)
        self.__listbox = Gtk.ListBox.new()
        self.__listbox.show()
        self.__listbox.connect("row-activated", self.__on_row_activated)
        self.__scrolled.add(self.__listbox)
        self.__popover.add(self.__scrolled)
        self.set_popover(self.__popover)
        size_group = Gtk.SizeGroup.new(Gtk.SizeGroupMode.HORIZONTAL)
        size_group.add_widget(self.__label)
        size_group.add_widget(self.__popover)

    def append(self, text):
        """
            Appends text to the list of strings stored in self
            @param text as str
        """
        row = ComboRow(text)
        row.show()
        self.__listbox.add(row)
        self.__label.set_text(text)

    def set_label(self, text):
        """
            Set button label
            @param text as str
        """
        self.__label.set_text(text)

    def get_active_id(self):
        """
            Get active id
            @return str
        """
        return self.__listbox.get_selected_row().title

    def set_active_id(self, text):
        """
            Mark item_id as active
            @parma text as str
        """
        for row in self.__listbox.get_children():
            if row.title == text:
                self.__listbox.select_row(row)
                self.__label.set_text(text)
                row.hide()
                break
        GLib.idle_add(self.__hide_row, row)

#######################
# PRIVATE             #
#######################
    def __hide_row(self, row):
        """
            Hide row, show others
            @param row as ComboRow
        """
        for _row in self.__listbox.get_children():
            if row != _row:
                _row.show()
        row.hide()
        self.__scrolled.get_vadjustment().set_value(0)

    def __sort_listbox(self, rowa, rowb):
        """
            Sort listbox
            @param rowa as ComboRow
            @param rowb as ComboRow
        """
        return rowa.index > rowb.index

    def __on_row_activated(self, listbox, row):
        """
            Close popover and change label
            @param listbox as Gtk.ListBox
            @param row as ComboRow
        """
        self.__label.set_text(row.title)
        self.__popover.popdown()
        emit_signal(self, "changed")
        # Delay to let popover popdown
        GLib.timeout_add(500, self.__hide_row, row)
