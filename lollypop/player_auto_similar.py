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

from gi.repository import Gio

from random import shuffle

from lollypop.objects_album import Album
from lollypop.objects_track import Track
from lollypop.logger import Logger
from lollypop.define import App, Repeat, StorageType
from lollypop.utils import sql_escape, get_network_available
from lollypop.utils import get_default_storage_type, emit_signal
from lollypop.utils_album import tracks_to_albums


class AutoSimilarPlayer:
    """
        Manage playback when going to end
    """

    def __init__(self):
        """
            Init player
        """
        self.__next_cancellable = Gio.Cancellable()
        self.__radio_cancellable = Gio.Cancellable()
        self.connect("next-changed", self.__on_next_changed)

    def next_album(self):
        """
            Get next album to add
            @return Album
        """
        genre_ids = App().artists.get_genre_ids(self.current_track.artist_ids,
                                                StorageType.COLLECTION)
        track_ids = App().tracks.get_randoms(genre_ids,
                                             StorageType.COLLECTION,
                                             1,
                                             100)
        if track_ids:
            return Track(track_ids[0]).album
        return None

    def play_radio_from_collection(self, artist_ids):
        """
            Play a radio from collection for artist ids
            @param artist_ids as [int]
        """
        genre_ids = App().artists.get_genre_ids(artist_ids,
                                                StorageType.COLLECTION)
        track_ids = App().tracks.get_randoms(genre_ids,
                                             StorageType.COLLECTION,
                                             False,
                                             100)
        albums = tracks_to_albums(
            [Track(track_id) for track_id in track_ids], False)
        self.play_albums(albums)

    def play_radio_from_spotify(self, artist_ids):
        """
            Play a radio from the Spotify for artist ids
            @param artist_ids as [int]
        """
        self.__play_radio_common()
        if get_network_available("SPOTIFY") and\
                get_network_available("YOUTUBE"):
            from lollypop.similars_spotify import SpotifySimilars
            similars = SpotifySimilars()
            self.__load_similars(similars, artist_ids)

    def play_radio_from_lastfm(self, artist_ids):
        """
            Play a radio from the Last.fm for artist ids
            @param artist_ids as [int]
        """
        self.__play_radio_common()
        if get_network_available("LASTFM") and\
                get_network_available("YOUTUBE"):
            from lollypop.similars_lastfm import LastFMSimilars
            similars = LastFMSimilars()
            self.__load_similars(similars, artist_ids)

    def play_radio_from_deezer(self, artist_ids):
        """
            Play a radio from the Last.fm for artist ids
            @param artist_ids as [int]
        """
        self.__play_radio_common()
        if get_network_available("DEEZER") and\
                get_network_available("YOUTUBE"):
            from lollypop.similars_deezer import DeezerSimilars
            similars = DeezerSimilars()
            self.__load_similars(similars, artist_ids)

    def play_radio_from_loved(self, artist_ids):
        """
            Play a radio from artists loved tracks
            @param artist_ids as [int]
        """
        track_ids = App().tracks.get_loved_track_ids(artist_ids,
                                                     StorageType.ALL)
        shuffle(track_ids)
        albums = tracks_to_albums([Track(track_id) for track_id in track_ids])
        App().player.play_albums(albums)

    def play_radio_from_populars(self, artist_ids):
        """
            Play a radio from artists popular tracks
            @param artist_ids as [int]
        """
        track_ids = App().tracks.get_populars(artist_ids, StorageType.ALL,
                                              False, 100)
        shuffle(track_ids)
        albums = tracks_to_albums([Track(track_id) for track_id in track_ids])
        App().player.play_albums(albums)

    @property
    def radio_cancellable(self):
        """
            Get cancellable
            @return Gio.Cancellable
        """
        return self.__radio_cancellable

#######################
# PROTECTED           #
#######################
    def _on_stream_start(self, bus, message):
        """
            Cancel radio loading if current not a web track
            @param bus as Gst.Bus
            @param message as Gst.Message
        """
        if not self.current_track.is_web:
            self.__radio_cancellable.cancel()

