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

from gi.repository import Gtk, GObject, GLib, Handy

from lollypop.helper_art import ArtBehaviour
from lollypop.define import App, ArtSize, MARGIN_SMALL, MARGIN
from lollypop.widgets_player_progress import ProgressPlayerWidget
from lollypop.widgets_player_buttons import ButtonsPlayerWidget
from lollypop.widgets_player_artwork import ArtworkPlayerWidget
from lollypop.widgets_player_label import LabelPlayerWidget
from lollypop.helper_size_allocation import SizeAllocationHelper
from lollypop.helper_signals import SignalsHelper, signals
from lollypop.utils import emit_signal


class MiniPlayer(Handy.WindowHandle, SizeAllocationHelper, SignalsHelper):
    """
        Mini player shown in folded window
    """
    __gsignals__ = {
        "revealed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals
    def __init__(self):
        """
            Init mini player
        """
        Handy.WindowHandle.__init__(self)
        SizeAllocationHelper.__init__(self)
        self.__previous_artwork_id = None
        self.__per_track_cover = App().settings.get_value(
            "allow-per-track-cover")
        self.get_style_context().add_class("black")
        self.__box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.__box.show()
        self.__box.get_style_context().add_class("padding")
        self.__revealer = Gtk.Revealer.new()
        self.__revealer.show()
        self.__revealer_box = Gtk.Box.new(Gtk.Orientation.VERTICAL,
                                          MARGIN_SMALL)
        self.__revealer_box.show()
        bottom_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, MARGIN_SMALL)
        bottom_box.show()
        self.__progress_widget = ProgressPlayerWidget()
        self.__progress_widget.show()
        self.__progress_widget.set_vexpand(True)
        self.__progress_widget.set_margin_start(MARGIN)
        self.__progress_widget.set_margin_end(MARGIN)
        buttons_widget = ButtonsPlayerWidget(["banner-button-big"])
        buttons_widget.show()
        buttons_widget.update()
        buttons_widget.set_property("valign", Gtk.Align.CENTER)
        buttons_widget.set_margin_end(MARGIN_SMALL)
        self.__artwork_widget = ArtworkPlayerWidget(ArtBehaviour.CROP_SQUARE)
        self.__artwork_widget.show()
        self.__artwork_widget.set_vexpand(True)
        self.__artwork_widget.set_property("margin", MARGIN_SMALL)
        self.__artwork_widget.get_style_context().add_class(
                "transparent-cover-frame")
        self.__label_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, MARGIN)
        self.__label_box.show()
        self.__label_box.set_property("margin", MARGIN_SMALL)
        self.__label_widget = LabelPlayerWidget(False, 9)
        self.__label_widget.show()
        self.__label_widget.update()
        self.__label_widget.set_margin_start(MARGIN_SMALL)
        self.__label_widget.set_margin_end(MARGIN_SMALL)
        self.__artwork_button = Gtk.Image.new()
        self.__artwork_button.show()
        self.__label_box.pack_start(self.__artwork_button, False, False, 0)
        self.__label_box.pack_start(self.__label_widget, False, False, 0)
        button = Gtk.Button.new()
        button.show()
        button.get_style_context().add_class("banner-button-big")
        button.set_property("halign", Gtk.Align.START)
        button.set_property("valign", Gtk.Align.CENTER)
        button.connect("clicked", self.__on_button_clicked)
        button.set_image(self.__label_box)
        button.set_margin_start(MARGIN_SMALL)
        self.__background = Gtk.Image()
        self.__background.show()
        # Assemble UI
        self.__box.pack_start(self.__revealer, False, True, 0)
        self.__box.pack_start(bottom_box, False, False, 0)
        bottom_box.pack_start(button, True, True, 0)
        bottom_box.pack_end(buttons_widget, False, False, 0)
        self.__revealer.add(self.__revealer_box)
        self.__revealer_box.pack_start(self.__artwork_widget, False, True, 0)
        self.__revealer_box.pack_end(self.__progress_widget, False, True, 0)
        overlay = Gtk.Overlay.new()
        overlay.show()
        overlay.add(self.__background)
        overlay.add_overlay(self.__box)
        self.add(overlay)
        return [
            (App().player, "current-changed", "_on_current_changed")
        ]

    def reveal(self, reveal):
        """
            Reveal miniplayer
            @param reveal as bool
        """
        if reveal:
            self.__update_progress_visibility()
            self.__revealer.set_reveal_child(True)
            emit_signal(self, "revealed", True)
            self.__progress_widget.update()
            size = min(ArtSize.FULLSCREEN, self.width // 2)
            self.__artwork_widget.set_art_size(size, size)
            self.__artwork_widget.update(True)
            if App().lookup_action("miniplayer").get_state():
                self.__artwork_button.set_from_icon_name(
                    "view-fullscreen-symbolic", Gtk.IconSize.BUTTON)
            else:
                self.__artwork_button.set_from_icon_name(
                    "pan-down-symbolic", Gtk.IconSize.BUTTON)
        else:
            self.__revealer.set_reveal_child(False)
            emit_signal(self, "revealed", False)
            self.update_artwork()
        self.__set_widgets_position()

    def update_artwork(self):
        """
            Update artwork
        """
        if not self.revealed:
            App().art_helper.set_album_artwork(
                    App().player.current_track.album,
                    ArtSize.SMALL,
                    ArtSize.SMALL,
                    self.__artwork_button.get_scale_factor(),
                    ArtBehaviour.CACHE |
                    ArtBehaviour.CROP_SQUARE,
                    self.__on_button_artwork)

    def do_get_preferred_width(self):
        """
            Force preferred width
        """
        (min, nat) = Gtk.Bin.do_get_preferred_width(self)
        # Allow resizing
        return (0, nat)

    def do_get_preferred_height(self):
        """
            Force preferred height
        """
        (min, nat) = self.__box.get_preferred_height()
        return (min, min)

    @property
    def revealed(self):
        """
            True if mini player revealed
            @return bool
        """
        return self.__revealer.get_reveal_child()

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update artwork and labels
            @param player as Player
        """
        if player.current_track.id is None:
            self.__on_artwork(None)
            return

        same_artwork = self.__previous_artwork_id ==\
            player.current_track.album.id and not self.__per_track_cover
        if same_artwork:
            return
        self.__previous_artwork_id = App().player.current_track.album.id
        allocation = self.get_allocation()
        self.__artwork_widget.set_artwork(
                allocation.width,
                allocation.height,
                self.__on_artwork,
                ArtBehaviour.BLUR_HARD | ArtBehaviour.DARKER)
        self.update_artwork()

    def _handle_width_allocate(self, allocation):
        """
            Handle artwork sizing
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            # We use parent height because we may be collapsed
            parent = self.get_parent()
            if parent is None:
                height = self.height
            else:
                height = parent.get_allocated_height()
            if self.__revealer.get_reveal_child():
                size = min(ArtSize.FULLSCREEN, self.width // 2)
                self.__artwork_widget.set_art_size(size, size)
                self.__artwork_widget.update(True)
            self.__artwork_widget.set_artwork(
                allocation.width + 100, height + 100,
                self.__on_artwork,
                ArtBehaviour.BLUR_HARD | ArtBehaviour.DARKER)

    def _handle_height_allocate(self, allocation):
        """
            Handle artwork sizing
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_height_allocate(self, allocation):
            # We use parent height because we may be collapsed
            parent = self.get_parent()
            if parent is None:
                height = allocation.height
            else:
                height = parent.get_allocated_height()
            self.__artwork_widget.set_artwork(
                allocation.width + 100, height + 100,
                self.__on_artwork,
                ArtBehaviour.BLUR_HARD | ArtBehaviour.DARKER)

#######################
# PRIVATE             #
#######################
    def __update_progress_visibility(self):
        """
            Update progress bar visibility
        """
        if App().player.current_track.id is not None:
            self.__progress_widget.show()
        else:
            self.__progress_widget.hide()

    def __set_widgets_position(self):
        """
            Add label widget to wanted UI part
        """
        parent = self.__label_widget.get_parent()
        if parent is not None:
            parent.remove(self.__label_widget)
        if self.revealed:
            self.__revealer_box.pack_start(self.__label_widget, False, True, 0)
        else:
            self.__label_box.pack_start(self.__label_widget, False, False, 0)

    def __on_button_clicked(self, *ignore):
        """
            Set revealer on/off
        """
        if App().lookup_action("miniplayer").get_state():
            App().lookup_action("miniplayer").change_state(
                GLib.Variant("b", False))
        else:
            self.reveal(not self.revealed)

    def __on_button_artwork(self, surface):
        """
           Set artwork on button
           @param surface as cairo.Surface
        """
        self.__artwork_button.set_from_surface(surface)
        del surface

    def __on_artwork(self, surface):
        """
            Set artwork
            @param surface as str
        """
        self.__background.set_from_surface(surface)
        if surface is None:
            self.__background.get_style_context().add_class("black")
        else:
            self.__background.get_style_context().remove_class("black")
            del surface
