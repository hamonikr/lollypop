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

from gi.repository import GLib, Gtk, Pango

from lollypop.define import App
from lollypop.helper_signals import SignalsHelper, signals
from lollypop.utils import on_query_tooltip


class LabelPlayerWidget(Gtk.Label, SignalsHelper):
    """
        Gtk.Label auto updated with current player status
    """

    @signals
    def __init__(self, fullscreen=False, font_size=None):
        """
            Init label
            @param fullscreen as bool
        """
        Gtk.Label.__init__(self)
        self.__fullscreen = fullscreen
        self.__font_size = font_size
        self.set_ellipsize(Pango.EllipsizeMode.END)
        self.set_has_tooltip(True)
        self.connect("query-tooltip", on_query_tooltip)
        return [
            (App().player, "current-changed", "_on_current_changed"),
        ]

    def update(self):
        """
            Update label
        """
        # Some tags contain \n inside them
        # Filter this
        artists = ", ".join(
            App().player.current_track.artists).replace("\n", "")
        title = App().player.current_track.title.replace("\n", "")
        artist_text = GLib.markup_escape_text(artists)
        title_text = GLib.markup_escape_text(title)
        if self.__font_size is None:
            markup = "<b>%s</b>" % artist_text
            markup += "\n<span size='small' alpha='50000'>%s</span>" %\
                title_text
        else:
            markup = "<span font='%s' size='x-large' ><b>%s</b></span>" % (
                                                           self.__font_size,
                                                           artist_text)
            markup += "\n<span font='%s' size='x-large'>%s</span>"\
                % (self.__font_size, title_text)
        if self.__fullscreen:
            album_text = "%s" % GLib.markup_escape_text(
                App().player.current_track.album.name)
            if App().player.current_track.year:
                album_text += " (%s)" % App().player.current_track.year
            if self.__font_size is None:
                markup += "\n<span size='x-small' alpha='40000'>%s</span>" %\
                    album_text
            else:
                markup += "\n<span font='%s' alpha='40000'>%s</span>" %\
                    (self.__font_size, album_text)
        self.set_markup(markup)

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update artwork and labels
            @param player as Player
        """
        self.update()
