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

import sqlite3
from threading import Lock
from random import shuffle
import itertools

from lollypop.define import App, LOLLYPOP_DATA_PATH
from lollypop.database_upgrade import DatabaseAlbumsUpgrade
from lollypop.sqlcursor import SqlCursor
from lollypop.logger import Logger
from lollypop.localized import LocalizedCollation
from lollypop.utils import noaccents, sql_escape


class MyLock:
    """
        Lock with status
    """
    def __init__(self):
        self.__lock = Lock()
        self.__locked = False

    def acquire(self):
        self.__locked = True
        self.__lock.acquire()

    def release(self):
        self.__locked = False
        self.__lock.release()

    @property
    def locked(self):
        return self.__locked


class Database:
    """
        Base database object
    """

    DB_PATH = "%s/lollypop.db" % LOLLYPOP_DATA_PATH

    # SQLite documentation:
    # In SQLite, a column with type INTEGER PRIMARY KEY
    # is an alias for the ROWID.
    # Here, we define an id INT PRIMARY KEY but never feed it,
    # this make VACUUM not destroy rowids...
    __create_albums = """CREATE TABLE albums (id INTEGER PRIMARY KEY,
                                              name TEXT NOT NULL,
                                              mb_album_id TEXT,
                                              lp_album_id TEXT,
                                              no_album_artist BOOLEAN NOT NULL,
                                              year INT,
                                              timestamp INT,
                                              uri TEXT NOT NULL,
                                              popularity INT NOT NULL,
                                              rate INT NOT NULL,
                                              loved INT NOT NULL,
                                              mtime INT NOT NULL,
                                              storage_type INT NOT NULL,
                                              synced INT NOT NULL)"""
    __create_artists = """CREATE TABLE artists (id INTEGER PRIMARY KEY,
                                               name TEXT NOT NULL,
                                               sortname TEXT NOT NULL,
                                               mb_artist_id TEXT)"""
    __create_featuring = """CREATE TABLE featuring (
                                               artist_id INT NOT NULL,
                                               album_id INT NOT NULL)"""
    __create_genres = """CREATE TABLE genres (id INTEGER PRIMARY KEY,
                                            name TEXT NOT NULL)"""
    __create_album_artists = """CREATE TABLE album_artists (
                                                album_id INT NOT NULL,
                                                artist_id INT NOT NULL)"""
    __create_album_genres = """CREATE TABLE album_genres (
                                                album_id INT NOT NULL,
                                                genre_id INT NOT NULL)"""
    __create_album_timed_popularity = """CREATE TABLE albums_timed_popularity (
                                                album_id INT NOT NULL,
                                                mtime INT NOT NULL,
                                                popularity INT NOT NULL)"""
    __create_tracks = """CREATE TABLE tracks (id INTEGER PRIMARY KEY,
                                              name TEXT NOT NULL,
                                              uri TEXT NOT NULL,
                                              duration INT,
                                              tracknumber INT,
                                              discnumber INT,
                                              discname TEXT,
                                              album_id INT NOT NULL,
                                              year INT,
                                              timestamp INT,
                                              popularity INT NOT NULL,
                                              loved INT NOT NULL DEFAULT 0,
                                              rate INT NOT NULL,
                                              ltime INT NOT NULL,
                                              mtime INT NOT NULL,
                                              storage_type INT NOT NULL,
                                              mb_track_id TEXT,
                                              lp_track_id TEXT,
                                              bpm DOUBLE
                                              )"""
    __create_track_artists = """CREATE TABLE track_artists (
                                                track_id INT NOT NULL,
                                                artist_id INT NOT NULL)"""
    __create_track_genres = """CREATE TABLE track_genres (
                                                track_id INT NOT NULL,
                                                genre_id INT NOT NULL)"""
    __create_album_artists_idx = """CREATE index idx_aa ON album_artists(
                                                album_id)"""
    __create_track_artists_idx = """CREATE index idx_ta ON track_artists(
                                                track_id)"""
    __create_album_genres_idx = """CREATE index idx_ag ON album_genres(
                                                album_id)"""
    __create_track_genres_idx = """CREATE index idx_tg ON track_genres(
                                                track_id)"""

    def __init__(self):
        """
            Create database tables or manage update if needed
        """
        self.thread_lock = MyLock()
        f = Gio.File.new_for_path(self.DB_PATH)
        upgrade = DatabaseAlbumsUpgrade()
        if not f.query_exists():
            try:
                d = Gio.File.new_for_path(LOLLYPOP_DATA_PATH)
                if not d.query_exists():
                    d.make_directory_with_parents()
                # Create db schema
                with SqlCursor(self, True) as sql:
                    sql.execute(self.__create_albums)
                    sql.execute(self.__create_artists)
                    sql.execute(self.__create_featuring)
                    sql.execute(self.__create_genres)
                    sql.execute(self.__create_album_genres)
                    sql.execute(self.__create_album_artists)
                    sql.execute(self.__create_album_timed_popularity)
                    sql.execute(self.__create_tracks)
                    sql.execute(self.__create_track_artists)
                    sql.execute(self.__create_track_genres)
                    sql.execute(self.__create_album_artists_idx)
                    sql.execute(self.__create_track_artists_idx)
                    sql.execute(self.__create_album_genres_idx)
                    sql.execute(self.__create_track_genres_idx)
                    sql.execute("PRAGMA user_version=%s" % upgrade.version)
            except Exception as e:
                Logger.error("Database::__init__(): %s" % e)
        else:
            upgrade.upgrade(self)

    def execute(self, request):
        """
            Execute SQL request (only smart one)
            @param request as str
            @return list
        """
        requests = []
        try:
            union_random = request.find("ORDER BY random()") != -1 and\
                request.find("UNION") != -1
            # Special case for UNION, does not support random()
            # Optimisation, split request and add LIMIT
            if union_random:
                request = request.replace("ORDER BY random()", "")
                limit_position = request.find("LIMIT")
                limit_str = request[limit_position:]
                limit_int = int(limit_str.replace("LIMIT ", ""))
                # Remove limit from main request
                request = request.replace(limit_str, "")
                request_split = request.split("UNION")
                sublimit = limit_int // len(request_split)
                for request in request_split:
                    request += " ORDER BY random() LIMIT %s" % sublimit
                    requests.append(request)
            else:
                requests = [request]
            ids = []
            with SqlCursor(App().db) as sql:
                for request in requests:
                    result = sql.execute(request)
                    ids += list(itertools.chain(*result))
                if union_random:
                    shuffle(ids)
                    return ids[:limit_int]
                else:
                    return ids
        except Exception as e:
            Logger.error("Database::execute(): %s -> %s", e, request)
        return []

    def get_cursor(self):
        """
            Return a new sqlite cursor
        """
        try:
            c = sqlite3.connect(self.DB_PATH, 600.0)
            c.create_collation("LOCALIZED", LocalizedCollation())
            c.create_function("noaccents", 1, noaccents)
            c.create_function("sql_escape", 1, sql_escape)
            return c
        except:
            exit(-1)

#######################
# PRIVATE             #
#######################