#######################
# PRIVATE             #
#######################
    def __load_similars(self, similars, artist_ids):
        """
            Load similars for artist ids
            @param similars as Similars
            @param artist ids as [int]
        """
        similars.connect("match-track", self.__on_match_track)
        similars.connect("finished", self.__on_finished)
        self.clear_albums()
        App().task_helper.run(similars.load_similars,
                              artist_ids,
                              StorageType.EPHEMERAL,
                              self.__radio_cancellable)

    def __play_radio_common(self):
        """
            Emit signal and reset cancellable
        """
        emit_signal(self, "loading-changed", True, Track())
        self.__radio_cancellable.cancel()
        self.__radio_cancellable = Gio.Cancellable()

    def __get_album_from_artists(self,  similar_artist_ids):
        """
            Add a new album to playback
            @param similar_artist_ids as [int]
            @return Album
        """
        # Get an album
        storage_type = get_default_storage_type()
        album_ids = App().albums.get_ids(
            [], similar_artist_ids, storage_type, False)
        shuffle(album_ids)
        while album_ids:
            album_id = album_ids.pop(0)
            if album_id not in self.album_ids:
                return Album(album_id, [], [], False)
        return None

    def __get_artist_ids(self, artists):
        """
            Get valid artist ids from list
            @param artists as []
            @return [int]
        """
        similar_artist_ids = []
        for (artist, cover_uri) in artists:
            if self.__next_cancellable.is_cancelled():
                return []
            similar_artist_id = App().artists.get_id_for_escaped_string(
                sql_escape(artist.lower()))
            if similar_artist_id is not None:
                if App().artists.has_albums(similar_artist_id):
                    similar_artist_ids.append(similar_artist_id)
        return similar_artist_ids

    def __on_get_artist_ids(self, similar_artist_ids, remote):
        """
            Get one albums from artist ids
            @param similar_artist_ids as [int]
            @param remote as bool
        """
        if self.__next_cancellable.is_cancelled():
            return
        album = None
        if similar_artist_ids:
            album = self.__get_album_from_artists(similar_artist_ids)
        if album is not None:
            Logger.info("Found a similar album")
            self.add_album(album)
        elif remote:
            from lollypop.similars_local import LocalSimilars
            similars = LocalSimilars()
            App().task_helper.run(
                similars.get_similar_artists,
                App().player.current_track.artist_ids,
                self.__next_cancellable,
                callback=(self.__on_get_local_similar_artists,))

    def __on_get_local_similar_artists(self, artists):
        """
            Add one album from artists to player
            @param artists as []
        """
        if self.__next_cancellable.is_cancelled():
            return
        App().task_helper.run(self.__get_artist_ids, artists,
                              callback=(self.__on_get_artist_ids, False))

    def __on_get_similar_artists(self, artists):
        """
            Add one album from artists to player
            @param artists as []
        """
        if self.__next_cancellable.is_cancelled():
            return
        App().task_helper.run(self.__get_artist_ids, artists,
                              callback=(self.__on_get_artist_ids, True))

    def __on_next_changed(self, player):
        """
            Add a new album if playback finished and wanted by user
        """
        self.__next_cancellable.cancel()
        # Do not load an album if a radio is loading
        if not self.__radio_cancellable.is_cancelled() or not self._albums:
            return
        self.__next_cancellable = Gio.Cancellable()
        # Check if we need to add a new album
        if App().settings.get_enum("repeat") == Repeat.AUTO_SIMILAR and\
                player.next_track.id is None and\
                player.current_track.id is not None and\
                player.current_track.id >= 0 and\
                player.current_track.artist_ids:
            from lollypop.similars import Similars
            similars = Similars()
            App().task_helper.run(
                similars.get_similar_artists,
                player.current_track.artist_ids,
                self.__next_cancellable,
                callback=(self.__on_get_similar_artists,))

    def __on_match_track(self, similars, track_id, storage_type):
        """
            Load/Play track album
            @param similars as Similars
            @param track_id as int
            @param storage_type as StorageType
        """
        track = Track(track_id)
        album = track.album
        if self.albums:
            self.add_album(album)
        else:
            self.play_album(album)

    def __on_finished(self, similars):
        """
            Cancel radio loading
            @param similars as Similars
        """
        self.__radio_cancellable.cancel()
