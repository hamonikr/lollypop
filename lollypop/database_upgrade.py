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

from gi.repository import GLib, Gio, Gtk

import itertools
from time import time
from gettext import gettext as _

from lollypop.sqlcursor import SqlCursor
from lollypop.utils import translate_artist_name
from lollypop.database_history import History
from lollypop.define import App, Type, StorageType, LOLLYPOP_DATA_PATH
from lollypop.logger import Logger
from lollypop.helper_task import TaskHelper


class DatabaseUpgrade:
    """
        Manage database schema upgrades
    """

    def __init__(self):
        """
            Init object
        """
        # Here are schema upgrade, key is database version,
        # value is sql request
        self._UPGRADES = {
        }

    def upgrade(self, db):
        """
            Upgrade db
            @param db as Database
        """
        version = 0
        SqlCursor.add(db)
        with SqlCursor(db, True) as sql:
            result = sql.execute("PRAGMA user_version")
            v = result.fetchone()
            if v is not None:
                version = v[0]
            if version < self.version:
                for i in range(version + 1, self.version + 1):
                    try:
                        if isinstance(self._UPGRADES[i], str):
                            sql.execute(self._UPGRADES[i])
                            SqlCursor.commit(db)
                        else:
                            self._UPGRADES[i](db)
                            SqlCursor.commit(db)
                    except Exception as e:
                        Logger.error("DB upgrade %s failed: %s" %
                                     (i, e))
                sql.execute("PRAGMA user_version=%s" % self.version)
        SqlCursor.remove(db)

    @property
    def version(self):
        """
            Current wanted version
        """
        return len(self._UPGRADES)


class DatabasePlaylistsUpgrade(DatabaseUpgrade):
    """
        Manage database schema upgrades
    """

    def __init__(self):
        """
            Init upgrade
        """
        DatabaseUpgrade.__init__(self)
        self._UPGRADES = {
           1: "ALTER TABLE playlists ADD synced INT NOT NULL DEFAULT 0",
           2: "ALTER TABLE playlists ADD smart_enabled INT NOT NULL DEFAULT 0",
           3: "ALTER TABLE playlists ADD smart_sql TEXT",
           4: self.__upgrade_4,
           5: "ALTER TABLE playlists ADD uri TEXT"
        }

#######################
# PRIVATE             #
#######################
    def __upgrade_4(self, db):
        """
            Import tracks from loved playlist to DB
        """
        with SqlCursor(db, True) as sql1:
            result = sql1.execute("SELECT uri\
                                   FROM tracks\
                                   WHERE playlist_id=?", (Type.LOVED,))
            with SqlCursor(App().db, True) as sql2:
                for uri in list(itertools.chain(*result)):
                    sql2.execute("UPDATE tracks SET loved=1 WHERE uri=?",
                                 (uri,))


