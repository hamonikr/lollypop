# Copyright (C) 2017 Jason Gray <jasonlevigray3@gmail.com>
# Copyright (C) 2017 Franz Dietrich <dietrich@teilgedanken.de>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
# END LICENSE

from gi.repository import Gtk, Gst

from gettext import gettext as _

from lollypop.define import App, PowerManagement


class Inhibitor:
    """
        Register to playback status changes so that standby/idle is only
        inhibited while playing
    """

    def __init__(self):
        self.__cookie = 0
        self.__status_handler_id = None      # The playback listener
        self.__override_inhibit = False

        # Load and apply the inhibit settings
        self.__on_powermanagement_setting_changed(App().settings)
        # Register to settings changes
        App().settings.connect(
            "changed::power-management",
            self.__on_powermanagement_setting_changed,
        )

    def __on_powermanagement_setting_changed(self, settings, name=None):
        if settings.get_enum("power-management") > 0:
            self.__enable_react_to_playback()
        else:
            self.__disable_react_to_playback()
        self.__uninhibit()
        self.__on_status_changed()

    def __disable_react_to_playback(self):
        if self.__status_handler_id is not None:
            App().player.disconnect(self.__status_handler_id)
            self.__status_handler_id = None

    def __enable_react_to_playback(self):
        if self.__status_handler_id is None:
            self.__status_handler_id = App().player.connect(
                "status-changed",
                self.__on_status_changed,
            )

    def __on_status_changed(self, player=None):
        """
            React to a change of playback state
        """
        if not player:
            player = App().player
        if player.get_status() == Gst.State.PLAYING:
            self.__inhibit()
        else:
            self.__uninhibit()

    def __get_flags_settings(self):
        """
            Get the inhibit flags according to the settings in dconf
        """
        power_management = App().settings.get_enum("power-management")
        if power_management == PowerManagement.BOTH:
            return Gtk.ApplicationInhibitFlags.IDLE | \
                           Gtk.ApplicationInhibitFlags.SUSPEND
        elif power_management == PowerManagement.SUSPEND:
            return Gtk.ApplicationInhibitFlags.SUSPEND
        elif power_management == PowerManagement.IDLE:
            return Gtk.ApplicationInhibitFlags.IDLE
        else:
            return None

    def __inhibit(self, flags=None):
        """
            Disable flags
            @param flags as Gtk.ApplicationInhibitFlags
        """
        if self.__override_inhibit:
            return
        if not flags:
            flags = self.__get_flags_settings()
        if not self.__cookie and flags:
            self.__cookie = App().inhibit(
                App().window,
                flags,
                _("Playing music"))

    def __uninhibit(self):
        """
            Remove all the powermanagement settings
        """
        if self.__override_inhibit:
            return
        if self.__cookie:
            App().uninhibit(self.__cookie)
            self.__cookie = 0

    def override_inhibit(self, flags):
        """
            Inhibit suspend or idle manually.
            The settings values from dconf are not applied while a
            override_inhibit() call is active.
            Disable the manual override with unoverride_inhibit().
            @param flags as Gtk.ApplicationInhibitFlags
        """
        self.__uninhibit()
        self.__inhibit(flags)
        self.__override_inhibit = True

    def unoverride_inhibit(self):
        """
            Remove the manual inhibit state and restore the settings from
            dconf
        """
        self.__override_inhibit = False
        self.__uninhibit()
        self.__on_status_changed()
