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
from locale import getdefaultlocale

from lollypop.logger import Logger
from lollypop.define import App


class SpotifyWebHelper:
    """
       Web helper for Spotify
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
            artist_name = GLib.uri_escape_string(
                artist_name, None, True).replace(" ", "+")
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            uri = "https://api.spotify.com/v1/search?q=%s&type=artist" %\
                artist_name
            (status,
             data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["artists"]["items"]:
                    return item["id"]
        except Exception as e:
            Logger.error("SpotifyWebHelper::get_artist_id(): %s", e)
        return None

    def get_track_payload(self, spotify_id, cancellable):
        """
            Get track payload for spotify id
            @param spotify_id as str
            @param cancellable as Gio.Cancellable
            @return {}/None
        """
        try:
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            uri = "https://api.spotify.com/v1/tracks/%s" % spotify_id
            (status,
             data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                return decode
        except Exception as e:
            Logger.error("SpotifyWebHelper::get_track_payload(): %s", e)
        return None

    def get_artist_top_tracks(self, spotify_id, cancellable):
        """
            Get top tracks for spotify id
            @param spotify_id as str
            @param cancellable as Gio.Cancellable
            @return str
        """
        try:
            locale = getdefaultlocale()[0][0:2]
            track_ids = []
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            uri = "https://api.spotify.com/v1/artists/%s/top-tracks" %\
                spotify_id
            uri += "?country=%s" % locale
            (status,
             data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["tracks"]:
                    track_ids.append(item["id"])
        except Exception as e:
            Logger.error("SpotifyWebHelper::get_artist_top_tracks(): %s", e)
        return track_ids

    def lollypop_album_payload(self, payload):
        """
            Convert payload to Lollypop one
            @param payload as {}
            return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["uri"] = "sp:%s" % payload["id"]
        lollypop_payload["name"] = payload["name"]
        artists = []
        for artist in payload["artists"]:
            artists.append(artist["name"])
        lollypop_payload["artists"] = ";".join(artists)
        lollypop_payload["track-count"] = payload["total_tracks"]
        lollypop_payload["date"] = "%sT00:00:00" % payload["release_date"]
        lollypop_payload["artwork-uri"] = payload["images"][0]["url"]
        return lollypop_payload

    def lollypop_track_payload(self, payload):
        """
            Convert payload to Lollypop one
            @param payload as {}
            return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["uri"] = "sp:%s" % payload["id"]
        lollypop_payload["name"] = payload["name"]
        artists = []
        for artist in payload["artists"]:
            artists.append(artist["name"])
        lollypop_payload["artists"] = ";".join(artists)
        lollypop_payload["discnumber"] = "1"
        lollypop_payload["tracknumber"] = payload["track_number"]
        lollypop_payload["duration"] = payload["duration_ms"]
        return lollypop_payload

#######################
# PRIVATE             #
#######################
