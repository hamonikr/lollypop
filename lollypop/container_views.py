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

from gi.repository import Gtk

from lollypop.define import App, Type, ViewType, StorageType
from lollypop.utils import emit_signal, get_default_storage_type


class ViewsContainer:
    """
        Views management for main view
    """

    def __init__(self):
        """
            Init container
        """
        pass

    def show_widget(self, widget):
        """
            Show widget
            @param widget as Gtk.Widget
        """
        from lollypop.view import View
        view = View(StorageType.ALL, ViewType.DEFAULT)
        view.show()
        view.add(widget)
        widget.set_vexpand(True)
        self._stack.add(view)
        self._stack.set_visible_child(view)

    def show_menu(self, widget):
        """
            Show menu widget
            @param widget as Gtk.Widget
        """
        def on_hidden(widget, hide, view):
            if hide:
                self._stack.set_transition_type(
                    Gtk.StackTransitionType.SLIDE_UP)
                self.go_back()
                self._stack.set_transition_type(
                    Gtk.StackTransitionType.CROSSFADE)
                App().enable_special_shortcuts(True)
                if App().lookup_action("reload").get_state():
                    self.reload_view()
            if self.can_go_back:
                emit_signal(self, "can-go-back-changed", True)

        from lollypop.view_menu import MenuView
        view = MenuView(widget)
        view.show()
        widget.connect("hidden", on_hidden, view)
        self._stack.add(view)
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_DOWN)
        self._stack.set_visible_child(view)
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        emit_signal(self, "can-go-back-changed", False)
        App().enable_special_shortcuts(False)
        self.dismiss_notification()

    def show_view(self, item_ids, data=None, storage_type=None):
        """
            Show view for item id
            @param item_ids as [int]
            @param data as object
            @param storage_type as StorageType
        """
        self.dismiss_notification()
        self.sub_widget.set_visible_child(self.grid_view)
        view = None
        if storage_type is None:
            storage_type = get_default_storage_type()
        hide_selection_list = True
        if item_ids:
            if item_ids[0] in [Type.POPULARS,
                               Type.LOVED,
                               Type.RECENTS,
                               Type.LITTLE,
                               Type.RANDOMS]:
                view = self._get_view_albums(item_ids, [], storage_type)
            elif item_ids[0] == Type.WEB:
                view = self._get_view_albums(item_ids, [], StorageType.SAVED)
            elif item_ids[0] == Type.SUGGESTIONS:
                view = self._get_view_suggestions(storage_type)
            elif item_ids[0] == Type.SEARCH:
                view = self.get_view_search(data)
            elif item_ids[0] == Type.INFO:
                view = self._get_view_info()
            elif item_ids[0] == Type.DEVICE_ALBUMS:
                view = self._get_view_device_albums(data)
            elif item_ids[0] == Type.DEVICE_PLAYLISTS:
                view = self._get_view_device_playlists(data)
            elif item_ids[0] == Type.LYRICS:
                view = self._get_view_lyrics()
            elif item_ids[0] == Type.GENRES:
                if data is None:
                    view = self._get_view_genres(storage_type)
                else:
                    view = self._get_view_albums([data], [], storage_type)
            elif item_ids[0] == Type.ALBUM:
                hide_selection_list = False
                view = self._get_view_album(data, storage_type)
            elif item_ids[0] == Type.YEARS:
                if data is None:
                    view = self._get_view_albums_decades(storage_type)
                else:
                    view = self._get_view_albums_years(data, storage_type)
            elif item_ids[0] == Type.PLAYLISTS:
                view = self._get_view_playlists(data)
            elif item_ids[0] == Type.EQUALIZER:
                from lollypop.view_equalizer import EqualizerView
                view = EqualizerView()
            elif item_ids[0] == Type.ALL:
                view = self._get_view_albums(item_ids, [], storage_type)
            elif item_ids[0] == Type.COMPILATIONS:
                view = self._get_view_albums(item_ids, [], storage_type)
            elif item_ids[0] == Type.ARTISTS:
                view = self._get_view_artists([], data, storage_type)
        self._sidebar.select_ids(item_ids, False)
        if hide_selection_list:
            self._hide_right_list()
            self.left_list.hide()
        if view is not None:
            self.set_focused_view(view)
            view.show()
            self._stack.add(view)
            self._stack.set_visible_child(view)
        emit_signal(self, "can-go-back-changed", self.can_go_back)

    def get_view_current(self):
        """
            Get view for current playlist
            @return View
        """
        from lollypop.view_current_albums import CurrentAlbumsView
        # Search view in children
        for (_view, _class, args, sidebar_id,
             selection_ids, position) in self._stack.history.items:
            if _class == CurrentAlbumsView and _view is not None:
                self._stack.history.remove(_view)
                return _view
        view = CurrentAlbumsView(ViewType.DND)
        view.populate()
        view.show()
        return view

    def get_view_search(self, search=""):
        """
            Get view for search
            @param search as str
            @return SearchView
        """
        from lollypop.view_search import SearchView
        view = None
        # Search view in current view
        if self.view is not None and isinstance(self.view, SearchView):
            view = self.view
        # Search view in children
        else:
            for (_view, _class, args, sidebar_id,
                 selection_ids, position) in self._stack.history.items:
                if _class == SearchView and _view is not None:
                    self._stack.history.remove(_view)
                    view = _view
                    break
        if view is None:
            view_type = ViewType.SCROLLED
            view = SearchView("", view_type)
            view.show()
        if search:
            view.set_search(search)
        else:
            view.grab_focus()
        return view

