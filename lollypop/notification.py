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

from gi.repository import Gdk, GLib, Gio
from gettext import gettext as _

from lollypop.define import App, ArtSize, Notifications


class NotificationManager:
    """
        Freedesktop notification support
    """

    def __init__(self):
        """
            Init notification object with lollypop infos
        """
        self.__notification_timeout_id = None
        App().player.connect("current-changed", self.__on_current_changed)
        self.__notification = Gio.Notification.new("")
        self.__action = Gio.Notification.new("")
        self.__action.add_button_with_target(
            _("Previous"),
            "app.shortcut",
            GLib.Variant("s", "prev"))
        self.__action.add_button_with_target(
            _("Next"),
            "app.shortcut",
            GLib.Variant("s", "next"))

    def send_track(self, track):
        """
            Send a message about track
            @param track as Track
        """
        if App().settings.get_enum("notifications") == Notifications.NONE:
            return
        state = App().window.get_window().get_state()
        if track.id is None or\
                state & Gdk.WindowState.FOCUSED or\
                App().is_fullscreen:
            return

        cover_path = App().album_art.get_cache_path(track.album,
                                                    ArtSize.BIG,
                                                    ArtSize.BIG)
        if cover_path is None:
            icon = Gio.Icon.new_for_string("org.gnome.Lollypop-symbolic")
        else:
            f = Gio.File.new_for_path(cover_path)
            icon = Gio.FileIcon.new(f)
        self.__action.set_icon(icon)
        self.__action.set_title(track.title)
        if track.album.name == "":
            self.__action.set_body(", ".join(track.artists))
        else:
            self.__action.set_body("%s - %s" % (", ".join(track.artists),
                                                track.album.name))
        App().send_notification("current-changed", self.__action)
        if self.__notification_timeout_id is not None:
            GLib.source_remove(self.__notification_timeout_id)
        self.__notification_timeout_id = GLib.timeout_add(
            5000, self.__withdraw_notification)

    def send(self, title, body=""):
        """
            Send message to user
            @param title as str
            @param body as str
        """
        self.__notification.set_title(title)
        if body:
            self.__notification.set_body(body)
        App().send_notification("send-message", self.__notification)

#######################
# PRIVATE             #
#######################
    def __withdraw_notification(self):
        """
            Remove notification
        """
        self.__notification_timeout_id = None
        App().withdraw_notification("current-changed")

    def __on_current_changed(self, player):
        """
            Send notification with track_id infos
            @param player Player
        """
        if App().settings.get_enum("notifications") != Notifications.ALL:
            return
        self.send_track(player.current_track)
