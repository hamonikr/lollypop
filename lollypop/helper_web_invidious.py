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

import json

from lollypop.helper_web_base import BaseWebHelper
from lollypop.define import App
from lollypop.utils import emit_signal
from lollypop.logger import Logger


class InvidiousWebHelper(BaseWebHelper):
    """
        Invidious helper
    """

    __BAD_SCORE = 1000000
    __SEARCH = "api/v1/search?q=%s"
    __VIDEO = "api/v1/videos/%s"

    def __init__(self):
        """
            Init heApper
        """
        BaseWebHelper.__init__(self)
        self.__server = App().settings.get_value(
            "invidious-server").get_string().strip("/")

    def get_uri_content(self, uri, cancellable):
        """
            Get content uri
            @param uri as str
            @param cancellable as Gio.Cancellable
            @return content uri as str/None
        """
        Logger.info("Loading %s with Invidious %s", uri, self.__server)
        youtube_id = uri.replace("https://www.youtube.com/watch?v=", "")
        video = self.__VIDEO % youtube_id
        uri = "%s/%s" % (self.__server, video)
        App().task_helper.load_uri_content(uri,
                                           cancellable,
                                           self.__on_uri_content)

#######################
# PRIVATE             #
#######################
    def __on_uri_content(self, uri, status, content):
        """
            Emit signal for content
            @param uri as str
            @param status as bool
            @param content as bytes
        """
        try:
            content_uri = ""
            if status:
                decode = json.loads(content.decode("utf-8"))
                for item in decode["adaptiveFormats"]:
                    if item["container"] == "webm" and\
                            item["encoding"] == "opus":
                        content_uri = item["url"]
                        break
        except Exception as e:
            Logger.warning("InvidiousWebHelper::__on_uri_content(): %s", e)
        emit_signal(self, "uri-content-loaded", content_uri)
