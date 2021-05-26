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

from gi.repository import Gio, GdkPixbuf, GLib, GObject

from PIL import Image, ImageFilter

from lollypop.define import CACHE_PATH
from lollypop.define import App, StoreExtention, ArtSize, ArtBehaviour
from lollypop.utils_file import create_dir


class ArtworkManager(GObject.GObject):
    """
        Common methods for artworks manager
    """

    __gsignals__ = {
        "artwork-cleared": (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        "album-artwork-changed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "artist-artwork-changed": (GObject.SignalFlags.RUN_FIRST,
                                   None, (str,)),
        "uri-artwork-found": (GObject.SignalFlags.RUN_FIRST, None,
                              (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        """
            Init artwork manager
        """
        GObject.GObject.__init__(self)
        create_dir(CACHE_PATH)
        App().settings.connect("changed::hd-artwork",
                               self.__on_hd_artwork_changed)
        self.__on_hd_artwork_changed()

    def save_pixbuf(self, pixbuf, path):
        """
            Save pixbuf at path
            @param pixbuf as GdkPixbuf.Pixbuf
            @param path as str
        """
        if self.__extension == StoreExtention.PNG:
            pixbuf.savev(path, "png", [None], [None])
        else:
            pixbuf.savev(path, "jpeg", ["quality"], ["100"])

    def add_extension(self, path):
        """
            Add file extension to path
            @param path as str
            @return str
        """
        if self.__extension == StoreExtention.PNG:
            return "%s.png" % path
        else:
            return "%s.jpg" % path

    def load_behaviour(self, pixbuf, width, height, behaviour):
        """
            Load behaviour on pixbuf
            @param width as int
            @param height as int
            @param behaviour as ArtBehaviour
        """
        # Crop image as square
        if behaviour & ArtBehaviour.CROP_SQUARE:
            pixbuf = self._crop_pixbuf_square(pixbuf)
        # Crop image keeping ratio
        elif behaviour & ArtBehaviour.CROP:
            pixbuf = self._crop_pixbuf(pixbuf, width, height)

        # Handle blur
        if behaviour & ArtBehaviour.BLUR:
            pixbuf = pixbuf.scale_simple(width,
                                         height,
                                         GdkPixbuf.InterpType.NEAREST)
            pixbuf = self._get_blur(pixbuf, 25)
        elif behaviour & ArtBehaviour.BLUR_HARD:
            pixbuf = pixbuf.scale_simple(width,
                                         height,
                                         GdkPixbuf.InterpType.NEAREST)
            pixbuf = self._get_blur(pixbuf, 50)
        elif behaviour & ArtBehaviour.BLUR_MAX:
            pixbuf = pixbuf.scale_simple(width,
                                         height,
                                         GdkPixbuf.InterpType.NEAREST)
            pixbuf = self._get_blur(pixbuf, 100)
        else:
            pixbuf = pixbuf.scale_simple(width,
                                         height,
                                         GdkPixbuf.InterpType.BILINEAR)
        return pixbuf

    def update_art_size(self):
        """
            Update value with some check
        """
        value = App().settings.get_value("cover-size").get_int32()
        # Check value as user can enter bad value via dconf
        if value < 50 or value > 400:
            value = 200
        ArtSize.BIG = value
        ArtSize.BANNER = int(ArtSize.BIG * 150 / 200)
        ArtSize.MEDIUM = int(ArtSize.BIG * 100 / 200)
        ArtSize.SMALL = int(ArtSize.BIG * 50 / 200)

    def save_pixbuf_from_data(self, store_path, data,
                              width=-1, height=-1):
        """
            Save a pixbuf at path from data
            @param store path as str
            @param data as bytes
            @param width as int
            @param height as int
        """
        if data is None:
            f = Gio.File.new_for_path(store_path)
            fstream = f.replace(None, False,
                                Gio.FileCreateFlags.REPLACE_DESTINATION, None)
            fstream.close()
        else:
            bytes = GLib.Bytes.new(data)
            stream = Gio.MemoryInputStream.new_from_bytes(bytes)
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
            if width != -1 and height != -1:
                pixbuf = pixbuf.scale_simple(width,
                                             height,
                                             GdkPixbuf.InterpType.BILINEAR)
            stream.close()
            self.save_pixbuf(pixbuf, store_path)

    @property
    def extension(self):
        """
            Get current artwork extension
            @return StoreExtention
        """
        return self.__extension

    @property
    def extension_str(self):
        """
            Get current artwork extension
            @return str
        """
        if self.__extension == StoreExtention.PNG:
            return "png"
        else:
            return "jpg"

#######################
# PROTECTED           #
#######################
    def _crop_pixbuf(self, pixbuf, wanted_width, wanted_height):
        """
            Crop pixbuf
            @param pixbuf as GdkPixbuf.Pixbuf
            @param wanted_width as int
            @param wanted height as int
            @return GdkPixbuf.Pixbuf
        """
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        aspect = width / height
        wanted_aspect = wanted_width / wanted_height
        if aspect > wanted_aspect:
            new_width = height * wanted_aspect
            offset = (width - new_width)
            new_pixbuf = pixbuf.new_subpixbuf(offset / 2,
                                              0,
                                              width - offset,
                                              height)
        else:
            new_height = width / wanted_aspect
            offset = (height - new_height)
            new_pixbuf = pixbuf.new_subpixbuf(0,
                                              offset / 2,
                                              width,
                                              height - offset)
        return new_pixbuf

    def _crop_pixbuf_square(self, pixbuf):
        """
            Crop pixbuf as square
            @param pixbuf as GdkPixbuf.Pixbuf
            @return GdkPixbuf.Pixbuf
        """
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        if width == height:
            new_pixbuf = pixbuf
        elif width > height:
            diff = (width - height)
            new_pixbuf = pixbuf.new_subpixbuf(diff / 2,
                                              0,
                                              width - diff,
                                              height)
        else:
            diff = (height - width)
            new_pixbuf = pixbuf.new_subpixbuf(0,
                                              diff / 2,
                                              width,
                                              height - diff)
        return new_pixbuf

    def _get_blur(self, pixbuf, gaussian):
        """
            Blur surface using PIL
            @param pixbuf as GdkPixbuf.Pixbuf
            @param gaussian as int
            @return GdkPixbuf.Pixbuf
        """
        if pixbuf is None:
            return None
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        data = pixbuf.get_pixels()
        stride = pixbuf.get_rowstride()
        has_alpha = pixbuf.get_has_alpha()
        if has_alpha:
            mode = "RGBA"
            dst_row_stride = width * 4
        else:
            mode = "RGB"
            dst_row_stride = width * 3
        tmp = Image.frombytes(mode, (width, height),
                              data, "raw", mode, stride)
        tmp = tmp.filter(ImageFilter.GaussianBlur(gaussian))
        bytes = GLib.Bytes.new(tmp.tobytes())
        del pixbuf
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(bytes,
                                                 GdkPixbuf.Colorspace.RGB,
                                                 has_alpha,
                                                 8,
                                                 width,
                                                 height,
                                                 dst_row_stride)
        return pixbuf

#######################
# PRIVATE             #
#######################
    def __on_hd_artwork_changed(self, *ignore):
        """
            Update extension value
        """
        if App().settings.get_value("hd-artwork"):
            self.__extension = StoreExtention.PNG
        else:
            self.__extension = StoreExtention.JPG
