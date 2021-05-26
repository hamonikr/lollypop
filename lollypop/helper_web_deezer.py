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

import json

from lollypop.logger import Logger
from lollypop.define import App


class DeezerWebHelper:
    """
        Web helper for Deezer
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
            @return {}
        """
        try:
            uri = "https://api.deezer.com/search/artist?q=%s" % artist_name
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for artist in decode["data"]:
                    return artist["id"]
        except Exception as e:
            Logger.warning("DeezerWebHelper::get_artist_id(): %s", e)
        return None

    def get_album_payload(self, album_id, cancellable):
        """
            Get album payload for id
            @param album_id as int
            @param cancellable as Gio.Cancellable
            @return {}
        """
        try:
            uri = "https://api.deezer.com/album/%s" % album_id
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                return decode
        except Exception as e:
            Logger.warning("DeezerWebHelper::get_album_payload(): %s", e)
        return None

    def get_track_payload(self, track_id, cancellable):
        """
            Get album payload for id
            @param album_id as int
            @param cancellable as Gio.Cancellable
            @return {}
        """
        try:
            uri = "https://api.deezer.com/track/%s" % track_id
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                return decode
        except Exception as e:
            Logger.warning("DeezerWebHelper::get_track_payload(): %s", e)
        return None

    def lollypop_album_payload(self, payload):
        """
            Convert payload to Lollypop one
            @param payload as {}
            return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["name"] = payload["title"]
        lollypop_payload["uri"] = "dz:%s" % payload["id"]
        lollypop_payload["artists"] = payload["artist"]["name"]
        lollypop_payload["track-count"] = payload["nb_tracks"]
        lollypop_payload["artwork-uri"] = payload["cover_big"]
        try:
            lollypop_payload["date"] = "%sT00:00:00" % payload["release_date"]
        except:
            lollypop_payload["date"] = None
        return lollypop_payload

    def lollypop_track_payload(self, payload):
        """
            Convert payload to Lollypop one
            @param payload as {}
            @return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["name"] = payload["title"]
        lollypop_payload["uri"] = "dz:%s" % payload["id"]
        lollypop_payload["artists"] = payload["artist"]["name"]
        try:
            lollypop_payload["discnumber"] = payload["disk_number"]
        except:
            lollypop_payload["discnumber"] = 1
        lollypop_payload["tracknumber"] = payload["track_position"]
        lollypop_payload["duration"] = payload["duration"] * 1000
        return lollypop_payload

#######################
# PRIVATE             #
#######################
