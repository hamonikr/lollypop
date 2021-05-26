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
from lollypop.define import App, Type, StorageType, OrderBy, LovedFlags
from lollypop.utils import get_default_storage_type, make_subrequest
from lollypop.utils import format_artist_name, remove_static


class ArtistsDatabase:
    """
        Artists database helper
    """

    def __init__(self, db):
        """
            Init artists database object
            @param db as Database
        """
        self.__db = db

    def add(self, name, sortname, mb_artist_id):
        """
            Add a new artist to database
            @param name as string
            @param sortname as string
            @param mb_artist_id as str
            @return inserted rowid as int
            @warning: commit needed
        """
        if sortname == "":
            sortname = format_artist_name(name)
        with SqlCursor(self.__db, True) as sql:
            result = sql.execute("INSERT INTO artists (name, sortname,\
                                  mb_artist_id)\
                                  VALUES (?, ?, ?)",
                                 (name, sortname, mb_artist_id))
            return result.lastrowid

    def set_sortname(self, artist_id, sort_name):
        """
            Set sort name
            @param artist_id as int
            @param sort_name a str
            @warning: commit needed
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE artists\
                         SET sortname=?\
                         WHERE rowid=?",
                        (sort_name, artist_id))

    def get_sortname(self, artist_id):
        """
            Return sortname
            @param artist_id as int
            @return sortname as string
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT sortname from artists\
                                  WHERE rowid=?", (artist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return self.get_name(artist_id)

    def get_id(self, name, mb_artist_id=None):
        """
            Get artist id
            @param name as string
            @param mb_artist_id as str
            @return (artist_id as int, name as str)
        """
        with SqlCursor(self.__db) as sql:
            request = "SELECT rowid, name from artists\
                     WHERE name=?"
            params = [name]
            if mb_artist_id:
                request += " AND (mb_artist_id=? OR mb_artist_id IS NULL)"
                params.append(mb_artist_id)
            request += " COLLATE NOCASE"
            result = sql.execute(request, params)
            v = result.fetchone()
            if v is not None:
                return (v[0], v[1])
            return (None, None)

    def get_id_for_escaped_string(self, name):
        """
            Get artist id
            @param name as escaped string
            @return int
        """
        with SqlCursor(self.__db) as sql:
            request = "SELECT rowid from artists WHERE sql_escape(name)=?"
            result = sql.execute(request, (name,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_name(self, artist_id):
        """
            Get artist name
            @param artist_id as int
            @return str
        """
        with SqlCursor(self.__db) as sql:
            if artist_id == Type.COMPILATIONS:
                return _("Many artists")

            if App().settings.get_value("show-artist-sort"):
                result = sql.execute(
                    "SELECT sortname from artists WHERE rowid=?",
                    (artist_id,))
            else:
                result = sql.execute(
                    "SELECT name from artists WHERE rowid=?",
                    (artist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return ""

    def set_name(self, artist_id, name):
        """
            Set artist name
            @param artist_id as int
            @param name as str
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE artists\
                         SET name=?\
                         WHERE rowid=?",
                        (name, artist_id))

    def set_mb_artist_id(self, artist_id, mb_artist_id):
        """
            Set MusicBrainz artist id
            @param artist_id as int
            @param mb_artist_id as str
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("UPDATE artists\
                         SET mb_artist_id=?\
                         WHERE rowid=?",
                        (mb_artist_id, artist_id))

    def get_mb_artist_id(self, artist_id):
        """
            Get MusicBrainz artist id for artist id
            @param artist_id as int
            @return MusicBrainz artist id as str
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT mb_artist_id FROM artists\
                                  WHERE rowid=?", (artist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return -1

    def has_albums(self, artist_id):
        """
            Get album for artist id
            @param artist_id as int
            @return bool
        """
        with SqlCursor(self.__db) as sql:
            storage_type = get_default_storage_type()
            request = "SELECT DISTINCT albums.rowid\
                       FROM album_artists, albums\
                       WHERE albums.rowid=album_artists.album_id\
                       AND album_artists.artist_id=?\
                       AND albums.storage_type & ?"
            result = sql.execute(request, (artist_id, storage_type))
            return len(list(itertools.chain(*result))) != 0

    def get(self, genre_ids, storage_type):
        """
            Get all available artists
            @param genre_ids as [int]
            @param storage_type as StorageType
            @return [int, str, str]
        """
        genre_ids = remove_static(genre_ids)
        if App().settings.get_value("show-artist-sort"):
            select = "artists.rowid, artists.sortname, artists.sortname"
        else:
            select = "artists.rowid, artists.name, artists.sortname"
        with SqlCursor(self.__db) as sql:
            result = []
            if not genre_ids or genre_ids[0] == Type.ALL:
                # Only artist that really have an album
                result = sql.execute(
                    "SELECT DISTINCT %s FROM artists, albums, album_artists\
                                  WHERE album_artists.artist_id=artists.rowid\
                                  AND album_artists.album_id=albums.rowid\
                                  AND albums.storage_type & ?\
                                  ORDER BY artists.sortname\
                                  COLLATE NOCASE COLLATE LOCALIZED" % select,
                    (storage_type,))
            else:
                filters = (storage_type,)
                filters += tuple(genre_ids)
                request = "SELECT DISTINCT %s\
                           FROM artists, albums, album_genres, album_artists\
                           WHERE artists.rowid=album_artists.artist_id\
                           AND albums.rowid=album_artists.album_id\
                           AND albums.storage_type & ?\
                           AND album_genres.album_id=albums.rowid AND"
                request += make_subrequest("album_genres.genre_id=?",
                                           "OR",
                                           len(genre_ids))
                request += " ORDER BY artists.sortname\
                            COLLATE NOCASE COLLATE LOCALIZED"
                result = sql.execute(request % select, filters)
            return [(row[0], row[1], row[2]) for row in result]

    def get_randoms(self, limit, storage_type):
        """
            Return random artists
            @param limit as int
            @return [int, str, str]
        """
        with SqlCursor(self.__db) as sql:
            request = "SELECT DISTINCT artists.rowid,\
                                       artists.name,\
                                       artists.sortname\
                                  FROM artists, albums, album_artists\
                                  WHERE album_artists.artist_id=artists.rowid\
                                  AND album_artists.album_id=albums.rowid\
                                  AND albums.storage_type & ?\
                                  AND not albums.loved & ?\
                                  ORDER BY random() LIMIT ?\
                                  COLLATE NOCASE COLLATE LOCALIZED"
            result = sql.execute(
                request, (storage_type, LovedFlags.SKIPPED, limit))
            return [(row[0], row[1], row[2]) for row in result]

    def get_ids(self, genre_ids, storage_type):
        """
            Get all available album artists
            @param genre_ids as [int]
            @param storage_type as StorageType
            @return artist ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            result = []
            if not genre_ids or genre_ids[0] == Type.ALL:
                # Only artist that really have an album
                result = sql.execute(
                    "SELECT DISTINCT artists.rowid\
                                  FROM artists, albums, album_artists\
                                  WHERE album_artists.artist_id=artists.rowid\
                                  AND album_artists.album_id=albums.rowid\
                                  AND albums.storage_type & ?\
                                  ORDER BY artists.sortname\
                                  COLLATE NOCASE COLLATE LOCALIZED",
                    (storage_type,))
            else:
                filters = (storage_type,)
                filters += tuple(genre_ids)
                request = "SELECT DISTINCT artists.rowid\
                           FROM artists, albums, album_genres, album_artists\
                           WHERE artists.rowid=album_artists.artist_id\
                           AND albums.storage_type & ?\
                           AND albums.rowid=album_artists.album_id\
                           AND album_genres.album_id=albums.rowid AND"
                request += make_subrequest("album_genres.genre_id=?",
                                           "OR",
                                           len(genre_ids))
                request += " ORDER BY artists.sortname\
                            COLLATE NOCASE COLLATE LOCALIZED"
                result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def get_genre_ids(self, artist_ids, storage_type):
        """
            Get genre ids for artist ids
            @param artist_ids as [int]
            @param storage_type as StorageType
            @return genre ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = (storage_type,)
            filters += tuple(artist_ids)
            request = "SELECT DISTINCT album_genres.genre_id\
                       FROM artists, album_genres, album_artists, albums\
                       WHERE album_artists.album_id=album_genres.album_id\
                       AND albums.storage_type & ?\
                       AND albums.rowid=album_artists.album_id AND"
            request += make_subrequest("album_artists.artist_id=?",
                                       "OR",
                                       len(artist_ids))
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def update_featuring(self):
        """
            Calculate featuring for current DB
        """
        with SqlCursor(self.__db, True) as sql:
            sql.execute("DELETE FROM featuring")
            result = sql.execute(
                        "SELECT track_artists.artist_id, tracks.album_id\
                         FROM tracks, track_artists\
                         WHERE track_artists.track_id = tracks.rowid\
                         AND NOT EXISTS (\
                          SELECT * FROM album_artists WHERE\
                          album_artists.album_id = tracks.album_id AND\
                          album_artists.artist_id = track_artists.artist_id)")
            for (artist_id, album_id) in result:
                sql.execute("INSERT INTO featuring (artist_id, album_id)\
                             VALUES (?, ?)", (artist_id, album_id))

    def get_featured(self, genre_ids, artist_ids, storage_type, skipped):
        """
            Get albums where artist is in featuring
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param skipped as bool
        """
        orderby = App().settings.get_enum("orderby")
        if orderby == OrderBy.ARTIST_YEAR:
            order = " ORDER BY artists.sortname\
                     COLLATE NOCASE COLLATE LOCALIZED,\
                     albums.timestamp,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.ARTIST_TITLE:
            order = " ORDER BY artists.sortname\
                     COLLATE NOCASE COLLATE LOCALIZED,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.TITLE:
            order = " ORDER BY albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.YEAR_DESC:
            order = " ORDER BY albums.timestamp DESC,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.YEAR_ASC:
            order = " ORDER BY albums.timestamp ASC,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        else:
            order = " ORDER BY albums.popularity DESC,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        with SqlCursor(self.__db) as sql:
            request = "SELECT DISTINCT featuring.album_id\
                       FROM featuring, album_genres, albums, artists\
                       WHERE albums.storage_type&? AND\
                             artists.rowid=featuring.artist_id AND\
                             albums.rowid=featuring.album_id AND "
            filters = (storage_type,)
            if artist_ids:
                filters += tuple(artist_ids)
                request += make_subrequest("featuring.artist_id=?",
                                           "OR",
                                           len(artist_ids))
            if genre_ids:
                filters += tuple(genre_ids)
                request += " AND "
                request += make_subrequest("album_genres.genre_id=?",
                                           "OR",
                                           len(genre_ids))
            if not skipped:
                filters += (LovedFlags.SKIPPED,)
                request += " AND not albums.loved & ?"
            request += order
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def exists(self, artist_id):
        """
            Return True if artist exist
            @param artist_id as int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT COUNT(1) FROM artists WHERE rowid=?",
                                 (artist_id,))
            v = result.fetchone()
            if v is not None:
                return bool(v[0])
            return False

    def search(self, searched, storage_type):
        """
            Search for artists looking like searched
            @param searched as str without accents
            @param storage_type as StorageType
            @return artist ids as [int]
        """
        with SqlCursor(self.__db) as sql:
            filters = ("%" + searched + "%", storage_type)
            request = "SELECT DISTINCT artists.rowid, artists.name\
                   FROM albums, album_artists, artists\
                   WHERE album_artists.artist_id=artists.rowid AND\
                   album_artists.album_id=albums.rowid AND\
                   noaccents(artists.name) LIKE ? AND\
                   albums.storage_type & ? LIMIT 25"
            result = sql.execute(request, filters)
            return list(result)

    def count(self):
        """
            Count artists
            @return int
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT COUNT(DISTINCT artists.rowid)\
                                  FROM artists, album_artists, albums\
                                  WHERE album_artists.album_id=albums.rowid\
                                  AND artists.rowid=album_artists.artist_id\
                                  AND albums.storage_type & ?",
                                 (StorageType.COLLECTION | StorageType.SAVED,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return 0

    def clean(self, commit=True):
        """
            Clean artists
            @param commit as bool
        """
        with SqlCursor(self.__db, commit) as sql:
            sql.execute("DELETE FROM artists WHERE artists.rowid NOT IN (\
                            SELECT album_artists.artist_id\
                            FROM album_artists) AND artists.rowid NOT IN (\
                                SELECT track_artists.artist_id\
                                FROM track_artists)")
