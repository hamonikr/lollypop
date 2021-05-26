# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2019 Jordi Romera <jordiromera@users.sourceforge.net>
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

from gi.repository import GLib, GObject, Gio, Gtk

from gi.repository.Gio import FILE_ATTRIBUTE_STANDARD_NAME, \
                              FILE_ATTRIBUTE_STANDARD_TYPE, \
                              FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,\
                              FILE_ATTRIBUTE_STANDARD_IS_SYMLINK,\
                              FILE_ATTRIBUTE_STANDARD_SYMLINK_TARGET,\
                              FILE_ATTRIBUTE_TIME_MODIFIED,\
                              FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE

from gettext import gettext as _
from time import time, sleep
from urllib.parse import urlparse
from multiprocessing import cpu_count

from lollypop.collection_item import CollectionItem
from lollypop.inotify import Inotify
from lollypop.define import App, ScanType, Type, StorageType, ScanUpdate
from lollypop.define import FileType
from lollypop.sqlcursor import SqlCursor
from lollypop.tagreader import TagReader, Discoverer
from lollypop.logger import Logger
from lollypop.database_history import History
from lollypop.objects_track import Track
from lollypop.utils_file import is_audio, is_pls, get_mtime, get_file_type
from lollypop.utils_album import tracks_to_albums
from lollypop.utils import emit_signal, profile, split_list
from lollypop.utils import get_lollypop_album_id, get_lollypop_track_id


SCAN_QUERY_INFO = "{},{},{},{},{},{}".format(
                                       FILE_ATTRIBUTE_STANDARD_NAME,
                                       FILE_ATTRIBUTE_STANDARD_TYPE,
                                       FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,
                                       FILE_ATTRIBUTE_STANDARD_IS_SYMLINK,
                                       FILE_ATTRIBUTE_STANDARD_SYMLINK_TARGET,
                                       FILE_ATTRIBUTE_TIME_MODIFIED)


