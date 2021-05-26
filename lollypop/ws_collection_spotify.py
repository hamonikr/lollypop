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
from time import time
from random import shuffle
from locale import getdefaultlocale

from lollypop.logger import Logger
from lollypop.utils import get_default_storage_type
from lollypop.helper_web_spotify import SpotifyWebHelper
from lollypop.define import App, StorageType


class SpotifyCollectionWebService(SpotifyWebHelper):
    """
        Add items to collection with Spotify
        Depends on SaveWebHelper
    """
    def __init__(self):
        """
            Init object
        """
        SpotifyWebHelper.__init__(self)

    def search_similar_albums(self, cancellable):
        """
            Add similar albums to DB
            @param cancellable as Gio.Cancellable
        """
        Logger.info("Get similar albums from Spotify")
        from lollypop.similars_spotify import SpotifySimilars
        similars = SpotifySimilars()
        try:
            storage_type = get_default_storage_type()
            artists = App().artists.get_randoms(
                self.MAX_ITEMS_PER_STORAGE_TYPE, storage_type)
            artist_names = [name for (aid, name, sortname) in artists]
            similar_ids = similars.get_similar_artist_ids(artist_names,
                                                          cancellable)
            # Add albums
            shuffle(similar_ids)
            for similar_id in similar_ids[:self.MAX_ITEMS_PER_STORAGE_TYPE]:
                albums_payload = self.__get_artist_albums_payload(similar_id,
                                                                  cancellable)
                shuffle(albums_payload)
                for album in albums_payload:
                    if cancellable.is_cancelled():
                        raise Exception("Cancelled")
                    lollypop_payload = SpotifyWebHelper.lollypop_album_payload(
                        self, album)
                    self.save_album_payload_to_db(
                                           lollypop_payload,
                                           StorageType.SPOTIFY_SIMILARS,
                                           True,
                                           cancellable)
                    break
        except Exception as e:
            Logger.warning("SpotifyWebService::search_similar_albums(): %s", e)

    def search_new_releases(self, cancellable):
        """
            Get new released albums from spotify
            @param cancellable as Gio.Cancellable
        """
        Logger.info("Get new releases from Spotify")
        try:
            locale = getdefaultlocale()[0][0:2]
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            uri = "https://api.spotify.com/v1/browse/new-releases"
            uris = ["%s?country=%s" % (uri, locale), uri]
            for uri in uris:
                if cancellable.is_cancelled():
                    raise Exception("cancelled")
                (status,
                 data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
                if status:
                    decode = json.loads(data.decode("utf-8"))
                    for album in decode["albums"]["items"]:
                        if cancellable.is_cancelled():
                            raise Exception("Cancelled")
                        lollypop_payload =\
                            SpotifyWebHelper.lollypop_album_payload(
                                self, album)
                        self.save_album_payload_to_db(
                                             lollypop_payload,
                                             StorageType.SPOTIFY_NEW_RELEASES,
                                             True,
                                             cancellable)
                    # Check if storage type needs to be updated
                    # Check if albums newer than a week are enough
                    timestamp = time() - 604800
                    newer_albums = App().albums.get_newer_for_storage_type(
                                             StorageType.SPOTIFY_NEW_RELEASES,
                                             timestamp)
                    if len(newer_albums) >= self.MIN_ITEMS_PER_STORAGE_TYPE:
                        break
        except Exception as e:
            Logger.warning("SpotifyWebService::search_new_releases(): %s", e)

#######################
# PRIVATE             #
#######################
    def __get_artist_albums_payload(self, spotify_id, cancellable):
        """
            Get albums payload for artist
            @param spotify_id as str
            @param cancellable as Gio.Cancellable
            @return {}
        """
        try:
            token = App().ws_director.token_ws.get_token("SPOTIFY",
                                                         cancellable)
            bearer = "Bearer %s" % token
            headers = [("Authorization", bearer)]
            uri = "https://api.spotify.com/v1/artists/%s/albums" % spotify_id
            (status,
             data) = App().task_helper.load_uri_content_sync_with_headers(
                    uri, headers, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                return decode["items"]
        except Exception as e:
            Logger.warning(
                "SpotifyWebService::__get_artist_albums_payload(): %s", e)
        return None
