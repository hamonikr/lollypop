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

from lollypop.logger import Logger
from lollypop.utils import emit_signal, get_network_available
from lollypop.helper_web_lastfm import LastFMWebHelper
from lollypop.helper_web_save import SaveWebHelper
from lollypop.define import LASTFM_API_KEY, App


class LastFMSearch(LastFMWebHelper, SaveWebHelper):
    """
        Search for LastFM
    """

    def __init__(self):
        """
            Init object
        """
        SaveWebHelper.__init__(self)
        LastFMWebHelper.__init__(self)

    def get(self, search, storage_type, cancellable):
        """
            Get albums for search
            We need a thread because we are going to populate DB
            @param search as str
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
        """
        if not get_network_available("LASTFM"):
            emit_signal(self, "finished")
            return
        try:
            uri = "http://ws.audioscrobbler.com/2.0/?method=album.search"
            uri += "&album=%s&api_key=%s&format=json" % (
                search, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            albums = []
            if status:
                decode = json.loads(data.decode("utf-8"))
                for album in decode["results"]["albummatches"]["album"]:
                    albums.append((album["name"], album["artist"]))
            for (album, artist) in albums:
                uri = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo"
                uri += "&api_key=%s&artist=%s&album=%s&format=json" % (
                    LASTFM_API_KEY,
                    GLib.uri_escape_string(artist, None, True),
                    GLib.uri_escape_string(album, None, True))
                (status, data) = App().task_helper.load_uri_content_sync(
                    uri, cancellable)
                if status:
                    decode = json.loads(data.decode("utf-8"))
                    try:
                        payload = self.lollypop_album_payload(decode["album"])
                        item = self.save_album_payload_to_db(payload,
                                                             storage_type,
                                                             True,
                                                             cancellable)
                        i = 1
                        for track in decode["album"]["tracks"]["track"]:
                            payload = self.lollypop_track_payload(track, i)
                            i += 1
                            self.save_track_payload_to_db(payload,
                                                          item,
                                                          storage_type,
                                                          True,
                                                          cancellable)
                    except Exception as e:
                        Logger.warning("LastFMSearch::get(): %s", e)
        except Exception as e:
            Logger.warning("LastFMSearch::get(): %s", e)
        if not cancellable.is_cancelled():
            emit_signal(self, "finished")

    def load_tracks(self, album_id, storage_type, cancellable):
        pass
