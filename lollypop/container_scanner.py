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

from lollypop.define import App, SelectionListMask, Type, ScanUpdate
from lollypop.utils import get_default_storage_type


class ScannerContainer:
    """
        Scanner management for main view
    """

    def __init__(self):
        """
            Init container
        """
        App().scanner.connect("updated", self.__on_collection_updated)

############
# PRIVATE  #
############
    def __handle_genre_update(self, genre_id, scan_update):
        """
            Add genre to genre list
            @param genre_id as int
            @param scan_update as ScanUpdate
        """
        if Type.GENRES_LIST in self.sidebar.selected_ids:
            storage_type = get_default_storage_type()
            if scan_update == ScanUpdate.ADDED:
                genre_name = App().genres.get_name(genre_id)
                self.left_list.add_value((genre_id, genre_name, genre_name))
            elif not App().artists.get_ids([genre_id], storage_type):
                self.left_list.remove_value(genre_id)

    def __handle_artist_update(self, artist_id, scan_update):
        """
            Add/remove artist to/from list
            @param artist_id as int
            @param scan_update as ScanUpdate
        """
        if Type.GENRES_LIST in self.sidebar.selected_ids:
            selection_list = self.right_list
            genre_ids = self.left_list.selected_ids
        elif Type.ARTISTS_LIST in self.sidebar.selected_ids and\
                self.left_list.mask & SelectionListMask.ARTISTS:
            selection_list = self.left_list
            genre_ids = []
        else:
            return
        storage_type = get_default_storage_type()
        artist_ids = App().artists.get_ids(genre_ids, storage_type)
        # We only test add, remove and absent is safe
        if artist_id not in artist_ids and scan_update == ScanUpdate.ADDED:
            return
        artist_name = App().artists.get_name(artist_id)
        sortname = App().artists.get_sortname(artist_id)
        genre_ids = []
        if scan_update == ScanUpdate.ADDED:
            selection_list.add_value((artist_id, artist_name, sortname))
        elif not App().albums.get_ids(
                genre_ids, [artist_id], storage_type, True):
            selection_list.remove_value(artist_id)

    def __on_collection_updated(self, scanner, item, scan_update):
        """
            Update lists based on collection changes
            @param scanner as CollectionScanner
            @param item as CollectionItem
            @param scan_update as ScanUpdate
        """
        for genre_id in item.genre_ids:
            self.__handle_genre_update(genre_id, scan_update)
        for artist_id in item.artist_ids:
            self.__handle_artist_update(artist_id, scan_update)
