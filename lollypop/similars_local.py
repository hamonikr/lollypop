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

from random import shuffle

from lollypop.define import App, StorageType
from lollypop.logger import Logger


class LocalSimilars:
    """
        Search similar artists locally
    """
    def __init__(self):
        """
            Init provider
        """
        pass

    def get_similar_artists(self, artist_names, cancellable):
        """
            Get similar artists
            @param artist_ids as [int]
            @param cancellable as Gio.Cancellable
            @return [(str, None)]
        """
        artist_ids = []
        for artist_name in artist_names:
            artist_ids.append(App().artists.get_id(artist_name)[0])
        genre_ids = App().artists.get_genre_ids(artist_ids,
                                                StorageType.COLLECTION)
        artists = App().artists.get(genre_ids, StorageType.COLLECTION)
        shuffle(artists)
        result = [(name, None) for (artist_id, name, sortname) in artists]
        if result:
            Logger.info("Found similar artists with LocalSimilars")
        return result
