# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2015 Jean-Philippe Braun <eon@patapon.info>
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

from urllib.parse import urlparse
from lollypop.define import App, StorageType
from lollypop.objects import Base


class Track(Base):
    """
        Represent a track
    """
    DEFAULTS = {"name": "",
                "album_id": None,
                "artist_ids": [],
                "genre_ids": [],
                "popularity": 0,
                "rate": 0,
                "album_name": "",
                "artists": [],
                "genres": [],
                "duration": 0,
                "number": 0,
                "discnumber": 0,
                "discname": "",
                "year": None,
                "timestamp": 0,
                "mtime": 1,
                "loved": False,
                "storage_type": StorageType.COLLECTION,
                "mb_track_id": None,
                "lp_track_id": None,
                "mb_artist_ids": []}

    def __init__(self, track_id=None, album=None):
        """
            Init track
            @param track_id as int
            @param album as Album
        """
        Base.__init__(self, App().tracks)
        self.id = track_id
        self._uri = None
        self.__uri_loaded = False

        if album is None:
            from lollypop.objects_album import Album
            self.__album = Album(self.album_id)
            self.__album.set_tracks([self], False)
        else:
            self.__album = album

    def __del__(self):
        """
            Remove ref cycles
        """
        self.__album = None

    # Used by pickle
    def __getstate__(self):
        self.db = None
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.db = App().tracks

    def set_album(self, album):
        """
            Set track album
            @param album as Album
        """
        self.__album = album

    def set_uri(self, uri):
        """
            Set uri
            @param uri as string
        """
        self._uri = uri

    def set_number(self, number):
        """
            Set number
            @param number as int
        """
        self._number = number

    def set_name(self, name):
        """
            Set name
            @param name as str
        """
        self._name = name

    def set_loved(self, loved):
        """
            Mark album as loved
            @param loved as bool
        """
        if self.id >= 0:
            App().tracks.set_loved(self.id, loved)
            self.loved = loved

    def get_featuring_artist_ids(self, album_artist_ids):
        """
            Get featuring artist ids
            @return [int]
        """
        artist_ids = self.db.get_artist_ids(self.id)
        return list(set(artist_ids) - set(album_artist_ids))

    def set_preloaded(self):
        """
            Mark track as preloaded
        """
        self.__uri_loaded = True

    @property
    def uri_loaded(self):
        """
            True if tracks uri is loaded
            @return bool
        """
        # We already have a valid URI (jamendo for example)
        if self.uri.startswith("http"):
            return True
        return self.__uri_loaded

    @property
    def is_web(self):
        """
            True if track is a web track
            @return bool
        """
        return not self.storage_type & (StorageType.COLLECTION |
                                        StorageType.EXTERNAL)

    @property
    def is_http(self):
        """
            True if track is a http track
            @return bool
        """
        parsed = urlparse(self.uri)
        return parsed.scheme in ["http", "https"]

    @property
    def position(self):
        """
            Get track position for album
            @return int
        """
        i = 0
        for track_id in self.__album.track_ids:
            if track_id == self.id:
                break
            i += 1
        return i

    @property
    def first(self):
        """
            Is track first for album
            @return bool
        """
        tracks = self.__album.tracks
        return tracks and self.id == tracks[0].id

    @property
    def last(self):
        """
            Is track last for album
            @return bool
        """
        tracks = self.__album.tracks
        return tracks and self.id == tracks[-1].id

    @property
    def title(self):
        """
            Get track name
            Alias to Track.name
        """
        return self.name

    @property
    def uri(self):
        """
            Get track file uri
            @return str
        """
        if self._uri is None:
            self._uri = App().tracks.get_uri(self.id)
        return self._uri

    @property
    def path(self):
        """
            Get track file path
            @return str
        """
        f = Gio.File.new_for_uri(self.uri)
        path = f.get_path()
        if path is None:
            return ""
        return path

    @property
    def album(self):
        """
            Get track"s album
            @return Album
        """
        return self.__album

    @property
    def album_artists(self):
        """
            Get track album artists, can be != than album.artists as track
            may not have any album
            @return str
        """
        if getattr(self, "_album_artists") is None:
            self._album_artists = self.album.artists
        return self._album_artists
