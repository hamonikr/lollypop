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

from gi.repository import Gtk, Pango, GLib, GObject

from gettext import gettext as _

from lollypop.define import App, ViewType, MARGIN_SMALL, IndicatorType
from lollypop.define import StorageType, LovedFlags
from lollypop.widgets_indicator import IndicatorWidget
from lollypop.utils import ms_to_string, on_query_tooltip, popup_widget
from lollypop.utils import emit_signal


class TrackRow(Gtk.ListBoxRow):
    """
        A track row
    """

    __gsignals__ = {
        "removed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def get_best_height(widget):
        """
            Calculate widget height
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(layout.get_pixel_size()[1])
        # application.css
        min_height = 32
        if font_height > min_height:
            height = font_height
        else:
            height = min_height
        return height

    def __init__(self, track, album_artist_ids, view_type):
        """
            Init row widgets
            @param track as Track
            @param album_artist_ids as [int]
            @param view_type as ViewType
        """
        # We do not use Gtk.Builder for speed reasons
        Gtk.ListBoxRow.__init__(self)
        self.__view_type = view_type
        self._track = track
        self.set_property("margin", MARGIN_SMALL)
        self._grid = Gtk.Grid()
        self._grid.set_property("valign", Gtk.Align.CENTER)
        self._grid.set_column_spacing(5)
        self._grid.show()
        if not view_type & ViewType.QUEUE:
            self._indicator = IndicatorWidget(self, view_type)
            self._indicator.show()
            self._indicator.set_valign(Gtk.Align.CENTER)
            self._grid.add(self._indicator)
        self._num_label = Gtk.Label.new()
        self._num_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._num_label.set_width_chars(4)
        self._num_label.get_style_context().add_class("dim-label")
        self.update_number_label()
        self._grid.add(self._num_label)
        self.__title_label = Gtk.Label.new()
        self.__title_label.set_property("has-tooltip", True)
        self.__title_label.connect("query-tooltip", on_query_tooltip)
        self.__title_label.set_property("hexpand", True)
        self.__title_label.set_property("halign", Gtk.Align.START)
        self.__title_label.set_property("xalign", 0)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.show()
        self._grid.add(self.__title_label)
        featuring_artist_ids = track.get_featuring_artist_ids(album_artist_ids)
        markup = GLib.markup_escape_text(self._track.name)
        if featuring_artist_ids:
            artists = []
            for artist_id in featuring_artist_ids:
                artists.append(App().artists.get_name(artist_id))
            markup += "\n<span size='x-small' alpha='40000'>%s</span>" %\
                GLib.markup_escape_text(", ".join(artists))
        self.__title_label.set_markup(markup)
        duration = ms_to_string(self._track.duration)
        self.__duration_label = Gtk.Label.new(duration)
        self.__duration_label.get_style_context().add_class("dim-label")
        self.__duration_label.show()
        self._grid.add(self.__duration_label)
        self.__action_button = None
        if self.__view_type & (
                ViewType.PLAYBACK | ViewType.PLAYLISTS):
            self.__action_button = Gtk.Button.new_from_icon_name(
               "list-remove-symbolic",
               Gtk.IconSize.MENU)
            self.__action_button.set_tooltip_text(
               _("Remove from playlist"))
        elif self.__view_type & (ViewType.ALBUM | ViewType.ARTIST):
            self.__action_button = Gtk.Button.new_from_icon_name(
               "view-more-symbolic",
               Gtk.IconSize.MENU)
        if self.__action_button is None:
            self.__duration_label.set_margin_end(MARGIN_SMALL)
        else:
            self.__action_button.show()
            self.__action_button.connect("clicked",
                                         self.__on_action_button_clicked)
            self.__action_button.set_margin_end(MARGIN_SMALL)
            self.__action_button.set_relief(Gtk.ReliefStyle.NONE)
            context = self.__action_button.get_style_context()
            context.add_class("menu-button")
            self._grid.add(self.__action_button)
        self.add(self._grid)
        if not view_type & ViewType.QUEUE:
            self.set_indicator(self._get_indicator_type())
        self.update_duration()
        self.get_style_context().add_class("trackrow")

    def update_duration(self):
        """
            Update track duration
        """
        self._track.reset("duration")
        duration = ms_to_string(self._track.duration)
        self.__duration_label.set_label(duration)

    def set_indicator(self, indicator_type=None):
        """
            Show indicator
            @param indicator_type as IndicatorType
        """
        # queued tracks do not have an indicator
        if self.__view_type & ViewType.QUEUE:
            return

        if indicator_type is None:
            indicator_type = self._get_indicator_type()
        self._indicator.clear()
        if indicator_type & IndicatorType.LOADING:
            self._indicator.set_opacity(1)
            self._indicator.load()
        elif indicator_type & IndicatorType.PLAY:
            self._indicator.set_opacity(1)
            self.set_state_flags(Gtk.StateFlags.VISITED, True)
            if indicator_type & IndicatorType.LOVED:
                self._indicator.play_loved()
            else:
                self._indicator.play()
        else:
            self.unset_state_flags(Gtk.StateFlags.VISITED)
            if indicator_type & IndicatorType.LOVED:
                self._indicator.set_opacity(1)
                self._indicator.loved()
            elif indicator_type & IndicatorType.SKIPPED:
                self._indicator.set_opacity(1)
                self._indicator.skip()
            else:
                self._indicator.set_opacity(0)

    def update_number_label(self):
        """
            Update position label for row
        """
        if App().player.is_in_queue(self._track.id):
            self._num_label.get_style_context().add_class("queued")
            pos = App().player.get_track_position(self._track.id)
            self._num_label.set_text(str(pos))
            self._num_label.show()
        elif not self.__view_type & ViewType.SEARCH:
            if self.__view_type & (ViewType.PLAYBACK | ViewType.PLAYLISTS):
                discs = App().albums.get_discs(self._track.album.id)
                if len(discs) > 1:
                    label = "%s: %s" % (self._track.discnumber,
                                        self._track.number)
                else:
                    label = "%s" % self._track.number
            else:
                label = "%s" % self._track.number
            self._num_label.set_markup(label)
            self._num_label.get_style_context().remove_class("queued")
            self._num_label.show()
        else:
            self._num_label.hide()

    def popup_menu(self, parent, x=None, y=None):
        """
            Popup menu for track
            @param parent as Gtk.Widget
            @param x as int
            @param y as int
        """
        def on_hidden(widget, hide):
            self.set_indicator()

        from lollypop.menu_objects import TrackMenu, TrackMenuExt
        from lollypop.widgets_menu import MenuBuilder
        menu = TrackMenu(self._track, self.__view_type)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        if not self._track.storage_type & StorageType.EPHEMERAL:
            menu_ext = TrackMenuExt(self._track)
            menu_ext.show()
            menu_widget.add_widget(menu_ext)
        if self.is_selected():
            popover = popup_widget(menu_widget, parent, x, y, None)
        else:
            popover = popup_widget(menu_widget, parent, x, y, self)
        if popover is None:
            menu_widget.connect("hidden", on_hidden)
        else:
            popover.connect("hidden", on_hidden)

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        return self.__title_label.get_text()

    @property
    def track(self):
        """
            Get row track
            @return Track
        """
        return self._track

#######################
# PROTECTED           #
#######################
    def _get_indicator_type(self):
        """
            Get indicator type for current row
            @return IndicatorType
        """
        indicator_type = IndicatorType.NONE
        if App().player.current_track.id == self._track.id:
            indicator_type |= IndicatorType.PLAY
        if self._track.loved & LovedFlags.LOVED:
            indicator_type |= IndicatorType.LOVED
        elif self._track.loved & LovedFlags.SKIPPED:
            indicator_type |= IndicatorType.SKIPPED
        return indicator_type

#######################
# PRIVATE             #
#######################
    def __on_action_button_clicked(self, button):
        """
            Show row menu
            @param button as Gtk.Button
        """
        if self.__view_type & (
                ViewType.PLAYBACK | ViewType.QUEUE | ViewType.PLAYLISTS):
            emit_signal(self, "removed")
        else:
            self.popup_menu(button)
