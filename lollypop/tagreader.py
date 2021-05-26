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

from gi.repository import Gst, GstPbutils, GLib, Gio

from re import match
from gettext import gettext as _

from lollypop.define import App
from lollypop.logger import Logger
from lollypop.utils_file import decodeUnicode, splitUnicode
from lollypop.utils import format_artist_name, get_iso_date_from_string
from lollypop.tag_frame_text import FrameTextTag
from lollypop.tag_frame_lang import FrameLangTag


class Discoverer:
    """
        Discover tags
    """

    def __init__(self):
        """
            Init tag reader
        """

        self._discoverer = GstPbutils.Discoverer.new(10 * Gst.SECOND)

    def get_info(self, uri):
        """
            Return information for file at uri
            @param uri as str
            @Exception GLib.Error
            @return GstPbutils.DiscovererInfo
        """
        info = self._discoverer.discover_uri(uri)
        return info


class TagReader:
    """
        Scanner tag reader
    """

    __STRING = ["title", "artist", "composer", "conductor",
                "musicbrainz-albumid", "musicbrainz-trackid",
                "musicbrainz-artistid", "musicbrainz-albumartistid",
                "version", "performer", "artist-sortname",
                "album-artist-sortname", "interpreted-by", "album-artist",
                "album", "genre", "lyrics", "publisher"]
    __INT = ["album-disc-number", "track-number"]
    __DOUBLE = ["beats-per-minute"]

    def __init__(self):
        """
            Init tag reader
        """
        pass

    def get_title(self, tags, filepath):
        """
            Return title for tags
            @param tags as Gst.TagList
            @param filepath as string
            @return title as string
        """
        if tags is None:
            return GLib.path_get_basename(filepath)
        title = self.__get(tags, ["title"])
        if not title:
            title = GLib.path_get_basename(filepath)
        return title

    def get_artists(self, tags):
        """
            Return artists for tags
            @param tags as Gst.TagList
            @return string like "artist1;artist2;..."
        """
        if tags is None:
            return _("Unknown")
        return self.__get(tags, ["artist"])

    def get_composers(self, tags):
        """
            Return composers for tags
            @param tags as Gst.TagList
            @return string like "composer1;composer2;..."
        """
        if tags is None:
            return _("Unknown")
        return self.__get(tags, ["composer"])

    def get_conductors(self, tags):
        """
            Return conductors for tags
            @param tags as Gst.TagList
            @return string like "conductor1;conductor2;..."
        """
        if tags is None:
            return _("Unknown")
        return self.__get(tags, ["conductor"])

    def get_mb_id(self, tags, name):
        """
            Get MusicBrainz ID
            @param tags as Gst.TagList
            @param name as str
            @return str
        """
        if tags is None or not name:
            return ""
        return self.__get(tags, ["musicbrainz-" + name])

    def get_mb_album_id(self, tags):
        """
            Get album id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'albumid')

    def get_mb_track_id(self, tags):
        """
            Get recording id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'trackid')

    def get_mb_artist_id(self, tags):
        """
            Get artist id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'artistid')

    def get_mb_album_artist_id(self, tags):
        """
            Get album artist id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'albumartistid')

    def get_version(self, tags):
        """
            Get recording version
            @param tags as Gst.TagList
            @return str
        """
        if tags is None:
            return ""
        return self.__get(tags, ["version"])

    def get_performers(self, tags):
        """
            Return performers for tags
            @param tags as Gst.TagList
            @return string like "performer1;performer2;..."
        """
        if tags is None:
            return _("Unknown")
        return self.__get(tags, ["performer"])

    def get_artist_sortnames(self, tags):
        """
            Return artist sort names
            @param tags as Gst.TagList
            @return artist sort names as "str;str"
        """
        if tags is None:
            return ""
        return self.__get(tags, ["artist-sortname"])

    def get_album_artist_sortnames(self, tags):
        """
            Return album artist sort names
            @param tags as Gst.TagList
            @return artist sort names as "str;str"
        """
        if tags is None:
            return ""
        return self.__get(tags, ["album-artist-sortname"])

    def get_remixers(self, tags):
        """
            Get remixers tag
            @param tags as Gst.TagList
            @return artist sort names as "str,str"
        """
        if tags is None:
            return _("Unknown")
        remixers = self.__get(tags, ["interpreted-by"])
        if not remixers:
            remixers = self.__get_extended(tags, ["REMIXER"])
        return remixers

    def get_album_artists(self, tags):
        """
            Return album artists for tags
            @param tags as Gst.TagList
            @return album artist as string or None
        """
        if tags is None:
            return _("Unknown")
        return self.__get(tags, ["album-artist"])

    def get_album_name(self, tags):
        """
            Return album for tags
            @param tags as Gst.TagList
            @return album name as string
        """
        if tags is None:
            return _("Unknown")
        album = self.__get(tags, ["album"])
        if not album:
            album = _("Unknown")
        return album

    def get_genres(self, tags):
        """
            Return genres for tags
            @param tags as Gst.TagList
            @return string like "genre1;genre2;..."
        """
        if tags is None:
            return _("Unknown")
        genres = self.__get(tags, ["genre"])
        if not genres:
            genres = _("Unknown")
        return genres

    def get_discname(self, tags):
        """
            Return disc name
            @param tags as Gst.TagList
            @return disc name as str
        """
        return self.__get_extended(tags, ['PART', 'DISCSUBTITLE'])

    def get_discnumber(self, tags):
        """
            Return disc number for tags
            @param tags as Gst.TagList
            @return disc number as int
        """
        if tags is None:
            return 0
        discnumber = self.__get(tags, ["album-disc-number"])
        if not discnumber:
            discnumber = 0
        return discnumber

    def get_compilation(self, tags):
        """
            Return True if album is a compilation
            @param tags as Gst.TagList
            @return bool
        """
        if tags is None:
            return False
        try:
            compilation = self.__get_private_string(tags, "TCMP", False)
            if not compilation:
                compilation = self.__get_extended(tags, ["COMPILATION"])
            if compilation:
                return compilation == 1
        except Exception as e:
            Logger.error("TagReader::get_compilation(): %s" % e)
        return False

    def get_tracknumber(self, tags, filename):
        """
            Return track number for tags
            @param tags as Gst.TagList
            @param filename as str
            @return track number as int
        """
        if tags is not None:
            tracknumber = self.__get(tags, ["track-number"])
        else:
            tracknumber = None
        if not tracknumber:
            # Guess from filename
            m = match("^([0-9]*)[ ]*-", filename)
            if m:
                try:
                    tracknumber = int(m.group(1))
                except:
                    tracknumber = 0
            else:
                tracknumber = 0
        return min(abs(tracknumber), GLib.MAXINT32)

    def get_year(self, tags):
        """
            Return track year for tags
            @param tags as Gst.TagList
            @return year and timestamp (int, int)
        """
        try:
            (exists_date, date) = tags.get_date_index("date", 0)
            (exists_datetime, datetime) = tags.get_date_time_index("datetime",
                                                                   0)
            year = timestamp = None
            if exists_datetime:
                if datetime.has_year():
                    year = datetime.get_year()
                if datetime.has_month():
                    month = datetime.get_month()
                else:
                    month = 1
                if datetime.has_day():
                    day = datetime.get_day()
                else:
                    day = 1
            if exists_date and date.valid():
                year = date.get_year()
                month = date.get_month()
                day = date.get_day()

            if year is not None:
                gst_datetime = Gst.DateTime.new_local_time(
                    year, month, day, 0, 0, 0)
                glib_datetime = gst_datetime.to_g_date_time()
                timestamp = glib_datetime.to_unix()
            return (year, timestamp)
        except Exception as e:
            Logger.error("TagReader::get_year(): %s", e)
        return (None, None)

    def get_original_year(self, tags):
        """
            Return original release year
            @param tags as Gst.TagList
            @return year and timestamp (int, int)
        """
        def get_id3():
            date_string = self.__get_private_string(tags, "TDOR", False)
            try:
                date = get_iso_date_from_string(date_string)
                datetime = GLib.DateTime.new_from_iso8601(date, None)
                return (datetime.get_year(), datetime.to_unix())
            except:
                pass
            return (None, None)

        def get_ogg():
            try:
                date_string = self.__get_extended(tags, ['ORIGINALDATE'])
                date = get_iso_date_from_string(date_string)
                datetime = GLib.DateTime.new_from_iso8601(date, None)
                return (datetime.get_year(), datetime.to_unix())
            except:
                pass
            return (None, None)

        if tags is None:
            return None
        values = get_id3()
        if values[0] is None:
            values = get_ogg()
        return values

    def get_bpm(self, tags):
        """
            Get BPM from tags
            @param tags as Gst.TagList
            @return int/None
        """
        bpm = self.__get(tags, ["beats-per-minute"])
        if not bpm:
            bpm = None
        return bpm

    def get_popm(self, tags):
        """
            Get popularity tag
            @param tags as Gst.TagList
            @return int
        """
        try:
            if tags is None:
                return 0
            size = tags.get_tag_size("private-id3v2-frame")
            for i in range(0, size):
                (exists, sample) = tags.get_sample_index("private-id3v2-frame",
                                                         i)
                if not exists:
                    continue
                (exists, m) = sample.get_buffer().map(Gst.MapFlags.READ)
                if not exists:
                    continue
                # Gstreamer 1.18 API breakage
                try:
                    bytes = m.data.tobytes()
                except:
                    bytes = m.data

                if len(bytes) > 4 and bytes[0:4] == b"POPM":
                    try:
                        popm = bytes.split(b"\x00")[6][0]
                    except:
                        popm = 0
                    if popm == 0:
                        value = 0
                    elif popm >= 1 and popm < 64:
                        value = 1
                    elif popm >= 64 and popm < 128:
                        value = 2
                    elif popm >= 128 and popm < 196:
                        value = 3
                    elif popm >= 196 and popm < 255:
                        value = 4
                    elif popm == 255:
                        value = 5
                    else:
                        value = 0
                    return value
        except Exception as e:
            Logger.warning("TagReader::get_popm(): %s", e)
        return 0

    def get_lyrics(self, tags):
        """
            Return lyrics for tags
            @parma tags as Gst.TagList
            @return lyrics as str
        """
        def get_mp4():
            return self.__get(tags, ["lyrics"])

        def get_id3():
            return self.__get_private_string(tags, "USLT", True)

        def get_ogg():
            return self.__get_extended(tags, ["LYRICS"])

        if tags is None:
            return ""
        lyrics = get_mp4()
        if not lyrics:
            lyrics = get_id3()
        if not lyrics:
            lyrics = get_ogg()
        return lyrics

    def get_synced_lyrics(self, tags):
        """
            Return synced lyrics for tags
            @parma tags as Gst.TagList
            @return lyrics as ([str, int])
        """
        def decode_lyrics(bytes_list, encoding):
            lyrics = []
            try:
                for frame in bytes_list:
                    (l, t) = splitUnicode(frame, encoding)
                    if l:
                        lyrics.append((decodeUnicode(l, encoding),
                                       int.from_bytes(t[1:4], "big")))
            except Exception as e:
                Logger.warning(
                        "TagReader::get_synced_lyrics.decode_lyrics(): %s", e)
            return lyrics

        def get_id3():
            try:
                b = self.__get_private_bytes(tags, "SYLT")
                if b:
                    frame = b[10:]
                    encoding = frame[0:1]
                    string = decode_lyrics(frame.split(b"\n"), encoding)
                    if string is not None:
                        return string
            except Exception as e:
                Logger.warning("TagReader::get_synced_lyrics.get_id3(): %s", e)
            return ""

        if tags is None:
            return ""
        lyrics = get_id3()
        return lyrics

    def add_artists(self, artists, sortnames, mb_artist_id=""):
        """
            Add artists to db
            @param artists as str
            @param sortnames as str
            @param mb_artist_id as str
            @return ([int], [int]): (added artist ids, artist ids)
        """
        artist_ids = []
        added_artist_ids = []
        artistsplit = artists.split(";")
        sortsplit = sortnames.split(";")
        sortlen = len(sortsplit)
        mbidsplit = mb_artist_id.split(";")
        mbidlen = len(mbidsplit)
        if len(artistsplit) != mbidlen:
            mbidsplit = []
            mbidlen = 0
        i = 0
        for artist in artistsplit:
            artist = artist.strip()
            if artist != "":
                if i >= mbidlen or mbidsplit[i] == "":
                    mbid = None
                else:
                    mbid = mbidsplit[i].strip()
                # Get artist id, add it if missing
                (artist_id, db_name) = App().artists.get_id(artist, mbid)
                if i >= sortlen or sortsplit[i] == "":
                    sortname = None
                else:
                    sortname = sortsplit[i].strip()
                if artist_id is None:
                    if sortname is None:
                        sortname = format_artist_name(artist)
                    artist_id = App().artists.add(artist, sortname, mbid)
                    added_artist_ids.append(artist_id)
                else:
                    # artists.get_id() is NOCASE, check if we need to update
                    # artist name
                    if db_name != artist:
                        App().artists.set_name(artist_id, artist)
                    if sortname is not None:
                        App().artists.set_sortname(artist_id, sortname)
                    if mbid is not None:
                        App().artists.set_mb_artist_id(artist_id, mbid)
                i += 1
                artist_ids.append(artist_id)
        return (added_artist_ids, artist_ids)

    def add_genres(self, genres):
        """
            Add genres to db
            @param genres as string
            @return ([int], [int]): (added genre ids, genre ids)
        """
        genre_ids = []
        added_genre_ids = []
        for genre in genres.split(";"):
            genre = genre.strip()
            if genre != "":
                # Get genre id, add genre if missing
                genre_id = App().genres.get_id(genre)
                if genre_id is None:
                    genre_id = App().genres.add(genre)
                    added_genre_ids.append(genre_id)
                genre_ids.append(genre_id)
        return (added_genre_ids, genre_ids)

    def add_album(self, album_name, mb_album_id, lp_album_id, artist_ids,
                  uri, loved, popularity, rate, synced, mtime, storage_type):
        """
            Add album to db
            @param album_name as str
            @param mb_album_id as str
            @param lp_album_id as str
            @param artist_ids as [int]
            @param uri as str
            @param loved as bool
            @param popularity as int
            @param rate as int
            @param synced as int
            @param mtime as int
            @param storage_type as StorageType
            @return (added as bool, album_id as int)
            @commit needed
        """
        added = False
        if uri.find("://") != -1:
            f = Gio.File.new_for_uri(uri)
            parent = f.get_parent()
            if parent is not None:
                uri = parent.get_uri()
        album_id = App().albums.get_id(album_name, mb_album_id, artist_ids)
        # Check storage type did not changed, remove album then
        if album_id is not None:
            current_storage_type = App().albums.get_storage_type(album_id)
            if current_storage_type != storage_type:
                App().tracks.remove_album(album_id)
                App().tracks.clean(False)
                App().albums.clean(False)
                App().artists.clean(False)
                album_id = None
        if album_id is None:
            added = True
            album_id = App().albums.add(album_name, mb_album_id, lp_album_id,
                                        artist_ids, uri, loved, popularity,
                                        rate, synced, mtime, storage_type)
        # Check if path did not change
        elif App().albums.get_uri(album_id) != uri:
            App().albums.set_uri(album_id, uri)
        return (added, album_id)

