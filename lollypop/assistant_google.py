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

from lollypop.assistant import Assistant


class GoogleAssistant(Assistant):
    """
        Google API assistant
    """

    def __init__(self):
        """
            Init assistant
        """
        rules = [
            {
              "title": _("What is the Google API key?"),
              "icon_name": "media-playback-start-symbolic",
              "markup": _("""
In order to enable YouTube playback,
you need to create a key for the

<b>"YouTube Data API v3"</b>
"""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Cancel"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Connect to the console"),
              "icon_name": "web-browser-symbolic",
              "markup": _("""
<b>Open and log</b> in to the <b>Google Developer Console</b>"""),
              "uri_label": _("Access Google Developer Console"),
              "uri": "https://console.developers.google.com/apis/",
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Activate the API"),
              "icon_name": "folder-new-symbolic",
              "markup": _("""
<b>Add a new project</b> in the console.

After that, <b>add a new API</b> and search
for the <b>"YouTube Data API v3"</b>.

<b>Activate that API</b> for your project"""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Copy the key"),
              "icon_name": "dialog-password-symbolic",
              "markup": _("""
Open <b>"Credentials"</b> in the sidebar and
create credentials for an API key.

Then click 'Finish' within this wizard.
Copy the API key to Lollypop.
"""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Finish"),
              "left_button_style": "suggested-action"
            },
        ]
        Assistant.__init__(self, rules)
