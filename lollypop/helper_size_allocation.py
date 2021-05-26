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

from gi.repository import GLib


class SizeAllocationHelper:
    """
        Listen to size-allocate signal and ignore unwanted allocations
    """

    def __init__(self, use_parent=False):
        """
            Init helper
            @param use_parent as bool: follow parent size allocation
        """
        self.__allocation_timeout_id = None
        self.__width = self.__height = 0
        if use_parent:
            parent = self.get_parent()
            parent.connect("size-allocate", self.__on_size_allocate)
        else:
            self.connect("size-allocate", self.__on_size_allocate)

    @property
    def width(self):
        """
            Get widget width
            @return int
        """
        return self.__width

    @property
    def height(self):
        """
            Get widget height
            @return int
        """
        return self.__height

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            @param allocation as Gtk.Allocation
            @return True if allocation is valid
        """
        if allocation.width == 1 or self.__width == allocation.width:
            return False
        self.__width = allocation.width
        return True

    def _handle_height_allocate(self, allocation):
        """
            @param allocation as Gtk.Allocation
            @return True if allocation is valid
        """
        if allocation.height == 1 or self.__height == allocation.height:
            return False
        self.__height = allocation.height
        return True

#######################
# PRIVATE             #
#######################
    def __handle_size_allocate(self, allocation):
        """
            Pass allocation to width/height handler
        """
        self.__allocation_timeout_id = None
        self._handle_width_allocate(allocation)
        self._handle_height_allocate(allocation)

    def __on_size_allocate(self, widget, allocation):
        """
            Filter unwanted allocations
            @param widget as Gtk.Widget
            @param allocation as Gtk.Allocation
        """
        if self.__allocation_timeout_id is not None:
            GLib.source_remove(self.__allocation_timeout_id)
        self.__allocation_timeout_id = GLib.idle_add(
            self.__handle_size_allocate, allocation)
