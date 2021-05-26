# Copyright (c) 2017-2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from threading import current_thread

from lollypop.define import App


class SqlCursor:
    """
        Context manager to get the SQL cursor
    """
    def add(obj):
        """
            Add cursor to thread list
        """
        name = current_thread().getName() + obj.__class__.__name__
        App().cursors[name] = obj.get_cursor()

    def remove(obj):
        """
            Remove cursor from thread list and commit
        """
        name = current_thread().getName() + obj.__class__.__name__
        if name in App().cursors.keys():
            obj.thread_lock.acquire()
            App().cursors[name].commit()
            obj.thread_lock.release()
            App().cursors[name].close()
            del App().cursors[name]

    def commit(obj):
        """
            Commit current obj
        """
        name = current_thread().getName() + obj.__class__.__name__
        if name in App().cursors.keys():
            obj.thread_lock.acquire()
            App().cursors[name].commit()
            obj.thread_lock.release()

    def __init__(self, obj, commit=False):
        """
            Init object
            @param obj as Database/Playlists/Radios
            @param commit as bool
        """
        self.__obj = obj
        self.__commit = commit
        self.__cursor = None

    def __enter__(self):
        """
            Get thread cursor or a new one
        """
        name = current_thread().getName() + self.__obj.__class__.__name__
        if name in App().cursors.keys():
            cursor = App().cursors[name]
            return cursor
        else:
            self.__cursor = self.__obj.get_cursor()
            return self.__cursor

    def __exit__(self, type, value, traceback):
        """
            Close cursor if not thread cursor
        """
        if self.__cursor is not None:
            if self.__commit:
                self.__obj.thread_lock.acquire()
                self.__cursor.commit()
                self.__obj.thread_lock.release()
            self.__cursor.close()
        self.__cursor = None
