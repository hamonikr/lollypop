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

from gi.repository import GLib

import sqlite3
from threading import Lock

from lollypop.sqlcursor import SqlCursor


class History:
    """
        History manager, allow Lollypop to restore stats when a file is moved
    """
    __LOCAL_PATH = GLib.get_user_data_dir() + "/lollypop"
    __DB_PATH = "%s/history.db" % __LOCAL_PATH
    __LIMIT = 1000000  # Delete when limit is reached
    __DELETE = 100     # How many elements to delete
    __create_history = """CREATE TABLE history (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            duration INT NOT NULL,
                            ltime INT NOT NULL,
                            popularity INT NOT NULL,
                            rate INT NOT NULL,
                            mtime INT NOT NULL,
                            album_rate INT NOT NULL,
                            loved INT NOT NULL,
                            album_loved INT NOT NULL,
                            album_synced INT NOT NULL,
                            album_popularity INT NOT NULL)"""

    def __init__(self):
        """
            Init playlists manager
        """
        self.thread_lock = Lock()
        # Create db schema
        try:
            with SqlCursor(self, True) as sql:
                sql.execute(self.__create_history)
        except:
            pass
        with SqlCursor(self, True) as sql:
            result = sql.execute("SELECT COUNT(*)\
                                  FROM history")
            v = result.fetchone()
            if v is not None and v[0] > self.__LIMIT:
                sql.execute("DELETE FROM history\
                             WHERE rowid IN (SELECT rowid\
                                             FROM history\
                                             LIMIT %s)" % self.__DELETE)
                sql.execute("VACUUM")

    def add(self, name, duration, popularity, rate, ltime, mtime, loved,
            album_loved, album_popularity, album_rate, album_synced):
        """
            Add an item to history
            @param name as str
            @param duration as int
            @param popularity as int
            @param rate as int
            @param ltime as int
            @param mtime as int
            @param loved as bool
            @param album_loved as bool
            @param album_popularity as int
            @param album_rate as int
            @param album_synced as int
            @thread safe
        """
        with SqlCursor(self, True) as sql:
            # Needed because of seconds to ms DB migration
            # Value in DB is rounded version of Gstreamer value
            duration //= 1000
            if self.exists(name, duration):
                sql.execute("UPDATE history\
                             SET popularity=?,rate=?,ltime=?,mtime=?,loved=?,\
                             album_loved=?,album_popularity=?,album_rate=?,\
                             album_synced=?\
                             WHERE name=? AND duration=?",
                            (popularity, rate, ltime, mtime, loved,
                             album_loved, album_popularity, album_rate,
                             album_synced,
                             name, duration))
            else:
                sql.execute("INSERT INTO history\
                             (name, duration, popularity, rate, ltime, mtime,\
                             loved, album_loved, album_popularity, album_rate,\
                             album_synced)\
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (name, duration, popularity, rate, ltime, mtime,
                             loved, album_loved, album_popularity, album_rate,
                             album_synced))

    def get(self, name, duration):
        """
            Get stats for track with name and duration
            @param name as str
            @param duration as int
            @return (popularity, ltime, mtime,
                     loved album, album_popularity, album_synced)
             as (int, int, int, int, int, int)
        """
        with SqlCursor(self) as sql:
            duration //= 1000
            result = sql.execute("SELECT popularity, rate, ltime, mtime,\
                                  loved, album_loved, album_popularity,\
                                  album_rate, album_synced\
                                  FROM history\
                                  WHERE name=?\
                                  AND duration=?",
                                 (name, duration))
            v = result.fetchone()
            if v is not None:
                return v
            return (0, 0, 0, 0, 0, 0, 0, 0, 0)

    def exists(self, name, duration):
        """
            Return True if entry exists
            @param name as str
            @param duration as int
            @return bool
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT rowid\
                                  FROM history\
                                  WHERE name=?\
                                  AND duration=?",
                                 (name, duration))
            v = result.fetchone()
            if v is not None:
                return True
            else:
                return False

    def get_cursor(self):
        """
            Return a new sqlite cursor
        """
        try:
            return sqlite3.connect(self.__DB_PATH, 600.0)
        except:
            exit(-1)

#######################
# PRIVATE             #
#######################
