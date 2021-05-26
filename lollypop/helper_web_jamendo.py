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


class JamendoWebHelper:
    """
        Web helper for Jamendo
    """

    def __init__(self):
        """
            Init helper
        """
        pass

    def lollypop_album_payload(self, payload):
        """
            Convert payload to Lollypop one
            @param payload as {}
            return {}
        """
        lollypop_payload = {}
        lollypop_payload["mbid"] = None
        lollypop_payload["name"] = payload["name"]
        lollypop_payload["uri"] = "jam:%s" % payload["id"]
        lollypop_payload["artists"] = payload["artist_name"]
        lollypop_payload["track-count"] = -1
        lollypop_payload["artwork-uri"] = payload["image"]
        try:
            lollypop_payload["date"] = "%sT00:00:00" %\
                payload["releasedate"]
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
        lollypop_payload["name"] = payload["name"]
        lollypop_payload["uri"] = payload["audio"]
        lollypop_payload["artists"] = payload["artist_name"]
        lollypop_payload["discnumber"] = 1
        lollypop_payload["tracknumber"] = payload["position"]
        lollypop_payload["duration"] = int(payload["duration"]) * 1000
        return lollypop_payload

#######################
# PRIVATE             #
#######################
