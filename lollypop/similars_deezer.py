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

import json

from lollypop.define import App
from lollypop.logger import Logger
from lollypop.utils import emit_signal
from lollypop.helper_web_deezer import DeezerWebHelper
from lollypop.helper_web_save import SaveWebHelper


class DeezerSimilars(SaveWebHelper, DeezerWebHelper):
    """
        Search similar artists with Deezer
    """
    def __init__(self):
        """
            Init provider
        """
        SaveWebHelper.__init__(self)
        DeezerWebHelper.__init__(self)

    def load_similars(self, artist_ids, storage_type, cancellable):
        """
            Load similar artists for artist ids
            @param artist_ids as int
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
        """
        for artist_id in artist_ids:
            artist_name = App().artists.get_name(artist_id)
            deezer_id = self.get_artist_id(artist_name, cancellable)
            try:
                uri = "https://api.deezer.com/artist/%s/radio" % deezer_id
                (status, data) = App().task_helper.load_uri_content_sync(
                    uri, cancellable)
                if status:
                    decode = json.loads(data.decode("utf-8"))
                    for payload in decode["data"]:
                        track_payload = self.get_track_payload(
                            payload["id"], cancellable)
                        album_payload = self.get_album_payload(
                            payload["album"]["id"], cancellable)
                        lollypop_payload = self.lollypop_album_payload(
                            album_payload)
                        item = self.save_album_payload_to_db(lollypop_payload,
                                                             storage_type,
                                                             True,
                                                             cancellable)
                        lollypop_payload = self.lollypop_track_payload(
                            track_payload)
                        self.save_track_payload_to_db(lollypop_payload,
                                                      item,
                                                      storage_type,
                                                      True,
                                                      cancellable)
            except Exception as e:
                Logger.error("DeezerSimilars::load_similars(): %s", e)
        emit_signal(self, "finished")

    def get_similar_artists(self, artist_names, cancellable):
        """
            Search similar artists
            @param artist_names as [str]
            @param cancellable as Gio.Cancellable
            @return [(str, str)] as [(artist_name, cover_uri)]
        """
        result = []
        for artist_name in artist_names:
            if cancellable.is_cancelled():
                return []
            deezer_id = self.get_artist_id(artist_name, cancellable)
            if deezer_id is None:
                continue
            if cancellable.is_cancelled():
                return []
            result += self.__get_similar_artists_from_deezer_id(deezer_id,
                                                                cancellable)
        result = [(name, uri) for (deezer_id, name, uri) in result]
        if result:
            Logger.info("Found similar artists with DeezerSimilars")
        return result

#######################
# PRIVATE             #
#######################
    def __get_similar_artists_from_deezer_id(self, deezer_id, cancellable):
        """
           Get similar artists from deezer id
           @param deezer_id as str
           @param cancellable as Gio.Cancellable
           @return [(str, str, str)] : list of (deezer_id, artist, cover_uri)
        """
        artists = []
        try:
            uri = "https://api.deezer.com/artist/%s/related" % deezer_id
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for artist in decode["data"]:
                    if "picture_xl" in artist.keys():
                        artwork_uri = artist["picture_xl"]
                    elif "picture_big" in artist.keys():
                        artwork_uri = artist["picture_big"]
                    elif "picture_medium" in artist.keys():
                        artwork_uri = artist["picture_medium"]
                    else:
                        artwork_uri = None
                    artists.append((artist["id"],
                                    artist["name"],
                                    artwork_uri))
        except:
            Logger.error(
                "DeezerSimilars::__get_similar_artists_from_deezer_id(): %s",
                deezer_id)
        return artists
