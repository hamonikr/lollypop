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

from gi.repository import Gio

from time import time

from lollypop.logger import Logger
from lollypop.sqlcursor import SqlCursor
from lollypop.ws_collection_spotify import SpotifyCollectionWebService
from lollypop.ws_collection_deezer import DeezerCollectionWebService
from lollypop.helper_web_save import SaveWebHelper
from lollypop.define import App, StorageType, NetworkAccessACL


class CollectionWebService(SaveWebHelper,
                           SpotifyCollectionWebService,
                           DeezerCollectionWebService):
    """
        Add items to collection based on current user settings
    """
    MIN_ITEMS_PER_STORAGE_TYPE = 10
    MAX_ITEMS_PER_STORAGE_TYPE = 50
    __METHODS = {
        StorageType.SPOTIFY_SIMILARS:
            SpotifyCollectionWebService.search_similar_albums,
        StorageType.SPOTIFY_NEW_RELEASES:
            SpotifyCollectionWebService.search_new_releases,
        StorageType.DEEZER_CHARTS:
            DeezerCollectionWebService.search_charts
    }

    def __init__(self):
        """
            Init object
        """
        SaveWebHelper.__init__(self)
        SpotifyCollectionWebService.__init__(self)
        DeezerCollectionWebService.__init__(self)
        self.__is_running = False
        self.__cancellable = Gio.Cancellable()

    def start(self):
        """
            Populate DB in a background task
        """
        if self.__is_running:
            return
        App().task_helper.run(self.__populate_db)
        return True

    def stop(self):
        """
            Stop db populate
            @return bool
        """
        self.__cancellable.cancel()
        return not self.__is_running

#######################
# PRIVATE             #
#######################
    def __populate_db(self):
        """
            Populate DB in a background task
        """
        try:
            monitor = Gio.NetworkMonitor.get_default()
            if monitor.get_network_metered():
                return
            Logger.info("Collection download started")
            self.__is_running = True
            self.__cancellable = Gio.Cancellable()
            acl_storage_types = []
            acl = App().settings.get_value("network-access-acl").get_int32()
            mask = App().settings.get_value("suggestions-mask").get_int32()
            if acl & NetworkAccessACL["SPOTIFY"]:
                acl_storage_types += [StorageType.SPOTIFY_SIMILARS,
                                      StorageType.SPOTIFY_NEW_RELEASES]
            if acl & NetworkAccessACL["DEEZER"]:
                acl_storage_types.append(StorageType.DEEZER_CHARTS)
            # Check if storage type needs to be updated
            # Check if albums newer than a week are enough
            timestamp = time() - 604800
            storage_types = []
            for storage_type in acl_storage_types:
                if not mask & storage_type:
                    continue
                newer_albums = App().albums.get_newer_for_storage_type(
                                                           storage_type,
                                                           timestamp)
                if len(newer_albums) < self.MIN_ITEMS_PER_STORAGE_TYPE:
                    storage_types.append(storage_type)
            # Update needed storage types
            if storage_types:
                for storage_type in storage_types:
                    if self.__cancellable.is_cancelled():
                        raise Exception("cancelled")
                    self.__METHODS[storage_type](self, self.__cancellable)
                self.clean_old_albums(storage_types)
                App().artists.update_featuring()
        except Exception as e:
            Logger.warning("CollectionWebService::__populate_db(): %s", e)
        self.__is_running = False
        Logger.info("Collection download finished")

    def clean_old_albums(self, storage_types):
        """
            Clean old albums from DB
            @param storage_types as [StorageType]
        """
        SqlCursor.add(App().db)
        # Remove older albums
        for storage_type in storage_types:
            # If too many albums, do some cleanup
            count = App().albums.get_count_for_storage_type(storage_type)
            diff = count - self.MAX_ITEMS_PER_STORAGE_TYPE
            if diff > 0:
                album_ids = App().albums.get_oldest_for_storage_type(
                    storage_type, diff)
                for album_id in album_ids:
                    # EPHEMERAL with not tracks will be cleaned below
                    App().albums.set_storage_type(album_id,
                                                  StorageType.EPHEMERAL)
                    App().tracks.remove_album(album_id, False)
        # On cancel, clean not needed, done in Application::quit()
        if not self.__cancellable.is_cancelled():
            App().tracks.clean(False)
            App().albums.clean(False)
            App().artists.clean(False)
        SqlCursor.remove(App().db)