class DatabaseAlbumsUpgrade(DatabaseUpgrade):
    """
        Manage database schema upgrades
    """

    def __init__(self):
        """
            Init upgrade
        """
        DatabaseUpgrade.__init__(self)
        self._UPGRADES = {
            1: "UPDATE tracks SET duration=CAST(duration as INTEGER);",
            2: "UPDATE albums SET artist_id=-2001 where artist_id=-999;",
            3: self.__upgrade_3,
            4: self.__upgrade_4,
            5: "CREATE index idx_aa ON album_artists(album_id)",
            6: "CREATE index idx_ta ON track_artists(track_id)",
            7: "ALTER TABLE tracks ADD discname TEXT",
            8: "CREATE index idx_ag ON album_genres(album_id)",
            9: "CREATE index idx_tg ON track_genres(track_id)",
            10: "UPDATE tracks set ltime=0 where ltime is null",
            11: "ALTER TABLE albums ADD synced INT NOT NULL DEFAULT 0",
            12: "ALTER TABLE tracks ADD persistent INT NOT NULL DEFAULT 1",
            13: self.__upgrade_13,
            14: "UPDATE albums SET synced=-1 where mtime=0",
            15: self.__upgrade_15,
            16: self.__upgrade_16,
            17: "ALTER TABLE albums ADD loved INT NOT NULL DEFAULT 0",
            18: self.__upgrade_18,
            19: self.__upgrade_19,
            20: self.__upgrade_20,
            21: self.__upgrade_21,
            22: self.__upgrade_22,
            23: self.__upgrade_23,
            24: "ALTER TABLE albums ADD album_id TEXT",
            25: "ALTER TABLE tracks ADD mb_track_id TEXT",
            26: self.__upgrade_26,
            27: "UPDATE tracks SET duration=CAST(duration AS INT)",
            28: self.__upgrade_28,
            29: self.__upgrade_29,
            30: "ALTER TABLE tracks ADD loved INT NOT NULL DEFAULT 0",
            31: self.__upgrade_31,
            32: "ALTER TABLE tracks ADD bpm DOUBLE",
            33: "ALTER TABLE artists ADD mb_artist_id TEXT",
            34: self.__upgrade_31,
            35: "UPDATE albums SET synced=2 WHERE synced=1",
            36: self.__upgrade_36,
            37: self.__upgrade_37,
            38: """CREATE TABLE albums_timed_popularity (
                                                album_id INT NOT NULL,
                                                mtime INT NOT NULL,
                                                popularity INT NOT NULL)""",
            39: self.__upgrade_39,
            40: """UPDATE tracks SET duration = duration * 1000""",
            # Here we force an mb_album_id if empty, needed by artwork
            41: """UPDATE albums SET mb_album_id=rowid
                   WHERE mb_album_id is null""",
            # Fix previous update
            42: """UPDATE albums SET mb_album_id=null
                   WHERE storage_type=2 AND rowid=mb_album_id""",
            43: """CREATE TABLE featuring (artist_id INT NOT NULL,
                                           album_id INT NOT NULL)""",
            44: self.__upgrade_44,
            45: self.__upgrade_45,
            46: self.__upgrade_46,
            47: self.__upgrade_47,
            48: self.__upgrade_48,
        }

