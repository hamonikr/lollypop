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

from gi.repository import GLib, Gtk

from gettext import gettext as _

from lollypop.define import App
from lollypop.helper_signals import SignalsHelper, signals


class PlayButton(Gtk.Button):
    """
        Gtk Button with a spinner
    """

    def __init__(self):
        """
            Init Button
        """
        Gtk.Button.__init__(self)
        self.__spinner = Gtk.Spinner.new()
        self.__spinner.show()
        self.__image = Gtk.Image.new_from_icon_name(
            "media-playback-start-symbolic", Gtk.IconSize.BUTTON)
        self.__image.show()
        self.set_image(self.__image)

    def set_loading(self, status):
        """
            Set button loading status
            @param status as bool
        """
        if status:
            self.set_image(self.__spinner)
            self.__spinner.start()
        else:
            self.set_image(self.__image)
            self.__spinner.stop()

    @property
    def image(self):
        """
            Get image
            @return Gtk.Image
        """
        return self.__image


class ButtonsPlayerWidget(Gtk.Box, SignalsHelper):
    """
        Box with playback buttons based on current player state
    """

    @signals
    def __init__(self, styles=[]):
        """
            Init box
            @param style as [str]
        """
        Gtk.Box.__init__(self)
        self.__prev_button_timeout_id = None
        self.__prev_button = Gtk.Button.new_from_icon_name(
            "media-skip-backward-symbolic", Gtk.IconSize.BUTTON)
        self.__prev_button.show()
        self.__prev_button.connect("clicked", self.__on_prev_button_clicked)
        self.__play_button = PlayButton()
        self.__play_button.show()
        self.__play_button.connect("clicked", self.__on_play_button_clicked)
        self.__next_button = Gtk.Button.new_from_icon_name(
            "media-skip-forward-symbolic", Gtk.IconSize.BUTTON)
        self.__next_button.show()
        self.__next_button.connect("clicked", self.__on_next_button_clicked)
        self.__play_button.set_sensitive(False)
        self.__prev_button.set_sensitive(False)
        self.__next_button.set_sensitive(False)
        self.get_style_context().add_class("linked")
        self.pack_start(self.__prev_button, True, True, 0)
        self.pack_start(self.__play_button, True, True, 0)
        self.pack_start(self.__next_button, True, True, 0)
        self.connect("destroy", self.__on_destroy)
        if styles:
            self.__set_styles(self.__prev_button, styles)
            self.__set_styles(self.__play_button, styles)
            self.__set_styles(self.__next_button, styles)
        else:
            self.__prev_button.set_size_request(42, -1)
            self.__play_button.set_size_request(60, -1)
            self.__next_button.set_size_request(42, -1)

        return [
            (App().player, "current-changed", "_on_current_changed"),
            (App().player, "status-changed", "_on_status_changed"),
            (App().player, "loading-changed", "_on_loading_changed"),
            (App().player, "next-changed", "_on_next_changed"),
            (App().player, "prev-changed", "_on_prev_changed")
        ]

    def update(self):
        """
            Update buttons
        """
        player = App().player
        self._on_current_changed(player)
        self._on_status_changed(player)

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update toolbar
            @param player as Player
        """
        def update_button():
            self.__prev_button_timeout_id = None
            self.__prev_button.get_image().set_from_icon_name(
                "media-seek-backward-symbolic", Gtk.IconSize.BUTTON)

        if self.__prev_button_timeout_id is not None:
            GLib.source_remove(self.__prev_button_timeout_id)
        self.__prev_button.get_image().set_from_icon_name(
            "media-skip-backward-symbolic", Gtk.IconSize.BUTTON)
        self.__prev_button_timeout_id = GLib.timeout_add(
            App().settings.get_value("previous-threshold").get_int32(),
            update_button)

        if App().player.current_track.id is None:
            self.__play_button.set_sensitive(False)
            self.__prev_button.set_sensitive(False)
            self.__next_button.set_sensitive(False)
        else:
            self.__play_button.set_sensitive(True)
            self.__prev_button.set_sensitive(True)
            self.__next_button.set_sensitive(True)

    def _on_prev_changed(self, player):
        """
            Update prev button
            @param player as Player
        """
        if player.prev_track.id is not None:
            prev_artists = GLib.markup_escape_text(
                ", ".join(player.prev_track.artists))
            prev_title = GLib.markup_escape_text(player.prev_track.title)
            self.__prev_button.set_tooltip_markup("<b>%s</b> - %s" %
                                                  (prev_artists,
                                                   prev_title))
        else:
            self.__prev_button.set_tooltip_text("")

    def _on_next_changed(self, player):
        """
            Update toolbar
            @param player as Player
        """
        if player.next_track.id is not None:
            next_artists = GLib.markup_escape_text(
                ", ".join(player.next_track.artists))
            next_title = GLib.markup_escape_text(player.next_track.title)
            self.__next_button.set_tooltip_markup("<b>%s</b> - %s" %
                                                  (next_artists,
                                                   next_title))
        else:
            self.__next_button.set_tooltip_text("")

    def _on_status_changed(self, player):
        """
            Update play button state
            @param player as Player
        """
        if player.is_playing:
            self.__play_button.image.set_from_icon_name(
                "media-playback-pause-symbolic", Gtk.IconSize.BUTTON)
            self.__play_button.set_tooltip_text(_("Pause"))
        else:
            self.__play_button.image.set_from_icon_name(
                "media-playback-start-symbolic", Gtk.IconSize.BUTTON)
            self.__play_button.set_tooltip_text(_("Play"))

    def _on_loading_changed(self, player, status, track):
        """
            Show a spinner on play button
            @param player as Player
            @param status as bool
            @param track as Track
        """
        self.__play_button.set_loading(status)

#######################
# PRIVATE             #
#######################
    def __set_styles(self, widget, styles):
        """
            Add styles to widget
            @param widget as Gtk.Widget
            @param styles as [str]
        """
        context = widget.get_style_context()
        for style in styles:
            context.add_class(style)

    def __on_prev_button_clicked(self, button):
        """
            Previous track on prev button clicked
            @param button as Gtk.Button
        """
        App().player.prev()

    def __on_play_button_clicked(self, button):
        """
            Play/Pause on play button clicked
            @param button as Gtk.Button
        """
        if App().player.is_playing:
            App().player.pause()
        else:
            App().player.play()

    def __on_next_button_clicked(self, button):
        """
            Next track on next button clicked
            @param button as Gtk.Button
        """
        App().player.next()

    def __on_destroy(self, widget):
        """
            Stop timeout
            @param widget as Gtk.Widget
        """
        if self.__prev_button_timeout_id is not None:
            GLib.source_remove(self.__prev_button_timeout_id)
            self.__prev_button_timeout_id = None
