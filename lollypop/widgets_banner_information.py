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

from gi.repository import Gtk, GLib, GObject

from lollypop.utils import emit_signal, on_query_tooltip, get_network_available
from lollypop.define import App, ArtSize, ArtBehaviour, ViewType
from lollypop.widgets_banner import BannerWidget
from lollypop.helper_signals import SignalsHelper, signals_map


class InformationBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for Information
    """

    __gsignals__ = {
        "search": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals_map
    def __init__(self, artist_id):
        """
            Init information banner
            @param artist_id as int
        """
        BannerWidget.__init__(self, ViewType.OVERLAY)
        self.__artist_id = artist_id
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/Lollypop/InformationBannerWidget.ui")
        builder.connect_signals(self)
        self.__button = builder.get_object("button")
        self.__badge_artwork = builder.get_object("badge_artwork")
        self.__title_label = builder.get_object("artist")
        self.__title_label.connect("query-tooltip", on_query_tooltip)
        self.__title_label.set_property("has-tooltip", True)
        self.__widget = builder.get_object("widget")
        self.__title_label.set_markup(GLib.markup_escape_text(
            App().artists.get_name(artist_id)))
#        self.__title_label.get_style_context().add_class("text-x-large")
        self._overlay.add_overlay(self.__widget)
        self._overlay.set_overlay_pass_through(self.__widget, True)
        self.__set_internal_size()
        if not get_network_available("WIKIPEDIA"):
            self.__button.set_sensitive(False)
        return [
               (App().window.container.widget, "notify::folded",
                "_on_container_folded"),
        ]

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        BannerWidget.update_for_width(self, width)
        self.__set_artwork()

    @property
    def button(self):
        """
            Get toggle button
            @return Gtk.ToggleButton
        """
        return self.__button

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
        """
        if BannerWidget._handle_width_allocate(self, allocation):
            self.__set_artwork()

    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        self.__set_internal_size()

    def _on_button_toggled(self, button):
        """
            Emit search signal
            @param button as Gtk.ToggleButton
        """
        if get_network_available("WIKIPEDIA"):
            emit_signal(self, "search", button.get_active())

#######################
# PRIVATE             #
#######################
    def __set_artwork(self):
        """
            Set artwork
        """
        if App().settings.get_value("artist-artwork") and App().animations:
            artist = App().artists.get_name(self.__artist_id)
            App().art_helper.set_artist_artwork(
                                        artist,
                                        # +100 to prevent resize lag
                                        self.width + 100,
                                        self.height,
                                        self.get_scale_factor(),
                                        ArtBehaviour.BLUR_HARD |
                                        ArtBehaviour.DARKER,
                                        self._on_artwork)
        else:
            self._artwork.get_style_context().add_class("default-banner")
        if self.width < ArtSize.BANNER * 3:
            if self.__widget.get_child_at(1, 0) == self.__title_label:
                self.__widget.remove(self.__title_label)
                self.__widget.attach(self.__title_label, 2, 2, 3, 1)
        elif self.__widget.get_child_at(2, 2) == self.__title_label:
            self.__widget.remove(self.__title_label)
            self.__widget.attach(self.__title_label, 1, 0, 1, 3)

    def __set_badge_artwork(self, art_size):
        """
            Set artist artwork on badge
            @param art_size as int
        """
        if App().settings.get_value("artist-artwork"):
            artist = App().artists.get_name(self.__artist_id)
            App().art_helper.set_artist_artwork(
                                        artist,
                                        art_size,
                                        art_size,
                                        self.get_scale_factor(),
                                        ArtBehaviour.ROUNDED |
                                        ArtBehaviour.CROP_SQUARE |
                                        ArtBehaviour.CACHE,
                                        self.__on_badge_artist_artwork,
                                        art_size)
        else:
            self.__badge_artwork.hide()

    def __set_internal_size(self):
        """
            Set content size based on current width
        """
        # Text size
        title_context = self.__title_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        if App().window.folded:
            art_size = ArtSize.MEDIUM
            cls = "text-large"
        else:
            art_size = ArtSize.BANNER
            cls = "text-x-large"
        self.__title_label.get_style_context().add_class(cls)
        self.__set_badge_artwork(art_size)

    def __on_badge_artist_artwork(self, surface, art_size):
        """
            Set artist artwork on badge
            @param surface as cairo.Surface
            @param art_size as int
        """
        if surface is None:
            self.__badge_artwork.get_style_context().add_class("circle-icon")
            self.__badge_artwork.set_size_request(art_size, art_size)
            self.__badge_artwork.set_from_icon_name(
                                              "avatar-default-symbolic",
                                              Gtk.IconSize.DIALOG)
        else:
            self.__badge_artwork.get_style_context().remove_class(
                "circle-icon")
            self.__badge_artwork.set_from_surface(surface)
