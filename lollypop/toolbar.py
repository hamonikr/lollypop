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

from gi.repository import GLib, Handy

from lollypop.define import App, Size
from lollypop.toolbar_playback import ToolbarPlayback
from lollypop.objects_track import Track
from lollypop.toolbar_info import ToolbarInfo
from lollypop.toolbar_title import ToolbarTitle
from lollypop.toolbar_end import ToolbarEnd
from lollypop.helper_size_allocation import SizeAllocationHelper
from lollypop.helper_signals import SignalsHelper, signals


class Toolbar(Handy.HeaderBar, SizeAllocationHelper, SignalsHelper):
    """
        Lollypop toolbar
    """

    @signals
    def __init__(self, window):
        """
            Init toolbar
            @param window as Window
        """
        Handy.HeaderBar.__init__(self)
        SizeAllocationHelper.__init__(self)
        self.__width = Size.MINI
        self.__timeout_id = None
        self.set_title("Lollypop")
        self.__toolbar_playback = ToolbarPlayback(window)
        self.__toolbar_playback.show()
        self.__toolbar_info = ToolbarInfo()
        self.__toolbar_info.show()
        self.__toolbar_title = ToolbarTitle()
        self.__toolbar_end = ToolbarEnd(window)
        self.__toolbar_end.show()
        self.pack_start(self.__toolbar_playback)
        self.pack_start(self.__toolbar_info)
        self.set_custom_title(self.__toolbar_title)
        self.pack_end(self.__toolbar_end)
        return [
            (App().player, "current-changed", "_on_current_changed"),
            (App().window.container.widget, "notify::folded",
             "_on_container_folded")
        ]

    def do_get_preferred_width(self):
        """
            Allow window resize
            @return (int, int)
        """
        width = max(Size.PHONE, self.__width)
        return (Size.PHONE, width)

    def hide_info_and_buttons(self, folded):
        """
            Hide information and buttons
            @param folded as bool
        """
        def show_children():
            self.__timeout_id = None
            self.__toolbar_info.show_children()

        if self.__timeout_id is not None:
            GLib.source_remove(self.__timeout_id)
            self.__timeout_id = None

        if folded:
            self.__toolbar_playback.player_buttons.hide()
            self.__toolbar_title.hide()
            self.__toolbar_info.hide_children()
        else:
            if App().player.current_track.id is not None:
                self.__toolbar_title.show()
            # If user double click headerbar to maximize window
            # We do not want info bar to receive click signal
            self.__timeout_id = GLib.timeout_add(200, show_children)
            self.__toolbar_playback.player_buttons.show()

    @property
    def end(self):
        """
            Return end toolbar
            @return ToolbarEnd
        """
        return self.__toolbar_end

    @property
    def info(self):
        """
            Return info toolbar
            @return ToolbarInfo
        """
        return self.__toolbar_info

    @property
    def title(self):
        """
            Return title toolbar
            @return ToolbarTitle
        """
        return self.__toolbar_title

    @property
    def playback(self):
        """
            Return playback toolbar
            @return ToolbarPlayback
        """
        return self.__toolbar_playback

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            width = self.__toolbar_playback.get_preferred_width()[1]
            width += self.__toolbar_end.get_preferred_width()[1]
            available = allocation.width - width
            if allocation.width < Size.BIG:
                title_width = available / 3
            else:
                title_width = available / 2.5
            self.__toolbar_title.set_width(title_width)
            self.__toolbar_info.set_width((available - title_width) / 2)

    def _on_current_changed(self, player):
        """
            Update buttons and progress bar
            @param player as Player
        """
        if player.current_track.id is not None and\
                not App().window.folded:
            if isinstance(player.current_track, Track):
                self.__toolbar_title.show()
            else:
                self.__toolbar_title.hide()
            self.__toolbar_info.show_children()
        else:
            self.__toolbar_title.hide()
            self.__toolbar_info.hide_children()

    def _on_container_folded(self, leaflet, folded):
        """
            Update internal widgets
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        self.hide_info_and_buttons(App().window.folded)
