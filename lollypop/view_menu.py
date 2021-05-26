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

from lollypop.view import View
from lollypop.define import ViewType, StorageType


class MenuView(View):
    """
        Show a menu
    """

    def __init__(self, menu):
        """
            Init view
            @param menu as Gtk.Widget
        """
        View.__init__(self, StorageType.ALL, ViewType.SCROLLED)
        menu.get_style_context().add_class("adaptive-menu")
        menu.set_vexpand(True)
        self.add_widget(menu)

    @property
    def args(self):
        return None
