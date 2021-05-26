# Copyright (c) 2014-2016 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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
from lollypop.define import Lp, Type


class MpdDatabase:
    """
        Databse request from MPD module
    """

    def count(self, album, artist_id, genre_id, year):
        """
            Count songs and play time
            @param album as string
            @param artist_id as int
            @param genre_id as int
            @param year as int
        """
        songs = 0
        playtime = 0
        with SqlCursor(Lp().db) as sql:
            result = self._get_tracks(sql, "COUNT(*), SUM(tracks.duration)",
                                      album, artist_id, genre_id, year)
            v = result.fetchone()
            if v is not None:
                if v[0] is not None:
                    songs = v[0]
                if v[1] is not None:
                    playtime = v[1]
            return (songs, playtime)

    def get_tracks_paths(self, album, artist_id, genre_id, year):
        """
            Get tracks path
            @param album as string
            @param artist_id as int
            @param genre_id as int
            @param year as int
            @return paths as [str]
        """
        with SqlCursor(Lp().db) as sql:
            result = self._get_tracks(sql, "filepath",
                                      album, artist_id, genre_id, year)
            return list(itertools.chain(*result))

    def get_tracks_ids(self, album, artist_id, genre_id, year):
        """
            Get tracks path
            @param album as string
            @param artist_id as int
            @param genre_id as int
            @param year as int
            @return paths as [str]
        """
        with SqlCursor(Lp().db) as sql:
            result = self._get_tracks(sql, "tracks.rowid",
                                      album, artist_id, genre_id, year)
            return list(itertools.chain(*result))

    def get_albums_names(self, artist_id, genre_id, year):
        """
            Get albums names
            @param artist_id as int
            @param genre_id as int
            @param year as int
            @return names as [str]
        """
        from_str = "albums "
        where_str = ""
        if artist_id is not None:
            where_str += " albums.artist_id = %s AND" % artist_id
        if genre_id is not None:
            from_str += ",album_genres"
            where_str += " album_genres.genre_id = %s\
                          AND album_genres.album_id = albums.rowid\
                          AND" % genre_id
        if year is None:
            where_str += " albums.year is null"
        elif year != Type.NONE:
            where_str += " albums.year = %s" % year

        with SqlCursor(Lp().db) as sql:
            request = "SELECT albums.name FROM "\
                       + from_str
            if where_str != "":
                request += " WHERE " + where_str
            if request.endswith("AND"):
                request = request[:-3]
            result = sql.execute(request)
            return list(itertools.chain(*result))

    def get_artists_names(self, genre_id):
        """
            Get artists names
            @param genre_id as int
            @return names as [str]
        """
        from_str = "artists, albums "
        where_str = " albums.artist_id = artists.rowid AND"
        if genre_id is not None:
            from_str += ", album_genres"
            where_str += " album_genres.genre_id = %s\
                          AND album_genres.album_id = albums.rowid\
                          AND" % genre_id

        with SqlCursor(Lp().db) as sql:
            request = "SELECT DISTINCT artists.name FROM "\
                       + from_str
            if where_str != "":
                request += " WHERE " + where_str
            if request.endswith("AND"):
                request = request[:-3]
            result = sql.execute(request)
            return list(itertools.chain(*result))

    def get_albums_years(self, album, artist_id, genre_id):
        """
            Get all availables albums years
            @param album as string
            @param artist_id as int
            @param genre_id as int
            @return years as [str]
        """
        from_str = "albums "
        where_str = "year is not null AND"
        if album is not None:
            where_str += ' albums.name = "%s" AND' % album
        if artist_id is not None:
            where_str += " albums.artist_id= %s AND" % artist_id
        if genre_id is not None:
            from_str += ",album_genres "
            where_str += " album_genres.genre_id = %s\
                          AND album_genres.album_id = albums.rowid\
                          AND" % genre_id
        request = "SELECT year FROM " + from_str
        if where_str != "":
            request += " WHERE " + where_str
        if request.endswith("AND"):
            request = request[:-3]
        with SqlCursor(Lp().db) as sql:
            result = sql.execute(request)
            return list(itertools.chain(*result))

    def listallinfos(self):
        """
            Get all tracks
            @return array [(
                     track.path,
                     track.artist,
                     track.album.name,
                     track.album_artist,
                     track.name,
                     track.album.year,
                     track.genre,
                     track.duration,
                     track.id,
                     track.position)]
        """
        request = "SELECT tracks.filepath, artists.name, albums.name,\
                   artists.name, tracks.name, albums.year, genres.name,\
                   tracks.duration, tracks.rowid, tracks.tracknumber\
                   FROM artists, albums, tracks, genres, track_genres\
                   WHERE albums.rowid = tracks.album_id\
                   AND artists.rowid = albums.artist_id\
                   AND genres.rowid = track_genres.genre_id\
                   AND tracks.rowid = track_genres.track_id"
        with SqlCursor(Lp().db) as sql:
            result = sql.execute(request)
            return list(result)

#######################
# PRIVATE             #
#######################
    def _get_tracks(self, sql, select_str, album, artist_id, genre_id, year):
        """
            Get tracks attributes
            @param sql as sqlite cursor
            @param select as string
            @param album as string
            @param artist_id as int
            @param genre_id as int
            @param year as int
            @return sqlite cursor
        """
        from_str = "tracks "
        where_str = ""
        if album is not None:
            from_str += ",albums"
            where_str += 'albums.name = "%s" AND\
                          tracks.album_id = albums.rowid AND' % album
        if artist_id is not None:
            from_str += ", artists"
            if "albums" not in from_str:
                from_str += ",albums"
                where_str += " tracks.album_id = albums.rowid AND"
            where_str += " artists.rowid = %s\
                          AND albums.artist_id = artists.rowid\
                          AND" % artist_id
        if genre_id is not None:
            from_str += ",track_genres"
            where_str += " track_genres.genre_id = %s\
                          AND track_genres.track_id = tracks.rowid\
                          AND" % genre_id
        if year is None:
            where_str += " tracks.year is null"
        elif year != Type.NONE:
            where_str += " tracks.year = %s" % year

        request = "SELECT %s FROM " % select_str\
                  + from_str
        if where_str != "":
            request += " WHERE " + where_str
        if request.endswith("AND"):
            request = request[:-3]
        result = sql.execute(request + "ORDER BY tracks.tracknumber")
        return result
