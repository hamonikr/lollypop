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

from random import shuffle, sample
import json

from lollypop.define import LASTFM_API_KEY, App
from lollypop.logger import Logger
from lollypop.utils import emit_signal, get_network_available
from lollypop.helper_web_lastfm import LastFMWebHelper
from lollypop.helper_web_save import SaveWebHelper


class LastFMSimilars(SaveWebHelper, LastFMWebHelper):
    """
        Search similar artists with Last.fm
    """
    def __init__(self):
        """
            Init provider
        """
        SaveWebHelper.__init__(self)
        LastFMWebHelper.__init__(self)

    def load_similars(self, artist_ids, storage_type, cancellable):
        """
            Load similar artists for artist ids
            @param artist_ids as int
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
        """
        names = [App().artists.get_name(artist_id) for artist_id in artist_ids]
        result = self.get_similar_artists(names, cancellable)
        tracks = []
        for (artist_name, cover_uri) in result:
            albums = self.get_artist_top_albums(artist_name, cancellable)
            albums = sample(albums, min(len(albums), 10))
            if not albums:
                continue
            for (album, artist) in albums:
                payload = self.get_album_payload(album, artist, cancellable)
                if payload is None:
                    continue
                lollypop_payload = self.lollypop_album_payload(payload)
                item = self.save_album_payload_to_db(lollypop_payload,
                                                     storage_type,
                                                     True,
                                                     cancellable)
                tracks = sample(payload["tracks"]["track"],
                                min(len(payload["tracks"]["track"]), 3))
                shuffle(tracks)
                i = 1
                for track in tracks:
                    lollypop_payload = self.lollypop_track_payload(track, i)
                    i += 1
                    self.save_track_payload_to_db(lollypop_payload,
                                                  item,
                                                  storage_type,
                                                  True,
                                                  cancellable)
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
            try:
                for similar in self.__get_similar_artists(artist_name):
                    if cancellable.is_cancelled():
                        raise Exception("cancelled")
                    result.append((similar, None))
            except Exception as e:
                Logger.error("LastFMSimilars::get_similar_artists(): %s", e)
        if result:
            Logger.info("Found similar artists with LastFMSimilars")
        return result

#######################
# PRIVATE             #
#######################
    def __get_similar_artists(self, artist):
        """
            Get similar artists
            @param artist as str
            @return similars as [str]
        """
        if not get_network_available("LASTFM"):
            return []
        artists = []
        try:
            uri = "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo"
            uri += "&artist=%s&api_key=%s&format=json" % (
                artist, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                content = json.loads(data.decode("utf-8"))
                for artist in content["artist"]["similar"]["artist"]:
                    artists.append(artist["name"])
        except:
            Logger.error(
                "LastFMWebHelper::__get_similar_artists(): %s", data)
        return artists
