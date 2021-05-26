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

from gi.repository import GObject

from lollypop.define import StorageType, App
from lollypop.utils import emit_signal, get_network_available
from lollypop.search_local import LocalSearch


class Search(GObject.Object):
    """
        Local search
    """
    __gsignals__ = {
        "match-artist": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "match-album": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "match-track": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        "finished": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self):
        """
            Init search
        """
        GObject.Object.__init__(self)
        self.__search_count = 0
        self.__local_search = LocalSearch()
        self.__connect_search_signals(self.__local_search)
        self.__web_search = None

    def set_web_search(self, name):
        """
            Set web search to name
            @param name as str
        """
        self.__web_search = None
        if not get_network_available("YOUTUBE"):
            return

        if name == "SPOTIFY":
            from lollypop.search_spotify import SpotifySearch
            self.__web_search = SpotifySearch()
            self.__connect_search_signals(self.__web_search)
        elif name == "LASTFM":
            from lollypop.search_lastfm import LastFMSearch
            self.__web_search = LastFMSearch()
            self.__connect_search_signals(self.__web_search)
        elif name == "MUSICBRAINZ":
            from lollypop.search_musicbrainz import MusicBrainzSearch
            self.__web_search = MusicBrainzSearch()
            self.__connect_search_signals(self.__web_search)
        elif name == "DEEZER":
            from lollypop.search_deezer import DeezerSearch
            self.__web_search = DeezerSearch()
            self.__connect_search_signals(self.__web_search)
        elif name == "JAMENDO":
            from lollypop.search_jamendo import JamendoSearch
            self.__web_search = JamendoSearch()
            self.__connect_search_signals(self.__web_search)

    def load_tracks(self, album, cancellable):
        """
            Load tracks for album with correct web service
            @param album as Album
            @param cancellable as Gio.Cancellable
        """
        uri = album.uri
        if not uri:
            pass
        elif uri.startswith("mb:"):
            from lollypop.search_musicbrainz import MusicBrainzSearch
            MusicBrainzSearch().load_tracks(album, cancellable)
        elif uri.startswith("dz:"):
            from lollypop.search_deezer import DeezerSearch
            DeezerSearch().load_tracks(album, cancellable)
        elif uri.startswith("jam:"):
            from lollypop.search_jamendo import JamendoSearch
            JamendoSearch().load_tracks(album, cancellable)
        # elif uri.startswith("sp:"): => compatibility
        else:
            from lollypop.search_spotify import SpotifySearch
            SpotifySearch().load_tracks(album, cancellable)

    def get(self, search, cancellable):
        """
            Get match for search
            @param search as str
            @param cancellable as Gio.Cancellable
        """
        # Only local items
        storage_type = StorageType.COLLECTION |\
            StorageType.SAVED |\
            StorageType.SEARCH
        App().task_helper.run(self.__local_search.get,
                              search, storage_type, cancellable)
        self.__search_count += 1
        if self.__web_search is not None:
            storage_type = StorageType.SEARCH | StorageType.EPHEMERAL
            App().task_helper.run(self.__web_search.get,
                                  search, storage_type, cancellable)
            self.__search_count += 1

#######################
# PRIVATE             #
#######################
    def __on_finished(self, search):
        """
            Emit finished signals if all search are finished
            @param search as Search provider
        """
        self.__search_count -= 1
        emit_signal(self, "finished", self.__search_count == 0)

    def __connect_search_signals(self, search):
        """
            Connect search signals
            @param search as Search provider
        """
        search.connect("match-artist",
                       lambda x, y, z: self.emit("match-artist", y, z))
        search.connect("match-album",
                       lambda x, y, z: self.emit("match-album", y, z))
        search.connect("match-track",
                       lambda x, y, z: self.emit("match-track", y, z))
        search.connect("finished", self.__on_finished)
