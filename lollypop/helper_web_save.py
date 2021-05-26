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

from gi.repository import GLib, GObject

from time import time
import json

from lollypop.logger import Logger
from lollypop.utils import emit_signal
from lollypop.utils import get_lollypop_album_id, get_lollypop_track_id
from lollypop.objects_album import Album
from lollypop.define import App, Type
from lollypop.collection_item import CollectionItem


class SaveWebHelper(GObject.Object):
    """
       Web helper for saving Spotify payloads
    """

    __gsignals__ = {
        "match-album": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "match-track": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "match-artist": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        """
            Init helper
        """
        GObject.Object.__init__(self)

    def save_track_payload_to_db(self, payload, item,
                                 storage_type, notify, cancellable):
        """
            Save track to DB
            @param payload as {}
            @param item as CollectionItem
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
            @param notify as bool
        """
        lp_track_id = get_lollypop_track_id(payload["name"],
                                            payload["artists"],
                                            item.album_name)
        item.track_id = App().tracks.get_id_for_lp_track_id(lp_track_id)
        if item.track_id < 0:
            self.__save_track(payload, item, storage_type)
        if notify:
            emit_signal(self, "match-track", item.track_id, storage_type)

    def save_album_payload_to_db(self, payload, storage_type,
                                 notify, cancellable):
        """
            Save album to DB
            @param payload as {}
            @param storage_type as StorageType
            @param notify as bool
            @param cancellable as Gio.Cancellable
            @return CollectionItem/None
        """
        lp_album_id = get_lollypop_album_id(payload["name"],
                                            payload["artists"])
        album_id = App().albums.get_id_for_lp_album_id(lp_album_id)
        if album_id >= 0:
            album = Album(album_id)
            if notify:
                emit_signal(self, "match-album", album_id, storage_type)
            return album.collection_item
        item = self.__save_album(payload, storage_type)
        album = Album(item.album_id)
        if notify:
            App().album_art.add_from_uri(album,
                                         payload["artwork-uri"],
                                         cancellable)
            emit_signal(self, "match-album", album.id, storage_type)
        return item

#######################
# PRIVATE             #
#######################
    def __get_date_from_payload(self, payload):
        """
            Get date from payload
            @param payload as {}
            @param return (int, int)
        """
        try:
            release_date = payload["date"]
            dt = GLib.DateTime.new_from_iso8601(release_date,
                                                GLib.TimeZone.new_local())
            return (dt.to_unix(), dt.get_year())
        except:
            pass
        return (None, None)

    def __get_cover_art_uri(self, mbid, cancellable):
        """
            Get cover art URI for mbid
            @param mbid as str
            @param cancellable as Gio.Cancellable
            @return str/None
        """
        try:
            uri = "http://coverartarchive.org/release/%s" % mbid
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for image in decode["images"]:
                    if not image["front"]:
                        continue
                    return image["image"]
        except Exception as e:
            Logger.error(e)
            Logger.error(
                "SaveWebHelper::__get_cover_art_uri(): %s", data)
        return None

    def __save_album(self, payload, storage_type):
        """
            Save album payload to DB
            @param payload as {}
            @param storage_type as StorageType
            @return CollectionItem
        """
        (timestamp, year) = self.__get_date_from_payload(payload)
        item = CollectionItem(uri=payload["uri"],
                              album_artists=payload["artists"],
                              album_name=payload["name"],
                              album_mtime=int(time()),
                              year=year,
                              timestamp=timestamp,
                              mb_album_id=payload["mbid"],
                              album_synced=payload["track-count"],
                              storage_type=storage_type)
        Logger.debug("SaveWebHelper::save_album(): %s - %s",
                     item.album_artists, item.album_name)
        App().scanner.save_album(item)
        App().albums.add_genre(item.album_id, Type.WEB)
        return item

    def __save_track(self, payload, item, storage_type):
        """
            Save track payload to DB
            @param payload as {}
            @param storage_type as StorageType
            @return track_id as int
        """
        item.track_name = payload["name"]
        item.artists = payload["artists"]
        Logger.debug("SaveWebHelper::save_track(): %s - %s",
                     item.artists, item.track_name)
        item.discnumber = int(payload["discnumber"])
        item.tracknumber = int(payload["tracknumber"])
        item.duration = payload["duration"]
        item.track_mtime = int(time())
        item.uri = payload["uri"]
        item.mb_track_id = payload["mbid"]
        item.storage_type = storage_type
        App().scanner.save_track(item)
