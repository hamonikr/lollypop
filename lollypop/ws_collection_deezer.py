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
from lollypop.helper_web_deezer import DeezerWebHelper
from lollypop.define import App, StorageType


class DeezerCollectionWebService(DeezerWebHelper):
    """
        Add items to collection with Deezer
        Depends on SaveWebHelper
    """
    def __init__(self):
        """
            Init object
        """
        DeezerWebHelper.__init__(self)

    def search_charts(self, cancellable):
        """
            Add charts to DB
            @param cancellable as Gio.Cancellable
        """
        Logger.info("Get charts with Deezer")
        try:
            album_ids = []
            uri = "https://api.deezer.com/chart/0/albums?limit=30"
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                for album in decode["data"]:
                    album_ids.append(album["id"])
            for album_id in album_ids:
                if cancellable.is_cancelled():
                    raise Exception("Cancelled")
                payload = DeezerWebHelper.get_album_payload(
                    self, album_id, cancellable)
                if payload is None:
                    continue
                lollypop_payload = DeezerWebHelper.lollypop_album_payload(
                    self, payload)
                self.save_album_payload_to_db(lollypop_payload,
                                              StorageType.DEEZER_CHARTS,
                                              True,
                                              cancellable)
        except Exception as e:
            Logger.warning(
                "DeezerCollectionWebService::search_charts(): %s", e)
