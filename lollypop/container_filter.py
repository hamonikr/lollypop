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

from lollypop.widgets_typeahead import TypeAheadWidget
from lollypop.define import App


class FilterContainer:
    """
        Filtering management
    """

    def __init__(self):
        """
            Init container
        """
        self.__index = 0
        self.__type_ahead = TypeAheadWidget()
        self.__type_ahead.show()
        self.grid_view.add(self.__type_ahead)

    def show_filter(self):
        """
            Show filtering widget
        """
        reveal = not self.__type_ahead.get_reveal_child()
        if reveal:
            self.__type_ahead.set_reveal_child(True)
            App().enable_special_shortcuts(False)
            self.__type_ahead.entry.grab_focus()
        elif self.__type_ahead.entry.has_focus():
            self.__type_ahead.set_reveal_child(False)
            App().enable_special_shortcuts(True)
            self.__type_ahead.entry.set_text("")
        else:
            self.__type_ahead.entry.grab_focus()

    @property
    def type_ahead(self):
        """
            Get typeahead widget
            @return TypeAheadWidget
        """
        return self.__type_ahead

############
# PRIVATE  #
############
