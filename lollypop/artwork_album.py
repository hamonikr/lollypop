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

from gi.repository import Gio, GdkPixbuf, GLib, Gst

from random import choice
from gettext import gettext as _
from time import time

from lollypop.helper_task import TaskHelper
from lollypop.tagreader import Discoverer
from lollypop.artwork_manager import ArtworkManager
from lollypop.artwork_downloader_album import AlbumArtworkDownloader
from lollypop.logger import Logger
from lollypop.define import CACHE_PATH, ALBUMS_WEB_PATH, ALBUMS_PATH
from lollypop.define import ArtSize, StorageType
from lollypop.define import App, StoreExtention, ArtBehaviour
from lollypop.utils import emit_signal
from lollypop.utils_file import create_dir, is_readonly


class AlbumArtwork(ArtworkManager, AlbumArtworkDownloader):
    """
        Album artwork manager
    """

    __MIMES = ("jpeg", "jpg", "png", "gif")

    def __init__(self):
        """
            Init album artwork manager
        """
        ArtworkManager.__init__(self)
        AlbumArtworkDownloader.__init__(self)
        create_dir(ALBUMS_PATH)
        create_dir(ALBUMS_WEB_PATH)
        self.__favorite = App().settings.get_value(
            "favorite-cover").get_string()
        if not self.__favorite:
            self.__favorite = App().settings.get_default_value(
                "favorite-cover").get_string()

    def get_cache_path(self, album, width, height):
        """
            get artwork cache path for album_id
            @param album as Album
            @param width as int
            @param height as int
            @return cover path as string or None if no cover
        """
        try:
            cache_path = "%s/%s_%s_%s" % (CACHE_PATH,
                                          album.lp_album_id,
                                          width,
                                          height)
            cache_path = self.add_extension(cache_path)
            f = Gio.File.new_for_path(cache_path)
            if f.query_exists():
                return cache_path
            else:
                self.get(album, width, height, 1)
                if f.query_exists():
                    return cache_path
        except Exception as e:
            Logger.error("AlbumArtwork::get_cache_path(): %s" % e)
        return None

    def get_uri(self, album):
        """
            Look for artwork in dir:
            - favorite from settings first
            - Artist_Album.jpg then
            - Any any supported image otherwise
            @param album as Album
            @return cover uri as string
        """
        if album.id is None:
            return None
        try:
            self.__update_uri(album)
            if not album.storage_type & StorageType.COLLECTION:
                store_path = "%s/%s" % (ALBUMS_WEB_PATH, album.lp_album_id)
                store_path = self.add_extension(store_path)
                uris = [GLib.filename_to_uri(store_path)]
            else:
                store_path = "%s/%s" % (ALBUMS_PATH, album.lp_album_id)
                store_path = self.add_extension(store_path)
                if self.extension == StoreExtention.PNG:
                    uris = [
                        # Default favorite artwork
                        "%s/%s.png" % (album.uri, self.__favorite),
                        "%s/%s.jpg" % (album.uri, self.__favorite),
                        # Used when album.uri is readonly or for Web
                        GLib.filename_to_uri(store_path),
                        # Used when having muliple albums in same folder
                        "%s/%s.png" % (album.uri, album.lp_album_id),
                        "%s/%s.jpg" % (album.uri, album.lp_album_id)
                    ]
                else:
                    uris = [
                        # Default favorite artwork
                        "%s/%s.jpg" % (album.uri, self.__favorite),
                        "%s/%s.png" % (album.uri, self.__favorite),
                        # Used when album.uri is readonly or for Web
                        GLib.filename_to_uri(store_path),
                        # Used when having muliple albums in same folder
                        "%s/%s.jpg" % (album.uri, album.lp_album_id),
                        "%s/%s.png" % (album.uri, album.lp_album_id)
                    ]
            for uri in uris:
                f = Gio.File.new_for_uri(uri)
                if f.query_exists():
                    return uri
        except Exception as e:
            Logger.error("AlbumArtwork::get_uri(): %s", e)
        return None

    def get_uris(self, album):
        """
            Get locally available artworks for album
            @param album as Album
            @return [paths]
        """
        if not album.storage_type & (StorageType.COLLECTION |
                                     StorageType.EXTERNAL):
            return []
        try:
            uris = []
            f = Gio.File.new_for_uri(album.uri)
            infos = f.enumerate_children(
                "standard::name",
                Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                None)
            all_uris = []
            for info in infos:
                f = infos.get_child(info)
                all_uris.append(f.get_uri())
            for uri in filter(lambda p: p.lower().endswith(self.__MIMES),
                              all_uris):
                uris.append(uri)
            infos.close(None)
        except Exception as e:
            Logger.error("AlbumArtwork::get_uris(): %s", e)
        return uris

    def get(self, album, width, height, scale_factor,
            behaviour=ArtBehaviour.CACHE | ArtBehaviour.CROP_SQUARE):
        """
            Return a cairo surface for album_id, covers are cached as jpg.
            @param album as Album
            @param width as int
            @param height as int
            @param scale_factor factor as int
            @param behaviour as ArtBehaviour
            @return cairo surface
            @thread safe
        """
        uri = None
        if album.id is None:
            return None
        width *= scale_factor
        height *= scale_factor
        # Blur when reading from tags can be slow, so prefer cached version
        # Blur allows us to ignore width/height until we want CROP/CACHE
        optimized_blur = behaviour & (ArtBehaviour.BLUR |
                                      ArtBehaviour.BLUR_HARD) and\
            not behaviour & (ArtBehaviour.CACHE |
                             ArtBehaviour.CROP |
                             ArtBehaviour.CROP_SQUARE)
        if optimized_blur:
            w = ArtSize.BIG * scale_factor
            h = ArtSize.BIG * scale_factor
        else:
            w = width
            h = height
        cache_path = "%s/%s_%s_%s" % (CACHE_PATH, album.lp_album_id, w, h)
        cache_path = self.add_extension(cache_path)
        pixbuf = None
        try:
            # Look in cache
            f = Gio.File.new_for_path(cache_path)
            if not behaviour & ArtBehaviour.NO_CACHE and f.query_exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(cache_path)
                if optimized_blur:
                    pixbuf = self.load_behaviour(pixbuf,
                                                 width, height, behaviour)
                return pixbuf
            # Use favorite folder artwork
            if pixbuf is None:
                uri = self.get_uri(album)
                data = None
                if uri is not None:
                    f = Gio.File.new_for_uri(uri)
                    (status, data, tag) = f.load_contents(None)
                    bytes = GLib.Bytes.new(data)
                    stream = Gio.MemoryInputStream.new_from_bytes(bytes)
                    pixbuf = GdkPixbuf.Pixbuf.new_from_stream(
                        stream, None)
                    stream.close()

            # Use tags artwork
            if pixbuf is None and album.tracks and\
                    album.storage_type & (StorageType.COLLECTION |
                                          StorageType.EXTERNAL):
                try:
                    track = choice(album.tracks)
                    pixbuf = self.__get_pixbuf_from_tags(track.uri)
                except Exception as e:
                    Logger.error("AlbumArtwork::get(): %s", e)

            # Use folder artwork
            if pixbuf is None and\
                    album.storage_type & (StorageType.COLLECTION |
                                          StorageType.EXTERNAL):
                uri = self.__get_first(album)
                # Look in album folder
                if uri is not None:
                    f = Gio.File.new_for_uri(uri)
                    (status, data, tag) = f.load_contents(None)
                    bytes = GLib.Bytes.new(data)
                    stream = Gio.MemoryInputStream.new_from_bytes(bytes)
                    pixbuf = GdkPixbuf.Pixbuf.new_from_stream(
                        stream, None)
                    stream.close()
            if pixbuf is None:
                self.download(album.id)
                return None
            pixbuf = self.load_behaviour(pixbuf,
                                         width, height, behaviour)
            if behaviour & ArtBehaviour.CACHE:
                self.save_pixbuf(pixbuf, cache_path)
            return pixbuf
        except Exception as e:
            Logger.warning("AlbumArtwork::get(): %s -> %s" % (uri, e))
            return None

    def add(self, album, data):
        """
            Add artwork for album as data
            @param album as Album
            @param data as bytes
        """
        self.uncache(album)
        try:
            if not album.storage_type & StorageType.COLLECTION:
                self.__save_web(album, data)
            elif is_readonly(album.uri):
                self.__save_ro(album, data)
            else:
                self.__save(album, data)
        except Exception as e:
            Logger.error("AlbumArtwork::add(): %s" % e)

    def move(self, old_lp_album_id, new_lp_album_id):
        """
            Move artwork from an old id to a new id
            @param old_lp_album_id as str
            @param new_lp_album_id s str
        """
        try:
            for store in [ALBUMS_WEB_PATH, ALBUMS_PATH]:
                old_path = "%s/%s" % (store, old_lp_album_id)
                old_path = self.add_extension(old_path)
                old = Gio.File.new_for_path(old_path)
                if old.query_exists():
                    new_path = "%s/%s" % (store, new_lp_album_id)
                    new_path = self.add_extension(new_path)
                    new = Gio.File.new_for_path(new_path)
                    old.move(new, Gio.FileCopyFlags.OVERWRITE, None, None)
                    break
        except Exception as e:
            Logger.error("AlbumArtwork::move(): %s" % e)

    def uncache(self, album, width=-1, height=-1):
        """
            Remove cover from cache for album id
            @param album as Album
            @param width as int
            @param height as int
        """
        try:
            from pathlib import Path
            if width == -1 or height == -1:
                if self.extension == StoreExtention.PNG:
                    extension = "png"
                else:
                    extension = "jpg"
                for p in Path(CACHE_PATH).glob(
                        "%s*.%s" % (album.lp_album_id, extension)):
                    p.unlink()
            else:
                cache_path = "%s/%s_%s_%s" % (CACHE_PATH,
                                              album.lp_album_id,
                                              width,
                                              height)
                f = Gio.File.new_for_path(self.add_extension(cache_path))
                if f.query_exists():
                    f.delete()
        except Exception as e:
            Logger.error("AlbumArtwork::clean(): %s" % e)

