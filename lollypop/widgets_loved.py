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

from gi.repository import Gtk

from gettext import gettext as _

from lollypop.define import App, Type, LovedFlags
from lollypop.objects_track import Track


class LovedWidget(Gtk.Bin):
    """
        Loved widget
    """

    def __init__(self, object, icon_size=Gtk.IconSize.BUTTON):
        """
            Init widget
            @param object as Album/Track
            @param icon_size as Gtk.IconSize
        """
        Gtk.Bin.__init__(self)
        self.__object = object
        self.__icon_size = icon_size
        self.__timeout_id = None
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/LovedWidget.ui")
        builder.connect_signals(self)
        self.__artwork = builder.get_object("artwork")
        self.add(builder.get_object("widget"))
        self.__set_artwork(self.__object.loved)

    def set_icon_size(self, icon_size):
        """
            Set widget icon size
            @param icon_size as Gtk.IconSize
        """
        self.__icon_size = icon_size
        self.__set_artwork(self.__object.loved)

#######################
# PROTECTED           #
#######################
    def _on_enter_notify_event(self, widget, event):
        """
            Update love opacity
            @param widget as Gtk.EventBox
            @param event as Gdk.Event
        """
        if self.__object.loved & LovedFlags.LOVED:
            loved = LovedFlags.NONE
        else:
            loved = LovedFlags.LOVED
        self.__set_artwork(loved)

    def _on_leave_notify_event(self, widget, event):
        """
            Update love opacity
            @param widget as Gtk.EventBox (can be None)
            @param event as Gdk.Event (can be None)
        """
        self.__set_artwork(self.__object.loved)

    def _on_button_release_event(self, widget, event):
        """
            Toggle loved status
            @param widget as Gtk.EventBox
            @param event as Gdk.Event
        """
        if self.__object.loved & LovedFlags.LOVED:
            loved = LovedFlags.NONE
        else:
            loved = LovedFlags.LOVED
        self.__object.set_loved(loved)
        if isinstance(self.__object, Track):
            # Clear loved playlist artwork cache
            name = App().playlists.get_name(Type.LOVED)
            App().art.remove_from_cache("playlist_" + name, "ROUNDED")
            name = App().playlists.get_name(Type.SKIPPED)
            App().art.remove_from_cache("playlist_" + name, "ROUNDED")
            # Update state on Last.fm
            status = True if loved & LovedFlags.LOVED else False
            for scrobbler in App().ws_director.scrobblers:
                scrobbler.set_loved(self.__object, status)
        self.__set_artwork(self.__object.loved)
        return True

#######################
# PRIVATE             #
#######################
    def __set_artwork(self, flags):
        """
            Set artwork base on object status
            @param flags as int
        """
        if flags & LovedFlags.LOVED:
            self.set_tooltip_text(_("Like"))
            self.__artwork.set_opacity(0.8)
            self.__artwork.set_from_icon_name("emblem-favorite-symbolic",
                                              self.__icon_size)
        else:
            self.set_tooltip_text(_("Allow playback"))
            self.__artwork.set_opacity(0.2)
            self.__artwork.set_from_icon_name("emblem-favorite-symbolic",
                                              self.__icon_size)
