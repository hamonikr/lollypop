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

from gi.repository import Gtk, Gio, GLib

from gettext import gettext as _
from random import choice

from lollypop.utils import set_cursor_type, on_query_tooltip, popup_widget
from lollypop.utils_artist import add_artist_to_playback, play_artists
from lollypop.define import App, ArtSize, ArtBehaviour, ViewType
from lollypop.widgets_banner import BannerWidget
from lollypop.helper_signals import SignalsHelper, signals_map


class ArtistBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for artist
    """

    @signals_map
    def __init__(self, genre_ids, artist_ids, storage_type, view_type):
        """
            Init artist banner
            @parma genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param view_type as ViewType (Unused)
        """
        BannerWidget.__init__(self, view_type | ViewType.OVERLAY)
        self.__genre_ids = genre_ids
        self.__artist_ids = artist_ids
        self.__storage_type = storage_type
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/ArtistBannerWidget.ui")
        builder.connect_signals(self)
        self.__badge_artwork = builder.get_object("badge_artwork")
        self.__labels = builder.get_object("label_event")
        self.__title_label = builder.get_object("artist")
        self.__title_label.connect("realize", set_cursor_type)
        self.__title_label.connect("query-tooltip", on_query_tooltip)
        self.__title_label.set_property("has-tooltip", True)
        self.__add_button = builder.get_object("add_button")
        self.__play_button = builder.get_object("play_button")
        self.__menu_button = builder.get_object("menu_button")
        if len(artist_ids) > 1:
            self.__menu_button.hide()
        builder.get_object("artwork_event").connect(
            "realize", set_cursor_type)
        self.__labels.connect("realize", set_cursor_type)
        self.__widget = builder.get_object("widget")
        artists = []
        for artist_id in self.__artist_ids:
            artists.append(App().artists.get_name(artist_id))
        self.__title_label.set_markup(GLib.markup_escape_text(
            ", ".join(artists)))
        self.__show_artwork = len(artist_ids) == 1
        self.__title_label.get_style_context().add_class("text-x-large")
        self._overlay.add_overlay(self.__widget)
        self._overlay.set_overlay_pass_through(self.__widget, True)
        self.__update_add_button()
        self.__set_internal_size()
        return [
               (App().window.container.widget, "notify::folded",
                "_on_container_folded"),
               (App().artist_art, "artist-artwork-changed",
                "_on_artist_artwork_changed"),
               (App().player, "playback-added", "_on_playback_changed"),
               (App().player, "playback-updated", "_on_playback_changed"),
               (App().player, "playback-setted", "_on_playback_changed"),
               (App().player, "playback-removed", "_on_playback_changed"),
               (App().settings, "changed::artist-artwork",
                "_on_artist_artwork_setting_changed")

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

    def _on_artist_artwork_setting_changed(self, settings, variant):
        """
            Update banner
            @param settings as Gio.Settings
            @param value as GLib.Variant
        """
        self.__set_artwork()

    def _on_label_button_release(self, eventbox, event):
        """
            Show artists information
            @param eventbox as Gtk.EventBox
            @param event as Gdk.Event
        """
        if len(self.__artist_ids) == 1:
            from lollypop.pop_information import InformationPopover
            self.__pop_info = InformationPopover(True)
            self.__pop_info.set_relative_to(eventbox)
            self.__pop_info.populate(self.__artist_ids[0])
            self.__pop_info.show()

    def _on_play_clicked(self, *ignore):
        """
            Play artist albums
        """
        play_artists(self.__artist_ids, self.__genre_ids)

    def _on_add_clicked(self, *ignore):
        """
            Add artist albums
        """
        icon_name = self.__add_button.get_image().get_icon_name()[0]
        add = icon_name == "list-add-symbolic"
        add_artist_to_playback(self.__artist_ids, self.__genre_ids, add)

    def _on_menu_button_clicked(self, button):
        """
            Show album menu
            @param button as Gtk.Button
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_artist import ArtistMenu
        from lollypop.menu_similars import SimilarsMenu
        from lollypop.menu_artwork import ArtistArtworkMenu
        menu = ArtistMenu(self.__artist_ids[0],
                          self.__storage_type,
                          self.view_type,
                          App().window.folded)
        menu_widget = MenuBuilder(menu, False)
        menu_widget.show()
        menu_ext = SimilarsMenu(self.__artist_ids[0])
        menu_ext.show()
        menu_widget.add_widget(menu_ext)
        if App().window.folded:
            menu_ext2 = ArtistArtworkMenu(self.__artist_ids[0],
                                          self.view_type,
                                          True)
            menu_ext2.connect("hidden", self.__close_artwork_menu)
            menu_ext2.show()
            menu_widget.add_widget(menu_ext2)
        popup_widget(menu_widget, button, None, None, button)

    def _on_badge_button_release(self, eventbox, event):
        """
            Show artist artwork manager
            @param eventbox as Gtk.EventBox
            @param event as Gdk.Event
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_artwork import ArtistArtworkMenu
        menu = Gio.Menu()
        if App().window.folded:
            from lollypop.menu_header import ArtistMenuHeader
            menu.append_item(ArtistMenuHeader(self.__artist_ids[0]))
        menu_widget = MenuBuilder(menu, False)
        menu_widget.show()
        menu_ext = ArtistArtworkMenu(self.__artist_ids[0],
                                     self.view_type,
                                     False)
        menu_ext.connect("hidden", self.__close_artwork_menu)
        menu_ext.show()
        menu_widget.add_widget(menu_ext)
        self.__artwork_popup = popup_widget(menu_widget,
                                            eventbox,
                                            None, None, None)

    def _on_artist_artwork_changed(self, art, prefix):
        """
            Update artwork if needed
            @param art as Art
            @param prefix as str
        """
        if len(self.__artist_ids) == 1:
            artist = App().artists.get_name(self.__artist_ids[0])
            if prefix == artist:
                self.__set_artwork()
                self.__set_internal_size()

    def _on_playback_changed(self, *ignore):
        """
            Update add button
        """
        self.__update_add_button()

#######################
# PRIVATE             #
#######################
    def __close_artwork_menu(self, action, variant):
        if App().window.folded:
            App().window.container.go_back()
        else:
            self.__artwork_popup.destroy()

    def __set_artwork(self):
        """
            Set artwork
        """
        if App().settings.get_value("artist-artwork") and App().animations:
            artist = App().artists.get_name(choice(self.__artist_ids))
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
            if self.__widget.get_child_at(1, 0) == self.__labels:
                self.__widget.remove(self.__labels)
                self.__widget.attach(self.__labels, 2, 2, 3, 1)
        elif self.__widget.get_child_at(2, 2) == self.__labels:
            self.__widget.remove(self.__labels)
            self.__widget.attach(self.__labels, 1, 0, 1, 3)

    def __set_badge_artwork(self, art_size):
        """
            Set artist artwork on badge
            @param art_size as int
        """
        if self.__show_artwork and\
                App().settings.get_value("artist-artwork"):
            artist = App().artists.get_name(self.__artist_ids[0])
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

    def __update_add_button(self):
        """
            Set image as +/-
        """
        album_ids = App().albums.get_ids(self.__genre_ids, self.__artist_ids,
                                         self.__storage_type, False)
        add = set(App().player.album_ids) & set(album_ids) != set(album_ids)
        if add:
            # Translators: artist context
            self.__add_button.set_tooltip_text(_("Add to current playlist"))
            self.__add_button.get_image().set_from_icon_name(
                "list-add-symbolic",
                Gtk.IconSize.BUTTON)
        else:
            # Translators: artist context
            self.__add_button.set_tooltip_text(
                _("Remove from current playlist"))
            self.__add_button.get_image().set_from_icon_name(
                "list-remove-symbolic",
                Gtk.IconSize.BUTTON)

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
