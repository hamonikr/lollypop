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

from gi.repository import Soup, Gio

import json
from hashlib import md5
from pickle import load, dump

from lollypop.helper_passwords import PasswordsHelper
from lollypop.logger import Logger
from lollypop.utils import get_network_available
from lollypop.define import LOLLYPOP_DATA_PATH, App
from lollypop.define import LASTFM_API_KEY, LASTFM_API_SECRET


class LastFMWebService:
    """
        Handle scrobbling to Last.fm and all authenticated API calls
    """

    def __init__(self, name):
        """
            Init service
            @param name as str
        """
        self.__name = name
        self.__queue = []
        if name == "LIBREFM":
            self.__uri = "https://libre.fm/2.0/"
        else:
            self.__uri = "https://ws.audioscrobbler.com/2.0/"
        self.start()

    def start(self):
        """
            Start web service (load save queue)
        """
        try:
            self.__cancellable = Gio.Cancellable()
            self.__queue = load(
                open(LOLLYPOP_DATA_PATH + "/%s_queue.bin" % self.__name, "rb"))
        except Exception as e:
            Logger.info("LastFMWebService::start(): %s", e)
            self.__queue = []

    def stop(self):
        """
            Stop current tasks and save queue to disk
            @return bool
        """
        self.__cancellable.cancel()
        try:
            with open(LOLLYPOP_DATA_PATH + "/%s_queue.bin" % self.__name,
                      "wb") as f:
                dump(list(self.__queue), f)
        except Exception as e:
            Logger.info("LastFMWebService::stop: %s", e)
        return True

    def listen(self, track, timestamp):
        """
            Submit a listen for a track (scrobble)
            @param track as Track
            @param timestamp as int
        """
        monitor = Gio.NetworkMonitor.get_default()
        if App().settings.get_value("disable-scrobbling") or\
                not get_network_available() or\
                monitor.get_network_metered():
            self.__queue.append((track, timestamp))
        elif track.id is not None and track.id >= 0:
            App().task_helper.run(self.__listen, track, timestamp)

    def playing_now(self, track):
        """
            Submit a playing now notification for a track
            @param track as Track
        """
        monitor = Gio.NetworkMonitor.get_default()
        if App().settings.get_value("disable-scrobbling") or\
                not get_network_available() or\
                monitor.get_network_metered():
            return
        if track.id is not None and track.id >= 0:
            App().task_helper.run(self.__playing_now, track)

    def love(self, artist, title):
        """
            Love track
            @param artist as string
            @param title as string
            @thread safe
        """
        App().task_helper.run(self.__love, artist, title, True)

    def unlove(self, artist, title):
        """
            Unlove track
            @param artist as string
            @param title as string
            @thread safe
        """
        App().task_helper.run(self.__love, artist, title, False)

    def set_loved(self, track, loved):
        """
            Add or remove track from loved playlist on Last.fm
            @param track as Track
            @param loved as bool
        """
        if loved == 1:
            self.love(",".join(track.artists), track.name)
        else:
            self.unlove(",".join(track.artists), track.name)

    def sync_loved_tracks(self):
        """
            Synced loved tracks from Last.fm
        """
        self.__passwords_helper = PasswordsHelper()
        self.__passwords_helper.get("LASTFM", self.__on_get_password)

