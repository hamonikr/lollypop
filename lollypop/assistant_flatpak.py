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

from gettext import gettext as _

from lollypop.define import App
from lollypop.assistant import Assistant


class FlatpakAssistant(Assistant):
    """
        Lollypop Flatpak package is now using Freedesktop API to gain access
        to directories, we need to revalidate collection
    """

    def __init__(self):
        """
            Init assistant
        """
        self.__rules = [
            {
              "title": _("Authorization needed"),
              "icon_name": "dialog-password-symbolic",
              "markup": _("""
In order to be able to access your collection,
you need to allow <b>Lollypop</b>."""),
              "uri_label": "",
              "uri": None,
              "right_button_label": None,
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Update folders"),
              "icon_name": "folder-music-symbolic",
              "markup": _("""
- <b>Open</b> Lollypop <b>preferences</b>
- Go to the <b>Music</b> tab
- <b>Remove</b> all folders from collection
- Then, <b>add</b> them again"""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Preferences"),
              "left_button_style": "suggested-action"
            },
        ]
        Assistant.__init__(self, self.__rules)
        self.resize(500, 100)
        self.connect("destroy", self.__on_destroy)

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, window):
        """
            Launch settings
            @param window as Gtk.Window
        """
        App().lookup_action("settings").activate(None)