##############
# PROTECTED  #
##############
    def _get_view_playlists(self, playlist_id=None):
        """
            Get playlists view for playlists
            @param playlist_id as int
            @return View
        """
        view_type = ViewType.PLAYLISTS | ViewType.SCROLLED
        if playlist_id is None:
            from lollypop.view_playlists_manager import PlaylistsManagerView
            view = PlaylistsManagerView(view_type)
        else:
            from lollypop.view_playlists import PlaylistsView
            view_type |= ViewType.DND
            view = PlaylistsView(playlist_id, view_type)
        view.populate()
        return view

    def _get_view_device_playlists(self, index):
        """
            Show playlists for device at index
            @param index as int
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_playlists_manager import PlaylistsManagerDeviceView
        view = PlaylistsManagerDeviceView(index, view_type)
        view.populate()
        return view

    def _get_view_lyrics(self):
        """
            Show lyrics for track
            @pram track as Track
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_lyrics import LyricsView
        view = LyricsView(view_type)
        view.populate(App().player.current_track)
        view.show()
        return view

    def _get_view_artists_rounded(self, storage_type):
        """
            Get rounded artists view
            @param storage_type as StorageType
            @return RoundedArtistsViewWithBanner
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_artists_rounded import RoundedArtistsViewWithBanner
        view = RoundedArtistsViewWithBanner(storage_type, view_type)
        self._stack.add(view)
        view.populate()
        view.show()
        return view

    def _get_view_artists(self, genre_ids, artist_ids, storage_type):
        """
            Get artists view for genres/artists
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @return ArtistViewBox/ArtistViewList
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_artist_list import ArtistViewList
        view = ArtistViewList(genre_ids, artist_ids,
                              storage_type, view_type)
        view.populate()
        view.show()
        return view

    def _get_view_suggestions(self, storage_type):
        """
            Get home view
            @param storage_type as StorageType
            @return SuggestionsView
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_suggestions import SuggestionsView
        view = SuggestionsView(storage_type, view_type)
        view.populate()
        view.show()
        return view

    def _get_view_albums_decades(self, storage_type):
        """
            Get album view for decades
            @param storage_type as StorageType
            @return DecadesBoxView
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_decades_box import DecadesBoxView
        view = DecadesBoxView(storage_type, view_type)
        view.populate()
        view.show()
        return view

    def _get_view_album(self, album, storage_type):
        """
            Show album
            @param album as Album
            @param storage_type as StorageType
            @return AlbumView
        """
        view_type = ViewType.SCROLLED |\
            ViewType.OVERLAY | ViewType.ALBUM
        from lollypop.view_album import AlbumView
        view = AlbumView(album, storage_type, view_type)
        view.populate()
        return view

    def _get_view_genres(self, storage_type):
        """
            Get view for genres
            @param storage_type as StorageType
            @return GenresBoxView
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_genres_box import GenresBoxView
        view = GenresBoxView(storage_type, view_type)
        view.populate()
        view.show()
        return view

    def _get_view_albums_years(self, years, storage_type):
        """
            Get album view for years
            @param years as [int]
            @param storage_type as StorageType
            @return AlbumsForYearsBoxView
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_albums_box import AlbumsForYearsBoxView
        view = AlbumsForYearsBoxView([Type.YEARS], years,
                                     storage_type, view_type)
        view.populate()
        return view

    def _get_view_albums(self, genre_ids, artist_ids, storage_type):
        """
            Get albums view for genres/artists
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @return AlbumsForGenresBoxView
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_albums_box import AlbumsForGenresBoxView
        view = AlbumsForGenresBoxView(genre_ids, artist_ids,
                                      storage_type, view_type)
        view.populate()
        return view

    def _get_view_device_albums(self, index):
        """
            Show albums for device at index
            @param index as int
            @return AlbumsDeviceBoxView
        """
        view_type = ViewType.SCROLLED
        from lollypop.view_albums_box import AlbumsDeviceBoxView
        view = AlbumsDeviceBoxView(index, view_type)
        view.populate()
        return view

    def _get_view_info(self):
        """
            Get view for information
            @return InformationView
        """
        from lollypop.view_information_stack import InformationViewStack
        view = InformationViewStack()
        view.populate()
        return view