#######################
# PRIVATE             #
#######################
    def __get_first(self, album):
        """
            Get first locally available artwork for album
            @param album as Album
            @return path or None
        """
        # Folders with many albums, get_uri()
        if App().albums.get_uri_count(album.uri) > 1:
            return None
        if not album.storage_type & (StorageType.COLLECTION |
                                     StorageType.EXTERNAL):
            return None
        f = Gio.File.new_for_uri(album.uri)
        infos = f.enumerate_children("standard::name",
                                     Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                                     None)
        all_uris = []
        for info in infos:
            f = infos.get_child(info)
            all_uris.append(f.get_uri())
        for uri in filter(
                lambda p: p.lower().endswith(self.__MIMES), all_uris):
            return uri
        infos.close(None)
        return None

    def __emit_update(self, album_id):
        """
            Announce album cover update
            @param album_id as int
        """
        if album_id is not None:
            emit_signal(self, "album-artwork-changed", album_id)

    def __update_uri(self, album):
        """
            Check if album uri exists, update if not
            @param album as Album
        """
        if not album.storage_type & StorageType.COLLECTION:
            return
        d = Gio.File.new_for_uri(album.uri)
        if not d.query_exists():
            if album.tracks:
                track_uri = album.tracks[0].uri
                f = Gio.File.new_for_uri(track_uri)
                p = f.get_parent()
                parent_uri = "" if p is None else p.get_uri()
                album.set_uri(parent_uri)

    def __save_web(self, album, data):
        """
            Save artwork for a web album
            @param album as Album
            @param data as bytes
        """
        store_path = "%s/%s" % (ALBUMS_WEB_PATH, album.lp_album_id)
        store_path = self.add_extension(store_path)
        self.save_pixbuf_from_data(store_path, data)
        self.__emit_update(album.id)

    def __save_ro(self, album, data):
        """
            Save artwork for a read only album
            @param album as Album
            @param data as bytes
        """
        store_path = "%s/%s" % (ALBUMS_PATH, album.lp_album_id)
        store_path = self.add_extension(store_path)
        self.save_pixbuf_from_data(store_path, data)
        self.__emit_update(album.id)

    def __save(self, album, data):
        """
            Save artwork for an album
            @param album as Album
            @param data as bytes
        """
        store_path = "%s/%s" % (ALBUMS_PATH, album.lp_album_id)
        store_path = self.add_extension(store_path)
        save_to_tags = App().settings.get_value("save-to-tags")
        # Multiple albums at same path
        uri_count = App().albums.get_uri_count(album.uri)
        art_uri = "%s/%s" % (album.uri, self.__favorite)
        art_uri = self.add_extension(art_uri)
        # Save cover to tags
        if save_to_tags and data is not None:
            helper = TaskHelper()
            helper.run(self.__add_to_tags, album, data)
        # We need to remove favorite if exists
        if uri_count > 1 or save_to_tags:
            f = Gio.File.new_for_uri(art_uri)
            if f.query_exists():
                f.trash()
        # Name file with album information
        if uri_count > 1:
            art_uri = "%s/%s" % (album.uri, album.lp_album_id)
            art_uri = self.add_extension(art_uri)
        self.save_pixbuf_from_data(store_path, data)
        # Keep file in store if empty
        if data is None:
            dst = Gio.File.new_for_uri(art_uri)
            if dst.query_exists():
                try:
                    dst.delete(None)
                except:
                    pass
        else:
            dst = Gio.File.new_for_uri(art_uri)
            src = Gio.File.new_for_path(store_path)
            src.move(dst, Gio.FileCopyFlags.OVERWRITE, None, None)
        self.__emit_update(album.id)

    def __get_pixbuf_from_tags(self, uri):
        """
            Return cover from tags
            @param uri as str
        """
        pixbuf = None
        # Internal URI are just like sp:
        if uri.find(":/") == -1:
            return
        try:
            discoverer = Discoverer()
            info = discoverer.get_info(uri)
            exist = False
            if info is not None:
                (exist, sample) = info.get_tags().get_sample_index("image", 0)
                if not exist:
                    (exist, sample) = info.get_tags().get_sample_index(
                        "preview-image", 0)
            if exist:
                (exist, mapflags) = sample.get_buffer().map(Gst.MapFlags.READ)
            if exist:
                bytes = GLib.Bytes.new(mapflags.data)
                stream = Gio.MemoryInputStream.new_from_bytes(bytes)
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
                stream.close()
        except Exception as e:
            Logger.error("AlbumArtwork::__get_pixbuf_from_tags(): %s" % e)
        return pixbuf

    def __add_to_tags(self, album, data):
        """
            Add image data to album tags
            @param album as Album
            @param data as bytes
        """
        # https://bugzilla.gnome.org/show_bug.cgi?id=747431
        bytes = GLib.Bytes.new(data)
        stream = Gio.MemoryInputStream.new_from_bytes(bytes)
        pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream,
                                                           ArtSize.MPRIS,
                                                           ArtSize.MPRIS,
                                                           True,
                                                           None)
        stream.close()
        if self.extension == StoreExtention.PNG:
            cache_path = "%s/lollypop_cover_tags.png" % CACHE_PATH
            pixbuf.savev(cache_path, "png", [None], [None])
        else:
            cache_path = "%s/lollypop_cover_tags.jpg" % CACHE_PATH
            pixbuf.savev(cache_path, "jpeg", ["quality"], [100])
        self.__write_image_to_tags(cache_path, album)

    def __write_image_to_tags(self, cache_path, album):
        """
            Save album at path to album tags
            @param cache_path as str
            @param album as Album
        """
        files = []
        for track in album.tracks:
            App().tracks.set_mtime(track.id, int(time()) + 10)
            f = Gio.File.new_for_uri(track.uri)
            if f.query_exists():
                files.append(f.get_path())
        worked = False
        arguments = [["kid3-cli", "-c", "set picture:'%s' ''" % cache_path],
                     ["flatpak-spawn", "--host", "kid3-cli",
                      "-c", "set picture:'%s' ''" % cache_path]]
        for argv in arguments:
            argv += files
            try:
                (pid, stdin, stdout, stderr) = GLib.spawn_async(
                    argv, flags=GLib.SpawnFlags.SEARCH_PATH |
                    GLib.SpawnFlags.STDOUT_TO_DEV_NULL,
                    standard_input=False,
                    standard_output=False,
                    standard_error=False
                )
                GLib.spawn_close_pid(pid)
                worked = True
                break
            except Exception as e:
                Logger.error("AlbumArtwork::__write_image_to_tags(): %s" % e)
        if worked:
            self.clean(album)
            GLib.timeout_add(2000, self.__emit_update, album.id)
        else:
            App().notify.send("Lollypop",
                              _("You need to install kid3-cli"))
