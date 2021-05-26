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


class IndicatorWidget(Gtk.EventBox):
    """
        Show play/loved indicator
        If embedded in a Popover, will not affect playlists but only player
        playlists
    """

    def __init__(self, row, view_type):
        """
            Init indicator widget, ui will be set when needed
            @param row as Row
            @param view_type as ViewType
        """
        Gtk.EventBox.__init__(self)
        self.__row = row
        self.__view_type = view_type
        self.__pass = 1
        self.__timeout_id = None
        self.__stack = None
        self.connect("destroy", self.__on_destroy)
        # min-width = 24px, borders = 2px, padding = 8px
        self.set_size_request(34, -1)
        self.__stack = Gtk.Stack()
        self.__stack.set_transition_duration(500)
        self.__stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.__stack.show()
        self.add(self.__stack)

    def play(self):
        """
            Show play indicator
        """
        self.__init_play()
        self.__stack.set_visible_child_name("play")

    def loved(self):
        """
            Show loved indicator
        """
        self.__init_loved()
        self.__loved.set_from_icon_name("emblem-favorite-symbolic",
                                        Gtk.IconSize.MENU)
        self.__stack.set_visible_child_name("loved")

    def skip(self):
        """
            Show skip indicator
        """
        self.__init_loved()
        self.__loved.set_from_icon_name("media-skip-forward-symbolic",
                                        Gtk.IconSize.MENU)
        self.__stack.set_visible_child_name("loved")

    def play_loved(self):
        """
            Show play/loved indicator
        """
        self.__init_play()
        self.__init_loved()
        self.__pass = 1
        self.play()
        self.__timeout_id = GLib.timeout_add(1000, self.__play_loved)

    def load(self):
        """
            Show load indicator
        """
        self.__init_load()
        self.__stack.set_visible_child_name("load")
        self.__stack.get_visible_child().start()

    def clear(self):
        """
            Clear widget
        """
        load = self.__stack.get_child_by_name("load")
        if load is not None:
            load.stop()
        if self.__timeout_id is not None:
            GLib.source_remove(self.__timeout_id)
            self.__timeout_id = None

#######################
# PRIVATE             #
#######################
    def __init_play(self):
        """
            Init play button
        """
        if self.__stack.get_child_by_name("play") is not None:
            return
        play = Gtk.Image.new_from_icon_name("media-playback-start-symbolic",
                                            Gtk.IconSize.MENU)
        play.show()
        self.__stack.add_named(play, "play")

    def __init_loved(self):
        """
            Init loved button
        """
        if self.__stack.get_child_by_name("loved") is not None:
            return
        self.__loved = Gtk.Image()
        self.__loved.show()
        self.__stack.add_named(self.__loved, "loved")

    def __init_load(self):
        """
            Init load spinner
        """
        if self.__stack.get_child_by_name("load") is not None:
            return
        spinner = Gtk.Spinner()
        spinner.show()
        self.__stack.add_named(spinner, "load")

    def __on_destroy(self, widget):
        """
            Clear timeout
            @param widget as Gtk.Widget
        """
        self.__row = None
        self.clear()

    def __play_loved(self):
        """
            Show play/loved indicator
        """
        if self.__timeout_id is None:
            return False
        if self.__stack.get_visible_child_name() == "play":
            if self.__pass == 5:
                self.__pass = 0
                self.loved()
        else:
            self.play()
        self.__pass += 1
        return True
