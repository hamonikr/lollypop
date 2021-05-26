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

from gi.repository import Gtk, Pango

from gettext import gettext as _

from lollypop.define import App, ArtSize, MARGIN, ViewType
from lollypop.define import SelectionListMask
from lollypop.utils import popup_widget
from lollypop.widgets_banner import BannerWidget
from lollypop.helper_signals import SignalsHelper, signals_map


class PlaylistsBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for playlists
    """

    @signals_map
    def __init__(self, view):
        """
            Init banner
            @param view as PlaylistView
        """
        BannerWidget.__init__(self, view.args["view_type"] | ViewType.OVERLAY)
        self.__view = view
        grid = Gtk.Grid()
        grid.set_property("valign", Gtk.Align.CENTER)
        grid.get_style_context().add_class("linked")
        grid.show()
        self.__title_label = Gtk.Label.new(
            "<b>" + _("Playlists") + "</b>")
        self.__title_label.show()
        self.__title_label.set_use_markup(True)
        self.__title_label.set_hexpand(True)
        self.__title_label.get_style_context().add_class("dim-label")
        self.__title_label.set_property("halign", Gtk.Align.START)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__new_button = Gtk.Button.new_from_icon_name(
            "document-new-symbolic", Gtk.IconSize.BUTTON)
        self.__new_button.connect("clicked", self.__on_new_button_clicked)
        self.__new_button.set_property("halign", Gtk.Align.CENTER)
        self.__new_button.get_style_context().add_class("banner-button")
        self.__new_button.show()
        self.__menu_button = Gtk.Button.new_from_icon_name(
            "view-more-symbolic", Gtk.IconSize.BUTTON)
        self.__menu_button.show()
        self.__menu_button.get_style_context().add_class("banner-button")
        self.__menu_button.set_property("halign", Gtk.Align.END)
        self.__menu_button.connect("clicked", self.__on_menu_button_clicked)
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        box.show()
        box.get_style_context().add_class("linked")
        box.add(self.__new_button)
        box.add(self.__menu_button)
        grid.add(self.__title_label)
        grid.add(box)
        grid.set_margin_start(MARGIN)
        grid.set_margin_end(MARGIN)
        self._overlay.add_overlay(grid)
        self._overlay.set_overlay_pass_through(grid, True)
        self.__set_internal_size()
        return [
            (App().window.container.widget, "notify::folded",
             "_on_container_folded"),
        ]

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
    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        self.__set_internal_size()

#######################
# PRIVATE             #
#######################
    def __set_internal_size(self):
        """
            Update font size
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

    def __on_new_button_clicked(self, button):
        """
            Add a new playlist
            @param button as Gtk.Button
        """
        App().playlists.add(App().playlists.get_new_name())

    def __on_menu_button_clicked(self, button):
        """
            Show playlist menu
            @param button as Gtk.Button
        """
        from lollypop.menu_selectionlist import SelectionListMenu
        from lollypop.widgets_menu import MenuBuilder
        menu = SelectionListMenu(self.__view,
                                 SelectionListMask.PLAYLISTS,
                                 App().window.folded)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button, None, None, button)
