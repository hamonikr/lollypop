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

from lollypop.objects_track import Track
from lollypop.utils import emit_signal


class QueuePlayer:
    """
        Manage queue
    """

    def __init__(self):
        """
            Init queue
        """
        self.__queue = []
        self._queue_current_track = None

    def set_queue(self, queue):
        """
            Set queue
            @param queue as [int]
        """
        self.__queue = queue

    def append_to_queue(self, track_id, notify=True):
        """
            Append track to queue,
            remove previous track if exist
            @param track_id as int
            @param notify as bool
        """
        if track_id in self.__queue:
            self.__queue.remove(track_id)
        self.__queue.append(track_id)
        self.set_next()
        self.set_prev()
        if notify:
            emit_signal(self, "queue-changed")

    def insert_in_queue(self, track_id, pos=0, notify=True):
        """
            Prepend track to queue,
            remove previous track if exist
            @param track_id as int
            @param pos as int
            @param notify as bool
        """
        if track_id in self.__queue:
            self.__queue.remove(track_id)
        self.__queue.insert(pos, track_id)
        self.set_next()
        self.set_prev()
        if notify:
            emit_signal(self, "queue-changed")

    def remove_from_queue(self, track_id, notify=True):
        """
            Remove track from queue
            @param track_id as int
            @param notify as bool
        """
        if track_id in self.__queue:
            self.__queue.remove(track_id)
        if notify:
            emit_signal(self, "queue-changed")

    def clear_queue(self, notify=True):
        """
            Set queue
            @param [ids as int]
            @param notify as bool
        """
        self.__queue = []
        if notify:
            emit_signal(self, "queue-changed")

    def is_in_queue(self, track_id):
        """
            True if track id exists in queue
            @param track_id as int
            @return bool
        """
        if self.__queue:
            return track_id in self.__queue
        else:
            return False

    def album_in_queue(self, album):
        """
            True if album id exists in queue
            @param album as Album
            @return bool
        """
        if self.__queue:
            union = set(self.__queue) & set(album.track_ids)
            return len(union) == len(album.track_ids)
        else:
            return False

    def get_track_position(self, track_id):
        """
            Return track position in queue
            @param track_id as int
            @return position as int
        """
        return self.__queue.index(track_id) + 1

    def next(self):
        """
            Get next track id
            @return Track
        """
        track_id = None
        if self.__queue:
            track_id = self.__queue[0]
            if self._queue_current_track is None:
                self._queue_current_track = self._current_track
        return Track(track_id)

    @property
    def queue(self):
        """
            Return queue
            @return [ids as int]
        """
        return self.__queue

#######################
# PRIVATE             #
#######################
