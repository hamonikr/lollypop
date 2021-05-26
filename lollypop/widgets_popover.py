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

from gi.repository import Gtk, GLib, GObject

from lollypop.utils import emit_signal


class Popover(Gtk.Popover):
    """
        Overlay to be compatible with MenuWidget
    """
    # Same signal than MenuWidget
    __gsignals__ = {
        "hidden": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, auto_destroy=True):
        """
            Init widget
            @param auto_destroy as bool
        """
        Gtk.Popover.__init__(self)
        self.connect("closed", self.__on_closed)
        self.__auto_destroy = auto_destroy

    def __on_closed(self, popover):
        """
            Destroy self
        """
        emit_signal(self, "hidden", True)
        if self.__auto_destroy:
            GLib.idle_add(self.destroy)
