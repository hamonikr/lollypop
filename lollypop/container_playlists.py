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

from lollypop.define import ViewType


class PlaylistsContainer:
    """
        Playlists management for main view
    """

    def __init__(self):
        """
            Init container
        """
        pass

    def show_smart_playlist_editor(self, playlist_id):
        """
            Show a view allowing user to edit smart view
            @param playlist_id as int
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_playlist_smart import SmartPlaylistView
        view = SmartPlaylistView(playlist_id, view_type)
        view.populate()
        view.show()
        self._stack.add(view)
        self._stack.set_visible_child(view)

##############
# PROTECTED  #
##############

############
# PRIVATE  #
############
