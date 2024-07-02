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

from gi.repository import Soup

import json
from base64 import b64encode
from time import time, sleep
from hashlib import md5

from lollypop.logger import Logger
from lollypop.utils import get_network_available
from lollypop.define import SPOTIFY_CLIENT_ID, SPOTIFY_SECRET, App
from lollypop.define import LASTFM_API_KEY, LASTFM_API_SECRET
from lollypop.helper_passwords import PasswordsHelper


class TokenWebService:
    """
        Get token from web services
    """

    def __init__(self):
        """
            Init object
        """
        self.__token_expires = {"SPOTIFY": 0}
        self.__tokens = {"SPOTIFY": None,
                         "LASTFM": None,
                         "LIBREFM": None}
        self.__loading_token = {"SPOTIFY": False,
                                "LASTFM": False,
                                "LIBREFM": False}
        self.__passwords_helper = PasswordsHelper()

    def get_token(self, service, cancellable):
        """
            Get a token for name
            @param service as str
            @param cancellable as Gio.Cancellable
            @return str/None
        """
        if self.__tokens[service] == "" or not get_network_available():
            return None
        while self.__loading_token[service]:
            sleep(0.1)
        # Remove 60 seconds to be sure
        token_expired = service in self.__token_expires.keys() and\
            int(time()) + 60 > self.__token_expires[service]
        if token_expired or self.__tokens[service] is None:
            self.__loading_token[service] = True
            self.__get_token(service, cancellable)
            self.__loading_token[service] = False
        return self.__tokens[service]

    def get_lastfm_auth_token(self, service, cancellable, callback):
        """
            Get a new initial auth token
            @param service as str
            @param cancellable as Gio.Cancellable
            @param callback as function
            @thread safe
        """
        try:
            def on_data(uri, status, data):
                if status:
                    decode = json.loads(data.decode("utf-8"))
                    token = "validation:%s" % decode["token"]
                    callback(token, service)
            if service == "LASTFM":
                uri = "https://ws.audioscrobbler.com/2.0/"
            else:
                uri = "https://libre.fm/2.0/"
            uri += "?api_key=%s&format=json&method=auth.gettoken" %\
                LASTFM_API_KEY
            api_sig = "api_key%smethodauth.gettoken%s" % (
                LASTFM_API_KEY, LASTFM_API_SECRET)
            encoded = md5(api_sig.encode("utf-8")).hexdigest()
            uri += "&api_sig=%s" % encoded
            App().task_helper.load_uri_content(uri, cancellable, on_data)
        except Exception as e:
            Logger.error(
                "TokenWebService::get_lastfm_auth_token(): %s", e)

    def clear_token(self, service, clear_secret=False):
        """
            Clear token
            @param service as str
            @param clear_secret as bool
        """
        self.__tokens[service] = None
        if clear_secret:
            self.__passwords_helper.clear(service)

#######################
# PRIVATE             #
#######################
    def __load_token_for_service(self, token, service):
        """
            Load token for service
            @param token as str
            @param service as str
        """
        if token is None:
            self.__tokens[service] = ""
        elif token.startswith("validation:"):
            validation_token = token.replace("validation:", "")
            self.__get_lastfm_token(validation_token, service, None)
        else:
            self.__tokens[service] = token

    def __get_token(self, service, cancellable):
        """
            Get a token for name
            @param service as str
            @param cancellable as Gio.Cancellable
        """
        if service == "SPOTIFY":
            self.__get_spotify_token(cancellable)
        else:
            token = self.__passwords_helper.get_token(service)
            self.__load_token_for_service(token, service)

    def __get_spotify_token(self, cancellable):
        """
            Get a new auth token
            @param cancellable as Gio.Cancellable
        """
        try:
            uri = "https://accounts.spotify.com/api/token"
            credentials = "%s:%s" % (SPOTIFY_CLIENT_ID, SPOTIFY_SECRET)
            encoded = b64encode(credentials.encode("utf-8"))
            credentials = encoded.decode("utf-8")
            data = Soup.form_encode_hash({"grant_type": "client_credentials"})
            msg = Soup.Message.new_from_encoded_form("POST", uri, data)
            request_headers = msg.get_property("request-headers")
            request_headers.append("Authorization",
                                   "Basic %s" % credentials)
            data = App().task_helper.send_message_sync(msg, cancellable)
            if data is not None:
                decode = json.loads(data.decode("utf-8"))
                self.__token_expires["SPOTIFY"] = int(time()) +\
                    int(decode["expires_in"])
                self.__tokens["SPOTIFY"] = decode["access_token"]
        except Exception as e:
            Logger.error("TokenWebService::__get_spotify_token(): %s", e)
        self.__loading_token["SPOTIFY"] = False

    def __get_lastfm_token(self, token, service, cancellable):
        """
            Get token validated by user
            @param token as str
            @param service as str
            @param cancellable as Gio.Cancellable
        """
        try:
            if service == "LASTFM":
                uri = "https://ws.audioscrobbler.com/2.0/"
                uri += "?api_key=%s&format=json" % LASTFM_API_KEY
                uri += "&method=auth.getsession&token=%s" % token
                api_sig = "api_key%smethodauth.getsessiontoken%s%s" % (
                    LASTFM_API_KEY, token, LASTFM_API_SECRET)
                encoded = md5(api_sig.encode("utf-8")).hexdigest()
                uri += "&api_sig=%s" % encoded
            else:
                uri = "https://libre.fm/2.0/?format=json"
                uri += "&method=auth.getsession&token=%s" % token
            (status, data) = App().task_helper.load_uri_content_sync(
                uri, cancellable)
            if status:
                decode = json.loads(data.decode("utf-8"))
                self.__tokens[service] = decode["session"]["key"]
                self.__passwords_helper.clear(service,
                                              self.__passwords_helper.store,
                                              service,
                                              decode["session"]["name"],
                                              self.__tokens[service])
        except:
            self.__passwords_helper.clear(service)
            Logger.error(
                "TokenWebService::__get_lastfm_session(): %s", decode)