class CollectionScanner(GObject.GObject, TagReader):
    """
        Scan user music collection
    """
    __gsignals__ = {
        "scan-finished": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        "updated": (GObject.SignalFlags.RUN_FIRST, None,
                    (GObject.TYPE_PYOBJECT, int))
    }

    def __init__(self):
        """
            Init collection scanner
        """
        GObject.GObject.__init__(self)
        self.__thread = None
        self.__tags = {}
        self.__items = []
        self.__notified_ids = []
        self.__pending_new_artist_ids = []
        self.__history = History()
        self.__progress_total = 1
        self.__progress_count = 0
        self.__progress_fraction = 0
        self.__disable_compilations = not App().settings.get_value(
                "show-compilations")
        if App().settings.get_value("auto-update"):
            self.__inotify = Inotify()
        else:
            self.__inotify = None
        App().albums.update_max_count()

    def update(self, scan_type, uris=[]):
        """
            Update database
            @param scan_type as ScanType
            @param uris as [str]
        """
        self.__disable_compilations = not App().settings.get_value(
                "show-compilations")
        App().lookup_action("update_db").set_enabled(False)
        # Stop previous scan
        if self.is_locked() and scan_type != ScanType.EXTERNAL:
            self.stop()
            GLib.timeout_add(250, self.update, scan_type, uris)
            return
        elif App().ws_director.collection_ws is not None and\
                not App().ws_director.collection_ws.stop():
            GLib.timeout_add(250, self.update, scan_type, uris)
            return
        else:
            if scan_type == ScanType.FULL:
                uris = App().settings.get_music_uris()
            if not uris:
                return
            # Register to progressbar
            if scan_type != ScanType.EXTERNAL:
                App().window.container.progress.add(self)
                App().window.container.progress.set_fraction(0, self)
            Logger.info("Scan started")
            # Launch scan in a separate thread
            self.__thread = App().task_helper.run(self.__scan, scan_type, uris)

    def save_album(self, item):
        """
            Add album to DB
            @param item as CollectionItem
        """
        Logger.debug("CollectionScanner::save_album(): "
                     "Add album artists %s" % item.album_artists)
        (item.new_album_artist_ids,
         item.album_artist_ids) = self.add_artists(item.album_artists,
                                                   item.aa_sortnames,
                                                   item.mb_album_artist_id)
        # We handle artists already created by any previous save_track()
        for artist_id in item.album_artist_ids:
            if artist_id in self.__pending_new_artist_ids:
                item.new_album_artist_ids.append(artist_id)
                self.__pending_new_artist_ids.remove(artist_id)

        item.lp_album_id = get_lollypop_album_id(item.album_name,
                                                 item.album_artists,
                                                 item.year)
        Logger.debug("CollectionScanner::save_track(): Add album: "
                     "%s, %s" % (item.album_name, item.album_artist_ids))
        (item.new_album, item.album_id) = self.add_album(
                                               item.album_name,
                                               item.mb_album_id,
                                               item.lp_album_id,
                                               item.album_artist_ids,
                                               item.uri,
                                               item.album_loved,
                                               item.album_pop,
                                               item.album_rate,
                                               item.album_synced,
                                               item.album_mtime,
                                               item.storage_type)
        if item.year is not None:
            App().albums.set_year(item.album_id, item.year)
            App().albums.set_timestamp(item.album_id, item.timestamp)

    def save_track(self, item):
        """
            Add track to DB
            @param item as CollectionItem
        """
        Logger.debug(
            "CollectionScanner::save_track(): Add artists %s" % item.artists)
        (item.new_artist_ids,
         item.artist_ids) = self.add_artists(item.artists,
                                             item.a_sortnames,
                                             item.mb_artist_id)

        self.__pending_new_artist_ids += item.new_artist_ids
        missing_artist_ids = list(
            set(item.album_artist_ids) - set(item.artist_ids))
        # Special case for broken tags
        # If all artist album tags are missing
        # Can't do more because don't want to break split album behaviour
        if len(missing_artist_ids) == len(item.album_artist_ids):
            item.artist_ids += missing_artist_ids

        if item.genres is None:
            (item.new_genre_ids, item.genre_ids) = ([], [Type.WEB])
        else:
            (item.new_genre_ids, item.genre_ids) = self.add_genres(item.genres)

        item.lp_track_id = get_lollypop_track_id(item.track_name,
                                                 item.artists,
                                                 item.album_name)

        # Add track to db
        Logger.debug("CollectionScanner::save_track(): Add track")
        item.track_id = App().tracks.add(item.track_name,
                                         item.uri,
                                         item.duration,
                                         item.tracknumber,
                                         item.discnumber,
                                         item.discname,
                                         item.album_id,
                                         item.original_year,
                                         item.original_timestamp,
                                         item.track_pop,
                                         item.track_rate,
                                         item.track_loved,
                                         item.track_ltime,
                                         item.track_mtime,
                                         item.mb_track_id,
                                         item.lp_track_id,
                                         item.bpm,
                                         item.storage_type)
        Logger.debug("CollectionScanner::save_track(): Update track")
        self.update_track(item)
        Logger.debug("CollectionScanner::save_track(): Update album")
        self.update_album(item)

    def update_album(self, item):
        """
            Update album artists based on album-artist and artist tags
            This code auto handle compilations: empty "album artist" with
            different artists
            @param item as CollectionItem
        """
        if item.album_artist_ids and not item.compilation:
            App().albums.set_artist_ids(item.album_id, item.album_artist_ids)
        # Set artist ids based on content
        else:
            if item.compilation:
                new_album_artist_ids = [Type.COMPILATIONS]
            else:
                new_album_artist_ids = App().albums.calculate_artist_ids(
                    item.album_id, self.__disable_compilations)
            App().albums.set_artist_ids(item.album_id, new_album_artist_ids)
            # We handle artists already created by any previous save_track()
            item.new_album_artist_ids = []
            for artist_id in new_album_artist_ids:
                if artist_id in self.__pending_new_artist_ids:
                    item.new_album_artist_ids.append(artist_id)
                    self.__pending_new_artist_ids.remove(artist_id)
        # Update lp_album_id
        lp_album_id = get_lollypop_album_id(item.album_name,
                                            item.album_artists,
                                            item.year)
        if lp_album_id != item.lp_album_id:
            App().album_art.move(item.lp_album_id, lp_album_id)
            App().albums.set_lp_album_id(item.album_id, lp_album_id)
            item.lp_album_id = lp_album_id
        # Update album genres
        for genre_id in item.genre_ids:
            App().albums.add_genre(item.album_id, genre_id)
        App().cache.clear_durations(item.album_id)

    def update_track(self, item):
        """
            Set track artists/genres
            @param item as CollectionItem
        """
        # Set artists/genres for track
        for artist_id in item.artist_ids:
            App().tracks.add_artist(item.track_id, artist_id)
        for genre_id in item.genre_ids:
            App().tracks.add_genre(item.track_id, genre_id)

    def del_from_db(self, uri, backup):
        """
            Delete track from db
            @param uri as str
            @param backup as bool
            @return (popularity, ltime, mtime,
                     loved album, album_popularity, album_rate)
        """
        try:
            track_id = App().tracks.get_id_by_uri(uri)
            duration = App().tracks.get_duration(track_id)
            album_id = App().tracks.get_album_id(track_id)
            album_artist_ids = App().albums.get_artist_ids(album_id)
            artist_ids = App().tracks.get_artist_ids(track_id)
            track_pop = App().tracks.get_popularity(track_id)
            track_rate = App().tracks.get_rate(track_id)
            track_ltime = App().tracks.get_ltime(track_id)
            album_mtime = App().tracks.get_mtime(track_id)
            track_loved = App().tracks.get_loved(track_id)
            album_pop = App().albums.get_popularity(album_id)
            album_rate = App().albums.get_rate(album_id)
            album_loved = App().albums.get_loved(album_id)
            album_synced = App().albums.get_synced(album_id)
            if backup:
                f = Gio.File.new_for_uri(uri)
                name = f.get_basename()
                self.__history.add(name, duration, track_pop, track_rate,
                                   track_ltime, album_mtime, track_loved,
                                   album_loved, album_pop, album_rate,
                                   album_synced)
            App().tracks.remove(track_id)
            genre_ids = App().tracks.get_genre_ids(track_id)
            App().albums.clean()
            App().genres.clean()
            App().artists.clean()
            App().cache.clear_durations(album_id)
            SqlCursor.commit(App().db)
            item = CollectionItem(album_id=album_id)
            if not App().albums.get_name(album_id):
                item.artist_ids = []
                for artist_id in album_artist_ids + artist_ids:
                    if not App().artists.get_name(artist_id):
                        item.artist_ids.append(artist_id)
                item.genre_ids = []
                for genre_id in genre_ids:
                    if not App().genres.get_name(genre_id):
                        item.genre_ids.append(genre_id)
                emit_signal(self, "updated", item, ScanUpdate.REMOVED)
            else:
                # Force genre for album
                genre_ids = App().tracks.get_album_genre_ids(album_id)
                App().albums.set_genre_ids(album_id, genre_ids)
                emit_signal(self, "updated", item, ScanUpdate.MODIFIED)
            return (track_pop, track_rate, track_ltime, album_mtime,
                    track_loved, album_loved, album_pop, album_rate)
        except Exception as e:
            Logger.error("CollectionScanner::del_from_db: %s" % e)
        return (0, 0, 0, 0, False, False, 0, 0)

    def is_locked(self):
        """
            True if db locked
            @return bool
        """
        return self.__thread is not None and self.__thread.is_alive()

    def stop(self):
        """
            Stop scan
        """
        self.__thread = None

    def reset_database(self):
        """
            Reset database
        """
        from lollypop.app_notification import AppNotification
        App().window.container.progress.add(self)
        App().window.container.progress.set_fraction(0, self)
        self.__progress_fraction = 0
        notification = AppNotification(_("Resetting database"), [], [], 10000)
        notification.show()
        App().window.container.add_overlay(notification)
        notification.set_reveal_child(True)
        App().task_helper.run(self.__reset_database)

    @property
    def inotify(self):
        """
            Get Inotify object
            @return Inotify
        """
        return self.__inotify

