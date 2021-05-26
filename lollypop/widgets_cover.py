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

from gi.repository import Gtk, Gio, GObject

from lollypop.define import App, ArtSize, ArtBehaviour, ViewType, Type
from lollypop.utils import set_cursor_type, popup_widget, emit_signal
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.helper_gestures import GesturesHelper


class CoverWidgetBase(SignalsHelper):
    """
        Widget showing current album cover
    """

    @signals_map
    def __init__(self, album, view_type):
        """
            Init cover widget
            @param album as Album
            @param view_type as ViewType
        """
        self.set_property("halign", Gtk.Align.START)
        self.set_property("valign", Gtk.Align.CENTER)
        self._album = album
        self._view_type = view_type
        self.__art_size = 1
        self._artwork = Gtk.Image.new()
        self._artwork.show()
        return [
            (App().album_art, "album-artwork-changed",
             "_on_album_artwork_changed")
        ]

    def set_art_size(self, art_size):
        """
            Set cover artwork size
            @param art_size as int
        """
        if self.__art_size == art_size:
            return
        self.__art_size = art_size
        App().art_helper.set_frame(self._artwork,
                                   "small-cover-frame",
                                   self.__art_size,
                                   self.__art_size)
        App().art_helper.set_album_artwork(
                self._album,
                self.__art_size,
                self.__art_size,
                self._artwork.get_scale_factor(),
                ArtBehaviour.CACHE | ArtBehaviour.CROP_SQUARE,
                self._on_album_artwork)

#######################
# PROTECTED           #
#######################
    def _on_album_artwork_changed(self, art, album_id):
        """
            Update cover for album_id
            @param art as Art
            @param album_id as int
        """
        if self._album is None:
            return
        if album_id == self._album.id:
            App().art_helper.set_album_artwork(
                self._album,
                self.__art_size,
                self.__art_size,
                self._artwork.get_scale_factor(),
                ArtBehaviour.CACHE | ArtBehaviour.CROP_SQUARE,
                self._on_album_artwork)

    def _on_album_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if surface is None:
            if self.__art_size == ArtSize.BANNER:
                icon_size = Gtk.IconSize.DIALOG
            else:
                icon_size = Gtk.IconSize.DND
            self._artwork.set_from_icon_name("folder-music-symbolic",
                                             icon_size)
        else:
            self._artwork.set_from_surface(surface)


class EditCoverWidget(Gtk.EventBox, CoverWidgetBase, GesturesHelper):
    """
        Widget showing current album cover (edition allowed)
    """

    def __init__(self, album, view_type):
        """
            Init widget
            @param album as Album
            @param view_type as ViewType
        """
        Gtk.EventBox.__init__(self)
        CoverWidgetBase.__init__(self, album, view_type)
        GesturesHelper.__init__(self, self)
        self.connect("realize", set_cursor_type)
        self.add(self._artwork)

#######################
# PROTECTED           #
#######################
    def _on_primary_press_gesture(self, x, y, event):
        """
            Show artwork popover
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        if self._view_type & ViewType.ALBUM:
            from lollypop.widgets_menu import MenuBuilder
            from lollypop.menu_artwork import AlbumArtworkMenu
            menu = Gio.Menu()
            if App().window.folded:
                from lollypop.menu_header import AlbumMenuHeader
                menu.append_item(AlbumMenuHeader(self._album))
            menu_widget = MenuBuilder(menu, False)
            menu_widget.show()
            menu_ext = AlbumArtworkMenu(self._album, self._view_type, False)
            menu_ext.connect("hidden", self.__close_artwork_menu)
            menu_ext.show()
            menu_widget.add_widget(menu_ext, False)
            self._artwork_popup = popup_widget(menu_widget, self,
                                               None, None, None)

#######################
# PRIVATE             #
#######################
    def __close_artwork_menu(self, action, variant):
        if App().window.folded:
            App().window.container.go_back()
        else:
            self._artwork_popup.destroy()


class BrowsableCoverWidget(Gtk.EventBox, CoverWidgetBase, GesturesHelper):
    """
        Widget showing current album cover
    """

    def __init__(self, album, view_type):
        """
            Init cover widget
            @param album as Album
            @param view_type as ViewType
        """
        Gtk.EventBox.__init__(self)
        CoverWidgetBase.__init__(self, album, view_type)
        self.add(self._artwork)
        GesturesHelper.__init__(self, self)
        self.connect("realize", set_cursor_type)

#######################
# PROTECTED           #
#######################
    def _on_primary_press_gesture(self, x, y, event):
        """
            Browse to album
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        App().window.container.show_view([Type.ALBUM], self._album)


class CoverWidget(Gtk.Bin, CoverWidgetBase):
    """
        Widget showing current album cover
    """

    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, album, view_type):
        """
            Init cover widget
            @param album as Album
            @param view_type as ViewType
        """
        Gtk.Bin.__init__(self)
        CoverWidgetBase.__init__(self, album, view_type)
        self.add(self._artwork)

#######################
# PRIVATE             #
#######################
    def _on_album_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        emit_signal(self, "populated")
        CoverWidgetBase._on_album_artwork(self, surface)
