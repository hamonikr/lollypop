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

from gi.repository import Gio, GObject

from hashlib import md5

from lollypop.logger import Logger
from lollypop.information_downloader import InformationDownloader


class InformationStore(GObject.Object, InformationDownloader):
    """
        Generic class to cache information
    """

    def __init__(self):
        """
            Init store
        """
        GObject.Object.__init__(self)
        InformationDownloader.__init__(self)

    def get_information(self, name, path):
        """
            Get information for name and path
            @param name as str
            @param path as str
            @return content as bytes
        """
        content = None
        try:
            encoded = md5(name.encode("utf-8")).hexdigest()
            filepath = "%s/%s.txt" % (path, encoded)
            f = Gio.File.new_for_path(filepath)
            if f.query_exists():
                (status, content, tag) = f.load_contents()
        except Exception as e:
            Logger.error("InformationStore::get_information(): %s", e)
        return content

    def save_information(self, name, path, content):
        """
            Save information for name and path
            @param name as str
            @param path as str
            @param content as bytes
        """
        try:
            if content is not None:
                encoded = md5(name.encode("utf-8")).hexdigest()
                filepath = "%s/%s.txt" % (path, encoded)
                f = Gio.File.new_for_path(filepath)
                fstream = f.replace(None, False,
                                    Gio.FileCreateFlags.REPLACE_DESTINATION,
                                    None)
                if fstream is not None:
                    fstream.write(content, None)
                    fstream.close()
        except Exception as e:
            Logger.error("InformationStore::save_information(): %s", e)
