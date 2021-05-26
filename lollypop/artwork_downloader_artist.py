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

from gi.repository import GLib

import json

from lollypop.define import App, AUDIODB_CLIENT_ID
from lollypop.define import FANARTTV_ID
from lollypop.define import StorageType
from lollypop.utils import get_network_available, emit_signal
from lollypop.logger import Logger
from lollypop.artwork_downloader import ArtworkDownloader


class ArtistArtworkDownloader(ArtworkDownloader):
    """
        Download artwork from the web
    """

    def __init__(self):
        """
            Init artwork downloader
        """
        ArtworkDownloader.__init__(self)
        self.__methods = {
            "AudioDB": self.__get_audiodb_artist_artwork_uri,
            "FanartTV": self.__get_fanarttv_artist_artwork_uri,
            "Spotify": self.__get_spotify_artist_artwork_uri,
            "Deezer": self.__get_deezer_artist_artwork_uri
        }
        self.__queue = []
        self.__downloading = False

    def add_from_uri(self, artist, uri, cancellable, storage_type):
        """
            Add artist artwork from URI
            @param artist as str
            @param uri as str
            @param cancellable as Gio.Cancellable
            @param storage_type as int
        """
        def on_uri_content(uri, status, data):
            if status:
                self.add(artist, data, storage_type)
                emit_signal(self, "artist-artwork-changed", artist)
        if uri:
            App().task_helper.load_uri_content(uri,
                                               cancellable,
                                               on_uri_content)

    def download(self, artist):
        """
            Cache artist artwork
            @param artist as str
        """
        if not get_network_available("DATA"):
            return
        self.__queue.append(artist)
        if not self.__downloading:
            App().task_helper.run(self.__download_queue)

    def search(self, artist, cancellable):
        """
            Search artist artwork
            @param album as str
            @param cancellable as Gio.Cancellable
        """
        results = []
        for api in self.__methods.keys():
            if cancellable.is_cancelled():
                return
            uris = self.__methods[api](artist, cancellable)
            for uri in uris:
                if cancellable.is_cancelled():
                    return
                results.append((uri, api))
        emit_signal(self, "uri-artwork-found", results)

#######################
# PRIVATE             #
#######################
    def __get_audiodb_artist_artwork_uri(self, artist, cancellable=None):
        """
            Get artist artwork using AutdioDB
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("AUDIODB"):
            return []
        uris = []
        try:
            artist = GLib.uri_escape_string(artist, None, True)
            uri = "https://theaudiodb.com/api/v1/json/"
            uri += "%s/search.php?s=%s" % (AUDIODB_CLIENT_ID, artist)
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["artists"]:
                    for key in ["strArtistFanart", "strArtistThumb"]:
                        uri = item[key]
                        if uri is not None:
                            uris.append(uri)
        except:
            Logger.error("AudioDB: %s", uri)
        return uris

    def __get_deezer_artist_artwork_uri(self, artist, cancellable=None):
        """
            Get artist artwork using Deezer
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("DEEZER"):
            return []
        uris = []
        try:
            artist_formated = GLib.uri_escape_string(
                artist, None, True).replace(" ", "+")
            uri = "https://api.deezer.com/search/artist/?" +\
                  "q=%s&output=json&index=0" % artist_formated
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["data"]:
                    uri = item["picture_xl"]
                    uris.append(uri)
        except:
            Logger.error("Deezer: %s", uri)
        return uris

    def __get_fanarttv_artist_artwork_uri(self, artist, cancellable=None):
        """
            Get artist artwork using FanartTV
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("FANARTTV"):
            return []
        uris = []
        try:
            mbid = self._get_musicbrainz_mbid("artist", artist, cancellable)
            if mbid is None:
                return []
            uri = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (
                mbid, FANARTTV_ID)
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["artistbackground"]:
                    uris.append(item["url"])
        except:
            Logger.error("FanartTV: %s", uri)
        return uris

    def __get_spotify_artist_artwork_uri(self, artist, cancellable=None):
        """
            Get artist artwork using Spotify
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("SPOTIFY"):
            return []
        uris = []
        try:
            artist_formated = GLib.uri_escape_string(
                artist, None, True).replace(" ", "+")
            uri = "https://api.spotify.com/v1/search?q=%s" % artist_formated +\
                  "&type=artist"
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            (status,
             data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["artists"]["items"]:
                    image_uri = item["images"][0]["url"]
                    uris.append(image_uri)
        except:
            Logger.error("Spotify: %s", uri)
        return uris

    def __download_queue(self):
        """
            Cache artwork for all artists
        """
        self.__downloading = True
        try:
            while self.__queue:
                artist = self.__queue.pop()
                found = False
                for api in self.__methods.keys():
                    result = self.__methods[api](artist)
                    for uri in result:
                        found = True
                        self.add_from_uri(artist, uri, self.cancellable,
                                          StorageType.COLLECTION)
                        break
                    # Found, do not search in another helper
                    if found:
                        break
                # Not found, save empty artwork
                if not found:
                    self.add(artist, None, StorageType.COLLECTION)
        except Exception as e:
            Logger.error("ArtistArtworkDownloader::__download_queue(): %s" % e)
        self.__downloading = False
