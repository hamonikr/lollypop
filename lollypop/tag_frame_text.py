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
from lollypop.utils_file import decodeUnicode, splitUnicode
from lollypop.tag_frame import FrameTag


class FrameTextTag(FrameTag):
    """
        Bytes representing a text frame
    """

    def __init__(self, bytes):
        """
            Init tag reader
            @param bytes as bytes
        """
        FrameTag.__init__(self, bytes)

    @property
    def string(self):
        """
            String representation of data
            @return str/None
        """
        try:
            (d, t) = splitUnicode(self.frame, self.encoding)
            return decodeUnicode(t, self.encoding)
        except Exception as e:
            Logger.error("FrameTextTag::string: %s, %s", e, self.frame)
            return ""
