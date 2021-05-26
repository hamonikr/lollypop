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

from gi.repository import GObject, Gio

from lollypop.define import CACHE_PATH, App
from lollypop.logger import Logger
from lollypop.utils import emit_signal


class WebHelper(GObject.Object):
    """
        Web helper
    """

    __gsignals__ = {
        "loaded": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, track, cancellable):
        """
            Init helper
            @param track as Track
            @param cancellable as Gio.Cancellable
        """
        GObject.Object.__init__(self)
        self.__track = track
        self.__cancellable = cancellable
        if App().settings.get_value("invidious-server").get_string():
            from lollypop.helper_web_invidious import InvidiousWebHelper
            self.__helpers = [InvidiousWebHelper()]
        else:
            from lollypop.helper_web_youtube import YouTubeWebHelper
            self.__helpers = [YouTubeWebHelper()]

    def __del__(self):
        self.__track = None

    def load(self):
        """
            Load track URI
        """
        uri = self.__load_from_cache()
        if uri is None:
            self.__load_uri_with_helper()
        else:
            Logger.info("%s loaded from cache", uri)
            self.__load_uri_content_with_helper(uri, None)

    def save(self, uri):
        """
            Save URI to cache
            @param uri as str
        """
        if not self.__track.lp_track_id:
            return
        try:
            f = Gio.File.new_for_path(
                "%s/%s" % (CACHE_PATH, self.__track.lp_track_id))
            fstream = f.replace(None, False,
                                Gio.FileCreateFlags.REPLACE_DESTINATION,
                                None)
            if fstream is not None:
                fstream.write(uri.encode("utf-8"), None)
                fstream.close()
        except Exception as e:
            Logger.error("WebHelper::save(): %s", e)

    @property
    def uri(self):
        """
            Get track URI
            @return str
        """
        return self.__load_from_cache()

#######################
# PRIVATE             #
#######################
    def __load_from_cache(self):
        """
            Load URI from cache
            @return str/None
        """
        if not self.__track.lp_track_id:
            return None
        try:
            f = Gio.File.new_for_path(
                "%s/%s" % (CACHE_PATH, self.__track.lp_track_id))
            if f.query_exists():
                (stats, content, tag) = f.load_contents()
                return content.decode("utf-8")
        except Exception as e:
            Logger.error("WebHelper::__load_from_cache(): %s", e)
        return None

    def __load_uri_with_helper(self):
        """
            Load track with an helper
        """
        if self.__helpers:
            helper = self.__helpers.pop(0)
            helper.connect("uri-loaded", self.__on_uri_loaded)
            helper.get_uri(self.__track, self.__cancellable)
        else:
            emit_signal(self, "loaded", "")

    def __load_uri_content_with_helper(self, uri, helper):
        """
            Load track uri with and helper
            @param uri as str
            @param helper as BaseWebHelper
        """
        if helper is None and self.__helpers:
            helper = self.__helpers.pop(0)
        if helper is not None:
            helper.connect("uri-content-loaded", self.__on_uri_content_loaded)
            helper.get_uri_content(uri, self.__cancellable)
        else:
            emit_signal(self, "loaded", "")

    def __on_uri_content_loaded(self, helper, uri):
        """
            Emit loaded signal with content
            @param helper as BaseWebHelper
            @param uri as str
        """
        emit_signal(self, "loaded", uri)

    def __on_uri_loaded(self, helper, uri):
        """
            Load URI content
            @param helper as BaseWebHelper
            @param uri as str
        """
        if uri:
            self.__load_uri_content_with_helper(uri, helper)
            self.save(uri)
        else:
            emit_signal(self, "loaded", "")
