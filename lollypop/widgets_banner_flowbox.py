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

from lollypop.define import ArtSize, ViewType, MARGIN, Size
from lollypop.widgets_banner import BannerWidget
from lollypop.utils import emit_signal, get_title_for_genres_artists


class FlowboxBannerWidget(BannerWidget):
    """
        Banner for flowbox
    """

    __gsignals__ = {
        "play-all": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        "show-menu": (GObject.SignalFlags.RUN_FIRST, None,
                      (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self, genre_ids, artist_ids, view_type, show_menu=False):
        """
            Init banner
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param view_type as ViewType
            @param show_menu as bool
        """
        BannerWidget.__init__(self, view_type | ViewType.OVERLAY)
        grid = Gtk.Grid.new()
        grid.show()
        grid.set_property("valign", Gtk.Align.CENTER)
        self.__title_label = Gtk.Label.new()
        self.__title_label.show()
        self.__title_label.set_margin_start(MARGIN)
        self.__title_label.set_hexpand(True)
        self.__title_label.set_property("halign", Gtk.Align.START)
        linked = Gtk.Grid.new()
        linked.show()
        linked.get_style_context().add_class("linked")
        linked.set_margin_end(MARGIN)
        linked.set_property("halign", Gtk.Align.END)
        self.__play_button = Gtk.Button.new_from_icon_name(
            "media-playback-start-symbolic", Gtk.IconSize.BUTTON)
        self.__play_button.show()
        self.__play_button.get_style_context().add_class("banner-button")
        self.__play_button.connect("clicked", self.__on_play_button_clicked)
        self.__shuffle_button = Gtk.Button.new_from_icon_name(
            "media-playlist-shuffle-symbolic", Gtk.IconSize.BUTTON)
        self.__shuffle_button.show()
        self.__shuffle_button.get_style_context().add_class("banner-button")
        self.__shuffle_button.connect("clicked",
                                      self.__on_shuffle_button_clicked)
        linked.add(self.__play_button)
        linked.add(self.__shuffle_button)
        if show_menu:
            self.__menu_button = Gtk.Button.new_from_icon_name(
                "view-more-symbolic", Gtk.IconSize.BUTTON)
            self.__menu_button.show()
            self.__menu_button.get_style_context().add_class("banner-button")
            self.__menu_button.connect("clicked",
                                       self.__on_menu_button_clicked)
            linked.add(self.__menu_button)
        grid.add(self.__title_label)
        grid.add(linked)
        self._overlay.add_overlay(grid)
        self._overlay.set_overlay_pass_through(grid, True)
        title_str = get_title_for_genres_artists(genre_ids, artist_ids)
        self.__title_label.set_markup("<b>%s</b>" %
                                      GLib.markup_escape_text(title_str))

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        BannerWidget.update_for_width(self, width)
        self.__set_internal_size()

    @property
    def height(self):
        """
            Get wanted height
            @return int
        """
        return ArtSize.SMALL

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            Update artwork
            @param allocation as Gtk.Allocation
        """
        if BannerWidget._handle_width_allocate(self, allocation):
            self.__set_internal_size()

#######################
# PRIVATE             #
#######################
    def __set_internal_size(self):
        """
            Set content size based on current width
        """
        title_context = self.__title_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        if self.width <= Size.MEDIUM:
            self.__title_label.get_style_context().add_class(
                "text-large")
        else:
            self.__title_label.get_style_context().add_class(
                "text-x-large")

    def __on_play_button_clicked(self, button):
        """
            Play playlist
            @param button as Gtk.Button
        """
        emit_signal(self, "play-all", False)

    def __on_shuffle_button_clicked(self, button):
        """
            Play playlist shuffled
            @param button as Gtk.Button
        """
        emit_signal(self, "play-all", True)

    def __on_menu_button_clicked(self, button):
        """
            Show sync menu
            @param button as Gtk.Button
        """
        self.emit("show-menu", button)
