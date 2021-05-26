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

from gi.repository import GLib, Gio

import json

from lollypop.define import App, GOOGLE_API_ID
from lollypop.utils import get_network_available, emit_signal
from lollypop.logger import Logger


class ArtworkDownloader:
    """
        Download artwork from the web
        Need to be herited by an ArtworkManager
    """

    def __init__(self):
        """
            Init art downloader
        """
        self.__cancellable = Gio.Cancellable()

    def search_artwork_from_google(self, search, cancellable):
        """
            Get google uri for search
            @param search as str
            @param cancellable as Gio.Cancellable
        """
        if not get_network_available("GOOGLE"):
            emit_signal(self, "uri-artwork-found", None)
            return
        key = App().settings.get_value("cs-api-key").get_string() or\
            App().settings.get_default_value("cs-api-key").get_string()
        uri = "https://www.googleapis.com/" +\
              "customsearch/v1?key=%s&cx=%s" % (key, GOOGLE_API_ID) +\
              "&q=%s&searchType=image" % GLib.uri_escape_string(search,
                                                                "",
                                                                False)
        App().task_helper.load_uri_content(uri,
                                           cancellable,
                                           self.__on_load_google_content)

    def search_artwork_from_startpage(self, search, cancellable):
        """
            Get google uri for search
            @param search as str
            @param cancellable as Gio.Cancellable
        """
        if not get_network_available("STARTPAGE"):
            emit_signal(self, "uri-artwork-found", None)
            return
        uri = "https://www.startpage.com/do/search?flimgsize=isz%3Al"
        uri += "&image-size-select=&flimgexwidth=&flimgexheight=&abp=-1"
        uri += "&cat=pics&query=%s" % GLib.uri_escape_string(search, "", False)
        App().task_helper.load_uri_content(uri,
                                           cancellable,
                                           self.__on_load_startpage_content)

    @property
    def cancellable(self):
        """
            Get global cancellable
            @return Gio.Cancellable
        """
        return self.__cancellable

#######################
# PROTECTED           #
#######################
    def _get_musicbrainz_mbid(self, mbid_type, string, cancellable):
        """
            Get musicbrainz mbid for type and string
            @param mbid_type as str ("artist" or "album")
            @param string as str
            @param cancellable as Gio.Cancellable
            @return str
        """
        try:
            if mbid_type == "artist":
                uri = "http://musicbrainz.org/ws/2/artist/" +\
                      "?query=%s&fmt=json"
            else:
                uri = "http://musicbrainz.org/ws/2/release-group/" +\
                      "?query=%s&fmt=json"
            string = GLib.uri_escape_string(string, None, True)
            (status, data) = App().task_helper.load_uri_content_sync(
                                                          uri % string,
                                                          cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                if mbid_type == "artist":
                    for item in decode["artists"]:
                        return item["id"]
                else:
                    mbid = None
                    for item in decode["release-groups"]:
                        if "primary-type" not in item.keys():
                            continue
                        if item["primary-type"] == "Album":
                            mbid = item["id"]
                            break
                        elif item["primary-type"] == "EP" and mbid is None:
                            mbid = item["id"]
                return mbid
        except:
            Logger.warning("MusicBrainz: %s", uri)
        return None

#######################
# PRIVATE             #
#######################
    def __on_load_google_content(self, uri, loaded, content):
        """
            Extract uris from content
            @param uri as str
            @param loaded as bool
            @param content as bytes
        """
        try:
            if not loaded:
                emit_signal(self, "uri-artwork-found", None)
                return
            decode = json.loads(content.decode("utf-8"))
            results = []
            for item in decode["items"]:
                if item["link"] is not None:
                    results.append((item["link"], "Google"))
            emit_signal(self, "uri-artwork-found", results)
        except Exception as e:
            emit_signal(self, "uri-artwork-found", None)
            Logger.error(
                "ArtworkDownloader::__on_load_google_content(): %s: %s"
                % (e, content))

    def __on_load_startpage_content(self, uri, loaded, content):
        """
            Extract uris from content
            @param uri as str
            @param loaded as bool
            @param content as bytes
        """
        import re

        def search_in_data(lines, found_uris=[]):
            if lines:
                line = lines.pop(0)
                # Do not call findall if nothing to find
                if line.find("oiu=") != -1:
                    res = re.findall(r'.*oiu=([^&]*).*', line)
                    for data in res:
                        uri = GLib.uri_unescape_string(data, "")
                        if uri in found_uris or uri is None:
                            continue
                        found_uris.append(uri)
                GLib.idle_add(search_in_data, lines, found_uris)
            else:
                results = [(uri, "Startpage") for uri in found_uris]
                emit_signal(self, "uri-artwork-found", results)

        try:
            if not loaded:
                emit_signal(self, "uri-artwork-found", None)
                return
            lines = content.decode("utf-8").splitlines()
            search_in_data(lines)
        except Exception as e:
            emit_signal(self, "uri-artwork-found", None)
            Logger.error("ArtworkDownloader::__on_load_startpage_content(): %s"
                         % e)