#######################
# PRIVATE             #
#######################
    def __upgrade_3(self, db):
        """
            Add a sorted field to artists
        """
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE artists ADD sortname TEXT")
            result = sql.execute("SELECT DISTINCT artists.rowid,\
                                  artists.name\
                                  FROM artists")
            for row in result:
                translated = translate_artist_name(row[1])
                sql.execute("UPDATE artists SET name=? WHERE rowid=?",
                            (translated, row[0]))
                sql.execute("UPDATE artists SET sortname=? WHERE rowid=?",
                            (row[1], row[0]))

    def __upgrade_4(self, db):
        """
            Add album artists table
        """
        with SqlCursor(db, True) as sql:
            sql.execute("CREATE TABLE album_artists (\
                                                album_id INT NOT NULL,\
                                                artist_id INT NOT NULL)")
            result = sql.execute("SELECT rowid from albums")
            for album_id in list(itertools.chain(*result)):
                result = sql.execute("SELECT artist_id\
                                     FROM albums\
                                     WHERE rowid=?",
                                     (album_id,))
                v = result.fetchone()
                if v is not None:
                    artist_id = v[0]
                    sql.execute("INSERT INTO album_artists\
                                (album_id, artist_id)\
                                VALUES(?, ?)",
                                (album_id, artist_id))
            sql.execute("CREATE TEMPORARY TABLE backup(id,\
                                                       name,\
                                                       no_album_artist,\
                                                       year,\
                                                       path,\
                                                       popularity,\
                                                       mtime)")
            sql.execute("INSERT INTO backup\
                        SELECT id,\
                               name,\
                               no_album_artist,\
                               year,\
                               path,\
                               popularity,\
                               mtime FROM albums")
            sql.execute("DROP TABLE albums")
            sql.execute("CREATE TABLE albums (id INTEGER PRIMARY KEY,\
                        name TEXT NOT NULL,\
                        no_album_artist BOOLEAN NOT NULL,\
                        year INT,\
                        path TEXT NOT NULL,\
                        popularity INT NOT NULL,\
                        mtime INT NOT NULL)")
            sql.execute("INSERT INTO albums\
                        SELECT id,\
                               name,\
                               no_album_artist,\
                               year,\
                               path,\
                               popularity,\
                               mtime FROM backup")
            sql.execute("DROP TABLE backup")

    def __upgrade_13(self, db):
        """
            Convert tracks filepath column to uri
        """
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE tracks RENAME TO tmp_tracks")
            sql.execute("""CREATE TABLE tracks (id INTEGER PRIMARY KEY,
                                              name TEXT NOT NULL,
                                              uri TEXT NOT NULL,
                                              duration INT,
                                              tracknumber INT,
                                              discnumber INT,
                                              discname TEXT,
                                              album_id INT NOT NULL,
                                              year INT,
                                              popularity INT NOT NULL,
                                              ltime INT NOT NULL,
                                              mtime INT NOT NULL,
                                              persistent INT NOT NULL
                                              DEFAULT 1)""")

            sql.execute("""INSERT INTO tracks(id, name, uri, duration,
                        tracknumber, discnumber, discname, album_id,
                        year, popularity, ltime, mtime, persistent) SELECT
                            id, name, filepath, duration,
                            tracknumber, discnumber, discname, album_id,
                            year, popularity, ltime, mtime, persistent FROM
                          tmp_tracks""")
            sql.execute("DROP TABLE tmp_tracks")
            result = sql.execute("SELECT rowid FROM tracks")
            for track_id in list(itertools.chain(*result)):
                result = sql.execute("SELECT uri FROM tracks WHERE rowid=?",
                                     (track_id,))
                v = result.fetchone()
                if v is not None:
                    uri = v[0]
                    if uri.startswith("/"):
                        uri = GLib.filename_to_uri(uri)
                        sql.execute("UPDATE tracks set uri=? WHERE rowid=?",
                                    (uri, track_id))
        with SqlCursor(App().playlists) as sql:
            sql.execute("ALTER TABLE tracks RENAME TO tmp_tracks")
            sql.execute("""CREATE TABLE tracks (playlist_id INT NOT NULL,
                                                uri TEXT NOT NULL)""")
            sql.execute("""INSERT INTO tracks(playlist_id, uri) SELECT
                            playlist_id, filepath FROM tmp_tracks""")
            sql.execute("DROP TABLE tmp_tracks")
            result = sql.execute("SELECT uri FROM tracks")
            for path in list(itertools.chain(*result)):
                if path.startswith("/"):
                    uri = GLib.filename_to_uri(path)
                    sql.execute("UPDATE tracks set uri=? WHERE uri=?",
                                (uri, path))

    def __upgrade_15(self, db):
        """
            Fix broken 0.9.208 release
        """
        pass

    def __upgrade_16(self, db):
        """
            Get rid of paths
        """
        paths = App().settings.get_value("music-path")
        uris = []
        for path in paths:
            uris.append(GLib.filename_to_uri(path))
        App().settings.set_value("music-uris", GLib.Variant("as", uris))
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE albums RENAME TO tmp_albums")
            sql.execute("""CREATE TABLE albums (
                                              id INTEGER PRIMARY KEY,
                                              name TEXT NOT NULL,
                                              no_album_artist BOOLEAN NOT NULL,
                                              year INT,
                                              uri TEXT NOT NULL,
                                              popularity INT NOT NULL,
                                              synced INT NOT NULL,
                                              mtime INT NOT NULL)""")

            sql.execute("""INSERT INTO albums(id, name, no_album_artist,
                        year, uri, popularity, synced, mtime) SELECT
                            id, name, no_album_artist,
                            year, path, popularity, synced, mtime FROM
                            tmp_albums""")
            sql.execute("DROP TABLE tmp_albums")
            result = sql.execute("SELECT rowid, uri FROM albums")
            for (rowid, uri) in result:
                if uri.startswith("/"):
                    uri = GLib.filename_to_uri(uri)
                    sql.execute("UPDATE albums set uri=? WHERE rowid=?",
                                (uri, rowid))

    def __upgrade_18(self, db):
        """
            Upgrade history
        """
        with SqlCursor(History()) as sql:
            sql.execute("ALTER TABLE history ADD loved_album\
                        INT NOT NULL DEFAULT 0")

    def __upgrade_19(self, db):
        """
            Upgrade history
        """
        with SqlCursor(History()) as sql:
            try:
                sql.execute("ALTER TABLE history ADD album_rate\
                            INT NOT NULL DEFAULT -1")
                sql.execute("ALTER TABLE history ADD rate\
                            INT NOT NULL DEFAULT -1")
            except:
                pass  # May fails if History was non existent
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE tracks ADD rate\
                        INT NOT NULL DEFAULT -1")
            sql.execute("ALTER TABLE albums ADD rate\
                        INT NOT NULL DEFAULT -1")

    def __upgrade_20(self, db):
        """
            Add mtimes tables
        """
        mtime = int(time())
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE album_genres\
                         ADD mtime INT NOT NULL DEFAULT %s" % mtime)
            sql.execute("ALTER TABLE track_genres\
                         ADD mtime INT NOT NULL DEFAULT %s" % mtime)
            # Remove mtimes from albums table
            sql.execute("CREATE TEMPORARY TABLE backup(\
                                          id INTEGER PRIMARY KEY,\
                                          name TEXT NOT NULL,\
                                          no_album_artist BOOLEAN NOT NULL,\
                                          year INT,\
                                          uri TEXT NOT NULL,\
                                          popularity INT NOT NULL,\
                                          rate INT NOT NULL,\
                                          loved INT NOT NULL,\
                                          synced INT NOT NULL)")
            sql.execute("INSERT INTO backup\
                            SELECT id,\
                                   name,\
                                   no_album_artist,\
                                   year,\
                                   uri,\
                                   popularity,\
                                   rate,\
                                   loved,\
                                   synced FROM albums")
            sql.execute("DROP TABLE albums")
            sql.execute("CREATE TABLE albums(\
                                          id INTEGER PRIMARY KEY,\
                                          name TEXT NOT NULL,\
                                          no_album_artist BOOLEAN NOT NULL,\
                                          year INT,\
                                          uri TEXT NOT NULL,\
                                          popularity INT NOT NULL,\
                                          rate INT NOT NULL,\
                                          loved INT NOT NULL,\
                                          synced INT NOT NULL)")
            sql.execute("INSERT INTO albums\
                            SELECT id,\
                                   name,\
                                   no_album_artist,\
                                   year,\
                                   uri,\
                                   popularity,\
                                   rate,\
                                   loved,\
                                   synced FROM backup")
            sql.execute("DROP TABLE backup")
            # Remove mtimes from tracks table
            sql.execute("CREATE TEMPORARY TABLE backup(\
                                          id INTEGER PRIMARY KEY,\
                                          name TEXT NOT NULL,\
                                          uri TEXT NOT NULL,\
                                          duration INT,\
                                          tracknumber INT,\
                                          discnumber INT,\
                                          discname TEXT,\
                                          album_id INT NOT NULL,\
                                          year INT,\
                                          popularity INT NOT NULL,\
                                          rate INT NOT NULL,\
                                          ltime INT NOT NULL,\
                                          persistent INT NOT NULL)")
            sql.execute("INSERT INTO backup\
                            SELECT id,\
                                   name,\
                                   uri,\
                                   duration,\
                                   tracknumber,\
                                   discnumber,\
                                   discname,\
                                   album_id,\
                                   year,\
                                   popularity,\
                                   rate,\
                                   ltime,\
                                   persistent FROM tracks")
            sql.execute("DROP TABLE tracks")
            sql.execute("CREATE TABLE tracks(\
                                          id INTEGER PRIMARY KEY,\
                                          name TEXT NOT NULL,\
                                          uri TEXT NOT NULL,\
                                          duration INT,\
                                          tracknumber INT,\
                                          discnumber INT,\
                                          discname TEXT,\
                                          album_id INT NOT NULL,\
                                          year INT,\
                                          popularity INT NOT NULL,\
                                          rate INT NOT NULL,\
                                          ltime INT NOT NULL,\
                                          persistent INT NOT NULL)")
            sql.execute("INSERT INTO tracks\
                            SELECT id,\
                                   name,\
                                   uri,\
                                   duration,\
                                   tracknumber,\
                                   discnumber,\
                                   discname,\
                                   album_id,\
                                   year,\
                                   popularity,\
                                   rate,\
                                   ltime,\
                                   persistent FROM backup")
            sql.execute("DROP TABLE backup")

    def __upgrade_21(self, db):
        pass

    def __upgrade_22(self, db):
        """
            Remove Charts/Web entries
        """
        with SqlCursor(db, True) as sql:
            # Remove persistent from tracks table
            sql.execute("CREATE TEMPORARY TABLE backup(\
                                          id INTEGER PRIMARY KEY,\
                                          name TEXT NOT NULL,\
                                          uri TEXT NOT NULL,\
                                          duration INT,\
                                          tracknumber INT,\
                                          discnumber INT,\
                                          discname TEXT,\
                                          album_id INT NOT NULL,\
                                          year INT,\
                                          popularity INT NOT NULL,\
                                          rate INT NOT NULL,\
                                          ltime INT NOT NULL)")
            sql.execute("INSERT INTO backup\
                            SELECT id,\
                                   name,\
                                   uri,\
                                   duration,\
                                   tracknumber,\
                                   discnumber,\
                                   discname,\
                                   album_id,\
                                   year,\
                                   popularity,\
                                   rate,\
                                   ltime FROM tracks")
            sql.execute("DROP TABLE tracks")
            sql.execute("CREATE TABLE tracks(\
                                          id INTEGER PRIMARY KEY,\
                                          name TEXT NOT NULL,\
                                          uri TEXT NOT NULL,\
                                          duration INT,\
                                          tracknumber INT,\
                                          discnumber INT,\
                                          discname TEXT,\
                                          album_id INT NOT NULL,\
                                          year INT,\
                                          popularity INT NOT NULL,\
                                          rate INT NOT NULL,\
                                          ltime INT NOT NULL)")
            sql.execute("INSERT INTO tracks\
                            SELECT id,\
                                   name,\
                                   uri,\
                                   duration,\
                                   tracknumber,\
                                   discnumber,\
                                   discname,\
                                   album_id,\
                                   year,\
                                   popularity,\
                                   rate,\
                                   ltime FROM backup")
            sql.execute("DROP TABLE backup")

    def __upgrade_23(self, db):
        """
            Restore back mtime in tracks
        """
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE tracks ADD mtime INT")
            sql.execute("ALTER TABLE albums ADD mtime INT")

            sql.execute("UPDATE tracks SET mtime = (\
                            SELECT mtime FROM track_genres\
                            WHERE track_genres.track_id=tracks.rowid)")

            sql.execute("UPDATE albums SET mtime = (\
                            SELECT mtime FROM album_genres\
                            WHERE album_genres.album_id=albums.rowid)")
            # Remove mtime from album_genres table
            sql.execute("CREATE TABLE album_genres2 (\
                                                album_id INT NOT NULL,\
                                                genre_id INT NOT NULL)")
            sql.execute("INSERT INTO album_genres2\
                            SELECT album_id,\
                                   genre_id FROM album_genres")
            sql.execute("DROP TABLE album_genres")
            sql.execute("ALTER TABLE album_genres2 RENAME TO album_genres")

            # Remove mtime from track_genres table
            sql.execute("CREATE TABLE track_genres2 (\
                                                track_id INT NOT NULL,\
                                                genre_id INT NOT NULL)")
            sql.execute("INSERT INTO track_genres2\
                            SELECT track_id,\
                                   genre_id FROM track_genres")
            sql.execute("DROP TABLE track_genres")
            sql.execute("ALTER TABLE track_genres2 RENAME TO track_genres")

    def __upgrade_26(self, db):
        """
            Rename album_id to mb_album_id in albums
        """
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE albums RENAME TO tmp_albums")
            sql.execute("""CREATE TABLE albums (
                               id INTEGER PRIMARY KEY,
                               name TEXT NOT NULL,
                               mb_album_id TEXT,
                               no_album_artist BOOLEAN NOT NULL,
                               year INT,
                               uri TEXT NOT NULL,
                               popularity INT NOT NULL,
                               rate INT NOT NULL,
                               loved INT NOT NULL,
                               mtime INT NOT NULL,
                               synced INT NOT NULL)""")

            sql.execute("""INSERT INTO albums (id, name, mb_album_id,
                            no_album_artist, year, uri, popularity, rate,
                            loved, mtime, synced) SELECT id, name, album_id,
                            no_album_artist, year, uri, popularity, rate,
                            loved, mtime, synced FROM tmp_albums""")
            sql.execute("DROP TABLE tmp_albums")

    def __upgrade_28(self, db):
        """
            Upgrade setting based on db
            https://gitlab.gnome.org/gnumdk/lollypop/issues/1368
        """
        with SqlCursor(db, True) as sql:
            result = sql.execute("SELECT albums.rowid\
                                  FROM albums, album_artists\
                                  WHERE album_artists.artist_id=?\
                                  AND album_artists.album_id=albums.rowid\
                                  LIMIT 1",
                                 (Type.COMPILATIONS,))
            if list(itertools.chain(*result)):
                App().settings.set_value("show-compilations",
                                         GLib.Variant("b", True))

    def __upgrade_29(self, db):
        """
            Upgrade year to year
        """
        from time import strptime, mktime
        from datetime import datetime
        for item in ["albums", "tracks"]:
            with SqlCursor(db, True) as sql:
                sql.execute("ALTER TABLE %s ADD timestamp INT" % item)
                result = sql.execute("SELECT rowid, year FROM %s" % item)
                for (rowid, year) in result:
                    if year is None:
                        continue
                    elif len(str(year)) == 2:
                        struct = strptime(str(year), "%y")
                    elif len(str(year)) == 4:
                        struct = strptime(str(year), "%Y")
                    else:
                        continue
                    dt = datetime.fromtimestamp(mktime(struct))
                    timestamp = dt.timestamp()
                    sql.execute(
                        "UPDATE %s set timestamp=? WHERE rowid=?" % item,
                        (timestamp, rowid))

    def __upgrade_31(self, db):
        """
            Delete history database related to upgrade 30
        """
        try:
            LOCAL_PATH = GLib.get_user_data_dir() + "/lollypop"
            DB_PATH = "%s/history.db" % LOCAL_PATH
            f = Gio.File.new_for_path(DB_PATH)
            f.delete(None)
        except Exception as e:
            Logger.error("DatabaseAlbumsUpgrade::__upgrade_31(): %s", e)

    def __upgrade_36(self, db):
        """
            Restore back mtime in tracks
        """
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE tracks ADD storage_type INT")
            sql.execute("ALTER TABLE albums ADD storage_type INT")
            sql.execute("UPDATE tracks SET storage_type=?\
                         WHERE mtime > 0", (StorageType.COLLECTION,))
            sql.execute("UPDATE albums SET storage_type=?\
                         WHERE mtime > 0", (StorageType.COLLECTION,))
            sql.execute("UPDATE tracks SET storage_type=?\
                         WHERE mtime = -1", (StorageType.SAVED,))
            sql.execute("UPDATE albums SET storage_type=?\
                         WHERE mtime = -1", (StorageType.SAVED,))

    def __upgrade_37(self, db):
        """
            Update Type.WEB and Type.COMPILATIONS
        """
        App().settings.reset("shown-album-lists")
        with SqlCursor(db, True) as sql:
            sql.execute("UPDATE track_genres SET genre_id=-9\
                         WHERE genre_id=-22")
            sql.execute("UPDATE album_genres SET genre_id=-9\
                         WHERE genre_id=-22")
            sql.execute("UPDATE album_artists SET artist_id=-10\
                         WHERE artist_id=-2001")

    def __upgrade_39(self, db):
        """
            Reset Spotify tracks: we are now using Spotify id as MusicBrainz id
        """
        with SqlCursor(db, True) as sql:
            for storage_type in [StorageType.SPOTIFY_NEW_RELEASES,
                                 StorageType.SPOTIFY_SIMILARS]:
                sql.execute("DELETE FROM tracks WHERE\
                             storage_type=? AND mb_track_id=''",
                            (storage_type,))
            sql.execute("DELETE FROM track_artists\
                         WHERE track_artists.track_id NOT IN (\
                            SELECT tracks.rowid FROM tracks)")
            sql.execute("DELETE FROM track_genres\
                         WHERE track_genres.track_id NOT IN (\
                            SELECT tracks.rowid FROM tracks)")
            sql.execute("DELETE FROM albums WHERE albums.rowid NOT IN (\
                            SELECT tracks.album_id FROM tracks)")
            sql.execute("DELETE FROM album_genres\
                         WHERE album_genres.album_id NOT IN (\
                            SELECT albums.rowid FROM albums)")
            sql.execute("DELETE FROM album_artists\
                         WHERE album_artists.album_id NOT IN (\
                            SELECT albums.rowid FROM albums)")
            sql.execute("DELETE FROM albums_timed_popularity\
                         WHERE albums_timed_popularity.album_id NOT IN (\
                            SELECT albums.rowid FROM albums)")
            sql.execute("DELETE FROM artists WHERE artists.rowid NOT IN (\
                            SELECT album_artists.artist_id\
                            FROM album_artists) AND artists.rowid NOT IN (\
                                SELECT track_artists.artist_id\
                                FROM track_artists)")

    def __upgrade_44(self, db):
        """
            Delete spotify albums as spotify id is not stored in URI
        """
        from lollypop.database_albums import AlbumsDatabase
        from lollypop.database_artists import ArtistsDatabase
        from lollypop.database_tracks import TracksDatabase
        albums = AlbumsDatabase(db)
        artists = ArtistsDatabase(db)
        tracks = TracksDatabase(db)
        for storage_type in [StorageType.SPOTIFY_NEW_RELEASES,
                             StorageType.SPOTIFY_SIMILARS,
                             StorageType.DEEZER_CHARTS]:
            album_ids = albums.get_for_storage_type(storage_type)
            for album_id in album_ids:
                # EPHEMERAL with not tracks will be cleaned below
                albums.set_storage_type(album_id, StorageType.EPHEMERAL)
                tracks.remove_album(album_id)
        tracks.clean()
        albums.clean()
        artists.clean()

    def __upgrade_45(self, db):
        """
            Add lp_album_id/lp_track_id
        """
        with SqlCursor(db, True) as sql:
            sql.execute("ALTER TABLE tracks ADD lp_track_id TEXT")
            sql.execute("ALTER TABLE albums ADD lp_album_id TEXT")

    def __upgrade_46(self, db):
        """
            Populate lp_album_id/lp_track_id
        """
        queue = LOLLYPOP_DATA_PATH + "/queue.bin"
        try:
            f = Gio.File.new_for_path(queue)
            f.delete(None)
        except:
            pass
        from lollypop.database_albums import AlbumsDatabase
        from lollypop.database_tracks import TracksDatabase
        from lollypop.utils import get_lollypop_album_id, get_lollypop_track_id
        albums = AlbumsDatabase(db)
        tracks = TracksDatabase(db)

        def do_migration(dialog, label, progress):
            GLib.idle_add(
                label.set_text,
                _("Please wait while Lollypop is updating albums"))
            album_ids = albums.get_ids([], [], StorageType.ALL, True)
            album_ids += albums.get_compilation_ids([], StorageType.ALL, True)
            count = len(album_ids)
            i = 0
            for album_id in album_ids:
                if i % 10 == 0:
                    GLib.idle_add(progress.set_fraction, i / count)
                name = albums.get_name(album_id)
                artists = ";".join(albums.get_artists(album_id))
                lp_album_id = get_lollypop_album_id(name, artists)
                albums.set_lp_album_id(album_id, lp_album_id)
                i += 1

            track_ids = tracks.get_ids(StorageType.ALL, True)
            count = len(track_ids)
            i = 0
            GLib.idle_add(
                label.set_text,
                _("Please wait while Lollypop is updating tracks"))
            for track_id in track_ids:
                if i % 10 == 0:
                    GLib.idle_add(progress.set_fraction, i / count)
                name = tracks.get_name(track_id)
                artists = ";".join(tracks.get_artists(track_id))
                album_name = tracks.get_album_name(track_id)
                lp_track_id = get_lollypop_track_id(name, artists, album_name)
                tracks.set_lp_track_id(track_id, lp_track_id)
                i += 1
            GLib.idle_add(dialog.destroy)

        dialog = Gtk.MessageDialog(buttons=Gtk.ButtonsType.NONE)
        progress = Gtk.ProgressBar.new()
        progress.show()
        label = Gtk.Label.new()
        label.show()
        grid = Gtk.Grid.new()
        grid.set_orientation(Gtk.Orientation.VERTICAL)
        grid.set_row_spacing(10)
        grid.show()
        grid.add(label)
        grid.add(progress)
        dialog.set_image(grid)
        helper = TaskHelper()
        helper.run(do_migration, dialog, label, progress)
        dialog.run()

    def __upgrade_47(self, db):
        """
        Update the covers for playlists.
        """
        from lollypop.art import clean_all_cache
        clean_all_cache()

    def __upgrade_48(self, db):
        """
            Convert loved to new flags
        """
        with SqlCursor(db, True) as sql:
            sql.execute("UPDATE tracks set loved=2 where loved=1")
            sql.execute("UPDATE tracks set loved=1 where loved=0")
            sql.execute("UPDATE tracks set loved=4 where loved=-1")
            sql.execute("UPDATE albums set loved=2 where loved=1")
            sql.execute("UPDATE albums set loved=1 where loved=0")
            sql.execute("UPDATE albums set loved=4 where loved=-1")
