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

from lollypop.logger import Logger


class FrameTag:
    """
        Bytes representing a frame
    """

    def __init__(self, bytes):
        """
            Init tag reader
            @param bytes as bytes
        """
        try:
            self.__key = bytes[0:4].decode("utf-8")
        except Exception as e:
            Logger.error("FrameTag::__init__(self): %s" % e)
            self.__key = "None"
        self.__bytes = bytes

    @property
    def frame(self):
        """
            Get frame
            @return bytes
        """
        return self.__bytes[10:]

    @property
    def encoding(self):
        """
            Get frame
            @return bytes
        """
        return self.frame[0:1]

    @property
    def key(self):
        """
            Get frame key
            @return str
        """
        return self.__key

    @property
    def string(self):
        """
            String representation of data
            @return str
        """
        return ""
