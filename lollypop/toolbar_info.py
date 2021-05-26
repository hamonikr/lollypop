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


from lollypop.utils import set_cursor_type, popup_widget
from lollypop.widgets_player_artwork import ArtworkPlayerWidget
from lollypop.widgets_player_label import LabelPlayerWidget
from lollypop.define import App, ArtBehaviour, StorageType, MARGIN_SMALL
from lollypop.define import ViewType
from lollypop.helper_gestures import GesturesHelper


class ToolbarInfo(Gtk.Bin, ArtworkPlayerWidget, GesturesHelper):
    """
        Informations toolbar
    """

    def __init__(self):
        """
            Init toolbar
        """
        Gtk.Bin.__init__(self)
        self.__width = 0
        horizontal_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 15)
        horizontal_box.show()
        self.__eventbox = Gtk.EventBox.new()
        self.__eventbox.add(horizontal_box)
        self.__eventbox.set_property("halign", Gtk.Align.START)
        self.__eventbox.show()
        self.__eventbox.connect("realize", set_cursor_type)
        self.add(self.__eventbox)
        GesturesHelper.__init__(self, self.__eventbox)
        self.special_headerbar_hack()

        self.__label = LabelPlayerWidget()
        self.__artwork = ArtworkPlayerWidget(ArtBehaviour.CROP_SQUARE |
                                             ArtBehaviour.CACHE)
        self.__artwork.set_property("has-tooltip", True)
        self.__artwork.set_margin_top(1)
        horizontal_box.pack_start(self.__artwork, False, False, 0)
        horizontal_box.pack_start(self.__label, False, False, 0)
        self.set_margin_start(MARGIN_SMALL)
        self.connect("realize", self.__on_realize)

    def show_children(self):
        """
            Show labels and artwork
        """
        self.__artwork.show()
        self.__label.show()

    def hide_children(self):
        """
            Hide labels and artwork, ignore self
        """
        self.__artwork.hide()
        self.__label.hide()

    def do_get_preferred_width(self):
        """
            We force preferred width
            @return (int, int)
        """
        return (self.__width, self.__width)

    def get_preferred_height(self):
        """
            Return preferred height
            @return (int, int)
        """
        return self.__labels.get_preferred_height()

    def set_width(self, width):
        """
            Set widget width
            @param width as int
        """
        self.__width = width
        self.set_property("width-request", width)

#######################
# PROTECTED           #
#######################
    def _on_primary_long_press_gesture(self, x, y):
        """
            Show menu
            @param x as int
            @param y as int
        """
        if App().window.folded or not self.__artwork.get_visible():
            return
        if App().player.current_track.id is not None:
            self.__popup_menu()

    def _on_primary_press_gesture(self, x, y, event):
        """
            Show information popover
            @param x as int
            @param y as int
            @param evnet as Gdk.Event
        """
        if App().window.folded or not self.__artwork.get_visible():
            return
        if App().player.current_track.id is not None:
            from lollypop.pop_information import InformationPopover
            popover = InformationPopover()
            popover.populate()
        popover.set_relative_to(self.__eventbox)
        popover.popup()

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show menu
            @param x as int
            @param y as int
        """
        self._on_primary_long_press_gesture(x, y)

#######################
# PRIVATE             #
#######################
    def __popup_menu(self):
        """
            Show contextual menu
        """
        if App().window.folded or not self.__artwork.get_visible():
            return
        track = App().player.current_track
        if track.id >= 0:
            from lollypop.menu_objects import TrackMenu, TrackMenuExt
            from lollypop.widgets_menu import MenuBuilder
            menu = TrackMenu(track, ViewType.TOOLBAR)
            menu_widget = MenuBuilder(menu)
            menu_widget.show()
            if not track.storage_type & StorageType.EPHEMERAL:
                menu_ext = TrackMenuExt(track)
                menu_ext.show()
                menu_widget.add_widget(menu_ext)
            self.set_state_flags(Gtk.StateFlags.FOCUSED, False)
            popup_widget(menu_widget, self.__eventbox, None, None, None)

    def __on_query_tooltip(self, widget, x, y, keyboard, tooltip):
        """
            Show tooltip if needed
            @param widget as Gtk.Widget
            @param x as int
            @param y as int
            @param keyboard as bool
            @param tooltip as Gtk.Tooltip
        """
        layout_title = self._title_label.get_layout()
        layout_artist = self._artist_label.get_layout()
        if layout_title.is_ellipsized() or layout_artist.is_ellipsized():
            artist = GLib.markup_escape_text(self._artist_label.get_text())
            title = GLib.markup_escape_text(self._title_label.get_text())
            tooltip.set_markup("<b>%s</b> - %s" % (artist, title))
        else:
            return False
        return True

    def __on_realize(self, toolbar):
        """
            Calculate art size
            @param toolbar as ToolbarInfos
        """
        art_size = self.get_allocated_height() - 1
        self.__artwork.set_art_size(art_size, art_size)
