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

from gi.repository import Gtk, GObject

from lollypop.define import App
from lollypop.utils import emit_signal
from lollypop.helper_signals import SignalsHelper, signals_map


class ApplicationMenu(Gtk.Bin, SignalsHelper):
    """
        Configure defaults items
    """

    __gsignals__ = {
        "hidden": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals_map
    def __init__(self):
        """
            Init popover
        """
        Gtk.Bin.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/Appmenu.ui")
        widget = builder.get_object("widget")
        self.add(widget)
        self.__volume = builder.get_object("volume")
        self.__volume.set_value(App().player.volume)
        builder.connect_signals(self)
        if App().settings.get_value("background-mode"):
            builder.get_object("quit_button").show()
        if App().window.folded:
            builder.get_object("shortcuts_button").hide()
        return [
                (App().player, "volume-changed", "_on_volume_changed")
        ]

#######################
# PROTECTED           #
#######################
    def _on_button_clicked(self, button):
        """
            Popdown popover if exists
            @param button as Gtk.Button
        """
        popover = self.get_ancestor(Gtk.Popover)
        if popover is not None:
            popover.popdown()
        else:
            emit_signal(self, "hidden", True)

    def _emit_hidden(self, button):
        """
            Emit hidden signal
        """
        emit_signal(self, "hidden", False)

    def _on_volume_value_changed(self, scale):
        """
            Set volume
            @param scale as Gtk.Scale
        """
        new_volume = scale.get_value()
        if new_volume != App().player.volume:
            App().player.set_volume(scale.get_value())

    def _on_volume_changed(self, player):
        """
            Set scale value
            @param player as Player
        """
        volume = self.__volume.get_value()
        if player.volume != volume:
            self.__volume.set_value(player.volume)

    def _mute_volume(self, event_box, event_button):
        """
            Mute the volume
            @param event_box as Gtk.EventBox
            @param event_button as Gdk.EventButton
        """
        self.__volume.set_value(0)
