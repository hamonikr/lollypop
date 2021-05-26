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

from lollypop.define import App
from lollypop.utils import get_network_available
from lollypop.similars_local import LocalSimilars
from lollypop.similars_spotify import SpotifySimilars
from lollypop.similars_lastfm import LastFMSimilars
from lollypop.similars_deezer import DeezerSimilars


class Similars():
    """
        Search similar artists
    """
    def __init__(self):
        """
            Init similars
        """
        self.__local_helper = LocalSimilars()
        self.__spotify_helper = SpotifySimilars()
        self.__lastfm_helper = LastFMSimilars()
        self.__deezer_helper = DeezerSimilars()

    def get_similar_artists(self, artist_ids, cancellable):
        """
            Get similar artists
            @param artist_ids as [int]
            @param cancellable as Gio.Cancellable
            @return [(str, None)]
        """
        artist_names = []
        result = []
        for artist_id in artist_ids:
            artist_names.append(App().artists.get_name(artist_id))

        if get_network_available("DEEZER"):
            result = self.__deezer_helper.get_similar_artists(
                artist_names, cancellable)
        if not result and get_network_available("SPOTIFY"):
            result = self.__spotify_helper.get_similar_artists(
                artist_names, cancellable)
        if not result and get_network_available("LASTFM"):
            result = self.__lastfm_helper.get_similar_artists(
                artist_names, cancellable)
        if not result:
            result = self.__local_helper.get_similar_artists(
                artist_names, cancellable)
        return result
