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

from gi.repository import Gio, GLib

from lollypop.logger import Logger
from lollypop.helper_task import TaskHelper
from lollypop.utils import escape, get_network_available
from lollypop.utils_file import create_dir
from lollypop.define import LYRICS_PATH


class LyricsHelper:
    """
        Sync lyrics helper
    """

    def __init__(self):
        """
            Init helper
        """
        self.__timestamps = {}
        self.__cancellable = Gio.Cancellable.new()
        create_dir(LYRICS_PATH)

    def load(self, track):
        """
            Load lyrics for track
            @param track as Track
        """
        self.__track = track
        self.__timestamps = {}
        uri_no_ext = ".".join(track.uri.split(".")[:-1])
        self.__lrc_file = Gio.File.new_for_uri(uri_no_ext + ".lrc")
        if self.__lrc_file.query_exists():
            self.__get_timestamps()
        else:
            from lollypop.tagreader import Discoverer, TagReader
            discoverer = Discoverer()
            tagreader = TagReader()
            try:
                info = discoverer.get_info(track.uri)
            except:
                info = None
            if info is not None:
                tags = info.get_tags()
                for (lyrics, timestamp) in tagreader.get_synced_lyrics(tags):
                    if timestamp in self.__timestamps.keys():
                        self.__timestamps[timestamp] += "\n%s" % lyrics
                    else:
                        self.__timestamps[timestamp] = lyrics

    def get_lyrics_for_timestamp(self, timestamp):
        """
            Get lyrics for timestamp
            @param timestamp as int
            @return ([str], str, [str])
        """
        previous = []
        next = []
        current = None
        for key in self.__timestamps.keys():
            if timestamp > key and current is None:
                if len(previous) == 5:
                    previous.pop(0)
                previous.append(self.__timestamps[key])
            elif current is None and previous:
                current = previous.pop(-1)
                next.append(self.__timestamps[key])
            elif timestamp < key and len(next) != 5:
                next.append(self.__timestamps[key])
            else:
                break
        if current is None:
            current = ""
        return (previous, [" ", current, " "], next)

    def get_lyrics_from_web(self, track, callback, *args):
        """
            Get lyrics from web for track
            @param track as Track
            @param callback as function
        """
        self.__cancellable = Gio.Cancellable.new()
        methods = []
        if get_network_available("BING"):
            methods.append(self.__download_bing_lyrics)
        if get_network_available("WIKIA"):
            methods.append(self.__download_wikia_lyrics)
        if get_network_available("GENIUS"):
            methods.append(self.__download_genius_lyrics)
        if get_network_available("METROLYRICS"):
            methods.append(self.__download_metro_lyrics)
        if methods:
            self.__get_lyrics_from_web(track, methods, callback, *args)
        else:
            callback(None, *args)

    def cancel(self):
        """
            Cancel current loading
        """
        self.__cancellable.cancel()

    @property
    def available(self):
        """
            True if lyrics available
            @return bool
        """
        return len(self.__timestamps.keys()) != 0

