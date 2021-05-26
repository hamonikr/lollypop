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


class ButtonProgressBar(Gtk.ProgressBar):
    """
        Simple progress bar with width contraint
    """

    def __init__(self):
        Gtk.ProgressBar.__init__(self)
        self.set_property("valign", Gtk.Align.END)
        self.get_style_context().add_class("progressbar-button")

    def do_get_preferred_width(self):
        return (24, 24)


class ProgressBar(Gtk.ProgressBar):
    """
        A smart/smooth FIFO progress bar
        Many objects can register and must call set_fraction(1) to unregister
    """

    def __init__(self):
        """
            Init progress bar
        """
        Gtk.ProgressBar.__init__(self)
        self.__callers = []
        self.__fraction = 0.0
        self.__pulse_timeout = None
        self.__progress_running = False

    def add(self, caller):
        """
            Add caller
            @param caller as Instance
        """
        if caller not in self.__callers:
            self.__callers.insert(0, caller)

    def set_fraction(self, fraction, caller):
        """
            Set fraction if caller is on top.
            @param fraction as float
            @param caller as object
        """
        if not self.__callers:
            return
        if self.__pulse_timeout is not None:
            GLib.source_remove(self.__pulse_timeout)
            self.__pulse_timeout = None
        if caller == self.__callers[0]:
            self.show()
            self.__fraction = fraction
            if fraction == 0:
                Gtk.ProgressBar.set_fraction(self, 0.0)
            elif not self.__progress_running:
                self.__progress_running = True
                self.__progress_update(caller)

    def pulse(self, pulse):
        """
            Make progress bar visible/pulse if pulse is True
            @param pulse as bool
        """
        # Only pulse if nobody is using the progressbar
        if self.__callers:
            return
        if pulse:
            self.show()
            if self.__pulse_timeout is None:
                self.__pulse_timeout = GLib.timeout_add(500, self.__pulse)
        else:
            self.hide()
            if self.__pulse_timeout is not None:
                GLib.source_remove(self.__pulse_timeout)
                self.__pulse_timeout = None

#######################
# PRIVATE             #
#######################
    def __reset(self, caller):
        """
            Reset and hide progressbar
            @param caller as object
        """
        self.hide()
        self.__fraction = 0.0
        Gtk.ProgressBar.set_fraction(self, 0.0)
        self.__progress_running = False
        self.__callers.remove(caller)

    def __pulse(self):
        """
            Make progress bar pulse while visible
            @param pulse as bool
        """
        if self.is_visible():
            Gtk.ProgressBar.pulse(self)
            return True
        else:
            Gtk.ProgressBar.set_fraction(self, 0.0)
            self.__pulse_timeout = None
            return False

    def __progress_update(self, caller):
        """
            Update progressbar smoothly
            @param caller as object
        """
        if caller != self.__callers[0]:
            self.__progress_running = False
            return
        current = self.get_fraction()
        if self.__fraction < 1:
            progress = (self.__fraction - current) / 10
        else:
            progress = 0.01
        if current < self.__fraction:
            Gtk.ProgressBar.set_fraction(self, current + progress)
        if current < 1.0:
            GLib.timeout_add(10, self.__progress_update, caller)
        else:
            GLib.timeout_add(1000, self.__reset, caller)
