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

from gi.repository import GLib, Gtk, Pango, GObject

from lollypop.define import ArtSize, ViewType, MARGIN, MARGIN_MEDIUM, App
from lollypop.utils import on_query_tooltip


class RoundedFlowBoxWidget(Gtk.FlowBoxChild):
    """
        Rounded flowbox child widget
    """

    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, data, name, sortname, view_type, font_height):
        """
            Init widget
            @param data as object
            @param name as str
            @param sortname as str
            @param view_type as ViewType
            @param font_height as int
        """
        # We do not use Gtk.Builder for speed reasons
        Gtk.FlowBoxChild.__init__(self)
        self._artwork = None
        self._data = data
        self._art_size = 1
        self.__name = name
        self.__sortname = sortname
        self.__view_type = view_type
        self.__font_height = font_height
        self._scale_factor = self.get_scale_factor()
        self.set_property("halign", Gtk.Align.CENTER)
        self.set_property("margin", MARGIN)
        self.update_art_size()

    def populate(self):
        """
            Populate widget content
        """
        self._grid = Gtk.Grid()
        self._grid.set_orientation(Gtk.Orientation.VERTICAL)
        self._grid.set_row_spacing(MARGIN_MEDIUM)
        self._grid.show()
        self._label = Gtk.Label.new()
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._label.set_property("halign", Gtk.Align.CENTER)
        self._label.set_property("has-tooltip", True)
        self._label.connect("query-tooltip", on_query_tooltip)
        self._label.set_markup(
            "<b>" + GLib.markup_escape_text(self.__name) + "</b>")
        self._label.show()
        self._artwork = Gtk.Image.new()
        self._artwork.show()
        self._artwork.set_size_request(self._art_size, self._art_size)
        self.set_artwork()
        self._grid.add(self._artwork)
        self._grid.add(self._label)
        self.add(self._grid)

    def update_art_size(self):
        """
            Update art size based on current window state
        """
        if self.__view_type & ViewType.SMALL:
            self._art_size = ArtSize.MEDIUM
        elif App().window.folded:
            self._art_size = ArtSize.BANNER
        else:
            self._art_size = ArtSize.BIG
        self.set_size_request(self._art_size,
                              self._art_size + self.__font_height * 2)
        if self._artwork is not None:
            self._artwork.set_size_request(self._art_size, self._art_size)

    def set_artwork(self):
        """
            Set artwork
        """
        pass

    def reset_artwork(self):
        """
            Reset widget artwork
        """
        self.update_art_size()
        if self._artwork is not None:
            self._artwork.set_from_surface(None)

    def do_get_preferred_width(self):
        """
            Return preferred width
            @return (int, int)
        """
        width = Gtk.FlowBoxChild.do_get_preferred_width(self)[0]
        return (width, width)

    def rename(self, name):
        """
            Rename widget
            @param name as str
        """
        self._label.set_markup("<b>" + GLib.markup_escape_text(name) + "</b>")

    @property
    def name(self):
        """
            Get name
            @return str
        """
        return self.__name

    @property
    def sortname(self):
        """
            Get sortname
            @return str
        """
        return self.__sortname

    @property
    def data(self):
        """
            Get associated data
            @return object
        """
        return self._data

    @property
    def is_populated(self):
        """
            True if album populated
        """
        return True

    @property
    def artwork(self):
        """
            Get album artwork
            @return Gtk.Image
        """
        return self._artwork

    @property
    def artwork_name(self):
        """
            Get artwork name
            return str
        """
        return self.name

#######################
# PROTECTED           #
#######################

    def _get_album_ids(self):
        return []

#######################
# PRIVATE             #
#######################
