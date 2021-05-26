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

from lollypop.define import App, ViewType
from lollypop.view import View
from lollypop.utils import get_default_storage_type
from lollypop.helper_signals import SignalsHelper, signals_map


class InformationViewStack(View, SignalsHelper):
    """
        InformationView stack showing current track
    """

    @signals_map
    def __init__(self):
        """
            Init artist infos
        """
        View.__init__(self, get_default_storage_type(), ViewType.DEFAULT)
        self.__stack = Gtk.Stack.new()
        self.__stack.show()
        self.__stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.__stack.set_transition_duration(500)
        self.add_widget(self.__stack)
        self.__populate()
        return [
            (App().player, "current-changed", "_on_current_changed"),
        ]

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update artist information
            @param player as Player
        """
        self.__populate()

#######################
# PRIVATE             #
#######################
    def __populate(self):
        """
            Add a new information view and destroy previous
        """
        if App().player.current_track.id is None:
            self.show_placeholder(True)
        else:
            self.show_placeholder(False)
            from lollypop.view_information import InformationView
            current_child = self.__stack.get_visible_child()
            if current_child is None or current_child.artist_name !=\
                    App().player.current_track.artists[0]:
                self.__view = InformationView(ViewType.SCROLLED, False)
                self.__view.show()
                self.__view.populate()
                self.__stack.add(self.__view)
                self.__stack.set_visible_child(self.__view)
                if current_child is not None:
                    GLib.timeout_add(500, current_child.destroy)
