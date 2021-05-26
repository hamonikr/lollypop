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

from gi.repository import Gio, GLib

from hashlib import sha256
from gettext import gettext as _

from lollypop.define import App
from lollypop.logger import Logger


class SyncMenu(Gio.Menu):
    """
        Sync menu
    """

    def __init__(self):
        """
            Init menu
        """
        Gio.Menu.__init__(self)
        self.__actions = []
        self.__all_devices = _("All devices")
        if App().devices:
            synced = self.__add_sync_action(self.__all_devices)
            for name in App().devices:
                self.__add_sync_action(name)
            if synced:
                for action in self.__actions:
                    action.set_enabled(False)

#######################
# PROTECTED           #
#######################
    def _get_synced(self, index):
        pass

    def _set_synced(self, index):
        pass

#######################
# PRIVATE             #
#######################
    def __add_sync_action(self, name):
        """
            Add sync action
            @param name as str
            @param status as bool
        """
        def on_get_synced(synced, sync_action):
            sync_action.set_state(GLib.Variant.new_boolean(synced))

        synced = False
        devices = list(App().settings.get_value("devices"))
        action_name = "sync_%s" % name
        encoded = sha256(action_name.encode("utf-8")).hexdigest()
        sync_action = Gio.SimpleAction.new_stateful(
                                          encoded,
                                          None,
                                          GLib.Variant.new_boolean(synced))
        App().add_action(sync_action)
        try:
            if name == self.__all_devices:
                index = 0
            else:
                index = devices.index(name) + 1
            App().task_helper.run(self._get_synced, index,
                                  callback=(on_get_synced, sync_action))
        except Exception as e:
            Logger.warning("SyncMenu::__add_sync_action(): %s", e)
        if name != self.__all_devices:
            self.__actions.append(sync_action)
        sync_action.connect("change-state",
                            self.__on_sync_action_change_state,
                            name)
        self.append(name, "app.%s" % encoded)
        return synced

    def __set_sync_action(self):
        """
            Set sync action
        """
        for mount in self.__vm.get_mounts():
            self.__add_sync_action(mount)

    def __on_mount_added(self, vm, mount):
        """
            On volume mounter
            @param vm as Gio.VolumeMonitor
            @param mount as Gio.Mount
        """
        self.__add_sync_action(mount)

    def __on_sync_action_change_state(self, action, variant, name):
        """
            Save album to collection
            @param Gio.SimpleAction
            @param GLib.Variant
            @param name as str
        """
        action.set_state(variant)
        if name == self.__all_devices:
            synced = variant.get_boolean()
            App().task_helper.run(self._set_synced, 0, synced)
            for action in self.__actions:
                action.set_enabled(not synced)
        else:
            devices = list(App().settings.get_value("devices"))
            if name not in devices:
                # Take an empty device index
                if "" in devices:
                    index = devices.index("")
                    devices[index] = name
                else:
                    devices.append(name)
                App().settings.set_value("devices",
                                         GLib.Variant("as", devices))
            index = devices.index(name) + 1
            App().task_helper.run(self._set_synced,
                                  index,
                                  variant.get_boolean())


class SyncAlbumsMenu(SyncMenu):
    """
        Sync menu for album
    """

    def __init__(self, albums):
        """
            Init menu
            @param albums as [Album]
        """
        if albums:
            self.__albums = albums
            SyncMenu.__init__(self)
        else:
            Gio.Menu.__init__(self)

#######################
# PROTECTED           #
#######################
    def _get_synced(self, index):
        """
            Get synced state for index
            @param index as int
            @return bool
        """
        for album in self.__albums:
            if not album.synced & (1 << index):
                return False
        return True

    def _set_synced(self, index, state):
        """
            Set synced state for index
            @param index as int
            @param state as bool
        """
        for album in self.__albums:
            if state:
                synced = album.synced | (1 << index)
            else:
                synced = album.synced & ~(1 << index)
            album.set_synced(synced)


class SyncPlaylistsMenu(SyncMenu):
    """
        Sync menu for playlist
    """

    def __init__(self, playlist_id):
        """
            Init menu
            @param album as Album
        """
        self.__playlist_id = playlist_id
        SyncMenu.__init__(self)

#######################
# PROTECTED           #
#######################
    def _get_synced(self, index):
        """
            Get synced state for index
            @param index as int
            @return bool
        """
        return App().playlists.get_synced(self.__playlist_id, index)

    def _set_synced(self, index, state):
        """
            Set synced state for index
            @param index as int
            @param state as bool
        """
        initial = App().playlists.get_synced(self.__playlist_id, index)
        if state:
            synced = initial | (1 << index)
        else:
            synced = initial & ~(1 << index)
        App().playlists.set_synced(self.__playlist_id, synced)
