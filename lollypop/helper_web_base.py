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

from gi.repository import GLib, GObject

import json

from lollypop.define import App, GOOGLE_API_ID
from lollypop.utils import get_network_available, get_page_score, emit_signal
from lollypop.logger import Logger


class BaseWebHelper(GObject.Object):
    """
        Base Web Helper
    """

    __gsignals__ = {
        "uri-loaded": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "uri-content-loaded": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    __BAD_SCORE = 1000000

    def __init__(self):
        """
            Init helper
        """
        GObject.Object.__init__(self)

    def get_uri(self, track, cancellable, methods=[]):
        """
            Get helper URI
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
        """
        if not methods:
            methods = [self.__get_youtube_id]
            if get_network_available("STARTPAGE"):
                methods.append(self.__get_youtube_id_start)
            if get_network_available("DUCKDUCKGO"):
                methods.append(self.__get_youtube_id_duckduck)
        method = methods.pop(0)
        method(track, cancellable, methods)

#######################
# PRIVATE             #
#######################
    def __get_youtube_id(self, track, cancellable, methods):
        """
            Get youtube id
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
        """
        unescaped = "%s %s" % (track.artists[0],
                               track.name)
        search = GLib.uri_escape_string(
                            unescaped.replace(" ", "+"),
                            None,
                            True)
        key = App().settings.get_value("cs-api-key").get_string()
        uri = "https://www.googleapis.com/youtube/v3/" +\
              "search?part=snippet&q=%s&" % search +\
              "type=video&key=%s&cx=%s" % (key, GOOGLE_API_ID)
        App().task_helper.load_uri_content(uri, cancellable,
                                           self.__on_get_youtube_id,
                                           track, cancellable, methods)

    def __get_youtube_id_start(self, track, cancellable, methods):
        """
            Get youtube id via startpage
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
            @return youtube id as str
        """
        unescaped = "%s %s" % (track.artists[0],
                               track.name)
        search = GLib.uri_escape_string(
                        unescaped.replace(" ", "+"),
                        None,
                        True)
        uri = "https://www.startpage.com/do/search?query=%s" % search
        App().task_helper.load_uri_content(uri, cancellable,
                                           self.__on_get_youtube_id_start,
                                           track, cancellable, methods)

    def __get_youtube_id_duckduck(self, track, cancellable, methods):
        """
            Get youtube id via duckduckgo
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
            @return youtube id as str
        """
        unescaped = "%s %s +youtube" % (track.artists[0],
                                        track.name)
        search = GLib.uri_escape_string(
                        unescaped.replace(" ", "+"),
                        None,
                        True)
        uri = "https://duckduckgo.com/lite/?q=%s" % search
        App().task_helper.load_uri_content(uri, cancellable,
                                           self.__on_get_youtube_id_duckduck,
                                           track, cancellable, methods)

    def __emit_uri_loaded(self, youtube_id, track, cancellable, methods):
        """
            Emit uri loaded for youtube_id
            @param youtube_id as bool
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
        """
        if youtube_id is not None:
            uri = "https://www.youtube.com/watch?v=%s" % youtube_id
            emit_signal(self, "uri-loaded", uri)
        elif methods:
            self.get_uri(track, cancellable, methods)
        else:
            emit_signal(self, "uri-loaded", "")

    def __on_get_youtube_id(self, uri, status, content, track,
                            cancellable, methods):
        """
            Get youtube id or run another method if not found
            @param uri as str
            @param status as bool
            @param content as bytes
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
        """
        try:
            youtube_id = None
            if status:
                decode = json.loads(content.decode("utf-8"))
                dic = {}
                best = self.__BAD_SCORE
                for i in decode["items"]:
                    score = get_page_score(i["snippet"]["title"],
                                           track.name,
                                           track.artists[0],
                                           track.album.name)
                    if score == -1 or score == best:
                        continue
                    elif score < best:
                        best = score
                    dic[score] = i["id"]["videoId"]
                # Return url from first dic item
                if best != self.__BAD_SCORE:
                    youtube_id = dic[best]
        except:
            Logger.warning("BaseWebHelper::__on_get_youtube_id(): %s", content)
        self.__emit_uri_loaded(youtube_id, track, cancellable, methods)

    def __on_get_youtube_id_start(self, uri, status, content, track,
                                  cancellable, methods):
        """
            Get youtube id or run another method if not found
            @param uri as str
            @param status as bool
            @param content as bytes
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
        """
        try:
            from bs4 import BeautifulSoup
            youtube_id = None
            html = content.decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            ytems = []
            for link in soup.findAll("a"):
                href = link.get("href")
                title = link.get_text()
                if href is None or title is None or\
                        href.find("youtube.com/watch?v") == -1:
                    continue
                youtube_id = href.split("watch?v=")[1]
                ytems.append((youtube_id, title))
            dic = {}
            best = self.__BAD_SCORE
            for (yid, title) in ytems:
                score = get_page_score(title, track.name,
                                       track.artists[0], track.album.name)
                if score == -1 or score == best:
                    continue
                elif score < best:
                    best = score
                dic[score] = yid
            # Return url from first dic item
            if best != self.__BAD_SCORE:
                youtube_id = dic[best]
        except Exception as e:
            print("$ sudo pip3 install beautifulsoup4")
            Logger.warning("BaseWebHelper::__get_youtube_id_start(): %s", e)
        self.__emit_uri_loaded(youtube_id, track, cancellable, methods)

    def __on_get_youtube_id_duckduck(self, uri, status, content, track,
                                     cancellable, methods):
        """
            Get youtube id or run another method if not found
            @param uri as str
            @param status as bool
            @param content as bytes
            @param track as Track
            @param cancellable as Gio.Cancellable
            @param methods as [function]
        """
        try:
            from bs4 import BeautifulSoup
            youtube_id = None
            html = content.decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            ytems = []
            for link in soup.findAll("a"):
                href = GLib.uri_unescape_string(link.get("href"), None)
                title = link.get_text()
                if href is None or title is None or\
                        href.find("youtube.com/watch?v") == -1:
                    continue
                youtube_id = href.split("watch?v=")[1]
                ytems.append((youtube_id, title))
            dic = {}
            best = self.__BAD_SCORE
            for (yid, title) in ytems:
                score = get_page_score(title, track.name,
                                       track.artists[0], track.album.name)
                if score == -1 or score == best:
                    continue
                elif score < best:
                    best = score
                dic[score] = yid
            # Return url from first dic item
            if best != self.__BAD_SCORE:
                youtube_id = dic[best]
        except Exception as e:
            print("$ sudo pip3 install beautifulsoup4")
            Logger.warning("BaseWebHelper::__get_youtube_id_duckduck(): %s", e)
        self.__emit_uri_loaded(youtube_id, track, cancellable, methods)
