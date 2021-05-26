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

from gi.repository import Gtk, GLib, Pango, GObject

from gettext import gettext as _

from lollypop.define import App, MARGIN, ViewType, ArtBehaviour
from lollypop.widgets_banner import BannerWidget
from lollypop.utils import emit_signal
from lollypop.helper_signals import SignalsHelper, signals_map


class LyricsBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for lyrics
    """

    __gsignals__ = {
        "translate": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals_map
    def __init__(self, view_type=ViewType.OVERLAY):
        """
            Init cover widget
            @param album
            @param view_type as ViewType
        """
        BannerWidget.__init__(self, view_type)
        self.__title_label = Gtk.Label.new()
        self.__title_label.show()
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.set_vexpand(True)
        self.__translate_button = Gtk.ToggleButton.new()
        image = Gtk.Image.new_from_icon_name(
            "accessories-dictionary-symbolic", Gtk.IconSize.BUTTON)
        image.show()
        self.__translate_button.set_image(image)
        self.__translate_button.show()
        self.__translate_button.connect("toggled",
                                        self.__on_lyrics_button_toggled)
        self.__translate_button.get_style_context().add_class(
            "banner-button")
        self.__translate_button.set_property("valign", Gtk.Align.CENTER)
        self.__translate_button.set_property("halign", Gtk.Align.END)
        self.__translate_button.set_hexpand(True)
        self.__translate_button.set_sensitive(False)
        grid = Gtk.Grid()
        grid.show()
        grid.set_column_spacing(MARGIN)
        grid.add(self.__title_label)
        grid.add(self.__translate_button)
        grid.set_property("margin", MARGIN)
        grid.set_margin_end(MARGIN)
        self._overlay.add_overlay(grid)
        self._overlay.set_overlay_pass_through(grid, True)
        self.__update()
        self.__set_internal_size()
        return [
            (App().player, "current-changed", "_on_current_changed"),
            (App().window.container.widget, "notify::folded",
             "_on_container_folded"),
            (App().album_art, "album-artwork-changed",
             "_on_album_artwork_changed")
        ]

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        BannerWidget.update_for_width(self, width)
        self.__set_artwork()

    @property
    def translate_button(self):
        """
            Get translate button
            @return Gtk.Button
        """
        return self.__translate_button

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

    def _on_album_artwork_changed(self, art, album_id):
        """
            Update cover for album_id
            @param art as Art
            @param album_id as int
        """
        if album_id == App().player.current_track.album.id:
            self.__set_artwork()

    def _on_current_changed(self, player):
        """
            Update labels and artwork
            @param player as Player
        """
        self.__update()

#######################
# PRIVATE             #
#######################
    def __update(self):
        """
            Update banner
        """
        if App().player.current_track.id is None:
            self.__title_label.set_text(_("No track playing"))
            self._on_artwork(None)
        else:
            markup = "%s\n" % GLib.markup_escape_text(
                App().player.current_track.name)
            artist_name = GLib.markup_escape_text(
                ", ".join(App().player.current_track.artists))
            markup += "<span size='x-small' alpha='40000'>%s</span>" %\
                artist_name
            self.__title_label.set_markup(markup)
            self.__set_artwork()

    def __set_artwork(self):
        """
            Set artwork
        """
        if not App().animations:
            return
        if App().player.current_track.id is None:
            self._artwork.get_style_context().add_class(
                "default-banner")
        else:
            self._artwork.get_style_context().remove_class(
                "default-banner")
            App().art_helper.set_album_artwork(
                    App().player.current_track.album,
                    # +100 to prevent resize lag
                    self.width + 100,
                    self.height,
                    self._artwork.get_scale_factor(),
                    ArtBehaviour.BLUR_HARD |
                    ArtBehaviour.DARKER,
                    self._on_artwork)

    def __set_internal_size(self):
        """
            Set text height
        """
        title_context = self.__title_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        if App().window.folded:
            self.__title_label.get_style_context().add_class(
                "text-large")
        else:
            self.__title_label.get_style_context().add_class(
                "text-x-large")

    def __on_lyrics_button_toggled(self, button):
        """
            Emit signals
            @param button as Gtk.ToggleButton
        """
        emit_signal(self, "translate", button.get_active())
