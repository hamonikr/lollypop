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
from lollypop.helper_web_deezer import DeezerWebHelper
from lollypop.helper_web_save import SaveWebHelper
from lollypop.define import App


class DeezerSearch(SaveWebHelper, DeezerWebHelper):
    """
        Search for Deezer
    """

    def __init__(self):
        """
            Init object
        """
        SaveWebHelper.__init__(self)
        DeezerWebHelper.__init__(self)

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
            uri = "https://api.deezer.com/search/album?q=%s" %\
                search
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for albums in decode["data"]:
                    payload = self.lollypop_album_payload(albums)
                    self.save_album_payload_to_db(payload,
                                                  storage_type,
                                                  True,
                                                  cancellable)
        except Exception as e:
            Logger.warning("DeezerSearch::get(): %s", e)
        if not cancellable.is_cancelled():
            emit_signal(self, "finished")

    def load_tracks(self, album, cancellable):
        """
            Load tracks for album
            @param album as Album
            @param cancellable as Gio.Cancellable
        """
        try:
            deezid = album.uri.replace("dz:", "")
            uri = "https://api.deezer.com/album/%s/tracks" %\
                deezid
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                # We want to share the same item as lp_album_id may change
                album_item = album.collection_item
                for track in decode["data"]:
                    lollypop_payload = self.lollypop_track_payload(track)
                    self.save_track_payload_to_db(lollypop_payload,
                                                  album_item,
                                                  album.storage_type,
                                                  False,
                                                  cancellable)
        except Exception as e:
            Logger.error("DeezerSearch::load_tracks(): %s", e)
