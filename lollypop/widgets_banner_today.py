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

from gi.repository import Gtk, GLib, Pango

from pickle import load, dump
from gettext import gettext as _

from lollypop.define import App, ArtSize, MARGIN, ViewType, StorageType
from lollypop.define import ArtBehaviour, LOLLYPOP_DATA_PATH
from lollypop.widgets_banner import BannerWidget
from lollypop.widgets_cover import BrowsableCoverWidget
from lollypop.objects_album import Album
from lollypop.logger import Logger
from lollypop.utils import get_default_storage_type, popup_widget
from lollypop.helper_signals import SignalsHelper, signals_map


class TodayBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for today album
    """

    def get_today_album():
        """
            Get today album
            @return Album/None
        """
        current_date = GLib.DateTime.new_now_local().get_day_of_year()
        (date, album_id) = (0, None)
        try:
            (date, album_id) = load(
                open(LOLLYPOP_DATA_PATH + "/today.bin", "rb"))
            if App().albums.get_storage_type(album_id) == StorageType.NONE:
                date = 0
        except Exception as e:
            Logger.warning("TodayBannerWidget::__get_today_album(): %s", e)
        try:
            if date != current_date:
                storage_type = get_default_storage_type()
                album_id = App().albums.get_randoms(
                    storage_type, None, False, 1)[0]
                dump((current_date, album_id),
                     open(LOLLYPOP_DATA_PATH + "/today.bin", "wb"))
            return Album(album_id)
        except Exception as e:
            Logger.error("TodayBannerWidget::__get_today_album(): %s", e)
        return None

    @signals_map
    def __init__(self, album, view_type):
        """
            Init cover widget
            @param album
            @param view_type as ViewType
        """
        BannerWidget.__init__(self, view_type | ViewType.OVERLAY)
        self.__album = album
        album_name = GLib.markup_escape_text(self.__album.name)
        self.__title_label = Gtk.Label.new()
        self.__title_label.show()
        markup = _("<b>Album of the day</b>\n")
        markup += "<span size='small' alpha='40000'>%s</span>\n" % album_name
        artist_name = GLib.markup_escape_text(", ".join(self.__album.artists))
        markup += "<span size='x-small' alpha='40000'>%s</span>" % artist_name
        self.__title_label.set_markup(markup)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.set_xalign(0.0)
        self.__title_label.set_vexpand(True)
        self.__title_label.set_margin_start(MARGIN)
        self.__cover_widget = BrowsableCoverWidget(self.__album, view_type)
        self.__cover_widget.show()
        play_button = Gtk.Button.new()
        play_button.show()
        play_button.set_property("valign", Gtk.Align.CENTER)
        image = Gtk.Image.new()
        image.show()
        play_button.set_image(image)
        play_button.connect("clicked", self.__on_play_button_clicked)
        play_button.get_style_context().add_class("banner-button")
        play_button.set_property("halign", Gtk.Align.END)
        play_button.set_hexpand(True)
        play_button.get_image().set_from_icon_name(
            "media-playback-start-symbolic", Gtk.IconSize.BUTTON)
        menu_button = Gtk.Button.new_from_icon_name(
            "view-more-symbolic", Gtk.IconSize.BUTTON)
        menu_button.show()
        menu_button.set_property("valign", Gtk.Align.CENTER)
        menu_button.get_style_context().add_class("banner-button")
        menu_button.set_property("halign", Gtk.Align.END)
        menu_button.connect("clicked", self.__on_menu_button_clicked)
        grid = Gtk.Grid()
        grid.show()
        grid.set_margin_start(MARGIN)
        grid.set_margin_end(MARGIN)
        grid.add(self.__cover_widget)
        grid.add(self.__title_label)
        box = Gtk.Box()
        box.show()
        box.get_style_context().add_class("linked")
        box.add(play_button)
        box.add(menu_button)
        grid.add(box)
        self._overlay.add_overlay(grid)
        self._overlay.set_overlay_pass_through(grid, True)
        self.__set_internal_size()
        return [
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
        if album_id == self.__album.id:
            self.__set_artwork()

#######################
# PRIVATE             #
#######################
    def __set_artwork(self):
        """
            Set artwork on banner
        """
        if App().animations:
            App().art_helper.set_album_artwork(
                    self.__album,
                    # +100 to prevent resize lag
                    self.width + 100,
                    self.height,
                    self._artwork.get_scale_factor(),
                    ArtBehaviour.BLUR_HARD |
                    ArtBehaviour.DARKER,
                    self._on_artwork)

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
        self.__cover_widget.set_art_size(art_size)

    def __on_play_button_clicked(self, button):
        """
            Play album
            @param button as Gtk.Button
        """
        App().player.play_album(self.__album)

    def __on_menu_button_clicked(self, button):
        """
            Show suggestions menu
            @param button as Gtk.Button
        """
        from lollypop.menu_suggestions import SuggestionsMenu
        from lollypop.widgets_menu import MenuBuilder
        menu = SuggestionsMenu(App().window.folded)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button, None, None, button)
