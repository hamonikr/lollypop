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

from gi.repository import Gio

from gettext import gettext as _

from lollypop.define import App


class CurrentAlbumsMenu(Gio.Menu):
    """
        Menu for current albums
    """

    def __init__(self, header=False):
        """
            Init menu
            @param header as bool
        """
        Gio.Menu.__init__(self)

        if header:
            from lollypop.menu_header import MenuHeader
            label = _("Playing albums")
            icon_name = "org.gnome.Lollypop-play-queue-symbolic"
            self.append_item(MenuHeader(label, icon_name))
        menu = Gio.Menu()
        save_playback_action = Gio.SimpleAction.new(name="save_playback")
        save_playback_action.connect(
            "activate", self.__on_save_playback_action_activate)
        App().add_action(save_playback_action)
        menu.append(_("Create a new playlist"), "app.save_playback")
        self.append_section(_("Playing albums"), menu)

    def __on_save_playback_action_activate(self, action, variant):
        """
            Create a new playlist based on current playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        def albums_to_playlist():
            tracks = []
            for album in App().player.albums:
                tracks += album.tracks
            if tracks:
                import datetime
                now = datetime.datetime.now()
                date_string = now.strftime("%Y-%m-%d-%H:%M:%S")
                playlist_id = App().playlists.add(date_string)
                App().playlists.add_tracks(playlist_id, tracks)
        App().task_helper.run(albums_to_playlist)
