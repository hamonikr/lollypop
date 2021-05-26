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
from gi.repository.Gio import FILE_ATTRIBUTE_TIME_ACCESS

from time import time

from lollypop.logger import Logger
from lollypop.define import App, FileType


def get_file_type(uri):
    """
        Get file type from file extension
        @param uri as str
    """
    audio = ["3gp", "aa", "aac", "aax", "act", "aiff", "alac", "amr", "ape",
             "au", "awb", "dct", "dss", "dvf", "flac", "gsm", "iklax", "ivs",
             "m4a", "m4b", "m4p", "mmf", "mp3", "mpc", "msv", "nmf", "nsf",
             "ogg", "opus", "ra", "raw", "rf64", "sln", "tta", "voc", "vox",
             "wav", "wma", "wv", "webm", "8svx", "cda"]
    other = ["7z", "arj", "deb", "pkg", "rar", "rpm", "tar.gz", "z", "zip",
             "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "db", "txt",
             "mov", "avi", "html", "ini", "cue", "nfo", "lrc"]
    image = ["ai", "bmp", "gif", "ico", "jpeg", "jpg",
             "png", "ps", "psd", "svg", "tif"]
    pls = ["pls", "m3u"]
    split = uri.lower().split(".")
    if len(split) < 2:
        return FileType.UNKNOWN
    elif split[-1] in audio:
        return FileType.AUDIO
    elif split[-1] in pls:
        return FileType.PLS
    elif split[-1] in image + other:
        return FileType.OTHER
    else:
        return FileType.UNKNOWN


def is_audio(info):
    """
        Return True if files is audio
        @param info as Gio.FileInfo
    """
    audio = ["application/ogg", "application/x-ogg", "application/x-ogm-audio",
             "audio/aac", "audio/mp4", "audio/mpeg", "audio/mpegurl",
             "audio/ogg", "audio/vnd.rn-realaudio", "audio/vorbis",
             "audio/x-flac", "audio/x-mp3", "audio/x-mpeg", "audio/x-mpegurl",
             "audio/x-ms-wma", "audio/x-musepack", "audio/x-oggflac",
             "audio/x-pn-realaudio", "application/x-flac", "audio/x-speex",
             "audio/x-vorbis", "audio/x-vorbis+ogg", "audio/x-wav",
             "x-content/audio-player", "audio/x-aac", "audio/m4a",
             "audio/x-m4a", "audio/mp3", "audio/ac3", "audio/flac",
             "audio/x-opus+ogg", "application/x-extension-mp4", "audio/x-ape",
             "audio/x-pn-aiff", "audio/x-pn-au", "audio/x-pn-wav",
             "audio/x-pn-windows-acm", "application/x-matroska",
             "audio/x-matroska", "audio/x-wavpack", "video/mp4",
             "audio/x-mod", "audio/x-mo3", "audio/x-xm", "audio/x-s3m",
             "audio/x-it", "audio/aiff", "audio/x-aiff"]
    if info is not None:
        if info.get_content_type() in audio:
            return True
    return False


def is_pls(info):
    """
        Return True if files is a playlist
        @param info as Gio.FileInfo
    """
    if info is not None:
        if info.get_content_type() in ["audio/x-mpegurl",
                                       "application/xspf+xml",
                                       "application/vnd.apple.mpegurl"]:
            return True
    return False


def get_mtime(info):
    """
        Return Last modified time of a given file
        @param info as Gio.FileInfo
    """
    mtime = info.get_attribute_as_string("time::modified")
    if mtime is None:
        return 0
    else:
        return int(mtime)


def remove_oldest(path, timestamp):
    """
        Remove oldest files at path
        @param path as str
        @param timestamp as int
    """
    SCAN_QUERY_INFO = "%s" % FILE_ATTRIBUTE_TIME_ACCESS
    try:
        d = Gio.File.new_for_path(path)
        infos = d.enumerate_children(SCAN_QUERY_INFO,
                                     Gio.FileQueryInfoFlags.NONE,
                                     None)
        for info in infos:
            f = infos.get_child(info)
            if info.get_file_type() == Gio.FileType.REGULAR:
                atime = int(info.get_attribute_as_string(
                    FILE_ATTRIBUTE_TIME_ACCESS))
                # File not used since one year
                if time() - atime > timestamp:
                    f.delete(None)
    except Exception as e:
        Logger.error("remove_oldest(): %s", e)


def is_readonly(uri):
    """
        Check if uri is readonly
    """
    try:
        if not uri:
            return True
        f = Gio.File.new_for_uri(uri)
        info = f.query_info("access::can-write",
                            Gio.FileQueryInfoFlags.NONE,
                            None)
        return not info.get_attribute_boolean("access::can-write")
    except:
        return True


def create_dir(path):
    """
        Create dir
        @param path as str
    """
    d = Gio.File.new_for_path(path)
    if not d.query_exists():
        try:
            d.make_directory_with_parents()
        except:
            Logger.info("Can't create %s" % path)


def install_youtube_dl():
    try:
        path = GLib.get_user_data_dir() + "/lollypop/python"
        argv = ["pip3", "install", "-t", path, "-U", "youtube-dl"]
        GLib.spawn_sync(None, argv, [], GLib.SpawnFlags.SEARCH_PATH, None)
    except Exception as e:
        Logger.error("install_youtube_dl: %s" % e)


def get_youtube_dl():
    """
        Get youtube-dl path and env
        @return (str, [])
    """
    if App().settings.get_value("recent-youtube-dl"):
        python_path = GLib.get_user_data_dir() + "/lollypop/python"
        path = "%s/bin/youtube-dl" % python_path
        env = ["PYTHONPATH=%s" % python_path]
        f = Gio.File.new_for_path(path)
        if f.query_exists():
            return (path, env)
    if GLib.find_program_in_path("youtube-dl"):
        return ("youtube-dl", [])
    else:
        return (None, [])


# From eyeD3 start
# eyeD3 is written and maintained by:
# Travis Shirk <travis@pobox.com>
def id3EncodingToString(encoding):
    from lollypop.define import LATIN1_ENCODING, UTF_8_ENCODING
    from lollypop.define import UTF_16_ENCODING, UTF_16BE_ENCODING
    if encoding == LATIN1_ENCODING:
        return "latin_1"
    elif encoding == UTF_8_ENCODING:
        return "utf_8"
    elif encoding == UTF_16_ENCODING:
        return "utf_16"
    elif encoding == UTF_16BE_ENCODING:
        return "utf_16_be"
    else:
        raise ValueError("Encoding unknown: %s" % encoding)


# From eyeD3 start
def decodeUnicode(bites, encoding):
    codec = id3EncodingToString(encoding)
    return bites.decode(codec)


def splitUnicode(data, encoding):
    from lollypop.define import UTF_16_ENCODING, UTF_16BE_ENCODING
    try:
        (d, t) = data.split(encoding, 1)
        # Try to fix invalid UTF16
        if encoding == UTF_16_ENCODING or encoding == UTF_16BE_ENCODING:
            if t[1] == 0:
                t = b''.join(t.split(b'\x00')) + b'\x00'
    except ValueError as e:
        Logger.warning("splitUnicode(): %s", e)
        (d, t) = data, b""
    return (d, t)
# From eyeD3 end
