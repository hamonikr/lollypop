# Copyright (c) 2014-2017 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from gi.repository import GLib

# from lollypop.utils import get_network_available
from lollypop.define import NetworkAccessACL, App, Type
from lollypop.ws_token import TokenWebService
from lollypop.logger import Logger


class DirectorWebService:
    """
        Manage web services
    """

    def __init__(self):
        """
            Init object
        """
        self.__token_ws = TokenWebService()
        self.__collection_ws = None
        self.__lastfm_ws = None
        self.__librefm_ws = None
        self.__listenbrainz_ws = None
        self.__spotify_timeout_id = None
        App().settings.connect("changed::network-access",
                               self.__on_network_access_acl_changed)
        App().settings.connect("changed::network-access-acl",
                               self.__on_network_access_acl_changed)

    def start(self):
        """
            Start all web services
        """
        if not App().settings.get_value("network-access"):
            network_acl = 0
        else:
            network_acl = App().settings.get_value(
                "network-access-acl").get_int32()
        self.__handle_collection(network_acl)
        self.__handle_lastfm(network_acl)
        self.__handle_listenbrainz(network_acl)

    def stop(self):
        """
            Stop all web services
            @return bool
        """
        stopped = stopping = 0
        if self.__lastfm_ws is not None:
            stopping += 1
            stopped += self.__lastfm_ws.stop()
        if self.__librefm_ws is not None:
            stopping += 1
            stopped += self.__librefm_ws.stop()
        if self.__listenbrainz_ws is not None:
            stopping += 1
            stopped += self.__listenbrainz_ws.stop()
        if self.__collection_ws is not None:
            stopping += 1
            stopped += self.__collection_ws.stop()
        return stopped == stopping

    @property
    def scrobblers(self):
        """
            Get all scrobbling services
            @return [LastFMWebService/ListenBrainzWebService]
        """
        web_services = []
        for ws in [self.__lastfm_ws, self.__librefm_ws,
                   self.__listenbrainz_ws]:
            if ws is not None:
                web_services.append(ws)
        return web_services

    @property
    def lastfm_ws(self):
        """
            Get Last.fm web service
            @return TokenWebService
        """
        return self.__lastfm_ws

    @property
    def token_ws(self):
        """
            Get token web service
            @return TokenWebService
        """
        return self.__token_ws

    @property
    def collection_ws(self):
        """
            Get Collection web service
            @return CollectionWebService
        """
        return self.__collection_ws

#######################
# PRIVATE             #
#######################
    def __handle_collection(self, acl):
        """
            Start/stop collection based on acl
            @param acl as int
        """
        show_album_lists = App().settings.get_value("shown-album-lists")
        if Type.SUGGESTIONS not in show_album_lists:
            return
        start = acl & NetworkAccessACL["YOUTUBE"] and\
            acl & NetworkAccessACL["DATA"]
        if start and self.__collection_ws is None:
            from lollypop.ws_collection import CollectionWebService
            self.__collection_ws = CollectionWebService()
            Logger.info("Collection web service started")
            self.__collection_ws.start()
            if self.__spotify_timeout_id is None:
                self.__spotify_timeout_id = GLib.timeout_add_seconds(
                    3600, self.__collection_ws.start)
        elif not start and self.__collection_ws is not None:
            if self.__spotify_timeout_id is not None:
                GLib.source_remove(self.__spotify_timeout_id)
                self.__spotify_timeout_id = None
            self.__collection_ws.stop()
            self.__collection_ws = None
            Logger.info("Collection web service stopping")

    def __handle_lastfm(self, acl):
        """
            Start/stop Last.fm based on acl
            @param acl as int
        """
        start = acl & NetworkAccessACL["LASTFM"]
        if start and self.__lastfm_ws is None:
            from lollypop.ws_lastfm import LastFMWebService
            self.__lastfm_ws = LastFMWebService("LASTFM")
            self.__lastfm_ws.start()
            Logger.info("Last.fm web service started")
        elif not start and self.__lastfm_ws is not None:
            self.__lastfm_ws = None
            Logger.info("Last.fm web service stopping")
        start = acl & NetworkAccessACL["LIBREFM"]
        if start and self.__librefm_ws is None:
            from lollypop.ws_lastfm import LastFMWebService
            self.__librefm_ws = LastFMWebService("LIBREFM")
            self.__librefm_ws.start()
            Logger.info("Libre.fm web service started")
        elif not start and self.__librefm_ws is not None:
            self.__librefm_ws = None
            Logger.info("Libre.fm web service stopping")

    def __handle_listenbrainz(self, acl):
        """
            Start/stop ListenBrainz based on acl
            @param acl as int
        """
        start = acl & NetworkAccessACL["MUSICBRAINZ"]
        if start and self.__listenbrainz_ws is None:
            from lollypop.ws_listenbrainz import ListenBrainzWebService
            self.__listenbrainz_ws = ListenBrainzWebService()
            self.__listenbrainz_ws.start()
            App().settings.bind("listenbrainz-user-token",
                                self.__listenbrainz_ws,
                                "user_token", 0)
            Logger.info("ListenBrainz web service started")
        elif not start and self.__listenbrainz_ws is not None:
            App().settings.unbind(self.__listenbrainz_ws,
                                  "listenbrainz-user-token")
            self.__listenbrainz_ws = None
            Logger.info("ListenBrainz web service stopping")

    def __on_network_access_acl_changed(self, *ignore):
        """
            Update available webservices
        """
        self.start()
