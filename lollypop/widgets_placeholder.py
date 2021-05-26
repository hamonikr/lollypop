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

from gi.repository import Gtk, GLib, Pango

from lollypop.define import App


class Placeholder(Gtk.Bin):
    def __init__(self, text, icon_name):
        """
            Init placeholder
            @param text as str
            @param icon_name as str
        """
        Gtk.Bin.__init__(self)
        self.__label = Gtk.Label.new()
        self.__label.show()
        self.__label.set_markup("%s" % GLib.markup_escape_text(text))
        self.__label.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.__label.set_line_wrap(True)
        self.set_folded(App().window.folded)
        label_style = self.__label.get_style_context()
        label_style.add_class("dim-label")
        image = Gtk.Image.new_from_icon_name(icon_name,
                                             Gtk.IconSize.DIALOG)
        image.show()
        image.get_style_context().add_class("dim-label")
        grid = Gtk.Grid()
        grid.show()
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        grid.set_column_spacing(20)
        grid.add(image)
        grid.add(self.__label)
        grid.set_vexpand(True)
        grid.set_hexpand(True)
        grid.set_property("halign", Gtk.Align.CENTER)
        grid.set_property("valign", Gtk.Align.CENTER)
        self.add(grid)

    def set_folded(self, folded):
        """
            Set label size
            @param folded as bool
        """
        style_context = self.__label.get_style_context()
        if folded:
            style_context.remove_class("text-xx-large")
            style_context.add_class("text-x-large")
        else:
            style_context.remove_class("text-x-large")
            style_context.add_class("text-xx-large")
