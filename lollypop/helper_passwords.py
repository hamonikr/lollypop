# Copyright (c) 2017 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

import gi
gi.require_version('Secret', '1')
from gi.repository import Secret, GLib

from lollypop.logger import Logger


class PasswordsHelper:
    """
        Simpler helper for Secret
    """

    def __init__(self):
        """
            Init helper
        """
        # Initial password lookup, prevent a lock issue in Flatpak backend
        if GLib.file_test("/app", GLib.FileTest.EXISTS):
            self.get_token("LASTFM")

    def get_token(self, service):
        """
            Get token for service
            @param service as str
        """
        try:
            SecretSchema = {
                "service": Secret.SchemaAttributeType.STRING
            }
            SecretAttributes = {
                "service": service
            }
            schema = Secret.Schema.new("org.gnome.Lollypop",
                                       Secret.SchemaFlags.NONE,
                                       SecretSchema)
            password = Secret.password_lookup_sync(schema, SecretAttributes,
                                                   None)
            return password
        except Exception as e:
            Logger.error("PasswordsHelper::get_token(): %s" % e)
        return None

    def get(self, service, callback, *args):
        """
            Get password
            @param service as str
            @param callback as function
            @param args
        """
        try:
            SecretSchema = {
                "service": Secret.SchemaAttributeType.STRING
            }
            SecretAttributes = {
                "service": service
            }
            schema = Secret.Schema.new("org.gnome.Lollypop",
                                       Secret.SchemaFlags.NONE,
                                       SecretSchema)
            Secret.password_search(schema,
                                   SecretAttributes,
                                   Secret.SearchFlags.UNLOCK |
                                   Secret.SearchFlags.LOAD_SECRETS,
                                   None,
                                   self.__on_secret_search,
                                   service,
                                   callback,
                                   *args)
        except Exception as e:
            Logger.warning("PasswordsHelper::get(): %s" % e)

    def store(self, service, login, password, callback=None, *args):
        """
            Store password
            @param service as str
            @param login as str
            @param password as str
            @param callback as function
        """
        try:
            schema_string = "org.gnome.Lollypop: %s@%s" % (service, login)
            SecretSchema = {
                "service": Secret.SchemaAttributeType.STRING,
                "login": Secret.SchemaAttributeType.STRING,
            }
            SecretAttributes = {
                "service": service,
                "login": login
            }
            schema = Secret.Schema.new("org.gnome.Lollypop",
                                       Secret.SchemaFlags.NONE,
                                       SecretSchema)
            Secret.password_store(schema, SecretAttributes,
                                  Secret.COLLECTION_DEFAULT,
                                  schema_string,
                                  password,
                                  None,
                                  callback,
                                  *args)
        except Exception as e:
            Logger.warning("PasswordsHelper::store(): %s" % e)

    def clear(self, service, callback=None, *args):
        """
            Clear password
            @param service as str
            @param callback as function
        """
        try:
            SecretSchema = {
                "service": Secret.SchemaAttributeType.STRING
            }
            SecretAttributes = {
                "service": service
            }
            schema = Secret.Schema.new("org.gnome.Lollypop",
                                       Secret.SchemaFlags.NONE,
                                       SecretSchema)
            Secret.password_clear(schema,
                                  SecretAttributes,
                                  None,
                                  self.__on_clear_search,
                                  callback,
                                  *args)
        except Exception as e:
            Logger.warning("PasswordsHelper::clear(): %s" % e)

#######################
# PRIVATE             #
#######################
    def __on_clear_search(self, source, result, callback=None, *args):
        """
            Clear passwords
            @param source as GObject.Object
            @param result as Gio.AsyncResult
            @param callback as function
        """
        try:
            if result is not None:
                Secret.password_clear_finish(result)
            if callback is not None:
                callback(*args)
        except Exception as e:
            Logger.error("PasswordsHelper::__on_clear_search(): %s" % e)

    def __on_secret_search(self, source, result, service, callback, *args):
        """
            Set userservice/password input
            @param source as GObject.Object
            @param result as Gio.AsyncResult
            @param service as str/None
            @param callback as function
            @param args
        """
        try:
            if result is not None:
                items = Secret.password_search_finish(result)
                for item in items:
                    attributes = item.get_attributes()
                    secret = item.retrieve_secret_sync()
                    callback(attributes,
                             secret.get().decode('utf-8'),
                             service,
                             *args)
                    break
            else:
                Logger.info("PasswordsHelper: no result!")
                callback(None, None, service, *args)
        except Exception as e:
            Logger.error("PasswordsHelper::__on_secret_search(): %s" % e)
            callback(None, None, service, *args)
