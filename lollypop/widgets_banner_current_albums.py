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

from lollypop.define import App, ArtSize, ViewType, Size
from lollypop.define import MARGIN
from lollypop.widgets_banner import BannerWidget
from lollypop.utils import emit_signal, popup_widget, get_human_duration
from lollypop.helper_signals import SignalsHelper, signals_map


class CurrentAlbumsBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for current albums
    """

    @signals_map
    def __init__(self, view):
        """
            Init banner
            @param view as AlbumsListView
        """
        BannerWidget.__init__(self, view.view_type | ViewType.OVERLAY)
        self.__duration_task = False
        self.__view = view
        self.__clear_button = Gtk.Button.new_from_icon_name(
            "edit-clear-all-symbolic",
            Gtk.IconSize.BUTTON)
        self.__clear_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__clear_button.set_tooltip_text(_("Clear albums"))
        self.__clear_button.set_sensitive(App().player.albums)
        self.__clear_button.connect("clicked", self.__on_clear_button_clicked)
        self.__clear_button.get_style_context().add_class("banner-button")
        self.__clear_button.show()
        self.__menu_button = Gtk.Button.new_from_icon_name(
            "view-more-symbolic",
            Gtk.IconSize.BUTTON)
        self.__menu_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__menu_button.set_sensitive(App().player.albums)
        self.__menu_button.connect("clicked", self.__on_menu_button_clicked)
        self.__menu_button.get_style_context().add_class("banner-button")
        self.__menu_button.show()
        self.__jump_button = Gtk.Button.new_from_icon_name(
            "go-jump-symbolic",
            Gtk.IconSize.BUTTON)
        self.__jump_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__jump_button.connect("clicked", self.__on_jump_button_clicked)
        self.__jump_button.set_tooltip_text(_("Go to current track"))
        self.__jump_button.set_sensitive(App().player.albums)
        self.__jump_button.get_style_context().add_class("banner-button")
        self.__jump_button.show()
        self.__title_label = Gtk.Label.new(
            "<b>" + _("Playing albums") + "</b>")
        self.__title_label.show()
        self.__title_label.set_use_markup(True)
        self.__title_label.set_hexpand(True)
        self.__title_label.get_style_context().add_class("dim-label")
        self.__title_label.set_property("halign", Gtk.Align.START)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__duration_label = Gtk.Label.new()
        self.__duration_label.show()
        self.__duration_label.set_property("halign", Gtk.Align.END)
        grid = Gtk.Grid()
        grid.show()
        grid.set_column_spacing(MARGIN)
        grid.set_property("valign", Gtk.Align.CENTER)
        grid.set_margin_start(MARGIN)
        grid.set_margin_end(MARGIN)
        grid.add(self.__title_label)
        grid.add(self.__duration_label)
        buttons = Gtk.Grid()
        buttons.show()
        buttons.get_style_context().add_class("linked")
        buttons.set_property("valign", Gtk.Align.CENTER)
        buttons.add(self.__jump_button)
        buttons.add(self.__clear_button)
        buttons.add(self.__menu_button)
        grid.add(buttons)
        self._overlay.add_overlay(grid)
        self._overlay.set_overlay_pass_through(grid, True)
        self.connect("destroy", self.__on_destroy)
        return [
            (view, "initialized", "_on_view_updated"),
            (App().player, "playback-added", "_on_playback_changed"),
            (App().player, "playback-updated", "_on_playback_changed"),
            (App().player, "playback-setted", "_on_playback_changed"),
            (App().player, "playback-removed", "_on_playback_changed"),
        ]

    def update_for_width(self, width):
        """
            Update banner internals for width, call this before showing banner
            @param width as int
        """
        BannerWidget.update_for_width(self, width)
        self.__set_internal_size()

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
    def clear_button(self):
        """
            Get clear button
            @return Gtk.Button
        """
        return self.__clear_button

    @property
    def menu_button(self):
        """
            Get menu button
            @return Gtk.Button
        """
        return self.__menu_button

    @property
    def jump_button(self):
        """
            Get jump button
            @return Gtk.Button
        """
        return self.__jump_button

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

    def _on_view_updated(self, view):
        """
            @param view as AlbumsListView
        """
        if self.__view.children:
            self.__duration_task = True
            App().task_helper.run(self.__calculate_duration)
        else:
            self.__duration_task = False
            self.__duration_label.set_text(get_human_duration(0))

    def _on_playback_changed(self, player, *ignore):
        """
            Update clear button state
            @param player as Player
        """
        sensitive = player.albums != []
        GLib.idle_add(self.__clear_button.set_sensitive, sensitive)
        GLib.idle_add(self.__clear_button.set_sensitive, sensitive)
        GLib.idle_add(self.__jump_button.set_sensitive, sensitive)
        GLib.idle_add(self.__menu_button.set_sensitive, sensitive)
        self.__duration_task = True
        App().task_helper.run(self.__calculate_duration)

#######################
# PRIVATE             #
#######################
    def __calculate_duration(self):
        """
            Calculate playback duration
        """
        GLib.idle_add(self.__duration_label.set_text, "")
        duration = 0
        for child in self.__view.children:
            if not self.__duration_task:
                return
            duration += child.album.duration
        self.__duration_task = False
        GLib.idle_add(self.__duration_label.set_text,
                      get_human_duration(duration))

    def __set_internal_size(self):
        """
            Update font size
        """
        duration_context = self.__duration_label.get_style_context()
        title_context = self.__title_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        for c in duration_context.list_classes():
            duration_context.remove_class(c)
        if self.width <= Size.MEDIUM:
            title_context.add_class("text-large")
        else:
            duration_context.add_class("text-large")
            title_context.add_class("text-x-large")

    def __on_jump_button_clicked(self, button):
        """
            Scroll to album
            @param button as Gtk.Button
        """
        self.__view.jump_to_current()

    def __on_menu_button_clicked(self, button):
        """
            Save to playlist
            @param button as Gtk.Button
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_current_albums import CurrentAlbumsMenu
        menu = CurrentAlbumsMenu(App().window.folded)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button, None, None, button)

    def __on_clear_button_clicked(self, button):
        """
            Clear albums
            @param button as Gtk.Button
        """
        self.__view.clear()
        self.__view.populate()
        emit_signal(App().player, "status-changed")

    def __on_destroy(self, widget):
        """
            Remove ref cycle
            @param widget as Gtk.Widget
        """
        self.__view = None
