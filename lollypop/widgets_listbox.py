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


class ListBox(Gtk.ListBox):
    def __init__(self):
        Gtk.ListBox.__init__(self)
        self.__width = 0

    def set_width(self, width):
        self.set_property("halign", Gtk.Align.CENTER)
        self.__width = width

    def do_get_preferred_width(self):
        if self.__width == 0:
            return Gtk.ListBox.do_get_preferred_width(self)
        else:
            return (self.__width, self.__width)
