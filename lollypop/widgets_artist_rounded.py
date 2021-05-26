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

from gi.repository import Gtk

from random import shuffle

from lollypop.define import App, ArtBehaviour, StorageType
from lollypop.utils import emit_signal
from lollypop.objects_album import Album
from lollypop.widgets_flowbox_rounded import RoundedFlowBoxWidget


class RoundedArtistWidget(RoundedFlowBoxWidget):
    """
        Artist photo or artist's albums in a rounded widget
    """

    def __init__(self, item, view_type, font_height):
        """
            Init widget
            @param item as (int, str, str)
            @param view_type as ViewType
            @param font_height as int
        """
        # Get values from DB
        if isinstance(item, int):
            artist_id = item
            artist_name = artist_sortname = App().artists.get_name(artist_id)
        else:
            artist_id = item[0]
            artist_name = item[1]
            artist_sortname = item[2]
        RoundedFlowBoxWidget.__init__(self, artist_id, artist_name,
                                      artist_sortname, view_type, font_height)

    def populate(self):
        """
            Populate widget content
        """
        if self._artwork is None:
            RoundedFlowBoxWidget.populate(self)
            self._artwork.get_style_context().add_class("circle-icon-large")
            self.connect("destroy", self.__on_destroy)
        else:
            self.set_artwork()

    def set_artwork(self):
        """
            Set artist artwork
        """
        self._set_artwork()

#######################
# PROTECTED           #
#######################
    def _set_artwork(self):
        """
            Set artist artwork
        """
        if self._artwork is None:
            return
        RoundedFlowBoxWidget.set_artwork(self)
        if App().settings.get_value("artist-artwork"):
            App().art_helper.set_artist_artwork(
                                            self.name,
                                            self._art_size,
                                            self._art_size,
                                            self._artwork.get_scale_factor(),
                                            ArtBehaviour.ROUNDED |
                                            ArtBehaviour.CROP_SQUARE |
                                            ArtBehaviour.CACHE,
                                            self.__on_artist_artwork)
        else:
            album_ids = App().albums.get_ids([], [self._data],
                                             StorageType.ALL, True)
            if album_ids:
                shuffle(album_ids)
                App().art_helper.set_album_artwork(
                                            Album(album_ids[0]),
                                            self._art_size,
                                            self._art_size,
                                            self._artwork.get_scale_factor(),
                                            ArtBehaviour.ROUNDED |
                                            ArtBehaviour.CROP_SQUARE |
                                            ArtBehaviour.CACHE,
                                            self.__on_artist_artwork)
            else:
                self.__on_artist_artwork(None)

#######################
# PRIVATE             #
#######################
    def __on_artist_artwork(self, surface):
        """
            Finish widget initialisation
            @param surface as cairo.Surface
        """
        if self._artwork is None:
            return
        if surface is None:
            self._artwork.set_from_icon_name("avatar-default-symbolic",
                                             Gtk.IconSize.DIALOG)
        else:
            self._artwork.set_from_surface(surface)
        emit_signal(self, "populated")

    def __on_destroy(self, widget):
        """
            Destroyed widget
            @param widget as Gtk.Widget
        """
        self.__artwork = None
