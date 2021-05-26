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

from lollypop.define import App, LASTFM_API_KEY
from lollypop.assistant import Assistant
from lollypop.helper_passwords import PasswordsHelper


class LastfmAssistant(Assistant):
    """
        Last.FM API assistant
    """

    def __init__(self, service):
        """
            Init assistant
            @param service as str
        """
        if service == "LASTFM":
            name = "Last.FM"
        else:
            name = "Libre.fm"
        self.__rules = [
            {
              "title": _("Scrobbling to %s") % name,
              "icon_name": "media-playback-start-symbolic",
              "markup": _("""
In order to send your activity to <b>%s</b>,
you need to allow <b>Lollypop</b>.""") % name,
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Cancel"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Connect to %s") % name,
              "icon_name": "web-browser-symbolic",
              "markup": _("""
<b>Open and login</b> to <b>%s</b>.
Then, allow Lollypop.""") % name,
              "uri_label": _("Access %s") % name,
              "uri": "",
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Next"),
              "left_button_style": "suggested-action"
            },
            {
              "title": _("Just play a track"),
              "icon_name": "emblem-music-symbolic",
              "markup": _("""
<b>Click "Finish"</b> once Lollypop has been allowed."""),
              "uri_label": "",
              "uri": None,
              "right_button_label": _("Back"),
              "right_button_style": "",
              "left_button_label": _("Finish"),
              "left_button_style": "suggested-action"
            },
        ]
        Assistant.__init__(self, self.__rules)
        self.connect("destroy", self.__on_destroy, service)
        App().ws_director.token_ws.clear_token(service, True)
        App().ws_director.token_ws.get_lastfm_auth_token(
            service, None, self.__on_token)

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, window, service):
        """
            Finish key activation
            @param window as Gtk.Window
            @param service as str
        """
        App().task_helper.run(
            App().ws_director.token_ws.get_token, service, None)

    def __on_token(self, token, service):
        """
            Store token
            @param token as str
            @param service as str
        """
        passwords_helper = PasswordsHelper()
        passwords_helper.store(service, service, token)
        validation_token = token.replace("validation:", "")
        if service == "LIBREFM":
            uri = "http://libre.fm/api/auth?api_key=%s&token=%s" % (
                LASTFM_API_KEY, validation_token)
        else:
            uri = "http://www.last.fm/api/auth?api_key=%s&token=%s" % (
                LASTFM_API_KEY, validation_token)
        self.update_uri(uri, 1)
        # Force web service to validate token
        App().ws_director.token_ws.clear_token(service)