#######################
# PRIVATE             #
#######################
    def __reset_database(self):
        """
            Reset database
        """
        def update_ui():
            App().window.container.go_home()
            App().scanner.update(ScanType.FULL)
        App().player.stop()
        if App().ws_director.collection_ws is not None:
            App().ws_director.collection_ws.stop()
        uris = App().tracks.get_uris()
        i = 0
        SqlCursor.add(App().db)
        SqlCursor.add(self.__history)
        count = len(uris)
        for uri in uris:
            self.del_from_db(uri, True)
            self.__update_progress(i, count, 0.01)
            i += 1
        App().tracks.del_persistent(False)
        App().tracks.clean(False)
        App().albums.clean(False)
        App().artists.clean(False)
        App().genres.clean(False)
        App().cache.clear_table("duration")
        SqlCursor.commit(App().db)
        SqlCursor.remove(App().db)
        SqlCursor.commit(self.__history)
        SqlCursor.remove(self.__history)
        GLib.idle_add(update_ui)

    def __update_progress(self, current, total, allowed_diff):
        """
            Update progress bar status
            @param current as int
            @param total as int
            @param allowed_diff as float => allows to prevent
                                            main loop flooding
        """
        new_fraction = current / total
        if new_fraction > self.__progress_fraction + allowed_diff:
            self.__progress_fraction = new_fraction
            GLib.idle_add(App().window.container.progress.set_fraction,
                          new_fraction, self)

    def __finish(self, items):
        """
            Notify from main thread when scan finished
            @param items as [CollectionItem]
        """
        track_ids = [item.track_id for item in items]
        self.__thread = None
        Logger.info("Scan finished")
        App().lookup_action("update_db").set_enabled(True)
        App().window.container.progress.set_fraction(1.0, self)
        self.stop()
        emit_signal(self, "scan-finished", track_ids)
        # Update max count value
        App().albums.update_max_count()
        # Update featuring
        App().artists.update_featuring()
        if App().ws_director.collection_ws is not None:
            App().ws_director.collection_ws.start()

    def __add_monitor(self, dirs):
        """
            Monitor any change in a list of directory
            @param dirs as str or list of directory to be monitored
        """
        if self.__inotify is None:
            return
        # Add monitors on dirs
        for d in dirs:
            # Handle a stop request
            if self.__thread is None:
                break
            if d.startswith("file://"):
                self.__inotify.add_monitor(d)

    @profile
    def __get_objects_for_uris(self, scan_type, uris):
        """
            Get all tracks and dirs in uris
            @param scan_type as ScanType
            @param uris as string
            @return ([(int, str)], [str], [str])
                    ([(mtime, file)], [dir], [stream])
        """
        files = []
        dirs = []
        streams = []
        walk_uris = []
        # Check collection exists
        for uri in uris:
            parsed = urlparse(uri)
            if parsed.scheme in ["http", "https"]:
                streams.append(uri)
            else:
                f = Gio.File.new_for_uri(uri)
                if f.query_exists():
                    walk_uris.append(uri)
                else:
                    return ([], [], [])

        while walk_uris:
            uri = walk_uris.pop(0)
            try:
                # Directly add files, walk through directories
                f = Gio.File.new_for_uri(uri)
                info = f.query_info(SCAN_QUERY_INFO,
                                    Gio.FileQueryInfoFlags.NONE,
                                    None)
                if info.get_file_type() == Gio.FileType.DIRECTORY:
                    dirs.append(uri)
                    infos = f.enumerate_children(SCAN_QUERY_INFO,
                                                 Gio.FileQueryInfoFlags.NONE,
                                                 None)
                    for info in infos:
                        f = infos.get_child(info)
                        child_uri = f.get_uri()
                        if info.get_is_hidden():
                            continue
                        # User do not want internal symlinks
                        elif info.get_is_symlink() and\
                                App().settings.get_value("ignore-symlinks"):
                            continue
                        walk_uris.append(child_uri)
                    infos.close(None)
                # Only happens if files passed as args
                else:
                    mtime = get_mtime(info)
                    files.append((mtime, uri))
            except Exception as e:
                Logger.error("CollectionScanner::__get_objects_for_uris(): %s"
                             % e)
        files.sort(reverse=True)
        return (files, dirs, streams)

    @profile
    def __scan(self, scan_type, uris):
        """
            Scan music collection for music files
            @param scan_type as ScanType
            @param uris as [str]
            @thread safe
        """
        try:
            self.__items = []
            App().art.clean_rounded()
            (files, dirs, streams) = self.__get_objects_for_uris(
                scan_type, uris)
            if len(uris) != len(streams) and not files:
                self.__flatpak_migration()
                App().notify.send("Lollypop",
                                  _("Scan disabled, missing collection"))
                return
            if scan_type == ScanType.NEW_FILES:
                db_uris = App().tracks.get_uris(uris)
            else:
                db_uris = App().tracks.get_uris()

            # Get mtime of all tracks to detect which has to be updated
            db_mtimes = App().tracks.get_mtimes()
            # * 2 => Scan + Save
            self.__progress_total = len(files) * 2 + len(streams)
            self.__progress_count = 0
            self.__progress_fraction = 0
            # Min: 1 thread, Max: 5 threads
            count = max(1, min(5, cpu_count() // 2))
            split_files = split_list(files, count)
            self.__tags = {}
            self.__notified_ids = []
            self.__pending_new_artist_ids = []
            threads = []
            for files in split_files:
                thread = App().task_helper.run(self.__scan_files,
                                               files, db_mtimes,
                                               scan_type)
                threads.append(thread)
            while threads:
                sleep(0.1)
                thread = threads[0]
                if not thread.is_alive():
                    threads.remove(thread)

            SqlCursor.add(App().db)
            if scan_type == ScanType.EXTERNAL:
                storage_type = StorageType.EXTERNAL
            else:
                storage_type = StorageType.COLLECTION
            self.__items += self.__save_in_db(storage_type)
            # Add streams to DB, only happening on command line/m3u files
            self.__items += self.__save_streams_in_db(streams, storage_type)

            self.__remove_old_tracks(db_uris, scan_type)

            if scan_type == ScanType.EXTERNAL:
                albums = tracks_to_albums(
                    [Track(item.track_id) for item in self.__items])
                App().player.play_albums(albums)
            else:
                self.__add_monitor(dirs)
                GLib.idle_add(self.__finish, self.__items)
            self.__tags = {}
            self.__items = []
            self.__pending_new_artist_ids = []
        except Exception as e:
            Logger.warning("CollectionScanner::__scan(): %s", e)
        SqlCursor.remove(App().db)
        App().settings.set_value("flatpak-access-migration",
                                 GLib.Variant("b", True))

    def __scan_to_handle(self, uri):
        """
            Check if file has to be handle by scanner
            @param f as Gio.File
            @return bool
        """
        try:
            file_type = get_file_type(uri)
            # Get file type using Gio (slower)
            if file_type == FileType.UNKNOWN:
                f = Gio.File.new_for_uri(uri)
                info = f.query_info(FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
                                    Gio.FileQueryInfoFlags.NONE)
                if is_pls(info):
                    file_type = FileType.PLS
                elif is_audio(info):
                    file_type = FileType.AUDIO
            if file_type == FileType.PLS:
                Logger.debug("Importing playlist %s" % uri)
                if App().settings.get_value("import-playlists"):
                    App().playlists.import_tracks(uri)
            elif file_type == FileType.AUDIO:
                Logger.debug("Importing audio %s" % uri)
                return True
        except Exception as e:
            Logger.error("CollectionScanner::__scan_to_handle(): %s" % e)
        return False

    def __scan_files(self, files, db_mtimes, scan_type):
        """
            Scan music collection for new audio files
            @param files as [str]
            @param db_mtimes as {}
            @param scan_type as ScanType
            @thread safe
        """
        discoverer = Discoverer()
        try:
            # Scan new files
            for (mtime, uri) in files:
                # Handle a stop request
                if self.__thread is None and scan_type != ScanType.EXTERNAL:
                    raise Exception("cancelled")
                try:
                    if not self.__scan_to_handle(uri):
                        self.__progress_count += 2
                        continue
                    db_mtime = db_mtimes.get(uri, 0)
                    if mtime > db_mtime:
                        # Do not use mtime if not intial scan
                        if db_mtimes:
                            mtime = int(time())
                        self.__tags[uri] = self.__get_tags(discoverer,
                                                           uri, mtime)
                        self.__progress_count += 1
                        self.__update_progress(self.__progress_count,
                                               self.__progress_total,
                                               0.001)
                    else:
                        # We want to play files, so put them in items
                        if scan_type == ScanType.EXTERNAL:
                            track_id = App().tracks.get_id_by_uri(uri)
                            item = CollectionItem(track_id=track_id)
                            self.__items.append(item)
                        self.__progress_count += 2
                        self.__update_progress(self.__progress_count,
                                               self.__progress_total,
                                               0.1)
                except Exception as e:
                    Logger.error("Scanning file: %s, %s" % (uri, e))
        except Exception as e:
            Logger.warning("CollectionScanner::__scan_files(): % s" % e)

    def __save_in_db(self, storage_type):
        """
            Save current tags into DB
            @param storage_type as StorageType
            @return [CollectionItem]
        """
        items = []
        for uri in list(self.__tags.keys()):
            # Handle a stop request
            if self.__thread is None:
                raise Exception("cancelled")
            Logger.debug("Adding file: %s" % uri)
            tags = self.__tags[uri]
            item = self.__add2db(uri, *tags, storage_type)
            items.append(item)
            self.__progress_count += 1
            self.__update_progress(self.__progress_count,
                                   self.__progress_total,
                                   0.001)
            if item.album_id not in self.__notified_ids:
                self.__notified_ids.append(item.album_id)
                self.__notify_ui(item)
            del self.__tags[uri]
        # Handle a stop request
        if self.__thread is None:
            raise Exception("cancelled")
        return items

    def __save_streams_in_db(self, streams, storage_type):
        """
            Save http stream to DB
            @param streams as [str]
            @param storage_type as StorageType
            @return [CollectionItem]
        """
        items = []
        for uri in streams:
            parsed = urlparse(uri)
            item = self.__add2db(uri, parsed.path, parsed.netloc,
                                 None, "", "", parsed.netloc,
                                 parsed.netloc, "", False, 0, False, 0, 0, 0,
                                 None, 0, "", "", "", "", 1, 0, 0, 0, 0, 0,
                                 False, 0, False, storage_type)
            items.append(item)
            self.__progress_count += 1
        return items

    def __notify_ui(self, item):
        """
            Notify UI for item
            @param items as CollectionItem
        """
        SqlCursor.commit(App().db)
        if item.new_album:
            emit_signal(self, "updated", item, ScanUpdate.ADDED)
        else:
            emit_signal(self, "updated", item, ScanUpdate.MODIFIED)

    def __remove_old_tracks(self, uris, scan_type):
        """
            Remove non existent tracks from DB
            @param scan_type as ScanType
        """
        if scan_type != ScanType.EXTERNAL and self.__thread is not None:
            # We need to check files are always in collections
            if scan_type == ScanType.FULL:
                collections = App().settings.get_music_uris()
            else:
                collections = None
            for uri in uris:
                # Handle a stop request
                if self.__thread is None:
                    raise Exception("cancelled")
                in_collection = True
                if collections is not None:
                    in_collection = False
                    for collection in collections:
                        if collection in uri:
                            in_collection = True
                            break
                f = Gio.File.new_for_uri(uri)
                if not in_collection:
                    Logger.warning(
                        "Removed, not in collection anymore: %s -> %s",
                        uri, collections)
                    self.del_from_db(uri, True)
                elif not f.query_exists():
                    Logger.warning("Removed, file has been deleted: %s", uri)
                    self.del_from_db(uri, True)

    def __get_tags(self, discoverer, uri, track_mtime):
        """
            Read track tags
            @param discoverer as Discoverer
            @param uri as string
            @param track_mtime as int
            @return ()
        """
        f = Gio.File.new_for_uri(uri)
        info = discoverer.get_info(uri)
        tags = info.get_tags()
        name = f.get_basename()
        duration = int(info.get_duration() / 1000000)
        Logger.debug("CollectionScanner::add2db(): Restore stats")
        # Restore stats
        track_id = App().tracks.get_id_by_uri(uri)
        if track_id is None:
            track_id = App().tracks.get_id_by_basename_duration(name,
                                                                duration)
        if track_id is None:
            (track_pop, track_rate, track_ltime,
             album_mtime, track_loved, album_loved,
             album_pop, album_rate, album_synced) = self.__history.get(
                name, duration)
        # Delete track and restore from it
        else:
            (track_pop, track_rate, track_ltime,
             album_mtime, track_loved, album_loved,
             album_pop, album_rate) = self.del_from_db(uri, False)

        Logger.debug("CollectionScanner::add2db(): Read tags")
        title = self.get_title(tags, name)
        version = self.get_version(tags)
        if version != "":
            title += " (%s)" % version
        artists = self.get_artists(tags)
        a_sortnames = self.get_artist_sortnames(tags)
        aa_sortnames = self.get_album_artist_sortnames(tags)
        album_artists = self.get_album_artists(tags)
        album_name = self.get_album_name(tags)
        album_synced = 0
        mb_album_id = self.get_mb_album_id(tags)
        mb_track_id = self.get_mb_track_id(tags)
        mb_artist_id = self.get_mb_artist_id(tags)
        mb_album_artist_id = self.get_mb_album_artist_id(tags)
        genres = self.get_genres(tags)
        discnumber = self.get_discnumber(tags)
        discname = self.get_discname(tags)
        tracknumber = self.get_tracknumber(tags, name)
        # We have popm in tags, override history one
        tag_track_rate = self.get_popm(tags)
        if tag_track_rate > 0:
            track_rate = tag_track_rate
        if album_mtime == 0:
            album_mtime = track_mtime
        bpm = self.get_bpm(tags)
        compilation = self.get_compilation(tags)
        (original_year, original_timestamp) = self.get_original_year(tags)
        (year, timestamp) = self.get_year(tags)
        if year is None:
            (year, timestamp) = (original_year, original_timestamp)
        elif original_year is None:
            (original_year, original_timestamp) = (year, timestamp)
        # If no artists tag, use album artist
        if artists == "":
            artists = album_artists
        if App().settings.get_value("import-advanced-artist-tags"):
            composers = self.get_composers(tags)
            conductors = self.get_conductors(tags)
            performers = self.get_performers(tags)
            remixers = self.get_remixers(tags)
            artists += ";%s" % performers if performers != "" else ""
            artists += ";%s" % conductors if conductors != "" else ""
            artists += ";%s" % composers if composers != "" else ""
            artists += ";%s" % remixers if remixers != "" else ""
        if artists == "":
            artists = _("Unknown")
        return (title, artists, genres, a_sortnames, aa_sortnames,
                album_artists, album_name, discname, album_loved, album_mtime,
                album_synced, album_rate, album_pop, discnumber, year,
                timestamp, original_year, original_timestamp,
                mb_album_id, mb_track_id, mb_artist_id,
                mb_album_artist_id, tracknumber, track_pop, track_rate, bpm,
                track_mtime, track_ltime, track_loved, duration, compilation)

    def __add2db(self, uri, name, artists,
                 genres, a_sortnames, aa_sortnames, album_artists, album_name,
                 discname, album_loved, album_mtime, album_synced, album_rate,
                 album_pop, discnumber, year, timestamp,
                 original_year, original_timestamp, mb_album_id,
                 mb_track_id, mb_artist_id, mb_album_artist_id,
                 tracknumber, track_pop, track_rate, bpm, track_mtime,
                 track_ltime, track_loved, duration, compilation,
                 storage_type=StorageType.COLLECTION):
        """
            Add new file to DB
            @param uri as str
            @param tags as *()
            @param storage_type as StorageType
            @return CollectionItem
        """
        item = CollectionItem(uri=uri,
                              track_name=name,
                              artists=artists,
                              genres=genres,
                              a_sortnames=a_sortnames,
                              aa_sortnames=aa_sortnames,
                              album_artists=album_artists,
                              album_name=album_name,
                              discname=discname,
                              album_loved=album_loved,
                              album_mtime=album_mtime,
                              album_synced=album_synced,
                              album_rate=album_rate,
                              album_pop=album_pop,
                              discnumber=discnumber,
                              year=year,
                              timestamp=timestamp,
                              original_year=original_year,
                              original_timestamp=original_timestamp,
                              mb_album_id=mb_album_id,
                              mb_track_id=mb_track_id,
                              mb_artist_id=mb_artist_id,
                              mb_album_artist_id=mb_album_artist_id,
                              tracknumber=tracknumber,
                              track_pop=track_pop,
                              track_rate=track_rate,
                              bpm=bpm,
                              track_mtime=track_mtime,
                              track_ltime=track_ltime,
                              track_loved=track_loved,
                              duration=duration,
                              compilation=compilation,
                              storage_type=storage_type)
        self.save_album(item)
        self.save_track(item)
        return item

    def __flatpak_migration(self):
        """
            https://github.com/flathub/org.gnome.Lollypop/pull/108
        """
        if GLib.file_test("/app", GLib.FileTest.EXISTS) and\
                not App().settings.get_value("flatpak-access-migration"):
            from lollypop.assistant_flatpak import FlatpakAssistant
            assistant = FlatpakAssistant()
            assistant.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            assistant.set_transient_for(App().window)
            GLib.timeout_add(1000, assistant.show)
