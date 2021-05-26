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


from gettext import gettext as _
import itertools

from lollypop.sqlcursor import SqlCursor
from lollypop.define import App, StorageType, Type, LovedFlags
from lollypop.utils import noaccents, make_subrequest


class TracksDatabase:
    """
        All functions take a sqlite cursor as last parameter,
        set another one if you"re in a thread
    """

    def __init__(self, db):
        """
            Init tracks database object
            @param db as database
        """
        self.__db = db

    def add(self, name, uri, duration, tracknumber, discnumber, discname,
            album_id, year, timestamp, popularity, rate, loved, ltime, mtime,
            mb_track_id, lp_track_id, bpm, storage_type):
        """
            Add a new track to database
            @param name as string
            @param uri as string,
            @param duration as int
            @param tracknumber as int
            @param discnumber as int
            @param discname as str
            @param album_id as int
            @param year as int
            @param timestamp as int
            @param popularity as int
            @param rate as int
            @param loved as bool
            @param ltime as int
            @param mtime as int
            @param mb_track_id as str
            @param lp_track_id as str
            @param bpm as double
            @return inserted rowid as int
            @warning: commit needed
        """
        with SqlCursor(self.__db, True) as sql:
            result = sql.execute(
                "INSERT INTO tracks (name, uri, duration, tracknumber,\
                discnumber, discname, album_id,\
                year, timestamp, popularity, rate, loved,\
                ltime, mtime, mb_track_id, lp_track_id, bpm, storage_type)\
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, uri, duration, tracknumber, discnumber,
                 discname, album_id, year, timestamp, popularity,
                 rate, loved, ltime, mtime, mb_track_id, lp_track_id,
                 bpm, storage_type))
            return result.lastrowid

    def add_artist(self, track_id, artist_id):
        """
            Add artist to track
            @param track_id as int
            @param artist_id as int
            @warning: commit needed
        """
        with SqlCursor(self.__db, True) as sql:
            artists = self.get_artist_ids(track_id)
            if artist_id not in artists:
                sql.execute("INSERT INTO "
                            "track_artists (track_id, artist_id)"
                            "VALUES (?, ?)", (track_id, artist_id))

    def add_genre(self, track_id, genre_id):
        """
            Add genre to track
            @param track_id as int
            @param genre_id as int
            @warning: commit needed
        """
        with SqlCursor(self.__db, True) as sql:
            genres = self.get_genre_ids(track_id)
            if genre_id not in genres:
                sql.execute("INSERT INTO\
                             track_genres (track_id, genre_id)\
                             VALUES (?, ?)",
                            (track_id, genre_id))

    def get_ids(self, storage_type, skipped):
        """
            Return all internal track ids
            @param storage_type as StorageType
            @param skipped as bool
            @return track ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = (storage_type,)
            request = "SELECT rowid FROM tracks\
                       WHERE storage_type & ?"
            if not skipped:
                request += " AND not loved &? "
                filters += (LovedFlags.SKIPPED,)
            request += " ORDER BY album_id"
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def get_ids_for_name(self, name):
        """
            Return tracks ids with name
            @param name as str
            @return track id as [int]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT rowid\
                                  FROM tracks WHERE noaccents(name)=?\
                                  COLLATE NOCASE",
                                 (noaccents(name),))
            return list(itertools.chain(*result))

    def get_id_by_uri(self, uri):
        """
            Return track id for uri
            @param uri as str
            @return track id as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT rowid FROM tracks WHERE uri=?",
                                 (uri,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_id_by_basename_duration(self, basename, duration):
        """
            Get track id by basename
            @param basename as str
            @param duration as int
            @return track_id as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT rowid FROM tracks\
                                  WHERE uri like ? AND duration=?",
                                 ("%" + basename, duration))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_name(self, track_id):
        """
            Get track name for track id
            @param track_id as int
            @return Name as string
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT name FROM tracks WHERE rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return ""

    def get_year(self, track_id):
        """
            Get track year
            @param track_id as int
            @return year as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT year FROM tracks WHERE rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v and v[0]:
                return v[0]
            return None

    def get_storage_type(self, track_id):
        """
            Get storage type
            @param track_id as int
            @return int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT storage_type FROM tracks WHERE\
                                 rowid=?", (track_id,))

            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_timestamp(self, track_id):
        """
            Get track timestamp
            @param track_id as int
            @return timestamp as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT timestamp FROM tracks WHERE rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v and v[0]:
                return v[0]
            return None

    def get_timestamp_for_album(self, album_id):
        """
            Get album timestamp based on tracks
            Use most used timestamp by tracks
            @param album_id as int
            @return int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT timestamp,\
                                  COUNT(timestamp) AS occurrence\
                                  FROM tracks\
                                  WHERE tracks.album_id=?\
                                  GROUP BY timestamp\
                                  ORDER BY occurrence DESC\
                                  LIMIT 1", (album_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_rate(self, track_id):
        """
            Get track rate
            @param track_id as int
            @return rate as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT rate FROM tracks WHERE rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v:
                return v[0]
            return 0

    def get_uri(self, track_id):
        """
            Get track uri for track id
            @param track_id as int
            @return uri as string
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT uri FROM tracks WHERE rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return ""

    def set_uri(self, track_id, uri):
        """
            Set track uri
            @param track_id as int
            @param uri as string
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks SET uri=?\
                         WHERE rowid=?",
                        (uri, track_id))

    def set_storage_type(self, track_id, storage_type):
        """
            Set storage type
            @param track_id as int
            @param storage_type as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks SET storage_type=?\
                         WHERE rowid=?",
                        (storage_type, track_id))

    def set_rate(self, track_id, rate):
        """
            Set track rate
            @param track_id as int
            @param rate as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks SET rate=?\
                         WHERE rowid=?",
                        (rate, track_id))

    def get_album_id(self, track_id):
        """
            Get album id for track id
            @param track_id as int
            @return album id as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT album_id FROM tracks WHERE rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return -1

    def get_mb_track_id(self, track_id):
        """
            Get MusicBrainz recording id for track id
            @param track_id as int
            @return recording id as str
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT mb_track_id FROM tracks\
                                  WHERE rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return ""

    def get_id_for_lp_track_id(self, lp_track_id):
        """
            Get track id for Lollypop recording id
            @param Lollypop id as str
            @return track id as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT rowid FROM tracks\
                                  WHERE lp_track_id=?", (lp_track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return -1

    def get_album_name(self, track_id):
        """
            Get album name for track id
            @param track_id as int
            @return album name as str
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT albums.name from albums,tracks\
                                  WHERE tracks.rowid=? AND\
                                  tracks.album_id=albums.rowid", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return _("Unknown")

    def get_artist_ids(self, track_id):
        """
            Get artist ids
            @param track_id as int
            @return artist ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT artist_id FROM track_artists\
                                  WHERE track_id=?", (track_id,))
            return list(itertools.chain(*result))

    def get_mb_artist_ids(self, track_id):
        """
            Get MusicBrainz artist ids
            @param track_id as int
            @return artist ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT mb_artist_id\
                                  FROM artists, track_artists\
                                  WHERE track_artists.track_id=?\
                                  AND track_artists.artist_id=artists.rowid",
                                 (track_id,))
            return list(itertools.chain(*result))

    def get_artists(self, track_id):
        """
            Get artist names
            @param track_id as int
            @return artists as [str]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT name FROM artists, track_artists\
                                  WHERE track_artists.track_id=?\
                                  AND track_artists.artist_id=artists.rowid",
                                 (track_id,))
            return list(itertools.chain(*result))

    def get_album_genre_ids(self, album_id):
        """
            Get album genre ids based on tracks
            @param album_id as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT track_genres.genre_id\
                                  FROM tracks, track_genres\
                                  WHERE tracks.album_id=? AND\
                                  track_genres.track_id=tracks.rowid",
                                 (album_id,))
            return list(itertools.chain(*result))

    def get_genre_ids(self, track_id):
        """
            Get genre ids
            @param track_id as int
            @return genre ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT genre_id FROM track_genres\
                                  WHERE track_id=?", (track_id,))
            return list(itertools.chain(*result))

    def get_genres(self, track_id):
        """
            Get genres
            @param track_id as int
            @return [str]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT name FROM genres, track_genres\
                                  WHERE track_genres.track_id=?\
                                  AND track_genres.genre_id=genres.rowid",
                                 (track_id,))
            return list(itertools.chain(*result))

    def get_mtimes(self):
        """
            Get mtime for tracks
            @return dict of {uri as string: mtime as int}
        """
        with SqlCursor(self.__db) as sql:
            mtimes = {}
            result = sql.execute("SELECT DISTINCT uri, mtime\
                                  FROM tracks WHERE storage_type & ?",
                                 (StorageType.COLLECTION,))
            for row in result:
                mtimes.update((row,))
            return mtimes

    def remove_album(self, album_id, commit=True):
        """
            Remove album
            @param album_id as int
            @param commit as bool
        """
        with SqlCursor(self.__db, commit) as sql:
            sql.execute("DELETE FROM tracks WHERE album_id=?", (album_id,))

    def del_non_persistent(self, commit=True):
        """
            Delete non persistent tracks
            @param commit as bool
        """
        with SqlCursor(self.__db, commit) as sql:
            sql.execute("DELETE FROM tracks WHERE storage_type & ?",
                        (StorageType.EPHEMERAL | StorageType.EXTERNAL,))

    def del_persistent(self, commit=True):
        """
            Delete persistent tracks
            @param commit as bool
        """
        with SqlCursor(self.__db, commit) as sql:
            sql.execute("DELETE FROM tracks WHERE storage_type & ?",
                        (StorageType.COLLECTION,))

    def get_uris(self, uris_concerned=None):
        """
            Get all tracks uri
            @param uris_concerned as [uri as str]
            @return [str]
        """
        with SqlCursor(self.__db) as sql:
            uris = []
            if uris_concerned:
                for uri in uris_concerned:
                    result = sql.execute("SELECT uri\
                                          FROM tracks\
                                          WHERE uri LIKE ? AND\
                                          storage_type & ?",
                                         (uri + "%", StorageType.COLLECTION))
                    uris += list(itertools.chain(*result))
            else:
                result = sql.execute("SELECT uri FROM tracks\
                                      WHERE  storage_type & ?",
                                     (StorageType.COLLECTION,))
                uris = list(itertools.chain(*result))
            return uris

    def get_number(self, track_id):
        """
            Get track position in album
            @param track_id as int
            @return position as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT tracknumber FROM tracks\
                                  WHERE rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_lp_track_id(self, track_id):
        """
            Get Lollypop id
            @param track_id as int
            @return str
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT lp_track_id FROM\
                                  tracks where rowid=?",
                                 (track_id,))
            v = result.fetchone()
            if v and v[0]:
                return v[0]
            return ""

    def get_discnumber(self, track_id):
        """
            Get disc number for track id
            @param track_id as int
            @return discnumber as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT discnumber FROM tracks\
                                  WHERE rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_discname(self, track_id):
        """
            Get disc name for track id
            @param track_id as int
            @return discname as str
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT discname FROM tracks\
                                  WHERE rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return ""

    def get_duration(self, track_id):
        """
            Get track duration for track id
            @param track_id as int
            @return duration as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT duration FROM tracks\
                                  WHERE rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def set_duration(self, track_id, duration):
        """
            Get track duration for track id
            @param track_id as int
            @param duration as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks\
                         SET duration=?\
                         WHERE rowid=?", (duration, track_id,))

    def set_mtime(self, track_id, mtime):
        """
            Set track_mtime
            @param track_id as int
            @param mtime as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks SET mtime=? WHERE rowid=?",
                        (mtime, track_id))

    def is_empty(self):
        """
            Return True if no tracks in db
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT COUNT(1) FROM tracks  LIMIT 1")
            v = result.fetchone()
            if v is not None:
                return v[0] == 0
            return True

    def get_loved_track_ids(self, artist_ids, storage_type):
        """
            Get loved track ids
            @param storage_type as StorageType
            @return [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = (LovedFlags.LOVED, storage_type)
            request = "SELECT tracks.rowid\
                       FROM tracks, album_artists, artists\
                       WHERE loved=? AND\
                       artists.rowid=album_artists.artist_id AND\
                       tracks.album_id=album_artists.album_id AND\
                       storage_type & ?"
            if artist_ids:
                filters += tuple(artist_ids)
                request += " AND "
                request += make_subrequest("album_artists.artist_id=?",
                                           "OR",
                                           len(artist_ids))
            request += " ORDER BY artists.name"
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def get_populars(self, artist_ids, storage_type, skipped, limit):
        """
            Return populars tracks
            @param artist_ids as int
            @param storage_type as StorageType
            @param skipped as bool
            @param limit as int
            @return track ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = (storage_type,)
            request = "SELECT tracks.rowid FROM"
            if artist_ids:
                request += " tracks, track_artists "
            else:
                request += " tracks "
            request += "WHERE rate >= 4 AND storage_type & ?"
            if artist_ids:
                filters += tuple(artist_ids)
                request += " AND track_artists.track_id=tracks.rowid AND"
                request += make_subrequest("track_artists.artist_id=?",
                                           "OR",
                                           len(artist_ids))
            if not skipped:
                request += " AND not loved &? "
                filters += (LovedFlags.SKIPPED,)
            filters += (limit,)
            request += " ORDER BY popularity DESC LIMIT ?"
            result = sql.execute(request, filters)
            track_ids = list(itertools.chain(*result))
            if len(track_ids) < limit:
                filters = (storage_type,)
                request = "SELECT tracks.rowid FROM"
                if artist_ids:
                    request += " tracks, track_artists "
                else:
                    request += " tracks "
                request += "WHERE popularity!=0 AND\
                            storage_type & ?"
                if artist_ids:
                    filters += tuple(artist_ids)
                    request += " AND track_artists.track_id=tracks.rowid AND"
                    request += make_subrequest("track_artists.artist_id=?",
                                               "OR",
                                               len(artist_ids))
                if not skipped:
                    request += " AND not loved &? "
                    filters += (LovedFlags.SKIPPED,)
                filters += (limit,)
                request += " ORDER BY popularity DESC LIMIT ?"
                result = sql.execute(request, filters)
                track_ids += list(itertools.chain(*result))
            return list(set(track_ids))

    def get_higher_popularity(self):
        """
            Get higher available popularity
            @return int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT popularity\
                                  FROM tracks\
                                  ORDER BY POPULARITY DESC LIMIT 1")
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_avg_popularity(self):
        """
            Return avarage popularity
            @return avarage popularity as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT AVG(popularity)\
                                  FROM (SELECT popularity\
                                        FROM tracks\
                                        ORDER BY POPULARITY DESC LIMIT 100)")
            v = result.fetchone()
            if v and v[0] is not None and v[0] > 5:
                return v[0]
            return 5

    def set_more_popular(self, track_id):
        """
            Increment popularity field
            @param track_id as int
            @raise sqlite3.OperationalError on db update
        """
        with SqlCursor(self.__db, True) as sql:
            result = sql.execute("SELECT popularity from tracks WHERE rowid=?",
                                 (track_id,))
            pop = result.fetchone()
            if pop:
                current = pop[0]
            else:
                current = 0
            current += 1
            sql.execute("UPDATE tracks set popularity=? WHERE rowid=?",
                        (current, track_id))

    def set_listened_at(self, track_id, time):
        """
            Set ltime for track
            @param track_id as int
            @param time as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks set ltime=? WHERE rowid=?",
                        (time, track_id))

    def get_little_played(self, storage_type, skipped, limit):
        """
            Return random tracks little played
            @param storage_type as StorageType
            @param skipped as bool
            @param limit as int
            @return tracks as [int]
        """
        with SqlCursor(self.__db) as sql:
            request = "SELECT rowid FROM tracks WHERE storage_type & ?"
            if not skipped:
                request += " AND loved !=-1 "
            request += " ORDER BY ltime, random() LIMIT ?"
            result = sql.execute(request, (storage_type, limit))
            return list(itertools.chain(*result))

    def get_recently_listened_to(self, storage_type, skipped, limit):
        """
            Return tracks listened recently
            @param storage_type as StorageType
            @param skipped as bool
            @param limit as int
            @return tracks as [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = (storage_type,)
            request = "SELECT tracks.rowid FROM tracks\
                       WHERE ltime!=0 AND storage_type & ?"
            if not skipped:
                request += " AND not loved &? "
                filters += (LovedFlags.SKIPPED,)
            request += " ORDER BY ltime DESC LIMIT ?"
            filters += (limit,)
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def get_skipped(self, storage_type):
        """
            Return skipped tracks
            @param storage_type as StorageType
            @return tracks as [int]
        """
        with SqlCursor(self.__db) as sql:
            request = "SELECT rowid FROM tracks\
                       WHERE loved & ? AND storage_type & ?"
            result = sql.execute(request, (LovedFlags.SKIPPED, storage_type))
            return list(itertools.chain(*result))

    def get_randoms(self, genre_ids, storage_type, skipped, limit):
        """
            Return random tracks
            @param genre_ids as [int]
            @param storage_type as StorageType
            @parma skipped as bool
            @param limit as int
            @return track ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = (storage_type,)
            request = "SELECT tracks.rowid FROM tracks"
            if genre_ids:
                request += ",track_genres"
            request += " WHERE storage_type & ? "
            if not skipped:
                request += " AND not loved &? "
                filters += (LovedFlags.SKIPPED,)
            if genre_ids:
                request += "AND tracks.rowid=track_genres.track_id"
                filters += tuple(genre_ids)
                request += " AND "
                request += make_subrequest("track_genres.genre_id=?",
                                           "OR",
                                           len(genre_ids))
            request += " ORDER BY random() LIMIT ?"
            filters += (limit,)
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def set_popularity(self, track_id, popularity):
        """
            Set popularity
            @param track_id as int
            @param popularity as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks set popularity=? WHERE rowid=?",
                        (popularity, track_id))

    def get_popularity(self, track_id):
        """
            Get popularity
            @param track_id  as int
            @return popularity as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT popularity FROM tracks WHERE\
                                 rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_loved(self, track_id):
        """
            Get track loved status
            @param track_id as int
            @return loved as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT loved FROM tracks WHERE\
                                 rowid=?", (track_id,))

            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_year_for_album(self, album_id, disc_number=None):
        """
            Get album year based on tracks
            Use most used year by tracks
            @param album_id as int
            @param disc_number as int/None
            @return int
        """
        with SqlCursor(self.__db) as sql:
            filters = (album_id,)
            request = "SELECT year, COUNT(year) AS occurrence FROM tracks\
                       WHERE tracks.album_id=?"
            if disc_number is not None:
                filters += (disc_number,)
                request += " AND tracks.discnumber=?"
            request += " GROUP BY year\
                        ORDER BY occurrence DESC"
            result = sql.execute(request, filters)
            v = list(result)
            # Ignore album with multiple original date
            if len(v) == 1:
                return v[0][0]
            return None

    def get_ltime(self, track_id):
        """
            Get listen time
            @param track_id  as int
            @return listen time as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT ltime FROM tracks WHERE\
                                 rowid=?", (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_mtime(self, track_id):
        """
            Get modification time
            @param track_id as int
            @return modification time as int
        """
        with SqlCursor(self.__db) as sql:
            request = "SELECT mtime FROM tracks\
                       WHERE tracks.rowid=?"
            result = sql.execute(request, (track_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def get_years(self, storage_type):
        """
            Return all tracks years and if unknown years exist
            @param storage_type as StorageType
            @return ([int], bool)
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT tracks.year\
                                  FROM tracks\
                                  WHERE storage_type & ?",
                                 (storage_type,))
            years = []
            unknown = False
            for year in list(itertools.chain(*result)):
                if year is None:
                    unknown = True
                elif year not in years:
                    years.append(year)
            return (years, unknown)

    def get_albums_by_disc_for_year(self, year, storage_type,
                                    skipped, limit=-1):
        """
            Return albums for year
            @param year as int
            @param storage_type as StorageType
            @param skipped as bool
            @param limit as int
            @return discs [(int, int)]
        """
        with SqlCursor(self.__db) as sql:
            order = " ORDER BY artists.sortname\
                     COLLATE NOCASE COLLATE LOCALIZED,\
                     tracks.timestamp,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED LIMIT ?"
            request = "SELECT DISTINCT tracks.album_id,\
                       discnumber,\
                       discname,\
                       albums.year\
                       FROM albums, tracks, album_artists, artists\
                       WHERE albums.rowid=album_artists.album_id AND\
                       artists.rowid=album_artists.artist_id AND\
                       tracks.album_id=albums.rowid AND\
                       tracks.year=? AND albums.storage_type & ?"
            filters = (year, storage_type)
            if not skipped:
                request += " AND not albums.loved &? "
                filters += (LovedFlags.SKIPPED,)
            filters += (limit,)
            request += " GROUP BY tracks.album_id"
            request += order
            result = sql.execute(request, filters)
            return list(result)

    def get_compilations_by_disc_for_year(self, year, storage_type,
                                          skipped, limit=-1):
        """
            Return compilations for year
            @param year as int
            @param storage_type as StorageType
            @param skipped as bool
            @param limit as int
            @return discs [(int, int)]
        """
        with SqlCursor(self.__db) as sql:
            order = " ORDER BY albums.timestamp, albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED LIMIT ?"
            request = "SELECT DISTINCT tracks.album_id,\
                       discnumber,\
                       discname,\
                       albums.year\
                       FROM albums, album_artists, tracks\
                       WHERE album_artists.artist_id=?\
                       AND album_artists.album_id=albums.rowid\
                       AND tracks.album_id=albums.rowid\
                       AND albums.storage_type & ?\
                       AND tracks.year=?"
            filters = (Type.COMPILATIONS, storage_type, year)
            if not skipped:
                request += " AND not albums.loved &? "
                filters += (LovedFlags.SKIPPED,)
            filters += (limit,)
            request += " GROUP BY tracks.album_id"
            request += order
            result = sql.execute(request, filters)
            return list(result)

    def set_lp_track_id(self, track_id, lp_track_id):
        """
            Set lp track id
            @param album_id as int
            @param lp_album_id as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks SET lp_track_id=? WHERE rowid=?",
                        (lp_track_id, track_id))

    def set_loved(self, track_id, loved):
        """
            Set track loved
            @param track_id as int
            @param loved as int
            @warning: commit needed
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE tracks SET loved=? WHERE rowid=?",
                        (loved, track_id))

    def count(self):
        """
            Count tracks
            @return int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT COUNT(1) FROM tracks\
                                  WHERE storage_type & ?",
                                 (StorageType.COLLECTION | StorageType.SAVED,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def clean(self, commit=True):
        """
            Clean database for track id
            @param commit as bool
        """
        with SqlCursor(self.__db, commit) as sql:
            sql.execute("DELETE FROM track_artists\
                         WHERE track_artists.track_id NOT IN (\
                            SELECT tracks.rowid FROM tracks)")
            sql.execute("DELETE FROM track_genres\
                         WHERE track_genres.track_id NOT IN (\
                            SELECT tracks.rowid FROM tracks)")

    def search(self, searched, storage_type):
        """
            Search for tracks looking like searched
            @param searched as str without accents
            @param storage_type as StorageType
            @return [(int, name)]
        """
        with SqlCursor(self.__db) as sql:
            filters = ("%" + searched + "%", storage_type)
            request = "SELECT rowid, name FROM tracks\
                       WHERE noaccents(name) LIKE ?\
                       AND tracks.storage_type & ? LIMIT 25"
            result = sql.execute(request, filters)
            return list(result)

    def search_performed(self, searched, storage_type):
        """
            Search tracks looking like searched with performers
            @param searched as str without accents
            @param storage_type as StorageType
            @return [(int, name)]
        """
        with SqlCursor(self.__db) as sql:
            filters = ("%" + searched + "%", storage_type)
            request = "SELECT DISTINCT tracks.rowid, artists.name\
                   FROM track_artists, tracks, artists\
                   WHERE track_artists.artist_id=artists.rowid AND\
                   track_artists.track_id=tracks.rowid AND\
                   noaccents(artists.name) LIKE ? AND\
                   tracks.storage_type & ? AND NOT EXISTS (\
                        SELECT album_artists.artist_id\
                        FROM album_artists\
                        WHERE album_artists.artist_id=artists.rowid)\
                    LIMIT 25"
            result = sql.execute(request, filters)
            return list(result)

    def search_track(self, artist, title):
        """
            Get track id for artist and title
            @param artist as string
            @param title as string
            @return track id as int
        """
        artist = noaccents(artist.lower())
        track_ids = self.get_ids_for_name(title)
        for track_id in track_ids:
            album_id = App().tracks.get_album_id(track_id)
            artist_ids = set(App().albums.get_artist_ids(album_id)) &\
                set(App().tracks.get_artist_ids(track_id))
            for artist_id in artist_ids:
                db_artist = noaccents(
                    App().artists.get_name(artist_id).lower())
                if artist.find(db_artist) != -1 or\
                        db_artist.find(artist) != -1:
                    return track_id
            artists = ", ".join(App().tracks.get_artists(track_id)).lower()
            if noaccents(artists) == artist:
                return track_id
        return None

    def remove(self, track_id):
        """
            Remove track
            @param track_id as int
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("DELETE FROM track_genres\
                         WHERE track_id=?", (track_id,))
            sql.execute("DELETE FROM track_artists\
                         WHERE track_id=?", (track_id,))
            sql.execute("DELETE FROM tracks\
                         WHERE rowid=?", (track_id,))
