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

from gi.repository import Gtk, GLib, Gio

from gettext import gettext as _

from lollypop.define import App, StorageType
from lollypop.define import ViewType, MARGIN
from lollypop.search import Search
from lollypop.view import View
from lollypop.utils import sql_escape
from lollypop.objects_album import Album
from lollypop.objects_track import Track
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.view_artists_line import ArtistsSearchLineView
from lollypop.view_albums_line import AlbumsSearchLineView
from lollypop.view_tracks_search import SearchTracksView
from lollypop.widgets_banner_search import SearchBannerWidget


class SearchGrid(Gtk.Grid):
    """
        A grid for search
    """

    def __init__(self, storage_type):
        """
            Init grid
            @param storage_type as StorageType
        """
        Gtk.Grid.__init__(self)
        self.set_row_spacing(MARGIN)
        self.get_style_context().add_class("padding")
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_property("valign", Gtk.Align.START)
        self.__artists_line_view = ArtistsSearchLineView(storage_type)
        self.__albums_line_view = AlbumsSearchLineView(storage_type)
        self.__search_tracks_view = SearchTracksView()
        self.add(self.__albums_line_view)
        self.add(self.__artists_line_view)
        self.add(self.__search_tracks_view)

    @property
    def search_tracks_view(self):
        """
            Get SearchTracksView
            @return SearchTracksView
        """
        return self.__search_tracks_view

    @property
    def artists_line_view(self):
        """
            Get ArtistsSearchLineView
            @return ArtistsSearchLineView
        """
        return self.__artists_line_view

    @property
    def albums_line_view(self):
        """
            Get AlbumsSearchLineView
            @return AlbumsSearchLineView
        """
        return self.__albums_line_view


class SearchStack(Gtk.Stack):
    """
        A stack for search
    """

    def __init__(self, storage_type):
        """
            Init stack
            @param storage_type as StorageType
        """
        Gtk.Stack.__init__(self)
        self.get_style_context().add_class("padding")
        self.__current_child = None
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_transition_duration(100)
        for i in range(0, 2):
            grid = SearchGrid(storage_type)
            grid.show()
            self.add(grid)

    def new_current_child(self):
        """
            Set a new current child for search
            This is not visible child
        """
        if self.__current_child is not None:
            self.__current_child.search_tracks_view.clear()
            self.__current_child.artists_line_view.clear()
            self.__current_child.albums_line_view.clear()
        for child in self.get_children():
            if child != self.get_visible_child():
                self.__current_child = child
                break

    @property
    def current_child(self):
        """
            Get non visible child
            @return SearchGrid
        """
        if self.__current_child is None:
            self.new_current_child()
        return self.__current_child


class SearchView(View, Gtk.Bin, SignalsHelper):
    """
        View for searching albums/tracks
    """

    @signals_map
    def __init__(self, initial_search, view_type):
        """
            Init Popover
            @param initial_search as str
        """
        View.__init__(self,
                      StorageType.COLLECTION |
                      StorageType.SAVED |
                      StorageType.SEARCH |
                      StorageType.EPHEMERAL |
                      StorageType.SPOTIFY_NEW_RELEASES |
                      StorageType.SPOTIFY_SIMILARS,
                      ViewType.SEARCH |
                      ViewType.SCROLLED |
                      ViewType.OVERLAY)
        Gtk.Bin.__init__(self)
        self.__timeout_id = None
        self.__current_search = ""
        self.__search = Search()
        self.__search.set_web_search(
            App().settings.get_value("web-search").get_string())
        self.__cancellable = Gio.Cancellable()
        self._empty_message = _("Search for artists, albums and tracks")
        self._empty_icon_name = "edit-find-symbolic"
        self.__cancellable = Gio.Cancellable()
        self.__banner = SearchBannerWidget()
        self.__banner.show()
        self.__stack = SearchStack(self.storage_type)
        self.__stack.show()
        self.add_widget(self.__stack, self.__banner)
        self.__banner.entry.connect("changed", self._on_search_changed)
        self.show_placeholder(True,
                              _("Search for artists, albums and tracks"))
        self.set_search(initial_search)
        return [
                (self.__search, "match-artist", "_on_match_artist"),
                (self.__search, "match-album", "_on_match_album"),
                (self.__search, "match-track", "_on_match_track"),
                (self.__search, "finished", "_on_search_finished"),
                (App().settings, "changed::web-search",
                 "_on_web_search_changed")
        ]

    def populate(self):
        """
            Populate search
            in db based on text entry current text
        """
        self.cancel()
        self.__stack.new_current_child()
        if len(self.__current_search) > 1:
            self.__banner.spinner.start()
            current_search = self.__current_search.lower()
            self.__search.get(current_search, self.__cancellable)
        else:
            self.show_placeholder(True,
                                  _("Search for artists, albums and tracks"))
            self.__banner.spinner.stop()

    def set_search(self, search):
        """
            Set search text
            @param search as str
        """
        self.__banner.entry.set_text(search)
        self.__banner.entry.grab_focus()

    def grab_focus(self):
        """
            Make search entry grab focus
        """
        self.__banner.entry.grab_focus()

    def cancel(self):
        """
            Cancel current search and replace cancellable
        """
        self.__cancellable.cancel()
        self.__cancellable = Gio.Cancellable()

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        search = self.__banner.entry.get_text().strip()
        return {"initial_search": search,
                "view_type": self.view_type}

