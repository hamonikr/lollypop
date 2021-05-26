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

from lollypop.utils_album import tracks_to_albums
from lollypop.utils import get_default_storage_type
from lollypop.define import App, ViewType, MARGIN, Type, Size
from lollypop.objects_album import Album
from lollypop.objects_track import Track
from lollypop.widgets_banner_playlist import PlaylistBannerWidget
from lollypop.view_albums_list import AlbumsListView
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.helper_size_allocation import SizeAllocationHelper


class PlaylistsView(AlbumsListView, SignalsHelper, SizeAllocationHelper):
    """
        View showing playlists
    """

    @signals_map
    def __init__(self, playlist_id, view_type):
        """
            Init PlaylistView
            @parma playlist_id as int
            @param view_type as ViewType
        """
        AlbumsListView.__init__(self, [], [], view_type |
                                ViewType.SCROLLED |
                                ViewType.OVERLAY)
        SizeAllocationHelper.__init__(self)
        self.__playlist_id = playlist_id
        self.box.set_width(Size.MEDIUM)
        if view_type & ViewType.DND:
            self.dnd_helper.connect("dnd-finished",
                                    self.__on_dnd_finished)
        self.__banner = PlaylistBannerWidget(playlist_id, self)
        self.__banner.show()
        self.add_widget(self.box, self.__banner)
        return [
                (App().playlists, "playlist-track-added",
                 "_on_playlist_track_added"),
                (App().playlists, "playlist-track-removed",
                 "_on_playlist_track_removed"),
                (App().playlists, "playlists-removed", "_on_playlist_removed"),
                (App().playlists, "playlists-renamed", "_on_playlist_renamed"),
                (App().playlists, "playlists-updated", "_on_playlist_updated")
        ]

    def populate(self):
        """
            Populate view
        """
        if App().playlists.get_smart(self.__playlist_id):
            self.__populate_smart()
        else:
            self.__populate()

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"playlist_id": self.__playlist_id,
                "view_type": self.view_type}

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        filtered = []
        for child in self.children:
            filtered.append(child)
            for subchild in child.children:
                filtered.append(subchild)
        return filtered

    @property
    def scroll_shift(self):
        """
            Get scroll shift for y axes
            @return int
        """
        return self.__banner.height + MARGIN

#######################
# PROTECTED           #
#######################
    def _on_playlist_track_added(self, playlists, playlist_id, uri):
        """
            Append track to album list
            @param playlists as Playlists
            @param playlist_id as int
            @param uri as str
        """
        if playlist_id == self.__playlist_id:
            track = Track(App().tracks.get_id_by_uri(uri))
            album = Album(track.album.id)
            album.set_tracks([track])
            self.add_reveal_albums([album])
            self.add_value(album)

    def _on_playlist_track_removed(self, playlists, playlist_id, uri):
        """
            Remove track from album list
            @param playlists as Playlists
            @param playlist_id as int
            @param uri as str
        """
        if playlist_id == self.__playlist_id:
            track = Track(App().tracks.get_id_by_uri(uri))
            for album_row in self.children:
                if album_row.album.id == track.album.id:
                    for track_row in album_row.children:
                        if track_row.track.id == track.id:
                            track_row.destroy()
                            if len(self.children) == 1:
                                album_row.destroy()
                                break

    def _on_playlist_updated(self, playlists, playlist_id):
        """
            Reload view
            @param playlists as Playlists
            @param playlist_id as int
        """
        self.clear()
        self.populate()

    def _on_playlist_removed(self, playlists, playlist_id):
        """
            Go back
            @param playlists as Playlists
            @param playlist_id as int
        """
        App().window.container.go_back()

    def _on_playlist_renamed(self, playlists, playlist_id):
        """
            Update banner
            @param playlists as Playlists
            @param playlist_id as int
        """
        self.__banner.rename(App().playlists.get_name(playlist_id))

    def _on_row_activated(self, row, track):
        """
            Start playback
            @param row as AlbumRow
            @param track_id as int
        """
        if App().player.is_party:
            App().player.load(track)
        else:
            albums = []
            for album_row in self.children:
                albums.append(album_row.album)
            App().player.play_track_for_albums(track, albums)

    def _on_track_removed(self, row, track):
        """
            @param row as AlbumRow
            @param track as Track
        """
        row.album.remove_track(track)
        App().playlists.remove_tracks(self.__playlist_id,
                                      [track],
                                      True)
        if not row.children:
            row.destroy()

#######################
# PRIVATE             #
#######################
    def __populate(self):
        """
            Populate view
        """
        def on_load(albums):
            self.add_reveal_albums(albums)
            AlbumsListView.populate(self, albums)

        def load():
            track_ids = []
            if self.__playlist_id == Type.LOVED:
                for track_id in App().tracks.get_loved_track_ids(
                        [],
                        self.storage_type):
                    if track_id not in track_ids:
                        track_ids.append(track_id)
            else:
                for track_id in App().playlists.get_track_ids(
                        self.__playlist_id):
                    if track_id not in track_ids:
                        track_ids.append(track_id)
            return tracks_to_albums(
                [Track(track_id) for track_id in track_ids])

        App().task_helper.run(load, callback=(on_load,))

    def __populate_smart(self):
        """
            Populate view
        """
        def on_load(albums):
            self.banner.spinner.stop()
            self.add_reveal_albums(albums)
            AlbumsListView.populate(self, albums)

        def load():
            request = App().playlists.get_smart_sql(self.__playlist_id)
            # We need to inject skipped/storage_type
            storage_type = get_default_storage_type()
            split = request.split("ORDER BY")
            split[0] += " AND tracks.loved != %s" % Type.NONE
            split[0] += " AND tracks.storage_type&%s " % storage_type
            track_ids = App().db.execute("ORDER BY".join(split))
            return tracks_to_albums(
                [Track(track_id) for track_id in track_ids])

        self.banner.spinner.start()
        App().task_helper.run(load, callback=(on_load,))

    def __on_dnd_finished(self, dnd_helper):
        """
            Save playlist if needed
            @param dnd_helper as DNDHelper
        """
        if self.__playlist_id >= 0:
            uris = []
            for child in self.children:
                for track in child.album.tracks:
                    uris.append(track.uri)
            App().playlists.clear(self.__playlist_id)
            App().playlists.add_uris(self.__playlist_id, uris)
