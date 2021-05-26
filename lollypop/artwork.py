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

from gi.repository import Gio, GdkPixbuf, Gdk

from hashlib import md5

from lollypop.artwork_manager import ArtworkManager
from lollypop.logger import Logger
from lollypop.define import CACHE_PATH, ALBUMS_WEB_PATH, ALBUMS_PATH
from lollypop.define import ARTISTS_PATH, TimeStamp
from lollypop.utils import emit_signal
from lollypop.utils_file import remove_oldest, create_dir


class Artwork(ArtworkManager):
    """
        Artwork manager
    """

    def __init__(self):
        """
            Init artwork manager
        """
        ArtworkManager.__init__(self)
        create_dir(CACHE_PATH)

    def add_to_cache(self, name, surface, prefix, scale_factor):
        """
            Add artwork to cache
            @param name as str
            @param surface as cairo.Surface
            @param prefix as str
            @param scale_factor as int
            @thread safe
        """
        try:
            encoded = md5(name.encode("utf-8")).hexdigest()
            width = surface.get_width() * scale_factor
            height = surface.get_height() * scale_factor
            cache_path = "%s/@%s@%s_%s_%s" % (CACHE_PATH,
                                              prefix,
                                              encoded,
                                              width, height)
            pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)
            self.save_pixbuf(pixbuf, self.add_extension(cache_path))
        except Exception as e:
            Logger.error("Art::add_artwork_to_cache(): %s" % e)

    def remove_from_cache(self, name, prefix):
        """
            Remove artwork from cache
            @param name as str
            @param prefix as str
        """
        try:
            from glob import glob
            encoded = md5(name.encode("utf-8")).hexdigest()
            search = "%s/@%s@%s_*.%s" % (CACHE_PATH,
                                         prefix,
                                         encoded,
                                         self.extension_str)
            pathes = glob(search)
            for path in pathes:
                f = Gio.File.new_for_path(path)
                f.delete(None)
            emit_signal(self, "artwork-cleared", name, prefix)
        except Exception as e:
            Logger.error("Art::remove_artwork_from_cache(): %s" % e)

    def get_from_cache(self, name, prefix, width, height):
        """
            Get artwork from cache
            @param name as str
            @param prefix as str
            @param width as int
            @param height as int
            @return GdkPixbuf.Pixbuf
        """
        try:
            encoded = md5(name.encode("utf-8")).hexdigest()
            cache_path = "%s/@%s@%s_%s_%s" % (CACHE_PATH,
                                              prefix,
                                              encoded,
                                              width, height)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                self.add_extension(cache_path))
            return pixbuf
        except Exception as e:
            Logger.warning("Art::get_artwork_from_cache(): %s" % e)
            return None

    def exists_in_cache(self, name, prefix, width, height):
        """
            True if artwork exists in cache
            @param name as str
            @param prefix as str
            @param width as int
            @param height as int
            @return bool
        """
        encoded = md5(name.encode("utf-8")).hexdigest()
        cache_path = "%s/@%s@%s_%s_%s" % (CACHE_PATH,
                                          prefix,
                                          encoded,
                                          width, height)
        f = Gio.File.new_for_path(self.add_extension(cache_path))
        return f.query_exists()

    def clean_artwork(self):
        """
            Remove old artwork from disk
        """
        try:
            remove_oldest(CACHE_PATH, TimeStamp.ONE_YEAR)
            remove_oldest(ARTISTS_PATH, TimeStamp.THREE_YEAR)
            remove_oldest(ALBUMS_PATH, TimeStamp.THREE_YEAR)
            remove_oldest(ALBUMS_WEB_PATH, TimeStamp.ONE_YEAR)
        except Exception as e:
            Logger.error("Art::clean_artwork(): %s", e)

    def clean_rounded(self):
        """
            Clean rounded artwork
        """
        try:
            from pathlib import Path
            extension = self.extension_str
            for p in Path(CACHE_PATH).glob("@ROUNDED*@*.%s" % extension):
                p.unlink()
        except Exception as e:
            Logger.error("Art::clean_all_cache(): %s", e)

    def clean_all_cache(self):
        """
            Remove all covers from cache
        """
        try:
            from pathlib import Path
            extension = self.extension_str
            for p in Path(CACHE_PATH).glob("*.%s" % extension):
                p.unlink()
        except Exception as e:
            Logger.error("Art::clean_all_cache(): %s", e)