#######################
# PRIVATE             #
#######################
    def __get_extended(self, tags, keys):
        """
            Return tag from tags following keys
            @param tags as Gst.TagList
            @param keys as [str]
            @return Tag as str
        """
        if tags is None:
            return ""
        items = []
        try:
            for i in range(tags.get_tag_size("extended-comment")):
                (exists, read) = tags.get_string_index("extended-comment", i)
                for key in keys:
                    if exists and read.startswith(key + "="):
                        items.append("".join(read.split("=")[1:]))
        except Exception as e:
            Logger.error("TagReader::__get_extended(): %s", e)
        return ";".join(items)

    def __get(self, tags, keys):
        """
            Return tag from tags following keys
            Only handles string/uint/double
            @param tags as Gst.TagList
            @param keys as [str]
            @return Tag as str/int/double. Empty string if does not exist
        """
        if tags is None:
            return ""
        items = []
        try:
            for key in keys:
                for i in range(tags.get_tag_size(key)):
                    if key in self.__STRING:
                        (exists, read) = tags.get_string_index(key, i)
                        if exists and read.strip(" "):
                            items.append(read)
                    elif key in self.__INT:
                        (exists, read) = tags.get_uint_index(key, i)
                        if exists:
                            return read
                    elif key in self.__DOUBLE:
                        (exists, read) = tags.get_double_index(key, i)
                        if exists:
                            return read
                    else:
                        Logger.error("Missing key" % key)
        except Exception as e:
            Logger.error("TagReader::__get(): %s", e)
        return ";".join(items)

    def __get_private_bytes(self, tags, key):
        """
            Get key from private frame
            @param tags as Gst.TagList
            @param key as str
            @return frame as bytes
        """
        try:
            size = tags.get_tag_size("private-id3v2-frame")
            encoded_key = key.encode("utf-8")
            for i in range(0, size):
                (exists, sample) = tags.get_sample_index(
                    "private-id3v2-frame",
                    i)
                if not exists:
                    continue
                (exists, m) = sample.get_buffer().map(Gst.MapFlags.READ)
                if not exists:
                    continue
                # Gstreamer 1.18 API breakage
                try:
                    b = m.data.tobytes()
                except:
                    b = m.data

                if b[0:len(encoded_key)] != encoded_key:
                    continue
                return b
        except Exception as e:
            Logger.error("TagReader::__get_private_bytes(): %s" % e)
        return b""

    def __get_private_string(self, tags, key, lang):
        """
            Get key from private frame
            @param tags as Gst.TagList
            @param key as str
            @param lang as bool
            @return Tag as str
        """
        try:
            b = self.__get_private_bytes(tags, key)
            if lang:
                frame = FrameLangTag(b)
            else:
                frame = FrameTextTag(b)
            if frame.key == key:
                return frame.string
        except Exception as e:
            Logger.error("TagReader::__get_private(): %s" % e)
        return ""