############
# PRIVATE  #
############
    def __str_to_timestamp(self, srt_timestamp):
        """
            Convert timestamp to time
            @timestamp as str [00:00.00]
            @return int
        """
        timestamp = int(srt_timestamp.split(".")[-1])
        seconds = int(srt_timestamp.split(".")[-2].split(":")[-1])
        minutes = int(srt_timestamp.split(".")[-2].split(":")[0])
        timestamp += seconds * 1000
        timestamp += minutes * 60000
        return timestamp

    def __get_timestamps(self):
        """
            Get timestamps from file
        """
        try:
            status = False
            if self.__lrc_file.query_exists():
                (status, content, tag) = self.__lrc_file.load_contents()
            if status:
                data = content.decode("utf-8").split("\n")
                for line in data:
                    if line.find("length") != -1:
                        continue
                    try:
                        str_timestamp = line.split("]")[0].split("[")[1]
                        timestamp = self.__str_to_timestamp(str_timestamp)
                        lyrics = " ".join(line.split("]")[1:])
                        if timestamp in self.__timestamps.keys():
                            self.__timestamps[timestamp] += "\n%s" % lyrics
                        else:
                            self.__timestamps[timestamp] = lyrics
                    except:
                        continue
        except Exception as e:
            Logger.error("SyncLyricsHelper::__get_timestamps(): %s", e)

    def __get_lyrics_from_web(self, track, methods, callback, *args):
        """
            Get lyrics from web for track
            @param track as Track
            @param methods as []
            @param callback as function
        """
        if methods:
            method = methods.pop(0)
            method(track, methods, callback, *args)
        else:
            callback("", *args)

    def __get_title(self, track, escape=False):
        """
            Get track title for lyrics
            @param track as Track
            @param escape as bool
            @return str
        """
        # Update lyrics
        title = track.name
        if escape:
            return GLib.uri_escape_string(title, None, False)
        else:
            return title

    def __get_artist(self, track, escape=False):
        """
            Get track artist for lyrics
            @param track as Track
            @param escape as bool
            @return str
        """
        if track.artists:
            artist = track.artists[0]
        elif track.album_artists:
            artist = track.album_artists[0]
        if escape:
            return GLib.uri_escape_string(artist, None, False)
        else:
            return artist

    def __download_bing_lyrics(self, track, methods, callback, *args):
        """
            Downloas lyrics from metro lyrics
            @param track as Track
            @param methods as []
            @param callback as function
        """
        title = self.__get_title(track, False)
        artist = self.__get_artist(track, False).lower()
        string = "%s %s" % (artist, title)
        uri = "https://www.bing.com/search?q=%s" % string
        helper = TaskHelper()
        helper.load_uri_content(uri,
                                self.__cancellable,
                                self.__on_lyrics_downloaded,
                                "b_heroLyrics",
                                "\n",
                                track,
                                methods,
                                callback,
                                *args)

    def __download_metro_lyrics(self, track, methods, callback, *args):
        """
            Downloas lyrics from metro lyrics
            @param track as Track
            @param methods as []
            @param callback as function
        """
        title = self.__get_title(track, False)
        artist = self.__get_artist(track, False).lower()
        string = "%s-lyrics-%s" % (title, artist)
        uri = "https://www.metrolyrics.com/%s.html" % string.replace(" ", "-")
        helper = TaskHelper()
        helper.load_uri_content(uri,
                                self.__cancellable,
                                self.__on_lyrics_downloaded,
                                "lyrics-body",
                                "",
                                track,
                                methods,
                                callback,
                                *args)

    def __download_wikia_lyrics(self, track, methods, callback, *args):
        """
            Downloas lyrics from wikia
            @param track as Track
            @param methods as []
            @param callback as function
        """
        title = self.__get_title(track, False)
        artist = self.__get_artist(track, False).lower()
        string = "%s:%s" % (artist, title)
        uri = "https://lyrics.wikia.com/wiki/%s" % string.replace(" ", "_")
        helper = TaskHelper()
        helper.load_uri_content(uri,
                                self.__cancellable,
                                self.__on_lyrics_downloaded,
                                "lyricbox",
                                "\n",
                                track,
                                methods,
                                callback,
                                *args)

    def __download_genius_lyrics(self, track, methods, callback, *args):
        """
            Download lyrics from genius
            @param track as Track
            @param methods as []
            @param callback as function
        """
        title = self.__get_title(track, False)
        artist = self.__get_artist(track, False)
        string = escape("%s %s" % (artist, title),
                        ignore=["_", "-", " ", ".", "/"]).replace(".", "")
        string = string.replace("/", " ")
        uri = "https://genius.com/%s-lyrics" % string.replace(" ", "-")
        helper = TaskHelper()
        helper.load_uri_content(uri,
                                self.__cancellable,
                                self.__on_lyrics_downloaded,
                                "song_body-lyrics",
                                "",
                                track,
                                methods,
                                callback,
                                *args)

    def __on_lyrics_downloaded(self, uri, status, data, cls, separator,
                               track, methods, callback, *args):
        """
            Search lyrics and pass to callback
            @param uri as str
            @param status as bool
            @param data as bytes
            @param cls as str
            @param separator as str
            @param track as Track
            @param methods as []
            @param callback as function
        """
        Logger.debug("LyricsHelper::__on_lyrics_downloaded(): %s", uri)
        if status:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(data, 'html.parser')
                lyrics = soup.find_all(
                    "div", class_=cls)[0].get_text(separator=separator)
                callback(lyrics, *args)
                return
            except Exception as e:
                Logger.warning("LyricsHelper::__on_lyrics_downloaded(): %s", e)
        self.__get_lyrics_from_web(track, methods, callback, *args)
