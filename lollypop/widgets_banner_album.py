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

from gi.repository import Gtk, Pango, GLib

from gettext import gettext as _

from lollypop.define import App, ArtSize, Type, ViewType
from lollypop.define import ArtBehaviour, MARGIN_MEDIUM, MARGIN, MARGIN_SMALL
from lollypop.widgets_rating import RatingWidget
from lollypop.widgets_loved import LovedWidget
from lollypop.widgets_label import LabelWidget
from lollypop.widgets_cover import EditCoverWidget, CoverWidget
from lollypop.widgets_banner import BannerWidget
from lollypop.utils import get_human_duration, on_query_tooltip
from lollypop.utils import popup_widget, emit_signal
from lollypop.helper_signals import SignalsHelper, signals_map


class AlbumBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for album
    """

    @signals_map
    def __init__(self, album, storage_type, view_type):
        """
            Init cover widget
            @param album
            @param storage_type as int
            @param view_type as ViewType
        """
        BannerWidget.__init__(self, view_type)
        self.__album = album
        self.__storage_type = storage_type
        self.__widget = None
        return [
                (App().window.container.widget, "notify::folded",
                 "_on_container_folded"),
                (App().album_art, "album-artwork-changed",
                 "_on_album_artwork_changed"),
                (App().player, "playback-added", "_on_playback_changed"),
                (App().player, "playback-updated", "_on_playback_changed"),
                (App().player, "playback-setted", "_on_playback_changed"),
                (App().player, "playback-removed", "_on_playback_changed")
        ]

    def populate(self):
        """
            Populate the view
        """
        if self.__widget is not None:
            return
        self.__widget = Gtk.Grid.new()
        self.__widget.set_margin_start(MARGIN)
        self.__widget.set_margin_end(MARGIN)
        self.__widget.set_margin_top(MARGIN_SMALL)
        self.__widget.set_margin_bottom(MARGIN_SMALL)
        self.__widget.set_row_spacing(MARGIN_SMALL)
        self.__widget.set_column_spacing(MARGIN_MEDIUM)
        self.__top_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.__middle_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.__bottom_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.__labels_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.__top_box.set_vexpand(True)
        self.__middle_box.set_halign(Gtk.Align.END)
        self.__middle_box.set_valign(Gtk.Align.CENTER)
        self.__middle_box.set_hexpand(True)
        self.__bottom_box.set_vexpand(True)
        self.__year_label = LabelWidget()
        self.__year_label.connect("clicked", self.__on_year_clicked)
        self.__year_label.set_justify(Gtk.Justification.RIGHT)
        self.__year_label.get_style_context().add_class("dim-label")
        self.__year_label.set_halign(Gtk.Align.END)
        self.__year_label.set_hexpand(True)
        self.__play_button = Gtk.Button.new_from_icon_name(
            "media-playback-start-symbolic", Gtk.IconSize.BUTTON)
        self.__add_button = Gtk.Button.new_from_icon_name(
            "list-add-symbolic", Gtk.IconSize.BUTTON)
        self.__menu_button = Gtk.Button.new_from_icon_name(
            "view-more-symbolic", Gtk.IconSize.BUTTON)
        self.__play_button.connect("clicked", self.__on_play_button_clicked)
        self.__add_button.connect("clicked", self.__on_add_button_clicked)
        self.__menu_button.connect("clicked", self.__on_menu_button_clicked)
        self.__title_label = Gtk.Label.new()
        self.__title_label.set_valign(Gtk.Align.END)
        self.__title_label.set_vexpand(True)
        self.__title_label.connect("query-tooltip", on_query_tooltip)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.set_halign(Gtk.Align.START)
        self.__title_label.set_xalign(0)
        self.__artist_label = LabelWidget()
        self.__artist_label.show()
        self.__artist_label.connect("clicked", self.__on_artist_clicked)
        self.__artist_label.set_valign(Gtk.Align.START)
        self.__artist_label.set_halign(Gtk.Align.START)
        self.__artist_label.connect("query-tooltip", on_query_tooltip)
        self.__artist_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__artist_label.set_xalign(0)
        self.__duration_label = Gtk.Label.new()
        self.__duration_label.get_style_context().add_class("dim-label")
        self.__top_box.pack_end(self.__year_label, False, True, 0)
        self.__middle_box.add(self.__play_button)
        self.__middle_box.add(self.__add_button)
        self.__middle_box.add(self.__menu_button)
        self.__middle_box.get_style_context().add_class("linked")
        self.__bottom_box.pack_end(self.__duration_label, False, True, 0)
        self.__labels_box.add(self.__title_label)
        self.__labels_box.add(self.__artist_label)
        self.__widget.attach(self.__top_box, 2, 0, 1, 1)
        self.__set_album_year(True)
        self.__widget.attach(self.__middle_box, 2, 1, 1, 1)
        self.__widget.attach(self.__bottom_box, 1, 2, 2, 1)
        self.__widget.attach(self.__labels_box, 1, 0, 1, 2)
        self.__widget.show_all()
        if self.view_type & ViewType.OVERLAY:
            style = "banner-button"
        else:
            style = "menu-button"
        self.__play_button.get_style_context().add_class(style)
        self.__add_button.get_style_context().add_class(style)
        self.__menu_button.get_style_context().add_class(style)
        self.__title_label.set_label(self.__album.name)
        if self.view_type & ViewType.ALBUM:
            self.__cover_widget = EditCoverWidget(self.__album, self.view_type)
            self.__artist_label.get_style_context().add_class("dim-label")
            self.__artist_label.set_label(", ".join(self.__album.artists))
        else:
            self.__artist_label.hide()
            self.__cover_widget = CoverWidget(self.__album, self.view_type)
            self.__cover_widget.set_margin_top(MARGIN_MEDIUM)
            self.__cover_widget.set_margin_bottom(MARGIN_MEDIUM)
            self.__cover_widget.connect("populated",
                                        self.__on_cover_populated)
        self.__cover_widget.show()
        human_duration = get_human_duration(self.__album.duration)
        self.__duration_label.set_text(human_duration)
        self.__widget.attach(self.__cover_widget, 0, 0, 1, 3)
        self.__loved_widget = LovedWidget(self.__album, Gtk.IconSize.INVALID)
        self.__loved_widget.show()
        self.__bottom_box.pack_start(self.__loved_widget, 0, False, False)
        self.__rating_widget = RatingWidget(self.__album, Gtk.IconSize.INVALID)
        self.__rating_widget.show()
        self.__bottom_box.pack_start(self.__rating_widget, 0, True, True)
        if self.view_type & ViewType.OVERLAY:
            self._overlay.add_overlay(self.__widget)
            self._overlay.set_overlay_pass_through(self.__widget, True)
        else:
            self.add(self.__widget)
        self.__update_add_button()
        self.__set_internal_size()

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        BannerWidget.update_for_width(self, width)
        self.__set_artwork()

    def set_selected(self, selected):
        """
            Mark widget as selected
            @param selected as bool
        """
        buttons = [self.__play_button, self.__add_button, self.__menu_button]
        for button in buttons:
            if selected:
                button.set_state_flags(Gtk.StateFlags.SELECTED, True)
            else:
                button.set_state_flags(Gtk.StateFlags.NORMAL, True)

    def update_duration(self):
        """
            Update duration label
        """
        human_duration = get_human_duration(self.__album.duration)
        self.__duration_label.set_text(human_duration)

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

    def __set_album_year(self, full):
        """
            Set album year
            @param full as int
        """
        if self.__album.year is not None:
            album_year = GLib.markup_escape_text(
                "%s" % self.__album.year)
            markup = None
            if full and self.__album.original_year is not None:
                original_year = GLib.markup_escape_text(
                    "%s" % self.__album.original_year)
                if original_year != album_year:
                    original_str = _("Released on %s") % original_year
                    markup = \
                        "%s\n<span size='x-small' alpha='40000'>%s</span>" %\
                        (album_year, original_str)
            if markup is None:
                markup = album_year
            self.__year_label.set_markup(markup)
            self.__year_label.show()

    def __set_artwork(self):
        """
            Set artwork on banner
        """
        if self._artwork is not None and\
                self.view_type & ViewType.ALBUM and\
                App().animations:
            App().art_helper.set_album_artwork(
                            self.__album,
                            # +100 to prevent resize lag
                            self.width + 100,
                            self.height,
                            self._artwork.get_scale_factor(),
                            ArtBehaviour.BLUR_HARD |
                            ArtBehaviour.DARKER,
                            self._on_artwork)
        if self.width < ArtSize.BANNER * 3:
            if self.__widget.get_child_at(2, 0) == self.__top_box:
                self.__widget.remove(self.__labels_box)
                self.__widget.remove(self.__top_box)
                self.__widget.attach(self.__top_box, 1, 1, 1, 1)
                self.__widget.attach(self.__labels_box, 1, 0, 2, 1)
                self.__set_album_year(False)
        elif self.__widget.get_child_at(1, 0) == self.__labels_box:
            self.__widget.remove(self.__labels_box)
            self.__widget.remove(self.__top_box)
            self.__widget.attach(self.__top_box, 2, 0, 1, 1)
            self.__widget.attach(self.__labels_box, 1, 0, 1, 2)
            self.__set_album_year(True)

    def __update_add_button(self):
        """
            Set image as +/-
        """
        albums = App().player.get_albums_for_id(self.__album.id)
        missing = False if albums else True
        for album in albums:
            for track in self.__album.tracks:
                if track.id not in album.track_ids:
                    missing = True
                    break
        if missing:
            self.__add_button.get_image().set_from_icon_name(
                "list-add-symbolic", Gtk.IconSize.BUTTON)
        else:
            self.__add_button.get_image().set_from_icon_name(
                "list-remove-symbolic", Gtk.IconSize.BUTTON)

    def __set_internal_size(self):
        """
            Set content size based on available width
        """
        classes = ["text-medium", "text-large", "text-x-large"]
        # Text size
        for label in [self.__title_label,
                      self.__artist_label,
                      self.__year_label,
                      self.__duration_label]:
            context = label.get_style_context()
            for c in classes:
                context.remove_class(c)

        if App().window.folded:
            art_size = ArtSize.MEDIUM
            icon_size = Gtk.IconSize.BUTTON
            cls_title = "text-medium"
            cls_others = "text-medium"
        elif not self.view_type & ViewType.OVERLAY:
            art_size = ArtSize.BANNER
            icon_size = Gtk.IconSize.LARGE_TOOLBAR
            cls_title = "text-large"
            cls_others = "text-large"
        else:
            art_size = ArtSize.BANNER
            icon_size = Gtk.IconSize.LARGE_TOOLBAR
            cls_title = "text-x-large"
            cls_others = "text-large"
        self.__title_label.get_style_context().add_class(cls_title)
        self.__artist_label.get_style_context().add_class(cls_title)
        self.__year_label.get_style_context().add_class(cls_others)
        self.__duration_label.get_style_context().add_class(cls_others)

        self.__rating_widget.set_icon_size(icon_size)
        self.__loved_widget.set_icon_size(icon_size)
        self.__cover_widget.set_art_size(art_size)

    def __on_cover_populated(self, widget):
        """
            Pass signal
            @param widget as Gtk.Widget
        """
        emit_signal(self, "populated")

    def __on_menu_button_clicked(self, button):
        """
            Show album menu
            @param button as Gtk.Button
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_objects import AlbumMenu
        from lollypop.menu_artwork import AlbumArtworkMenu
        menu = AlbumMenu(self.__album,
                         self.__storage_type,
                         self.view_type)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        if App().window.folded:
            menu_ext = AlbumArtworkMenu(self.__album, self.view_type, True)
            menu_ext.connect("hidden", self.__close_artwork_menu)
            menu_ext.show()
            menu_widget.add_widget(menu_ext, -2)
        popup_widget(menu_widget, button, None, None, button)

    def __on_play_button_clicked(self, button):
        """
            Play album
           @param button as Gtk.Button
        """
        selected = button.get_state_flags() & Gtk.StateFlags.SELECTED
        App().player.play_album(self.__album.clone(selected))

    def __on_add_button_clicked(self, button):
        """
            Add/Remove album
           @param button as Gtk.Button
        """
        selected = button.get_state_flags() & Gtk.StateFlags.SELECTED
        add = self.__add_button.get_image().get_icon_name()[0] ==\
            "list-add-symbolic"
        albums = App().player.get_albums_for_id(self.__album.id)
        if albums:
            if add:
                for track in self.__album.tracks:
                    albums[0].append_track(track)
                emit_signal(App().player, "playback-updated", albums[0])
            else:
                for album in albums:
                    for track in self.__album.tracks:
                        album.remove_track(track)
                        if album.id is None:
                            App().player.remove_album(album)
                            break
                emit_signal(App().player, "playback-updated", album)
        else:
            App().player.add_album(self.__album.clone(selected))

    def __on_year_clicked(self, label):
        """
            Show year view
            @param label as LabelWidget
        """
        App().window.container.show_view([Type.YEARS], [self.__album.year])

    def __on_artist_clicked(self, label):
        """
            Show artist view
            @param label as LabelWidget
        """
        App().window.container.show_view([Type.ARTISTS],
                                         self.__album.artist_ids)
