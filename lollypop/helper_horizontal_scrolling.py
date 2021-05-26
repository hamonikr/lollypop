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

from gi.repository import GLib, Gtk

from lollypop.define import ArtSize
from lollypop.helper_size_allocation import SizeAllocationHelper


class HorizontalScrollingHelper(SizeAllocationHelper):
    """
        Manage 2 button and scroll a scrolled window
    """

    def __init__(self):
        """
            Init helper
        """
        SizeAllocationHelper.__init__(self)
        self.__adjustment = self.scrolled.get_hadjustment()
        self.__adjustment.connect("value-changed", self.update_buttons)
        self._backward_button.connect("clicked",
                                      self.__on_backward_button_clicked)
        self._forward_button.connect("clicked",
                                     self.__on_forward_button_clicked)
        self.scrolled.get_hscrollbar().hide()
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC,
                                 Gtk.PolicyType.NEVER)

    def __del__(self):
        """
            Remove ref cycle
        """
        self.__adjustment = None

    def update_buttons(self, *ignore):
        """
            Update buttons state
        """
        value = self.scrolled.get_allocated_width()
        self._backward_button.set_sensitive(self.__adjustment.get_value() !=
                                            self.__adjustment.get_lower())
        self._forward_button.set_sensitive(self.__adjustment.get_value() !=
                                           self.__adjustment.get_upper() -
                                           value)

#######################
# PRIVATE             #
#######################
    def _handle_width_allocate(self, allocation):
        """
            @param allocation as Gtk.Allocation
            @return True if allocation is valid
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            self.update_buttons()

    def __smooth_scrolling(self, value, direction):
        """
            Emulate smooth scrolling
        """
        if value > 0:
            value -= 1
            current = self.__adjustment.get_value()
            if direction == Gtk.DirectionType.LEFT:
                self.__adjustment.set_value(current - 1)
            else:
                self.__adjustment.set_value(current + 1)
            if value % 10:
                GLib.idle_add(self.__smooth_scrolling, value, direction)
            else:
                GLib.timeout_add(1, self.__smooth_scrolling, value, direction)
        else:
            self.update_buttons()
            self.__adjustment.connect("value-changed", self.update_buttons)

    def __on_backward_button_clicked(self, backward_button):
        """
            Scroll left
            @param backward_button as Gtk.Button
        """
        self.__adjustment.disconnect_by_func(self.update_buttons)
        backward_button.set_sensitive(False)
        value = self.scrolled.get_allocated_width() - ArtSize.BIG
        self.__smooth_scrolling(value, Gtk.DirectionType.LEFT)

    def __on_forward_button_clicked(self, forward_button):
        """
            Scroll right
            @param forward_button as Gtk.Button
        """
        self.__adjustment.disconnect_by_func(self.update_buttons)
        forward_button.set_sensitive(False)
        value = self.scrolled.get_allocated_width() - ArtSize.BIG
        self.__smooth_scrolling(value, Gtk.DirectionType.RIGHT)
