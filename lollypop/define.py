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

# This is global object initialised at lollypop start
# member init order is important!

from gi.repository import Gio, GLib


App = Gio.Application.get_default

LASTFM_API_KEY = "7a9619a850ccf7377c46cf233c51e3c6"
LASTFM_API_SECRET = "9254319364d73bec6c59ace485a95c98"

DISCOGS_API_KEY = "vcKgyONtKsaQZLvpUfOU"
DISCOGS_API_SECRET = "SmWphfGWALsmDnoyhPuQlDDQEIvFJuPM"

GOOGLE_API_ID = "015987506728554693370:waw3yqru59a"

MARGIN_BIG = 30
MARGIN = 15
MARGIN_MEDIUM = 10
MARGIN_SMALL = 5

LOLLYPOP_DATA_PATH = GLib.get_user_data_dir() + "/lollypop"
# All cache goes here
CACHE_PATH = GLib.get_user_cache_dir() + "/lollypop"
# Stores for albums
ALBUMS_PATH = LOLLYPOP_DATA_PATH + "/albums"
ALBUMS_WEB_PATH = LOLLYPOP_DATA_PATH + "/albums_web"
# Stores for artists
ARTISTS_PATH = LOLLYPOP_DATA_PATH + "/artists"
# Store for lyrics
LYRICS_PATH = LOLLYPOP_DATA_PATH + "/lyrics"


class TimeStamp:
    ONE_YEAR = 31536000
    TWO_YEAR = 63072000
    THREE_YEAR = 94608000


class FileType:
    UNKNOWN = 0
    AUDIO = 1
    PLS = 2
    OTHER = 3


class Repeat:
    NONE = 0
    AUTO_SIMILAR = 1
    AUTO_RANDOM = 2
    TRACK = 3
    ALL = 4


class LovedFlags:
    NONE = 1 << 0
    LOVED = 1 << 1
    SKIPPED = 1 << 2


class GstPlayFlags:
    GST_PLAY_FLAG_VIDEO = 1 << 0  # We want video output
    GST_PLAY_FLAG_AUDIO = 1 << 1  # We want audio output
    GST_PLAY_FLAG_TEXT = 1 << 3   # We want subtitle output


class StorageType:
    NONE = 1 << 0
    COLLECTION = 1 << 1
    EPHEMERAL = 1 << 2
    SAVED = 1 << 3
    SPOTIFY_NEW_RELEASES = 1 << 4
    SPOTIFY_SIMILARS = 1 << 5
    EXTERNAL = 1 << 6
    SEARCH = 1 << 7
    DEEZER_CHARTS = 1 << 8
    ALL = 1 << 1 | 1 << 2 | 1 << 3 | 1 << 4 | 1 << 5 | 1 << 6 | 1 << 7 | 1 << 8


class ArtBehaviour:
    NONE = 1 << 0
    ROUNDED = 1 << 1
    ROUNDED_BORDER = 1 << 2
    BLUR = 1 << 3
    BLUR_HARD = 1 << 4
    BLUR_MAX = 1 << 5
    FALLBACK = 1 << 6
    DARKER = 1 << 7
    LIGHTER = 1 << 8
    CROP = 1 << 9
    CROP_SQUARE = 1 << 10
    CACHE = 1 << 11
    NO_CACHE = 1 << 12


class ViewType:
    DEFAULT = 1 << 0
    TWO_COLUMNS = 1 << 1
    SINGLE_COLUMN = 1 << 2
    DND = 1 << 3
    SEARCH = 1 << 4
    PLAYLISTS = 1 << 5
    ALBUM = 1 << 6
    SMALL = 1 << 7
    QUEUE = 1 << 8
    SCROLLED = 1 << 9
    OVERLAY = 1 << 10
    FULLSCREEN = 1 << 11
    PLAYBACK = 1 << 12
    BANNER = 1 << 13
    ARTIST = 1 << 14
    TOOLBAR = 1 << 15


