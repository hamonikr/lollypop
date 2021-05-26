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


class CollectionItem:
    """
        A collection item with an track id and associated album/genres/artists
    """

    def __init__(self, track_id=None, album_id=None, new_album=False,
                 genres=None, genre_ids=[], new_genre_ids=[], artist_ids=[],
                 new_artist_ids=[], album_artist_ids=[],
                 new_album_artist_ids=[], album_name="", track_name="",
                 album_artists="", artists="", aa_sortnames="", a_sortnames="",
                 year=None, timestamp=None,
                 original_year=None, original_timestamp=None,
                 mb_album_artist_id="",
                 mb_album_id=None, mb_artist_id="", mb_track_id=None,
                 lp_album_id=None, uri="", album_loved=False,
                 album_pop=0, album_rate=0, album_synced=0,
                 album_mtime=0, duration=0, tracknumber=0,
                 discnumber=1, discname="", track_mtime=0, track_pop=0,
                 track_rate=0, track_loved=False, track_ltime=0, bpm=0,
                 compilation=False,
                 storage_type=0):
        """
            Init item
            @param track_id as int
            @param album_id as int
            @param new_album as bool
            @param genres as str
            @param genre_ids as [int]
            @param new_genre_ids as [int]
            @param artist_ids as [int]
            @param new_artist_ids as [int]
            @param album_artist_ids as [int]
            @param new_album_artist_ids as [int]
            @param album_name as str
            @param track_name as str
            @param album_artists as str
            @param artists as str
            @param aa_sortnames as str
            @param a_sortnames as str
            @param year as int
            @param timestamp as int
            @param original_year as int
            @param original_timestamp as int
            @param mb_album_artist_id as str
            @param mb_album_id as str
            @param mb_artist_id as str
            @param mb_track_id as str
            @param lp_album_id as str
            @param uri as str
            @param album_loved as bool
            @param album_pop as int
            @param album_rate as int
            @param album_synced as bool
            @param album_mtime as int
            @param duration as int
            @param tracknumber as int
            @param discnumber as int
            @param discname as str
            @param track_mtime as int
            @param track_pop as int
            @param track_rate as int
            @param track_loved as bool
            @param track_ltime as int
            @param bpm as int
            @param compilation as bool
            @param storage_type as StorageType
        """
        self.track_id = track_id
        self.album_id = album_id
        self.new_album = new_album
        self.genres = genres
        self.genre_ids = genre_ids
        self.new_genre_ids = new_genre_ids
        self.artist_ids = artist_ids
        self.new_artist_ids = new_artist_ids
        self.album_artist_ids = album_artist_ids
        self.new_album_artist_ids = new_album_artist_ids
        self.album_name = album_name
        self.track_name = track_name
        self.album_artists = album_artists
        self.artists = artists
        self.aa_sortnames = aa_sortnames
        self.a_sortnames = a_sortnames
        self.year = year
        self.timestamp = timestamp
        self.original_year = original_year
        self.original_timestamp = original_timestamp
        self.mb_album_artist_id = mb_album_artist_id
        self.mb_album_id = mb_album_id
        self.mb_artist_id = mb_artist_id
        self.mb_track_id = mb_track_id
        self.lp_album_id = lp_album_id
        self.uri = uri
        self.album_loved = album_loved
        self.album_pop = album_pop
        self.album_rate = album_rate
        self.album_synced = album_synced
        self.album_mtime = album_mtime
        self.duration = duration
        self.tracknumber = tracknumber
        self.discnumber = discnumber
        self.discname = discname
        self.track_mtime = track_mtime
        self.track_pop = track_pop
        self.track_rate = track_rate
        self.track_loved = track_loved
        self.track_ltime = track_ltime
        self.bpm = bpm
        self.compilation = compilation
        self.storage_type = storage_type
