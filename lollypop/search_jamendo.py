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
from lollypop.utils import emit_signal, get_network_available
from lollypop.helper_web_jamendo import JamendoWebHelper
from lollypop.helper_web_save import SaveWebHelper
from lollypop.define import App


class JamendoSearch(SaveWebHelper, JamendoWebHelper):
    """
        Search for Jamendo
    """

    def __init__(self):
        """
            Init object
        """
        SaveWebHelper.__init__(self)
        JamendoWebHelper.__init__(self)

    def get(self, search, storage_type, cancellable):
        """
            Get albums for search
            We need a thread because we are going to populate DB
            @param search as str
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
        """
        if not get_network_available("DEEZER"):
            emit_signal(self, "finished")
            return
        try:
            # Albums
            uri = "https://api.jamendo.com/v3.0/albums/"
            uri += "?client_id=6a13ad2c&format=jsonpretty"
            uri += "&limit=10&namesearch=%s" % search
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for album in decode["results"]:
                    payload = self.lollypop_album_payload(album)
                    self.save_album_payload_to_db(payload,
                                                  storage_type,
                                                  True,
                                                  cancellable)
            # Artists
            uri = "https://api.jamendo.com/v3.0/artists/albums/"
            uri += "?client_id=6a13ad2c&format=jsonpretty"
            uri += "&limit=10&namesearch=%s" % search
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for artist in decode["results"]:
                    App().art.add_from_uri(artist["name"], artist["image"],
                                           cancellable, storage_type)
                    for album in artist["albums"]:
                        album["artist_name"] = artist["name"]
                        payload = self.lollypop_album_payload(album)
                        self.save_album_payload_to_db(payload,
                                                      storage_type,
                                                      True,
                                                      cancellable)
        except Exception as e:
            Logger.warning("JamendoSearch::get(): %s", e)
        if not cancellable.is_cancelled():
            emit_signal(self, "finished")

    def load_tracks(self, album, cancellable):
        """
            Load tracks for album
            @param album as Album
            @param cancellable as Gio.Cancellable
        """
        try:
            jamid = album.uri.replace("jam:", "")
            uri = "https://api.jamendo.com/v3.0/albums/tracks/"
            uri += "?client_id=6a13ad2c&format=jsonpretty&id=%s" % jamid
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                # We want to share the same item as lp_album_id may change
                album_item = album.collection_item
                for result in decode["results"]:
                    for track in result["tracks"]:
                        track["artist_name"] = result["artist_name"]
                        lollypop_payload = self.lollypop_track_payload(track)
                        self.save_track_payload_to_db(lollypop_payload,
                                                      album_item,
                                                      album.storage_type,
                                                      False,
                                                      cancellable)
        except Exception as e:
            Logger.error("JamendoSearch::load_tracks(): %s", e)
