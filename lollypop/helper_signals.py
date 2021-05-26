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

from functools import wraps

from lollypop.define import App
from lollypop.logger import Logger
# For lint
App()


def signals(f):
    """
        Decorator to init signal helper
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        ret = f(*args, **kwargs)
        SignalsHelper.__init__(args[0])
        args[0].init(ret)

    return wrapper


def signals_map(f):
    """
        Decorator to init signal helper
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        ret = f(*args, **kwargs)
        SignalsHelper.__init__(args[0])
        args[0].init_map(ret)

    return wrapper


class SignalsHelper():
    """
        Helper for autoconnect/disconnect signals on map
        Keep signals cached when unmapped
    """

    def __init__(self):
        """
            Init helper
        """
        if not hasattr(self, "_connected"):
            self._connected = {}
            self.__signal_ids = []
            self.__allow_duplicate = []
            self.__cached = {}

    def allow_duplicate(self, callback_str):
        """
            Allow duplicate signal emit for callback while hidden
            @param callback_str as str
        """
        callback = getattr(self, callback_str)
        if callback not in self.__allow_duplicate:
            self.__allow_duplicate.append(callback)

    def init(self, signals):
        """
            Init signals
            @param signals as []
        """
        self._connect_signals(signals, False)
        self.__init(signals, False)

    def init_map(self, signals):
        """
            Init signals on map
            @param signals as []
        """
        self.__signal_ids.append(
                     self.connect("map",
                                  lambda x: self._connect_signals(
                                    signals, True)))
        self.__init(signals, True)

#######################
# PROTECTED           #
#######################
    def _connect_signals(self, signals, on_map):
        """
            Connect signals
            @param signals as []
            @param on_map on bool
        """
        for (obj, signal, callback_str) in signals:
            if obj is None:
                Logger.debug("Can't connect signal: %s -> %s",
                             signal, callback_str)
                continue
            name = "%s_%s" % (obj, signal)
            if name in self._connected.keys():
                continue
            callback = getattr(self, callback_str)
            if on_map:
                self._connected[name] = obj.connect(signal,
                                                    self.__on_signal,
                                                    callback)
            else:
                self._connected[name] = obj.connect(signal, callback)

    def _disconnect_signals(self, signals):
        """
            Disconnect signals
            @param signals as []
        """
        for (obj, signal, callback_str) in signals:
            if obj is None:
                Logger.warning("Can't disconnect signal: %s -> %s",
                               signal, callback_str)
                continue
            name = "%s_%s" % (obj, signal)
            if name not in self._connected.keys():
                continue
            connect_id = self._connected[name]
            obj.disconnect(connect_id)
            del self._connected[name]

#######################
# PRIVATE             #
#######################
    def __init(self, signals, on_map):
        """
            Init signals
            @param signals as []
            @param on_map on bool
        """
        if on_map:
            self.connect("map", self.__on_map)
            self.connect("unmap", self.__on_unmap)
        self.connect("destroy",
                     lambda x: self._disconnect_signals(signals))

    def __on_map(self, widget):
        """
            Run cached callbacks
            @param widget as Gtk.Widget
        """
        for callback in self.__cached.keys():
            (obj, callback_args) = self.__cached[callback]
            callback(obj, *callback_args)
        self.__cached = {}

    def __on_unmap(self, widget):
        """
            Disconnect initial map signal
            @param widget as Gtk.Widget
        """
        for signal_id in self.__signal_ids:
            self.disconnect(signal_id)
        self.__signal_ids = []

    def __on_signal(self, obj, *args):
        """
            Keep callback in cache if self not mapped
        """
        callback = args[-1]
        callback_args = args[:-1]
        if self.get_mapped() or callback in self.__allow_duplicate:
            callback(obj, *callback_args)
        else:
            self.__cached[callback] = (obj, callback_args)
