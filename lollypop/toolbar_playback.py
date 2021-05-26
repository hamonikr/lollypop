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

from lollypop.define import App
from lollypop.widgets_player_buttons import ButtonsPlayerWidget


class ToolbarPlayback(Gtk.Box):
    """
        Playback toolbar
    """

    def __init__(self, window):
        """
            Init toolbar
            @parma window as Window
        """
        Gtk.Box.__init__(self)
        self.__back_button = Gtk.Button.new_from_icon_name(
            "go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.__back_button.show()
        self.__back_button.connect("clicked", self.__on_back_button_clicked)
        self.__player_buttons = ButtonsPlayerWidget()
        self.__player_buttons.show()
        self.set_spacing(10)
        self.pack_start(self.__back_button, False, False, 0)
        self.pack_start(self.__player_buttons, False, False, 0)
        window.container.connect("can-go-back-changed",
                                 self.__on_can_go_back_changed)

    @property
    def player_buttons(self):
        """
            Get player buttons
            @return Gtk.Box
        """
        return self.__player_buttons

    @property
    def back_button(self):
        """
            Get back button
            @return Gtk.Button
        """
        return self.__back_button

#######################
# PRIVATE             #
#######################
    def __on_back_button_clicked(self, button):
        """
            Go back in container stack
            @param button as Gtk.Button
        """
        App().window.container.go_back()

    def __on_can_go_back_changed(self, container, back):
        """
            Make button sensitive
            @param container as Container
            @param back as bool
        """
        if back:
            self.__back_button.set_sensitive(True)
        else:
            self.__back_button.set_sensitive(False)