#######################
# PRIVATE             #
#######################
    def __love(self, artist, title, status):
        """
            Love track
            @param artist as string
            @param title as string
            @param status as bool
        """
        try:
            token = App().ws_director.token_ws.get_token(
                self.__name, self.__cancellable)
            if token is None:
                return
            if status:
                args = self.__get_args_for_method("track.love")
            else:
                args = self.__get_args_for_method("track.unlove")
            args.append(("artist", artist))
            args.append(("track", title))
            args.append(("sk", token))
            api_sig = self.__get_sig_for_args(args)
            args.append(("api_sig", api_sig))
            post_data = {}
            for (name, value) in args:
                post_data[name] = value
            msg = Soup.form_request_new_from_hash("POST",
                                                  self.__uri,
                                                  post_data)
            msg.request_headers.append("Accept-Charset", "utf-8")
            data = App().task_helper.send_message_sync(msg, self.__cancellable)
            if data is not None:
                Logger.debug("%s: %s", self.__uri, data)
        except Exception as e:
            Logger.error("LastFMWebService::__love(): %s" % e)

    def __get_args_for_method(self, method):
        """
            Get arguments for method
            @param method as str
            @return [str]
        """
        args = [("method", method)]
        args.append(("api_key", LASTFM_API_KEY))
        return args

    def __get_sig_for_args(self, args):
        """
            Get API sig for method
            @param args as [str]
            @return str
        """
        args.sort()
        api_sig = ""
        for (name, value) in args:
            api_sig += "%s%s" % (name, value)
        api_sig += LASTFM_API_SECRET
        return md5(api_sig.encode("utf-8")).hexdigest()

    def __listen(self, track, timestamp):
        """
            Scrobble track
            @param track as Track
            @param timestamp as int
        """
        tracks = self.__queue + [(track, timestamp)]
        self.__queue = []
        try:
            for (track, timestamp) in tracks:
                token = App().ws_director.token_ws.get_token(
                    self.__name, self.__cancellable)
                if token is None:
                    return
                args = self.__get_args_for_method("track.scrobble")
                args.append(("artist", track.artists[0]))
                args.append(("albumArtist", track.album.artists[0]))
                args.append(("track", track.name))
                args.append(("album", track.album.name))
                if track.mbid and track.mbid.find(":") == -1:
                    args.append(("mbid", track.mbid))
                args.append(("timestamp", str(timestamp)))
                args.append(("sk", token))
                api_sig = self.__get_sig_for_args(args)
                args.append(("api_sig", api_sig))
                post_data = {}
                for (name, value) in args:
                    post_data[name] = value
                msg = Soup.form_request_new_from_hash("POST",
                                                      self.__uri,
                                                      post_data)
                msg.request_headers.append("Accept-Charset", "utf-8")
                data = App().task_helper.send_message_sync(msg,
                                                           self.__cancellable)
                if data is not None:
                    Logger.debug("%s: %s", self.__uri, data)
                else:
                    self.__queue.append((track, timestamp))
        except Exception as e:
            Logger.error("LastFMWebService::__listen(): %s" % e)

    def __playing_now(self, track):
        """
            Now playing track
            @param track as Track
        """
        try:
            token = App().ws_director.token_ws.get_token(
                self.__name, self.__cancellable)
            if token is None:
                return
            args = self.__get_args_for_method("track.updateNowPlaying")
            args.append(("artist", track.artists[0]))
            args.append(("albumArtist", track.album.artists[0]))
            args.append(("track", track.name))
            args.append(("album", track.album.name))
            if track.mbid and track.mbid.find(":") == -1:
                args.append(("mbid", track.mbid))
            args.append(("duration", str(track.duration // 1000)))
            args.append(("sk", token))
            api_sig = self.__get_sig_for_args(args)
            args.append(("api_sig", api_sig))
            post_data = {}
            for (name, value) in args:
                post_data[name] = value
            msg = Soup.form_request_new_from_hash("POST",
                                                  self.__uri,
                                                  post_data)
            msg.request_headers.append("Accept-Charset", "utf-8")
            data = App().task_helper.send_message_sync(msg, self.__cancellable)
            if data is not None:
                Logger.debug("%s: %s -> %s", self.__uri, data, post_data)
        except Exception as e:
            Logger.error("LastFMWebService::__playing_now(): %s" % e)

    def __populate_loved_tracks(self, user):
        """
            Populate loved tracks playlist
            @parma user as str
        """
        try:
            uri = "http://ws.audioscrobbler.com/2.0/"
            uri += "?method=user.getLovedTracks"
            uri += "&user=%s&api_key=%s&format=json&limit=1000" % (
                user, LASTFM_API_KEY)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                content = json.loads(data.decode("utf-8"))
                for track in content["lovedtracks"]["track"]:
                    artist = track["artist"]["name"]
                    name = track["name"]
                    track_id = App().tracks.search_track(artist, name)
                    if track_id is None:
                        Logger.warning(
                            "LastFM: can't find %s, %s" % (
                                artist, name))
                    else:
                        App().tracks.set_loved(track_id, 1)
        except Exception as e:
            Logger.error("LastFM::__populate_loved_tracks: %s" % e)

    def __on_get_password(self, attributes, password, service):
        """
            Populate loved tracks
            @param attributes as {}
            @param password as str
            @param service as str
        """
        if attributes is not None:
            App().task_helper.run(
                self.__populate_loved_tracks, attributes["login"])
