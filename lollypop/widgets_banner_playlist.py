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

from gi.repository import Gtk, GLib

from random import shuffle

from lollypop.utils import get_human_duration, popup_widget
from lollypop.utils_album import tracks_to_albums
from lollypop.define import App, ArtSize, ViewType
from lollypop.objects_track import Track
from lollypop.widgets_banner import BannerWidget
from lollypop.helper_signals import SignalsHelper, signals_map


class PlaylistBannerWidget(BannerWidget, SignalsHelper):
    """
        Banner for playlist
    """

    @signals_map
    def __init__(self, playlist_id, view):
        """
            Init banner
            @param playlist_id as int
            @param view as AlbumsListView
        """
        BannerWidget.__init__(self, view.args["view_type"] | ViewType.OVERLAY)
        self.__duration_task = False
        self.__playlist_id = playlist_id
        self.__view = view
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/Lollypop/PlaylistBannerWidget.ui")
        self.__title_label = builder.get_object("title")
        self.__spinner = builder.get_object("spinner")
        self.__duration_label = builder.get_object("duration")
        self.__play_button = builder.get_object("play_button")
        self.__shuffle_button = builder.get_object("shuffle_button")
        self.__menu_button = builder.get_object("menu_button")
        widget = builder.get_object("widget")
        self._overlay.add_overlay(widget)
        self._overlay.set_overlay_pass_through(widget, True)
        self.__title_label.set_label(App().playlists.get_name(playlist_id))
        builder.connect_signals(self)
        self.connect("destroy", self.__on_destroy)
        self.__set_internal_size()
        return [
            (view, "initialized", "_on_view_updated"),
            (App().window.container.widget, "notify::folded",
             "_on_container_folded"),
            (App().player, "duration-changed", "_on_view_updated"),
            (App().playlists, "playlist-track-added", "_on_playlist_changed"),
            (App().playlists, "playlist-track-removed",
             "_on_playlist_changed"),
        ]

    def rename(self, name):
        """
            Rename playlist
            @param name as str
        """
        self.__title_label.set_label(name)

    @property
    def spinner(self):
        """
            Get spinner
            @return Gtk.Spinner
        """
        return self.__spinner

    @property
    def height(self):
        """
            Get wanted height
            @return int
        """
        return ArtSize.SMALL

#######################
# PROTECTED           #
#######################
    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        self.__set_internal_size()

    def _on_view_updated(self, *ignore):
        """
            Update duration
        """
        if self.__view.children:
            self.__duration_task = True
            App().task_helper.run(self.__calculate_duration)
        else:
            self.__duration_task = False
            self.__duration_label.set_text(get_human_duration(0))

    def _on_play_button_clicked(self, button):
        """
            Play playlist
            @param button as Gtk.Button
        """
        tracks = []
        for album_row in self.__view.children:
            for track in album_row.album.tracks:
                tracks.append(track)
        if tracks:
            albums = tracks_to_albums(tracks)
            App().player.play_track_for_albums(tracks[0], albums)

    def _on_shuffle_button_clicked(self, button):
        """
            Play playlist shuffled
            @param button as Gtk.Button
        """
        track_ids = []
        for album_row in self.__view.children:
            for track in album_row.album.tracks:
                track_ids.append(track.id)
        if track_ids:
            shuffle(track_ids)
            albums = tracks_to_albums(
                [Track(track_id) for track_id in track_ids])
            App().player.play_track_for_albums(albums[0].tracks[0], albums)

    def _on_menu_button_clicked(self, button):
        """
            Show playlist menu
            @param button as Gtk.Button
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_playlist import PlaylistMenu, PlaylistMenuExt
        menu = PlaylistMenu(self.__playlist_id,
                            self.view_type,
                            App().window.folded)
        menu_widget = MenuBuilder(menu)
        if self.__playlist_id >= 0:
            menu_widget = MenuBuilder(menu)
            menu_ext = PlaylistMenuExt(self.__playlist_id)
            menu_ext.show()
            menu_widget.add_widget(menu_ext)
        else:
            menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button, None, None, button)

    def _on_playlist_changed(self, playlists, playlist_id, uri):
        """
            Update duration
            @param playlists as Playlists
            @param playlist_id as int
            @param uri as str
        """
        if self.__playlist_id == playlist_id:
            self.__calculate_duration()

#######################
# PRIVATE             #
#######################
    def __calculate_duration(self):
        """
            Calculate playback duration
        """
        duration = 0
        for child in self.__view.children:
            if not self.__duration_task:
                return
            duration += child.album.duration
        GLib.idle_add(self.__duration_label.set_text,
                      get_human_duration(duration))

    def __set_internal_size(self):
        """
            Update font size
        """
        duration_context = self.__duration_label.get_style_context()
        title_context = self.__title_label.get_style_context()
        for c in title_context.list_classes():
            title_context.remove_class(c)
        for c in duration_context.list_classes():
            duration_context.remove_class(c)
        if App().window.folded:
            title_context.add_class("text-large")
        else:
            title_context.add_class("text-x-large")
            duration_context.add_class("text-large")

    def __on_get_duration(self, duration):
        """
            Update label
            @param duration as int
        """
        self.__duration_label.set_text(get_human_duration(duration))

    def __on_destroy(self, widget):
        """
            Remove ref cycle
            @param widget as Gtk.Widget
        """
        self.__view = None