NetworkAccessACL = {
    "DATA": 1 << 1,
    "LASTFM": 1 << 2,
    "SPOTIFY": 1 << 3,
    "YOUTUBE": 1 << 4,
    "GOOGLE": 1 << 5,
    "STARTPAGE": 1 << 6,
    "WIKIPEDIA": 1 << 7,
    "JAMENDO": 1 << 8,
    "MUSICBRAINZ": 1 << 9,
    "ITUNES": 1 << 10,
    "DEEZER": 1 << 11,
    "WIKIA": 1 << 12,
    "GENIUS": 1 << 13,
    "AUDIODB": 1 << 14,
    "FANARTTV": 1 << 15,
    "DUCKDUCKGO": 1 << 16,
    "LIBREFM": 1 << 17,
    "METROLYRICS": 1 << 18,
    "BING": 1 << 19,
}


class StoreExtention:
    JPG = 0
    PNG = 1


class LoadingState:
    NONE = 0
    RUNNING = 1
    ABORTED = 2
    FINISHED = 3


class IndicatorType:
    NONE = 1 << 0
    PLAY = 1 << 1
    LOVED = 1 << 2
    SKIPPED = 1 << 3
    LOADING = 1 << 4


class ArtSize:
    SMALL = 50     # Depends on cover-size in gsettings
    MEDIUM = 100
    BANNER = 150   # Depends on cover-size in gsettings
    BIG = 200      # Depends on cover-size in gsettings
    MINIPLAYER = 300
    FULLSCREEN = 400
    MPRIS = 900


class ScanType:
    EXTERNAL = 0
    NEW_FILES = 1
    FULL = 2


class ScanUpdate:
    ADDED = 0
    REMOVED = 1
    MODIFIED = 2


class SelectionListMask:
    NONE = 1 << 0
    SIDEBAR = 1 << 1
    FASTSCROLL = 1 << 2
    ARTISTS = 1 << 3
    GENRES = 1 << 4
    PLAYLISTS = 1 << 5
    COMPILATIONS = 1 << 6
    LABEL = 1 << 7
    ELLIPSIZE = 1 << 8


class Notifications:
    NONE = 0
    ALL = 1
    MPRIS = 2


class PowerManagement:
    NONE = 0             # Use OS defaults
    IDLE = 1             # Inhibit screensaver
    SUSPEND = 2          # Inhibit suspend
    BOTH = 3             # Inhibit screensaver and suspend


class ReplayGain:
    NONE = 0
    TRACK = 1
    ALBUM = 1


class Size:
    MINI = 250
    PHONE = 360  # Librem Phone
    SMALL = 500
    MEDIUM = 720
    NORMAL = 850
    BIG = 1000


class OrderBy:
    ARTIST_YEAR = 0
    ARTIST_TITLE = 1
    TITLE = 2
    YEAR_DESC = 3
    POPULARITY = 4
    YEAR_ASC = 5


# Order is important
class Type:
    NONE = -1
    SUGGESTIONS = -2
    POPULARS = -3
    RANDOMS = -4
    RECENTS = -5
    LOVED = -6
    LITTLE = -7
    SKIPPED = -8
    # WEB is stored in DB, can't be changed
    WEB = -9
    # Stored in DB, can't be changed
    COMPILATIONS = -10
    ARTISTS = -11
    ARTISTS_LIST = -12
    GENRES = -13
    GENRES_LIST = -14
    YEARS = -15
    PLAYLISTS = -16
    SMART = -19
    EQUALIZER = -20
    DEVICE_ALBUMS = -27
    DEVICE_PLAYLISTS = -28
    ALBUM = -29
    ALL = -99
    SEPARATOR = -100
    CURRENT = -101
    INFO = -102
    SEARCH = -103
    LYRICS = -104


LATIN1_ENCODING = b"\x00"
"""Byte code for latin1"""
UTF_16_ENCODING = b"\x01"
"""Byte code for UTF-16"""
UTF_16BE_ENCODING = b"\x02"
"""Byte code for UTF-16 (big endian)"""
UTF_8_ENCODING = b"\x03"
"""Byte code for UTF-8 (Not supported in ID3 versions < 2.4)"""


SPOTIFY_CLIENT_ID = "0b144843878a46b2b12e0958c342c3ac"
SPOTIFY_SECRET = "265ab8e057684f1b9e69e0c58f4881c1"
AUDIODB_CLIENT_ID = "195003"
FANARTTV_ID = "1cb10bc910c8d4fc34e0c78ac4e8ef46"
