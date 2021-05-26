# Copyright (c) 2018 Philipp Wolfer <ph.wolfer@gmail.com>
# Copyright (c) 2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from gi.repository import Soup, GObject, Gio

import json
from pickle import load, dump

from lollypop.logger import Logger
from lollypop.define import App, LOLLYPOP_DATA_PATH, Type
from lollypop.utils import get_network_available


class ListenBrainzWebService(GObject.GObject):
    """
        Submit listens to ListenBrainz.org.

        See https://listenbrainz.readthedocs.io/en/latest/dev/api.html
    """

    user_token = GObject.Property(type=str, default="plop")

    def __init__(self):
        """
            Init ListenBrainz object
        """
        GObject.GObject.__init__(self)
        try:
            self.__uri = "https://api.listenbrainz.org/1/submit-listens"
            self.__name = "listenbrainz"
            self.__queue = []
            self.start()
        except Exception as e:
            Logger.info("LastFM::__init__(): %s", e)

    def start(self):
        """
            Start web service (load save queue)
        """
        try:
            self.__cancellable = Gio.Cancellable()
            self.__queue = load(
                open(LOLLYPOP_DATA_PATH + "/%s_queue.bin" % self.__name, "rb"))
        except Exception as e:
            Logger.info("ListenBrainzWebService::start(): %s", e)
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
            Logger.info("ListenBrainzWebService::stop: %s", e)
        return True

    def listen(self, track, timestamp):
        """
            Submit a listen for a track (scrobble)
            @param track as Track
            @param timestamp as int
        """
        monitor = Gio.NetworkMonitor.get_default()
        if not App().settings.get_value(
                "listenbrainz-user-token").get_string():
            return
        elif App().settings.get_value("disable-scrobbling") or\
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
        if not App().settings.get_value(
                "listenbrainz-user-token").get_string():
            return
        elif App().settings.get_value("disable-scrobbling") or\
                not get_network_available():
            return
        if track.id is not None and track.id >= 0:
            App().task_helper.run(self.__playing_now, track)

    def love(self, artist, title):
        pass

    def unlove(self, artist, title):
        pass

    def set_loved(self, track, loved):
        pass

#######################
# PRIVATE             #
#######################
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
                payload = self.__get_payload(track)
                payload[0]["listened_at"] = timestamp
                post_data = {
                    "listen_type": "single",
                    "payload": payload
                }
                body = json.dumps(post_data).encode("utf-8")
                msg = Soup.Message.new("POST", self.__uri)
                msg.set_request("application/json",
                                Soup.MemoryUse.STATIC,
                                body)
                msg.request_headers.append("Accept-Charset", "utf-8")
                msg.request_headers.append("Authorization",
                                           "Token %s" % self.user_token)
                msg.request_headers.append("Content-Type", "application/json")
                data = App().task_helper.send_message_sync(msg,
                                                           self.__cancellable)
                if data is not None:
                    Logger.debug("%s: %s", self.__uri, data)
                else:
                    self.__queue.append((track, timestamp))
        except Exception as e:
            Logger.error("ListenBrainzWebService::__listen(): %s" % e)

    def __playing_now(self, track):
        """
            Now playing track
            @param track as Track
        """
        try:
            payload = self.__get_payload(track)
            post_data = {
                "listen_type": "playing_now",
                "payload": payload
            }
            body = json.dumps(post_data).encode("utf-8")
            msg = Soup.Message.new("POST", self.__uri)
            msg.set_request("application/json",
                            Soup.MemoryUse.STATIC,
                            body)
            msg.request_headers.append("Accept-Charset", "utf-8")
            msg.request_headers.append("Authorization",
                                       "Token %s" % self.user_token)
            data = App().task_helper.send_message_sync(msg,
                                                       self.__cancellable)
            if data is not None:
                Logger.debug("%s: %s", self.__uri, data)
        except Exception as e:
            Logger.error("ListenBrainzWebService::__playing_now(): %s" % e)

    def __get_payload(self, track):
        """
            Build payload from track
            @param track as Track
            @return payload as []
        """
        if track.album.artist_ids[0] == Type.COMPILATIONS:
            artist = track.artists[0]
        else:
            artist = track.album.artists[0]
        payload = {
            "track_metadata": {
                "artist_name": artist,
                "track_name": track.title,
                "release_name": track.album_name,
                "additional_info": {
                    "listening_from": "Lollypop",
                    "artist_mbids": [
                        mbid for mbid in track.mb_artist_ids if mbid
                    ],
                    "release_mbid": track.album.mb_album_id,
                    "recording_mbid": track.mb_track_id,
                    "tracknumber": track.number
                }
            }
        }
        return [payload]
