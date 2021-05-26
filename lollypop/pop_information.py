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

from lollypop.define import App, Size, ViewType
from lollypop.view_information import InformationView
from lollypop.widgets_popover import Popover


class InformationPopover(Popover):
    """
        Popover with artist information
    """

    def __init__(self, minimal=False):
        """
            Init artist infos
            @param minimal as bool
        """
        Popover.__init__(self)
        self.__minimal = minimal
        self.__width = 10
        self.__view = InformationView(ViewType.SCROLLED |
                                      ViewType.SMALL, minimal)
        self.__view.show()
        self.connect("map", self.__on_map)
        self.get_style_context().add_class("padding")
        self.add(self.__view)

    def populate(self, artist_id=None):
        """
            Show information for artists
            @param artist_id as int
        """
        self.__view.populate(artist_id)

    def do_get_preferred_width(self):
        return (self.__width, self.__width)

#######################
# PROTECTED           #
#######################

#######################
# PRIVATE             #
#######################
    def __on_map(self, widget):
        """
            Connect signal and resize
            @param widget as Gtk.Widget
        """
        size = App().window.get_size()
        if self.__minimal:
            self.__width = min(size[0] * 0.95, 500)
            self.set_size_request(self.__width,
                                  min(size[1] * 0.5, 600))
        else:
            self.__width = Size.NORMAL
            self.set_size_request(self.__width,
                                  min(size[1] * 0.7, 800))
