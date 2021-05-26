# Copyright (c) 2014-2017 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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
import re
from locale import getdefaultlocale

from lollypop.logger import Logger
from lollypop.define import App, LASTFM_API_KEY
from lollypop.utils import get_network_available


class LastFMWebHelper:
    """
        Web helper for Last.fm
    """

    def __init__(self):
        """
            Init helper
        """
        pass

    def get_artist_id(self, artist_name, cancellable):
        """
            Get artist id
            @param artist_name as str
            @param cancellable as Gio.Cancellable
            @return str/None
        """
        try:
            uri = "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo"
            uri += "&artist=%s&api_key=%s&format=json" % (
                artist_name, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                content = json.loads(data.decode("utf-8"))
                return content["artist"]["mbid"]
        except:
            Logger.error(
                "LastFMWebHelper::get_artist_id(): %s", uri)
        return None

    def get_artist_top_albums(self, artist, cancellable):
        """
            Get top albums for artist
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return [(str, str)]
        """
        artist = GLib.uri_escape_string(artist, None, True)
        albums = []
        try:
            uri = "http://ws.audioscrobbler.com/2.0/"
            uri += "?method=artist.gettopalbums"
            uri += "&artist=%s&api_key=%s&format=json" % (
                artist, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                content = json.loads(data.decode("utf-8"))
                for album in content["topalbums"]["album"]:
                    albums.append((album["name"], album["artist"]["name"]))
        except:
            Logger.error(
                "LastFMWebHelper::get_artist_top_albums(): %s", uri)
        return albums

    def get_album_payload(self, album, artist, cancellable):
        """
            Get album payload for mbid
            @param album as str
            @param artist as str
            @param cancellable as Gio.Cancellable
            @return {}
        """
        artist = GLib.uri_escape_string(artist, None, True)
        album = GLib.uri_escape_string(album, None, True)
        try:
            uri = "http://ws.audioscrobbler.com/2.0/"
            uri += "?method=album.getInfo"
            uri += "&album=%s&artist=%s&api_key=%s&format=json" % (
                album, artist, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                return json.loads(data.decode("utf-8"))["album"]
        except:
            Logger.error(
                "LastFMWebHelper::get_album_payload(): %s", uri)
        return {}

    def get_lollypop_payload(self, mbid, cancellable):
        """
            Get track payload for mbid
            @param mbid as str
            @param cancellable as Gio.Cancellable
            @return {}/None
        """
        try:
            uri = "http://ws.audioscrobbler.com/2.0/"
            uri += "?method=track.getInfo"
            uri += "&mbid=%s&api_key=%s&format=json" % (
                mbid, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                return json.loads(data.decode("utf-8"))["track"]
        except:
            Logger.error(
                "LastFMWebHelper::get_lollypop_payload(): %s", uri)
        return None

    def get_artist_bio(self, artist):
        """
            Get artist biography
            @param artist as str
            @return content as bytes/None
        """
        if not get_network_available("LASTFM"):
            return None
        artist = GLib.uri_escape_string(artist, None, True)
        try:
            language = getdefaultlocale()[0][0:2]
            uri = "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo"
            uri += "&artist=%s&api_key=%s&format=json&lang=%s" % (
                artist, LASTFM_API_KEY, language)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                content = json.loads(data.decode("utf-8"))
                bio = content["artist"]["bio"]["content"]
                bio = re.sub(r"<.*Last.fm.*>.", "", bio)
                return bio.encode(encoding="UTF-8")
        except:
            Logger.error(
                "LastFMWebHelper::get_artist_bio(): %s", uri)
        return None

    def lollypop_album_payload(self, payload):
        """
            Convert payload to Lollypop one
            @param payload as {}
            return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["name"] = payload["name"]
        lollypop_payload["uri"] = ""
        lollypop_payload["artists"] = payload["artist"]
        lollypop_payload["track-count"] = len(payload["tracks"])
        lollypop_payload["date"] = None
        try:
            artwork_uri = payload["image"][-1]["#text"]
        except:
            artwork_uri = None
        lollypop_payload["artwork-uri"] = artwork_uri
        return lollypop_payload

    def lollypop_track_payload(self, payload, tracknumber):
        """
            Convert payload to Lollypop one
            @param payload as {}
            @param tracknumber as int
            @return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["name"] = payload["name"]
        lollypop_payload["uri"] = ""
        lollypop_payload["artists"] = payload["artist"]["name"]
        lollypop_payload["discnumber"] = "1"
        lollypop_payload["tracknumber"] = tracknumber
        lollypop_payload["duration"] = int(payload["duration"]) * 1000
        return lollypop_payload

#######################
# PRIVATE             #
#######################
