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

from lollypop.define import CACHE_PATH
from lollypop.sqlcursor import SqlCursor
from lollypop.database import Database
from lollypop.logger import Logger


class CacheDatabase:
    """
        Cache calculation into database
    """
    DB_PATH = "%s/cache_v1.db" % CACHE_PATH

    # SQLite documentation:
    # In SQLite, a column with type INTEGER PRIMARY KEY
    # is an alias for the ROWID.
    # Here, we define an id INT PRIMARY KEY but never feed it,
    # this make VACUUM not destroy rowids...
    __create_duration = """CREATE TABLE duration (
                            id TEXT PRIMARY KEY,
                            album_id INT NOT NULL,
                            duration INT NOT NULL DEFAULT 0)"""

    def __init__(self):
        """
            Create database tables
        """
        self.thread_lock = Lock()
        f = Gio.File.new_for_path(self.DB_PATH)
        if not f.query_exists():
            try:
                d = Gio.File.new_for_path(CACHE_PATH)
                if not d.query_exists():
                    d.make_directory_with_parents()
                # Create db schema
                with SqlCursor(self, True) as sql:
                    sql.execute(self.__create_duration)
            except Exception as e:
                Logger.error("DatabaseCache::__init__(): %s" % e)

    def set_duration(self, album_id, album_hash, duration):
        """
            Set duration in cache for album
            @param album_id as int
            @param album_hash as str
            @param duration as int
        """
        try:
            with SqlCursor(self, True) as sql:
                sql.execute("INSERT INTO duration (id, album_id, duration)\
                             VALUES (?, ?, ?)",
                            (album_hash, album_id, duration))
        except Exception as e:
            Logger.error("DatabaseCache::set_duration(): %s", e)

    def get_duration(self, album_hash):
        """
            Get duration in cache for album
            @param album_hash as str
            @return int/None
        """
        try:
            with SqlCursor(self) as sql:
                result = sql.execute("SELECT duration\
                                      FROM duration\
                                      WHERE id=?",
                                     (album_hash,))
                v = result.fetchone()
                if v is not None:
                    return v[0]
        except Exception as e:
            Logger.error("DatabaseCache::get_duration(): %s", e)
        return None

    def clear_durations(self, album_id):
        """
            Clear durations for album_id
            @param album_id as int
        """
        with SqlCursor(self, True) as sql:
            sql.execute("DELETE FROM duration WHERE album_id=?",
                        (album_id,))

    def clear_table(self, table):
        """
            Clear table
            @param table as str
        """
        with SqlCursor(self, True) as sql:
            sql.execute('DELETE FROM "%s"' % table)

    def clean(self, commit=True):
        """
            Clean cache
            @param commit as bool
        """
        with SqlCursor(self, commit) as sql:
            sql.execute('ATTACH DATABASE "%s" AS music' % Database.DB_PATH)
            sql.execute("DELETE FROM duration WHERE duration.album_id NOT IN (\
                            SELECT albums.rowid FROM music.albums)")

    def get_cursor(self):
        """
            Return a new sqlite cursor
        """
        try:
            c = sqlite3.connect(self.DB_PATH, 600.0)
            return c
        except:
            exit(-1)

#######################
# PRIVATE             #
#######################
