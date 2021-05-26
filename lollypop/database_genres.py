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

import itertools

from lollypop.sqlcursor import SqlCursor
from lollypop.define import App, Type, OrderBy, LovedFlags
from lollypop.utils import get_network_available, sql_escape


class GenresDatabase:
    """
        Genres database helper
    """

    def __init__(self, db):
        """
            Init genres database object
            @param db as Database
        """
        self.__db = db

    def add(self, name):
        """
            Add a new genre to database
            @param name as string
            @return inserted rowid as int
            @warning: commit needed
        """
        with SqlCursor(self.__db, True) as sql:
            result = sql.execute("INSERT INTO genres (name) VALUES (?)",
                                 (name,))
            return result.lastrowid

    def get_id(self, name):
        """
            Get genre id for name
            @param name as string
            @return genre id as int
        """
        with SqlCursor(self.__db) as sql:
            # Escape string to fix mixed tags:
            # Alternative Rock, Aternative-Rock, alternative rock
            result = sql.execute("SELECT rowid FROM genres\
                                  WHERE sql_escape(name)=?",
                                 (sql_escape(name),))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_name(self, genre_id):
        """
            Get genre name for genre id
            @param genre_id as int
            @return str
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT name FROM genres\
                                  WHERE rowid=?", (genre_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_album_ids(self, ignore=False):
        """
            Get all availables albums for genres
            @param genre_ids as [int]
            @param ignore as bool
            @return [int]
        """
        orderby = App().settings.get_enum("orderby")
        order = " ORDER BY genres.name, "
        if orderby == OrderBy.ARTIST_YEAR:
            order += " artists.sortname\
                     COLLATE NOCASE COLLATE LOCALIZED,\
                     albums.timestamp,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.ARTIST_TITLE:
            order += " artists.sortname\
                     COLLATE NOCASE COLLATE LOCALIZED,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.NAME:
            order += " albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        elif orderby == OrderBy.YEAR_DESC:
            order += " albums.timestamp DESC,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        else:
            order += " albums.popularity DESC,\
                     albums.name\
                     COLLATE NOCASE COLLATE LOCALIZED"
        with SqlCursor(self.__db) as sql:
            filters = ()
            request = "SELECT albums.rowid\
                       FROM albums, album_genres, genres,\
                            album_artists, artists\
                       WHERE album_genres.album_id=albums.rowid\
                       AND album_genres.genre_id = genres.rowid\
                       AND album_artists.artist_id = artists.rowid\
                       AND album_artists.album_id = albums.rowid"
            if not get_network_available():
                request += " AND albums.synced!=%s" % Type.NONE
            if ignore:
                request += " AND not albums.loved & ?"
                filters += (LovedFlags.SKIPPED,)
            request += order
            result = sql.execute(request, filters)
            return list(itertools.chain(*result))

    def get(self):
        """
            Get all availables genres
            @return [(int, str, str)]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT DISTINCT\
                                  genres.rowid, genres.name, genres.name\
                                  FROM genres\
                                  WHERE EXISTS (\
                                    SELECT *\
                                    FROM album_genres, album_artists\
                                    WHERE album_genres.album_id=\
                                        album_artists.album_id AND\
                                        album_artists.artist_id != ? AND\
                                        album_genres.genre_id=genres.rowid)\
                                  ORDER BY genres.name\
                                  COLLATE NOCASE COLLATE LOCALIZED",
                                 (Type.COMPILATIONS,))
            return list(result)

    def get_ids(self):
        """
            Get all availables genres ids
            @return [id as int]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT DISTINCT genres.rowid\
                                  FROM genres\
                                  WHERE EXISTS (\
                                    SELECT *\
                                    FROM album_genres, album_artists\
                                    WHERE album_genres.album_id=\
                                        album_artists.album_id AND\
                                        album_artists.artist_id != ? AND\
                                        album_genres.genre_id=genres.rowid)\
                                  ORDER BY genres.name\
                                  COLLATE NOCASE COLLATE LOCALIZED",
                                 (Type.COMPILATIONS,))
            return list(itertools.chain(*result))

    def get_random(self):
        """
            Return a random genre
            @return [int]
        """
        with SqlCursor(self.__db) as sql:
            result = sql.execute("SELECT genres.rowid, genres.name\
                                  FROM genres\
                                  WHERE EXISTS (\
                                    SELECT albums.rowid\
                                    FROM albums, album_genres\
                                    WHERE albums.loved != -1 AND\
                                          albums.rowid =\
                                            album_genres.album_id AND\
                                          album_genres.genre_id =\
                                            genres.rowid)\
                                  ORDER BY random() LIMIT 1")
            genres = list(result)
            return genres[0] if genres else (None, "")

    def clean(self, commit=True):
        """
            Clean genres
            @param commit as bool
        """
        with SqlCursor(self.__db, commit) as sql:
            sql.execute("DELETE FROM genres WHERE genres.rowid NOT IN (\
                            SELECT album_genres.genre_id FROM album_genres)")
            sql.execute("DELETE FROM genres WHERE genres.rowid NOT IN (\
                            SELECT track_genres.genre_id FROM track_genres)")
