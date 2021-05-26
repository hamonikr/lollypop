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

from gi.repository import GObject, GLib, Gio, TotemPlParser

from gettext import gettext as _
import itertools
import sqlite3
from datetime import datetime
from threading import Lock
import json

from lollypop.database import Database
from lollypop.define import App, Type
from lollypop.objects_track import Track
from lollypop.sqlcursor import SqlCursor
from lollypop.localized import LocalizedCollation
from lollypop.shown import ShownPlaylists
from lollypop.utils import emit_signal, get_default_storage_type
from lollypop.utils_file import get_mtime
from lollypop.logger import Logger
from lollypop.database_upgrade import DatabasePlaylistsUpgrade


class Playlists(GObject.GObject):
    """
        Playlists manager
    """
    __LOCAL_PATH = GLib.get_user_data_dir() + "/lollypop"
    _DB_PATH = "%s/playlists.db" % __LOCAL_PATH
    __gsignals__ = {
        "playlists-added": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "playlists-removed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "playlists-updated": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "playlists-renamed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "playlist-track-added": (
            GObject.SignalFlags.RUN_FIRST, None, (int, str)),
        "playlist-track-removed": (
            GObject.SignalFlags.RUN_FIRST, None, (int, str))
    }
    __create_playlists = """CREATE TABLE playlists (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            synced INT NOT NULL DEFAULT 0,
                            smart_enabled INT NOT NULL DEFAULT 0,
                            smart_sql TEXT,
                            uri TEXT,
                            mtime BIGINT NOT NULL)"""

    __create_tracks = """CREATE TABLE tracks (
                        playlist_id INT NOT NULL,
                        uri TEXT NOT NULL)"""

    def __init__(self):
        """
            Init playlists manager
        """
        self.thread_lock = Lock()
        GObject.GObject.__init__(self)
        upgrade = DatabasePlaylistsUpgrade()
        # Create db schema
        f = Gio.File.new_for_path(self._DB_PATH)
        if not f.query_exists():
            try:
                with SqlCursor(self, True) as sql:
                    sql.execute(self.__create_playlists)
                    sql.execute(self.__create_tracks)
                    sql.execute("PRAGMA user_version=%s" % upgrade.version)
            except:
                pass
        else:
            upgrade.upgrade(self)

    def get_new_name(self):
        """
            Get a name for a new playlist
            @return str
        """
        existing_playlists = []
        for (playlist_id, name) in App().playlists.get():
            existing_playlists.append(name)

        # Search for an available name
        count = 1
        name = _("New playlist ") + str(count)
        while name in existing_playlists:
            count += 1
            name = _("New playlist ") + str(count)
        return name

    def add(self, name):
        """
            Add a playlist
            @param name as str
            @return playlist_id as int
            @thread safe
        """
        if name == _("Loved tracks"):
            return Type.LOVED
        lastrowid = 0
        with SqlCursor(self, True) as sql:
            result = sql.execute("INSERT INTO playlists (name, mtime)\
                                  VALUES (?, ?)",
                                 (name, 0))
            lastrowid = result.lastrowid
        emit_signal(self, "playlists-added", lastrowid)
        return lastrowid

    def exists(self, playlist_id):
        """
            Return True if playlist exists
            @param playlist_id as int
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT rowid\
                                  FROM playlists\
                                  WHERE rowid=?",
                                 (playlist_id,))
            v = result.fetchone()
            if v is not None:
                return True
            else:
                return False

    def rename(self, playlist_id, name):
        """
            Rename playlist
            @param playlist_id as int
            @param name as str
        """
        with SqlCursor(self, True) as sql:
            sql.execute("UPDATE playlists\
                        SET name=?\
                        WHERE rowid=?",
                        (name, playlist_id))
        emit_signal(self, "playlists-renamed", playlist_id)
        App().art.remove_from_cache("playlist_" + name, "ROUNDED")

    def remove(self, playlist_id):
        """
            Remove playlist
            @param playlist_id as int
        """
        name = self.get_name(playlist_id)
        with SqlCursor(self, True) as sql:
            sql.execute("DELETE FROM playlists\
                        WHERE rowid=?",
                        (playlist_id,))
            sql.execute("DELETE FROM tracks\
                        WHERE playlist_id=?",
                        (playlist_id,))
        emit_signal(self, "playlists-removed", playlist_id)
        App().art.remove_from_cache("playlist_" + name, "ROUNDED")

    def clear(self, playlist_id):
        """
            Clear playlsit
            @param playlist_id as int
        """
        with SqlCursor(self, True) as sql:
            sql.execute("DELETE FROM tracks\
                         WHERE playlist_id=?", (playlist_id,))
        self.sync_to_disk(playlist_id)

    def add_uri(self, playlist_id, uri, signal=False):
        """
            Add uri to playlist
            @param playlist_id as int
            @param uri as str
            @param signal as bool
        """
        if self.exists_track(playlist_id, uri):
            return
        with SqlCursor(self, True) as sql:
            sql.execute("INSERT INTO tracks VALUES (?, ?)", (playlist_id, uri))
        if signal:
            emit_signal(self, "playlist-track-added", playlist_id, uri)

    def add_uris(self, playlist_id, uris, signal=False):
        """
            Add uris to playlists (even if exists)
            @param playlist_id as int
            @param uris as [str]
            @param signal as bool
        """
        for uri in uris:
            self.add_uri(playlist_id, uri, signal)
        self.sync_to_disk(playlist_id)

    def add_tracks(self, playlist_id, tracks, signal=False):
        """
            Add tracks to playlist
            @param playlist_id as int
            @param tracks as [Track]
            @param signal as bool
        """
        for track in tracks:
            self.add_uri(playlist_id, track.uri, signal)
        self.sync_to_disk(playlist_id)

    def remove_uri(self, playlist_id, uri, signal=False):
        """
            Remove uri from playlist
            @param playlist_id as int
            @param uri a str
            @param signal as bool
        """
        if not self.exists_track(playlist_id, uri):
            return
        with SqlCursor(self, True) as sql:
            sql.execute("DELETE FROM tracks WHERE uri=? AND playlist_id=?",
                        (uri, playlist_id))
        if signal:
            emit_signal(self, "playlist-track-removed", playlist_id, uri)

    def remove_uris(self, playlist_id, uris, signal=False):
        """
            Remove uris from playlist
            @param playlist_id as int
            @param uris as [str]
            @param signal as bool
        """
        for uri in uris:
            self.remove_uri(playlist_id, uri, signal)
        self.sync_to_disk(playlist_id)

    def remove_tracks(self, playlist_id, tracks, signal=False):
        """
            Remove tracks from playlist
            @param playlist_id as int
            @param tracks as [Track]
            @param signal as bool
        """
        for track in tracks:
            self.remove_uri(playlist_id, track.uri, signal)
        self.sync_to_disk(playlist_id)

    def get(self):
        """
            Return availables playlists
            @return [int, str, str]
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT rowid, name\
                                  FROM playlists\
                                  ORDER BY name\
                                  COLLATE NOCASE COLLATE LOCALIZED")
            return list(result)

    def get_ids(self):
        """
            Return availables playlists
            @return [int]
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT rowid\
                                  FROM playlists\
                                  ORDER BY name\
                                  COLLATE NOCASE COLLATE LOCALIZED")
            return list(itertools.chain(*result))

    def get_track_uris(self, playlist_id):
        """
            Return available track uris for playlist
            @param playlist_id as int
            @return [str]
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT uri\
                                  FROM tracks\
                                  WHERE playlist_id=?", (playlist_id,))
            return list(itertools.chain(*result))

    def get_smart_track_uris(self, playlist_id):
        """
            Return available track uris for playlist
            @param playlist_id as int
            @return [str]
        """
        request = self.get_smart_sql(playlist_id)
        # We need to inject skipped/storage_type
        storage_type = get_default_storage_type()
        split = request.split("ORDER BY")
        split[0] += " AND tracks.loved != %s" % Type.NONE
        split[0] += " AND tracks.storage_type&%s " % storage_type
        track_ids = App().db.execute("ORDER BY".join(split))
        return [Track(track_id).uri for track_id in track_ids]

    def get_track_ids(self, playlist_id):
        """
            Return availables track ids for playlist
            @param playlist_id as int
            @return [int]
        """
        track_ids = []
        limit = App().settings.get_value("view-limit").get_int32()
        storage_type = get_default_storage_type()
        if playlist_id == Type.POPULARS:
            track_ids = App().tracks.get_populars([], storage_type,
                                                  False, limit)
        elif playlist_id == Type.RECENTS:
            track_ids = App().tracks.get_recently_listened_to(storage_type,
                                                              False,
                                                              limit)
        elif playlist_id == Type.LITTLE:
            track_ids = App().tracks.get_little_played(storage_type,
                                                       False,
                                                       limit)
        elif playlist_id == Type.RANDOMS:
            track_ids = App().tracks.get_randoms([], storage_type,
                                                 False, limit)
        elif playlist_id == Type.SKIPPED:
            track_ids = App().tracks.get_skipped(storage_type)
        elif playlist_id == Type.ALL:
            track_ids = App().tracks.get_ids(storage_type, False)
        elif playlist_id == Type.LOVED:
            track_ids = App().tracks.get_loved_track_ids([], storage_type)
        else:
            with SqlCursor(self) as sql:
                result = sql.execute("SELECT music.tracks.rowid\
                                      FROM tracks, music.tracks\
                                      WHERE tracks.playlist_id=?\
                                      AND music.tracks.uri=\
                                      main.tracks.uri",
                                     (playlist_id,))
                track_ids = list(itertools.chain(*result))
        return track_ids

    def get_tracks(self, playlist_id):
        """
            Return availables tracks for playlist
            @param playlist_id as int
            @return [Track]
        """
        return [Track(track_id)
                for track_id in self.get_track_ids(playlist_id)]

    def get_duration(self, playlist_id):
        """
            Return playlist duration
            @param playlist_id as int
            @return duration as int
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT SUM(music.tracks.duration)\
                                  FROM tracks, music.tracks\
                                  WHERE tracks.playlist_id=?\
                                  AND music.tracks.uri=\
                                  main.tracks.uri",
                                 (playlist_id,))
            v = result.fetchone()
            if v is not None and v[0] is not None:
                return v[0]
            return 0

    def get_id(self, playlist_name):
        """
            Get playlist id
            @param playlist_name as str
            @return playlst id as int
        """
        if playlist_name == _("Loved tracks"):
            return Type.LOVED

        with SqlCursor(self) as sql:
            result = sql.execute("SELECT rowid\
                                 FROM playlists\
                                 WHERE name=?", (playlist_name,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def get_name(self, playlist_id):
        """
            Get playlist name
            @param playlist_id as int
            @return playlist name as str
        """
        if playlist_id < 0:
            for (id, name, sortname) in ShownPlaylists.get(True):
                if id == playlist_id:
                    return name

        with SqlCursor(self) as sql:
            result = sql.execute("SELECT name\
                                 FROM playlists\
                                 WHERE rowid=?", (playlist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return ""

    def get_synced(self, playlist_id, index):
        """
            True if playlist synced
            @param playlist_id as int
            @param index as int
            @return bool
        """
        if playlist_id < 0:
            internal_ids = App().settings.get_value(
                    "sync-internal-ids").get_string()
            try:
                data = json.loads(internal_ids)
                data.keys()
            except:
                data = {}
            synced_ids = []
            for synced_id in data.keys():
                if data[synced_id] & (1 << index):
                    synced_ids.append(int(synced_id))
            return playlist_id in synced_ids
        else:
            with SqlCursor(self) as sql:
                result = sql.execute("SELECT synced\
                                     FROM playlists\
                                     WHERE rowid=?", (playlist_id,))
                v = result.fetchone()
                if v is not None:
                    return v[0] & (1 << index)
                return False

    def get_synced_ids(self, index):
        """
            Return availables synced playlists
            @return [int]
        """
        with SqlCursor(self) as sql:
            internal_ids = App().settings.get_value(
                    "sync-internal-ids").get_string()
            try:
                data = json.loads(internal_ids)
                data.keys()
            except:
                data = {}
            synced_ids = []
            for playlist_id in data.keys():
                if data[playlist_id] & (1 << index):
                    synced_ids.append(int(playlist_id))
            result = sql.execute("SELECT rowid\
                                  FROM playlists\
                                  WHERE synced & (1 << ?)\
                                  ORDER BY name\
                                  COLLATE NOCASE COLLATE LOCALIZED",
                                 (index,))
            return list(itertools.chain(*result)) + synced_ids

    def get_smart(self, playlist_id):
        """
            True if playlist is smart
            @param playlist_id as int
            @return bool
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT smart_enabled\
                                 FROM playlists\
                                 WHERE rowid=?", (playlist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return False

    def get_smart_sql(self, playlist_id):
        """
            Get SQL smart request
            @param playlist_id as int
            @return str
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT smart_sql\
                                 FROM playlists\
                                 WHERE rowid=?", (playlist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def set_synced(self, playlist_id, synced):
        """
            Mark playlist as synced
            @param playlist_id as int
            @param synced as bool
        """
        if playlist_id < 0:
            internal_ids = App().settings.get_value(
                "sync-internal-ids").get_string()
            try:
                data = json.loads(internal_ids)
                data.keys()
            except:
                data = {}
            data[str(playlist_id)] = synced
            internal_ids = json.dumps(data)
            App().settings.set_value("sync-internal-ids",
                                     GLib.Variant("s", internal_ids))
        else:
            with SqlCursor(self, True) as sql:
                sql.execute("UPDATE playlists\
                            SET synced=?\
                            WHERE rowid=?",
                            (synced, playlist_id))

    def set_smart(self, playlist_id, smart):
        """
            Mark playlist as smart
            @param playlist_id as int
            @param smart as bool
        """
        with SqlCursor(self, True) as sql:
            sql.execute("UPDATE playlists\
                        SET smart_enabled=?\
                        WHERE rowid=?",
                        (smart, playlist_id))
            emit_signal(self, "playlists-updated", playlist_id)

    def set_smart_sql(self, playlist_id, request):
        """
            Set playlist SQL smart request
            @param playlist_id as int
            @param request as str
        """
        name = self.get_name(playlist_id)
        # Clear cache
        App().art.remove_from_cache("playlist_" + name, "ROUNDED")
        with SqlCursor(self, True) as sql:
            sql.execute("UPDATE playlists\
                        SET smart_sql=?\
                        WHERE rowid=?",
                        (request, playlist_id))
            emit_signal(self, "playlists-updated", playlist_id)

    def get_position(self, playlist_id, track_id):
        """
            Get track position in playlist
            @param playlist_id as int
            @param track_id as int
            @return position as int
        """
        i = 0
        for tid in self.get_track_ids(playlist_id):
            if track_id == tid:
                break
            i += 1
        return i

    def exists_track(self, playlist_id, uri):
        """
            Check if track id exist in playlist
            @param playlist_id as int
            @param uri as str
            @return bool
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT uri\
                                  FROM tracks\
                                  WHERE playlist_id=?\
                                  AND uri=?", (playlist_id, uri))
            v = result.fetchone()
            if v is not None:
                return True
            return False

    def set_sync_uri(self, playlist_id, uri):
        """
            Set sync URI
            @param playlist_id as int
            @param uri as str
        """
        with SqlCursor(self, True) as sql:
            sql.execute("UPDATE playlists\
                        SET uri=?\
                        WHERE rowid=?", (uri, playlist_id))

    def get_sync_uri(self, playlist_id):
        """
            Get sync URI
            @param playlist_id as int
            @return str/None
        """
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT uri\
                                  FROM playlists\
                                  WHERE rowid=?", (playlist_id,))
            v = result.fetchone()
            if v is not None:
                return v[0]
            return None

    def sync_to_disk(self, playlist_id, create=False):
        """
            Sync playlist_id to disk
            @param playlist_id as int
            @param create as bool => create file
        """
        try:
            name = self.get_name(playlist_id)
            # Clear cache
            App().art.remove_from_cache("playlist_" + name, "ROUNDED")
            playlist_uri = self.get_sync_uri(playlist_id)
            if playlist_uri is None:
                return
            f = Gio.File.new_for_uri(playlist_uri)
            if not f.query_exists() and not create:
                return
            if self.get_smart(playlist_id):
                uris = self.get_smart_track_uris(playlist_id)
            else:
                uris = self.get_track_uris(playlist_id)
            if not uris:
                return
            stream = f.replace(None, False,
                               Gio.FileCreateFlags.REPLACE_DESTINATION, None)
            stream.write("#EXTM3U\n".encode("utf-8"))
            playlist_dir_uri = playlist_uri.replace(f.get_basename(), "")
            for uri in uris:
                if uri.startswith("web://"):
                    continue
                if playlist_dir_uri in uri:
                    filepath = uri.replace(playlist_dir_uri, "")
                    string = "%s\n" % GLib.uri_unescape_string(filepath, None)
                else:
                    string = "%s\n" % uri
                stream.write(string.encode("utf-8"))
            stream.close()
        except Exception as e:
            Logger.error("Playlists::sync_to_disk(): %s", e)

    def exists_album(self, playlist_id, album):
        """
            Return True if object_id is already present in playlist
            @param playlist_id as int
            @param album as Album/Disc
            @return bool
        """
        # We do not use Album object for performance reasons
        playlist_uris = self.get_track_uris(playlist_id)
        track_uris = album.track_uris
        return len(set(playlist_uris) & set(track_uris)) == len(track_uris)

    def remove_device(self, index):
        """
            Remove device from DB
            @param index as int => device index
        """
        with SqlCursor(self, True) as sql:
            sql.execute("UPDATE playlists SET synced = synced & ~(1<<?)",
                        (index,))

    def import_tracks(self, uri):
        """
            Import file as playlist
            @param uri as str
        """
        f = Gio.File.new_for_uri(uri)
        # Create playlist and get id
        basename = ".".join(f.get_basename().split(".")[:-1])
        playlist_id = self.get_id(basename)
        # Do not reimport playlists
        if playlist_id is not None:
            return
        playlist_id = self.add(basename)
        # Check mtime has been updated
        with SqlCursor(self) as sql:
            result = sql.execute("SELECT mtime\
                                 FROM playlists\
                                 WHERE rowid=?", (playlist_id,))
            v = result.fetchone()
            if v is not None:
                db_mtime = v[0]
            else:
                db_mtime = 0
            info = f.query_info(Gio.FILE_ATTRIBUTE_TIME_MODIFIED,
                                Gio.FileQueryInfoFlags.NONE, None)
            mtime = get_mtime(info)
            if db_mtime >= mtime:
                return

        # Load playlist
        parser = TotemPlParser.Parser.new()
        uris = []
        parser.connect("entry-parsed", self.__on_entry_parsed,
                       playlist_id, uris)
        parser.parse_async(f.get_uri(), True,
                           None, self.__on_parse_finished,
                           playlist_id, uris)

    def get_cursor(self):
        """
            Return a new sqlite cursor
        """
        try:
            sql = sqlite3.connect(self._DB_PATH, 600.0)
            sql.execute('ATTACH DATABASE "%s" AS music' % Database.DB_PATH)
            sql.create_collation("LOCALIZED", LocalizedCollation())
            return sql
        except:
            exit(-1)

#######################
# PRIVATE             #
#######################
    def __on_parse_finished(self, parser, result, playlist_id, uris):
        """
            Add tracks to playlists
            @param parser as TotemPlParser.Parser
            @param result as Gio.AsyncResult
            @param playlist_id as int
            @param uris as [str]
        """
        self.clear(playlist_id)
        self.add_uris(playlist_id, uris)
        with SqlCursor(self, True) as sql:
            sql.execute("UPDATE playlists SET mtime=?\
                         WHERE rowid=?", (datetime.now().strftime("%s"),
                                          playlist_id))

    def __on_entry_parsed(self, parser, uri, metadata, playlist_id, uris):
        """
            Play stream
            @param parser as TotemPlParser.Parser
            @param track uri as str
            @param metadata as GLib.HastTable
            @param playlist_id as int
            @param uris as [str]
        """
        uris.append(uri)
