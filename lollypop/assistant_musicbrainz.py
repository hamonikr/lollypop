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


class MusicbrainzAssistant(Assistant):
    """
        MusicBrainz API assistant
    """

    def __init__(self):
        """
            Init assistant
        """
        rules = [
            {
              "title": _("Scrobbling to ListenBrainz"),
              "icon_name": "media-playback-start-symbolic",
              "markup": _("""
In order to send your activity to <b>ListenBrainz</b>,
you need to allow <b>Lollypop</b>."""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Cancel"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Connect to ListenBrainz"),
              "icon_name": "web-browser-symbolic",
              "markup": _("""
<b>Open and login</b> to <b>ListenBrainz</b>."""),
              "uri_label": _("Access ListenBrainz"),
              "uri": "https://listenbrainz.org/profile",
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Copy key"),
              "icon_name": "emblem-music-symbolic",
              "markup": _("""
<b>Finish</b> the activation by copying <b>API-Key</b> in Lollypop."""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Finish"),
              "left_button_style": "suggested-action"
            },
        ]
        Assistant.__init__(self, rules)
