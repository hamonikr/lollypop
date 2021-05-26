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

from gi.repository import Gtk, GLib

from lollypop.define import App, ArtSize, ViewType
from lollypop.widgets_banner import BannerWidget
from lollypop.utils import popup_widget


class SearchBannerWidget(BannerWidget):
    """
        Banner for search
    """

    def __init__(self):
        """
            Init banner
        """
        BannerWidget.__init__(self, ViewType.OVERLAY)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/SearchBannerWidget.ui")
        self.__menu = builder.get_object("menu")
        self.__spinner = builder.get_object("spinner")
        self.__entry = builder.get_object("entry")
        widget = builder.get_object("widget")
        self._overlay.add_overlay(widget)
        self._overlay.set_overlay_pass_through(widget, True)
        self.connect("map", self.__on_map)
        builder.connect_signals(self)

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        BannerWidget.update_for_width(self, width)
        self.__entry.set_size_request(self.width / 3, -1)

    @property
    def spinner(self):
        """
            Get banner spinner
            @return Gtk.Spinner
        """
        return self.__spinner

    @property
    def entry(self):
        """
            Get banner entry
            @return Gtk.Entry
        """
        return self.__entry

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
            Update entry width
            @param allocation as Gtk.Allocation
        """
        if BannerWidget._handle_width_allocate(self, allocation):
            self.__entry.set_size_request(self.width / 3, -1)

    def _on_menu_button_clicked(self, button):
        """
            Show playlist menu
            @param button as Gtk.Button
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_search import SearchMenu
        menu = SearchMenu(App().window.folded)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button, None, None, button)

#######################
# PRIVATE             #
#######################
    def __on_map(self, widget):
        """
            Grab focus
            @param widget as Gtk.Widget
        """
        GLib.idle_add(self.__entry.grab_focus)
