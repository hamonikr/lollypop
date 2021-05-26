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

from gi.repository import GLib


class AdaptiveHelper:
    """
        Adaptive support for View
    """

    def __init__(self):
        """
            Init view
        """
        self.__sidebar_id = None
        self.__selection_ids = {"left": [], "right": []}

    def set_sidebar_id(self, sidebar_id):
        """
            Set sidebar id
            @param sidebar_id as int
        """
        self.__sidebar_id = sidebar_id

    def set_selection_ids(self, selection_ids):
        """
            Set selection ids
            @param selection_ids as {"left": [int], "right": [int])
        """
        self.__selection_ids = selection_ids

    def destroy_later(self):
        """
            Delayed destroy
            Allow animations in stack
        """
        def do_destroy():
            self.destroy()
        self.stop()
        if self.args is not None:
            GLib.timeout_add(1000, do_destroy)

    @property
    def sidebar_id(self):
        """te
            Get sidebar id
            @return int
        """
        return self.__sidebar_id

    @property
    def selection_ids(self):
        """
            Get selection ids (sidebar id + extra ids)
            return [int]
        """
        return self.__selection_ids

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {}
