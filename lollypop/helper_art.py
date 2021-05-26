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

from gi.repository import GObject, GLib, Gtk, Gdk

import cairo

from lollypop.define import App, ArtBehaviour
from lollypop.utils import get_round_surface


class ArtHelper(GObject.Object):
    """
        Helper to load artwork smoothly
    """

    def __init__(self):
        """
            Init helper
        """
        GObject.Object.__init__(self)

    def set_frame(self, image, frame, width, height):
        """
            Update image for frame
            @param image as Gtk.Image
            @param frame as str
            @param width as int
            @param height as int
        """
        context = image.get_style_context()
        for c in context.list_classes():
            context.remove_class(c)
        context.add_class(frame)
        padding = context.get_padding(Gtk.StateFlags.NORMAL)
        border = context.get_border(Gtk.StateFlags.NORMAL)
        image.set_size_request(width + padding.left +
                               padding.right + border.left + border.right,
                               height + padding.top +
                               padding.bottom + border.top + border.bottom)

    def set_album_artwork(self, album, width, height, scale_factor,
                          effect, callback, *args):
        """
            Set artwork for album id
            @param album as Album
            @param width as int
            @param height as int
            @param scale_factor as int
            @param effect as ArtBehaviour
            @param callback as function
        """
        App().task_helper.run(App().album_art.get,
                              album,
                              width,
                              height,
                              scale_factor,
                              effect,
                              callback=(self._on_get_artwork_pixbuf,
                                        width,
                                        height,
                                        scale_factor,
                                        effect,
                                        callback,
                                        *args))

    def set_artist_artwork(self, name, width, height, scale_factor,
                           effect, callback, *args):
        """
            Set artwork for album id
            @param name as str
            @param width as int
            @param height as int
            @param scale_factor as int
            @param effect as ArtBehaviour
            @param callback as function
        """
        App().task_helper.run(App().artist_art.get,
                              name,
                              width,
                              height,
                              scale_factor,
                              effect,
                              callback=(self._on_get_artwork_pixbuf,
                                        width,
                                        height,
                                        scale_factor,
                                        effect,
                                        callback,
                                        *args))

#######################
# PROTECTED           #
#######################
    def _on_get_artwork_pixbuf(self, pixbuf, width, height, scale_factor,
                               effect, callback, *args):
        """
            Transform pixbuf to surface and load surface effects
            @param pixbuf as Gdk.Pixbuf
            @param size as int
            @param scale_factor as int
            @param effect as ArtBehaviour
            @param callback as function
        """
        surface = None
        if pixbuf is not None:
            if effect & ArtBehaviour.ROUNDED:
                radius = pixbuf.get_width() / 2
                surface = get_round_surface(pixbuf, scale_factor, radius)
            elif effect & ArtBehaviour.ROUNDED_BORDER:
                surface = get_round_surface(pixbuf, scale_factor, 5)
            else:
                surface = Gdk.cairo_surface_create_from_pixbuf(
                        pixbuf, scale_factor, None)
        App().task_helper.run(self.__surface_effects, surface, width, height,
                              scale_factor, effect, callback, *args)

#######################
# PRIVATE             #
#######################
    def __surface_effects(self, surface, width, height, scale_factor,
                          effect, callback, *args):
        """
            Load surface effects
            @param surface as cairo.Surface
            @param size as int
            @param scale_factor as int
            @param effect as ArtBehaviour
            @param callback as function
        """
        if effect & ArtBehaviour.DARKER:
            self.__set_color(surface, 0, 0, 0)
        if effect & ArtBehaviour.LIGHTER:
            self.__set_color(surface, 1, 1, 1)
        GLib.idle_add(callback, surface, *args)

    def __set_color(self, surface, r, g, b):
        """
            Get a darker pixbuf
            @param surface as cairo.Surface
            @param r as int
            @param g as int
            @param b as int
            @return cairo.Surface
        """
        if surface is not None:
            ctx = cairo.Context(surface)
            ctx.rectangle(0, 0, surface.get_width(), surface.get_height())
            ctx.set_source_rgba(r, g, b, 0.5)
            ctx.fill()
