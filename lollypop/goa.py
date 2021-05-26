# Copyright (c) 2018 Philipp Wolfer <ph.wolfer@gmail.com>
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
from gi.repository import GObject

try:
    gi.require_version("Goa", "1.0")
    from gi.repository import Goa
except:
    pass

from lollypop.logger import Logger
from lollypop.utils import emit_signal


class GoaSyncedAccount(GObject.Object):
    """
        Provides access to a GOA account with given provider_name.

        The account will be kept in sync and will be updated if accounts
        are added, removed or changed.
    """

    __gsignals__ = {
        "account-switched": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, provider_name):
        """
            Initialize a new GoaSyncedAccount for provider_name
            @param provider_name as str
        """
        GObject.Object.__init__(self)
        self._provider_name = provider_name
        self._proxy = None
        self._account = None
        self._oauth2_based = None
        try:
            self._client = Goa.Client.new_sync()
            self.__find_account()
            emit_signal(self, "account-switched")
            self._client.connect("account-added", self.__on_account_added)
            self._client.connect("account-removed", self.__on_account_removed)
            self._client.connect("account-changed", self.__on_account_changed)
        except:
            Logger.debug("GOA not available")
            self.__client = None

    @property
    def has_account(self):
        """
            True if there is an account with provider_name, False otherwise
            @return bool
        """
        return self._proxy is not None

    @property
    def account(self):
        """
            Return current GOA account
            @return Goa.Account
        """
        if self._proxy is None:
            return None
        if self._account is None:
            self._account = self._proxy.get_account()
        return self._account

    @property
    def oauth2_based(self):
        """
            Get OAuth2Based for current account
            @return Goa.OAuth2Based
        """
        if self._proxy is None:
            return None
        if self._oauth2_based is None:
            self._oauth2_based = self._proxy.get_oauth2_based()
        return self._oauth2_based

#######################
# PRIVATE             #
#######################
    def __find_account(self):
        """
            Find account matching current provider
        """
        Logger.debug("GOA __find_account")
        self._proxy = None
        try:
            for proxy in self._client.get_accounts():
                if self.__account_matches_provider(proxy):
                    Logger.debug("GOA account found")
                    self._proxy = proxy
                    return
        except Exception as e:
            Logger.debug("GOA __find_account failed: %s" % e)
            pass

    def __account_matches_provider(self, proxy):
        """
            True if current account match proxy account provider
            @param proxy as Goa.Object
            @return bool
        """
        account = proxy.get_account()
        Logger.debug("GOA __account_matches_provider: %s = %s ?" %
                     (account.props.provider_name, self._provider_name))
        return account.props.provider_name == self._provider_name

    def __on_account_added(self, client, proxy):
        """
            Update proxy and emit account-switched
            @param client as Goa.Client
            @param proxy as Goa.Object
        """
        Logger.debug("GOA account added")
        if self._proxy is None and self.__account_matches_provider(proxy):
            self._proxy = proxy
            emit_signal(self, "account-switched")

    def __on_account_removed(self, client, proxy):
        """
            Try finding a new account and emit account-switched
            @param client as Goa.Client
            @param proxy as Goa.Object
        """
        Logger.debug("GOA account removed")
        if self._proxy == proxy:
            self.__find_account()
            emit_signal(self, "account-switched")

    def __on_account_changed(self, client, proxy):
        """
            Reset current account settings
            @param client as Goa.Client
            @param proxy as Goa.Object
        """
        Logger.debug("GOA account changed")
        if self._proxy == proxy:
            self._account = None
            self._oauth2_based = None
