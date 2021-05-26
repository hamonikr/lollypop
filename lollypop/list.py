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


class LinkedList:
    """
        Double linked list
    """

    def __init__(self, value=None, next=None, prev=None):
        """
            Init list
            @param value as int
        """
        self.__value = value
        self.__next = next
        self.__prev = prev

    def set_next(self, next):
        """
            Set next
            @param next as linked list
        """
        self.__next = next

    def set_prev(self, prev):
        """
            Set prev
            @param prev as linked list
        """
        self.__prev = prev

    @property
    def has_next(self):
        """
            True if list has next
            @return bool
        """
        return self.__next is not None

    @property
    def has_prev(self):
        """
            True if list has prev
            @return bool
        """
        return self.__prev is not None

    @property
    def prev(self):
        """
            Return prev
            @return prev as LinkedList
        """
        return self.__prev

    @property
    def next(self):
        """
            Return next
            @return next as LinkedList
        """
        return self.__next

    @property
    def value(self):
        """
            Get value
            @return value as int
        """
        return self.__value
