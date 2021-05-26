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

from lollypop.define import App, Type, AUDIODB_CLIENT_ID
from lollypop.define import FANARTTV_ID
from lollypop.utils import get_network_available, emit_signal
from lollypop.logger import Logger
from lollypop.objects_album import Album
from lollypop.artwork_downloader import ArtworkDownloader


class AlbumArtworkDownloader(ArtworkDownloader):
    """
        Download artwork from the web
    """

    def __init__(self):
        """
            Init artwork downloader
        """
        ArtworkDownloader.__init__(self)
        self.__methods = {
            "AudioDB": self.__get_audiodb_album_artwork_uri,
            "FanartTV": self.__get_fanarttv_album_artwork_uri,
            "Spotify": self.__get_spotify_album_artwork_uri,
            "Itunes": self.__get_itunes_album_artwork_uri,
            "Deezer": self.__get_deezer_album_artwork_uri,
            "Last.fm": self.__get_lastfm_album_artwork_uri
        }
        self.__queue = []
        self.__downloading = False

    def add_from_uri(self, album, uri, cancellable):
        """
            Add album artwork
            @param album as Album
            @param uri as str
            @param cancellable as Gio.Cancellable
        """
        def on_uri_content(uri, status, data):
            if status:
                self.add(album, data)
                emit_signal(self, "album-artwork-changed", album.id)
        if uri:
            App().task_helper.load_uri_content(uri,
                                               cancellable,
                                               on_uri_content)

    def download(self, album_id):
        """
            Download album artwork
            @param album_id as int
        """
        if not get_network_available("DATA"):
            return
        self.__queue.append(album_id)
        if not self.__downloading:
            App().task_helper.run(self.__download_queue)

    def search(self, artist, album, cancellable):
        """
            Search album artworks
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
        """
        results = []
        for api in self.__methods.keys():
            if cancellable.is_cancelled():
                return
            uris = self.__methods[api](artist, album, cancellable)
            for uri in uris:
                if cancellable.is_cancelled():
                    return
                results.append((uri, api))
        emit_signal(self, "uri-artwork-found", results)

#######################
# PRIVATE             #
#######################
    def __get_deezer_album_artwork_uri(self, artist, album, cancellable=None):
        """
            Get album artwork using Deezer
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("DEEZER"):
            return []
        uris = []
        try:
            album_formated = GLib.uri_escape_string(album, None, True)
            uri = "https://api.deezer.com/search/album/?" +\
                  "q=%s&output=json" % album_formated
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["data"]:
                    uri = item["cover_xl"]
                    uris.append(uri)
        except:
            Logger.error("Deezer: %s", uri)
        return uris

    def __get_fanarttv_album_artwork_uri(self, artist, album,
                                         cancellable=None):
        """
            Get album artwork using FanartTV
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("FANARTTV"):
            return []
        uris = []
        try:
            search = "%s %s" % (artist, album)
            mbid = self._get_musicbrainz_mbid("album", search, cancellable)
            if mbid is None:
                return []
            uri = "http://webservice.fanart.tv/v3/music/albums/%s?api_key=%s"\
                % (mbid, FANARTTV_ID)
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for cover in decode["albums"][mbid]["albumcover"]:
                    uris.append(cover["url"])
        except:
            Logger.error("FanartTV: %s", uri)
        return uris

    def __get_spotify_album_artwork_uri(self, artist, album, cancellable=None):
        """
            Get album artwork using Spotify
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
            @tread safe
        """
        # Spotify API need an artist
        if not get_network_available("SPOTIFY") or not artist:
            return []
        uris = []
        try:
            artist_formated = GLib.uri_escape_string(
                "%s %s" % (artist, album), None, True).replace(" ", "+")
            uri = "https://api.spotify.com/v1/search?q=%s" % artist_formated +\
                  "&type=album"
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            (status,
             data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["albums"]["items"]:
                    uris.append(item["images"][0]["url"])
        except:
            Logger.error("Spotify: %s", uri)
        return uris

    def __get_itunes_album_artwork_uri(self, artist, album, cancellable=None):
        """
            Get album artwork using Itunes
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
            @tread safe
        """
        if not get_network_available("ITUNES"):
            return []
        uris = []
        try:
            album_formated = GLib.uri_escape_string(
                album, None, True).replace(" ", "+")
            uri = "https://itunes.apple.com/search" +\
                  "?entity=album&term=%s" % album_formated
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                if "results" in decode.keys():
                    for item in decode["results"]:
                        uris.append(item["artworkUrl60"].replace(
                            "60x60", "1024x1024"))
        except:
            Logger.error("Itunes: %s", uri)
        return uris

    def __get_audiodb_album_artwork_uri(self, artist, album, cancellable=None):
        """
            Get album artwork using AudioDB
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
        """
        if not get_network_available("AUDIODB"):
            return []
        uris = []
        try:
            album = GLib.uri_escape_string(album, None, True)
            artist = GLib.uri_escape_string(artist, None, True)
            uri = "https://theaudiodb.com/api/v1/json/"
            uri += "%s/searchalbum.php?s=%s&a=%s" % (AUDIODB_CLIENT_ID,
                                                     artist,
                                                     album)
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["album"]:
                    uris.append(item["strAlbumThumb"])
        except:
            Logger.error("AudioDB: %s", uri)
        return uris

    def __get_lastfm_album_artwork_uri(self, artist, album, cancellable=None):
        """
            Get album artwork using Last.fm
            @param artist as str
            @param album as str
            @param cancellable as Gio.Cancellable
            @return uris as [str]
            @tread safe
        """
        if not get_network_available("LASTFM"):
            return []
        uris = []
        try:
            from lollypop.helper_web_lastfm import LastFMWebHelper
            helper = LastFMWebHelper()
            payload = helper.get_album_payload(album, artist, cancellable)
            if "image" in payload.keys() and payload["image"]:
                artwork_uri = payload["image"][-1]["#text"]
                uris.append(artwork_uri)
        except:
            Logger.error("Last.FM: %s - %s", artist, album)
        return uris

    def __download_queue(self):
        """
            Cache albums artwork (from queue)
        """
        self.__downloading = True
        try:
            while self.__queue:
                album_id = self.__queue.pop()
                album = App().albums.get_name(album_id)
                artist_ids = App().albums.get_artist_ids(album_id)
                is_compilation = artist_ids and\
                    artist_ids[0] == Type.COMPILATIONS
                if is_compilation:
                    artist = ""
                else:
                    artist = ", ".join(App().albums.get_artists(album_id))
                found = False
                for api in self.__methods.keys():
                    result = self.__methods[api](artist, album)
                    for uri in result:
                        self.add_from_uri(
                            Album(album_id), uri, self.cancellable)
                        break
                    # Found, do not search in another helper
                    if found:
                        break
                # Not found, save empty artwork
                if not found:
                    self.add(Album(album_id), None)
        except Exception as e:
            Logger.error("AlbumArtworkDownloader::__download_queue: %s" % e)
        self.__downloading = False