#######################
# PROTECTED           #
#######################
    def _on_map(self, widget):
        """
            Disable shortcuts and update buttons
            @param widget as Gtk.Widget
        """
        View._on_map(self, widget)
        App().enable_special_shortcuts(False)

    def _on_unmap(self, widget):
        """
            Cancel current loading and enable shortcuts
            @param widget as Gtk.Widget
        """
        View._on_unmap(self, widget)
        App().enable_special_shortcuts(True)
        self.cancel()
        self.__banner.spinner.stop()

    def _on_match_artist(self, search, artist_id, storage_type):
        """
            Add a new artist to view
            @param search as *Search
            @param artist_id as int
            @param storage_type as StorageType
        """
        if storage_type & StorageType.SEARCH:
            self.__stack.current_child.artists_line_view.show()
            self.__stack.current_child.artists_line_view.add_value(artist_id)
            self.show_placeholder(False)

    def _on_match_album(self, search, album_id, storage_type):
        """
            Add a new album to view
            @param search as *Search
            @param artist_id as int
            @param storage_type as StorageType
        """
        if storage_type & StorageType.SEARCH:
            artist_match = False
            album = Album(album_id)
            if album.artists:
                artist = sql_escape(album.artists[0])
                search = sql_escape(self.__current_search)
                artist_match = artist.find(search) != -1
            if artist_match:
                self._on_match_artist(search,
                                      album.artist_ids[0],
                                      storage_type)
            else:
                self.__stack.current_child.albums_line_view.show()
                self.__stack.current_child.albums_line_view.add_value(album)
                self.show_placeholder(False)

    def _on_match_track(self, search, track_id, storage_type):
        """
            Add a new track to view
            @param search as *Search
            @param track_id as int
            @param storage_type as StorageType
        """
        if storage_type & StorageType.SEARCH:
            track = Track(track_id)
            self.__stack.current_child.search_tracks_view.show()
            self.__stack.current_child.search_tracks_view.append_row(track)
            self.show_placeholder(False)

    def _on_search_finished(self, search_handler, last):
        """
            Stop spinner and show placeholder if not result
            @param search_handler as LocalSearch/WebSearch
            @param last as bool
        """
        tracks_len = len(
            self.__stack.current_child.search_tracks_view.children)
        albums_len = len(
            self.__stack.current_child.albums_line_view.children)
        artists_len = len(
            self.__stack.current_child.artists_line_view.children)
        empty = albums_len == 0 and tracks_len == 0 and artists_len == 0
        self.__stack.set_visible_child(self.__stack.current_child)
        if last:
            self.__banner.spinner.stop()
            if empty:
                self.show_placeholder(True, _("No results for this search"))

    def _on_web_search_changed(self, settings, value):
        """
            Show/hide labels
            @param settings as Gio.Settings
            @param value as GLib.Variant
        """
        self.__search.set_web_search(
            App().settings.get_value("web-search").get_string())

#######################
# PRIVATE             #
#######################
    def __set_no_result_placeholder(self):
        """
            Set placeholder for no result
        """
        self.__placeholder.set_text()

    def _on_search_changed(self, widget):
        """
            Timeout filtering
            @param widget as Gtk.TextEntry
        """
        if self.__timeout_id is not None:
            GLib.source_remove(self.__timeout_id)
        self.__timeout_id = GLib.timeout_add(
                500,
                self.__on_search_changed_timeout)

    def __on_search_changed_timeout(self):
        """
            Populate widget
        """
        self.__timeout_id = None
        new_search = self.__banner.entry.get_text().strip()
        if self.__current_search != new_search:
            self.__current_search = new_search
            self.populate()

    def __on_button_clicked(self, button):
        """
            Reload search for current button
            @param button as Gtk.RadioButton
        """
        if button.get_active():
            self.__current_search = self.__banner.entry.get_text().strip()
            if self.__current_search:
                self.populate()
