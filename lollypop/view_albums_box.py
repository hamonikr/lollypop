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
from time import time
from random import shuffle

from lollypop.view_flowbox import FlowBoxView
from lollypop.widgets_album_simple import AlbumSimpleWidget
from lollypop.define import App, Type, ViewType, ScanUpdate, StorageType
from lollypop.objects_album import Album
from lollypop.utils import get_icon_name, get_network_available, popup_widget
from lollypop.utils import get_title_for_genres_artists
from lollypop.utils import remove_static
from lollypop.utils_file import get_youtube_dl
from lollypop.utils_album import get_album_ids_for
from lollypop.helper_signals import SignalsHelper, signals_map


class AlbumsBoxView(FlowBoxView, SignalsHelper):
    """
        Show albums in a box
    """

    @signals_map
    def __init__(self, genre_ids, artist_ids, storage_type, view_type):
        """
            Init album view
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        FlowBoxView.__init__(self, storage_type, view_type)
        self.__time = time() + 10
        self._genre_ids = genre_ids
        self._artist_ids = artist_ids
        self._storage_type = storage_type
        self.__populate_wanted = True
        if genre_ids and genre_ids[0] < 0:
            if genre_ids[0] == Type.WEB:
                (youtube_dl, env) = get_youtube_dl()
                if youtube_dl is None:
                    self._empty_message = _("Missing youtube-dl command")
                    self.show_placeholder(True)
                    self.__populate_wanted = False
                elif not get_network_available("YOUTUBE"):
                    self._empty_message =\
                        _("Network unavailable or disabled in settings")
                    self.show_placeholder(True)
                    self.__populate_wanted = False
            self._empty_icon_name = get_icon_name(genre_ids[0])
        return [
            (App().scanner, "updated", "_on_collection_updated"),
            (App().player, "loading-changed", "_on_loading_changed"),
            (App().player, "current-changed", "_on_current_changed"),
            (App().album_art, "album-artwork-changed", "_on_artwork_changed")
        ]

    def populate(self, albums=[]):
        """
            Populate view for album ids
            Show artist_ids/genre_ids if empty
            @param albums as [Album]
        """
        def on_load(albums):
            if albums:
                FlowBoxView.populate(self, albums)
                self.show_placeholder(False)
            else:
                self.show_placeholder(True)

        def load():
            # No skipped albums for this views
            if self._genre_ids and self._genre_ids[0] in [Type.POPULARS,
                                                          Type.LITTLE,
                                                          Type.RANDOMS,
                                                          Type.RECENTS]:
                skipped = False
            else:
                skipped = True
            album_ids = get_album_ids_for(self._genre_ids, self._artist_ids,
                                          self.storage_type, skipped)
            albums = []
            for album_id in album_ids:
                album = Album(album_id, self._genre_ids,
                              self._artist_ids, True)
                album.set_storage_type(self.storage_type)
                albums.append(album)
            return albums

        if albums:
            FlowBoxView.populate(self, albums)
        elif self.__populate_wanted:
            App().task_helper.run(load, callback=(on_load,))

    def add_value(self, album):
        """
            Add a new album
            @param album as Album
        """
        self.show_placeholder(False)
        FlowBoxView.add_value_unsorted(self, album)

    def clear(self):
        """
            Clear view
        """
        for child in self._box.get_children():
            child.destroy()

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"genre_ids": self._genre_ids,
                "artist_ids": self._artist_ids,
                "storage_type": self._storage_type,
                "view_type": self.view_type & ~ViewType.SMALL}

#######################
# PROTECTED           #
#######################
    def _get_child(self, value, position=-1):
        """
            Get a child for view
            @param value as object
            @param position as int
            @return row as SelectionListRow
        """
        if self.destroyed:
            return None
        widget = AlbumSimpleWidget(value,  self._genre_ids, self._artist_ids,
                                   self.view_type, self.font_height)
        self._box.insert(widget, position)
        widget.show()
        return widget

    def _get_menu_widget(self, child):
        """
            Get menu widget
            @param child as AlbumSimpleWidget
            @return Gtk.Widget
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_objects import AlbumMenu
        menu = AlbumMenu(child.data, self.storage_type, self.view_type)
        return MenuBuilder(menu)

    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        for child in self._box.get_children():
            child.set_selection()

    def _on_collection_updated(self, scanner, item, scan_update):
        """
            Handles changes in collection
            @param scanner as CollectionScanner
            @param item as CollectionItem
            @param scan_update as ScanUpdate
        """
        # On first update, ignore notifications for 10 seconds
        # Next, ignore notifications for 120 seconds
        if scan_update == ScanUpdate.ADDED and time() > self.__time:
            wanted = True
            for genre_id in item.genre_ids:
                genre_ids = remove_static(self._genre_ids)
                if genre_ids and genre_id not in genre_ids:
                    wanted = False
            for artist_id in item.artist_ids:
                artist_ids = remove_static(self._artist_ids)
                if artist_ids and artist_id not in artist_ids:
                    wanted = False
            if wanted:
                self.__time = time() + 120
                App().window.container.show_notification(
                    _("New albums available"),
                    [_("Refresh")],
                    [App().window.container.reload_view])
        elif scan_update == ScanUpdate.REMOVED:
            for child in self.children:
                if child.data.id == item.album_id:
                    child.destroy()
                    break

    def _on_artwork_changed(self, artwork, album_id):
        """
            Update children artwork if matching album id
            @param artwork as Artwork
            @param album_id as int
        """
        for child in self._box.get_children():
            if child.data.id == album_id:
                child.set_artwork()

    def _on_loading_changed(self, player, status, track):
        """
            Update row loading status
            @param player as Player
            @param status as bool
            @param track as Track
        """
        for child in self.children:
            if child.artwork is None:
                continue
            if child.data.id == track.album.id:
                context = child.artwork.get_style_context()
                if status:
                    context.add_class("load-animation")
                else:
                    context.remove_class("load-animation")
                break

    def _on_child_activated(self, flowbox, child):
        """
            Navigate into child
            @param flowbox as Gtk.FlowBox
            @param child as Gtk.FlowBoxChild
        """
        if child.artwork is None:
            return

        def show_album(status, child):
            child.artwork.get_style_context().remove_class("load-animation")
            App().window.container.show_view([Type.ALBUM], child.data,
                                             self.storage_type)

        if child.data.storage_type & StorageType.COLLECTION:
            App().window.container.show_view([Type.ALBUM], child.data)
        else:
            child.artwork.get_style_context().add_class("load-animation")
            cancellable = Gio.Cancellable.new()
            App().task_helper.run(child.data.load_tracks,
                                  cancellable,
                                  callback=(show_album, child))

    def _on_tertiary_press_gesture(self, x, y, event):
        """
            Play albums
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        child = self._box.get_child_at_pos(x, y)
        if child is None or child.artwork is None:
            return

        def play_album(status, child):
            child.artwork.get_style_context().remove_class("load-animation")
            App().player.play_album(child.data.clone(False))

        if child.data.storage_type & StorageType.COLLECTION:
            App().player.play_album(child.data.clone(False))
        else:
            child.artwork.get_style_context().add_class("load-animation")
            cancellable = Gio.Cancellable.new()
            App().task_helper.run(child.data.load_tracks,
                                  cancellable,
                                  callback=(play_album, child))


class AlbumsForGenresBoxView(AlbumsBoxView):
    """
        Show albums in a box for genres (static or not)
    """

    def __init__(self, genre_ids, artist_ids, storage_type, view_type):
        """
            Init album view
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        AlbumsBoxView.__init__(self, genre_ids, artist_ids, storage_type,
                               view_type | ViewType.OVERLAY)
        from lollypop.widgets_banner_flowbox import FlowboxBannerWidget
        self.__banner = FlowboxBannerWidget(genre_ids, artist_ids,
                                            view_type, True)
        self.__banner.show()
        self.__banner.connect("play-all", self.__on_banner_play_all)
        self.__banner.connect("show-menu", self.__on_banner_show_menu)
        self.add_widget(self._box, self.__banner)

#######################
# PROTECTED           #
#######################
    def _on_map(self, widget):
        """
            Set initial view state
            @param widget as GtK.Widget
        """
        AlbumsBoxView._on_map(self, widget)
        if self.view_type & ViewType.SCROLLED:
            self.scrolled.grab_focus()

#######################
# PRIVATE             #
#######################
    def __on_banner_play_all(self, banner, random):
        """
            Play all albums
            @param banner as AlbumsBannerWidget
            @param random as bool
        """
        albums = [c.data.clone(False) for c in self._box.get_children()]
        if not albums:
            return
        if random:
            shuffle(albums)
            App().player.play_album_for_albums(albums[0], albums)
        else:
            App().player.play_album_for_albums(albums[0], albums)

    def __on_banner_show_menu(self, banner, button):
        """
            Show contextual menu
            @param banner as AlbumsBannerWidget
            @param button as Gtk.Button
        """
        from lollypop.menu_objects import AlbumsMenu
        from lollypop.widgets_menu import MenuBuilder
        albums = []
        for child in self._box.get_children():
            if child.data.storage_type & StorageType.COLLECTION:
                albums.append(child.data)
        title = get_title_for_genres_artists(self._genre_ids, self._artist_ids)
        menu = AlbumsMenu(title, albums, self.view_type)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        popup_widget(menu_widget, button, None, None, button)


class AlbumsForYearsBoxView(AlbumsForGenresBoxView):
    """
        Years album box
    """

    def __init__(self, genre_ids, artist_ids, storage_type, view_type):
        """
            Init view
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        AlbumsForGenresBoxView.__init__(self, genre_ids, artist_ids,
                                        storage_type, view_type)

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            FlowBoxView.populate(self, items)

        def get_album(album_id, disc_number, disc_name, album_year, year):
            album = Album(album_id, [Type.YEARS], [])
            if year != album_year:
                album.set_disc_number(disc_number)
            return album

        def load():
            albums = []
            for year in self._artist_ids:
                items = App().tracks.get_compilations_by_disc_for_year(
                    year, self.storage_type, True)
                items += App().tracks.get_albums_by_disc_for_year(
                    year, self.storage_type, True)
                albums += [get_album(item[0], item[1], item[2], item[3], year)
                           for item in items]
            return albums

        App().task_helper.run(load, callback=(on_load,))


class AlbumsDeviceBoxView(AlbumsBoxView):
    """
        Device album box
    """

    def __init__(self, index, view_type):
        """
            Init view
            @param index as int
            @param view_type as ViewType
            @param index as int
        """
        AlbumsBoxView.__init__(self, [], [], StorageType.COLLECTION, view_type)
        self.add_widget(self._box)
        self.__index = index

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            FlowBoxView.populate(self, items)

        def load():
            album_ids = App().albums.get_synced_ids(0)
            album_ids += App().albums.get_synced_ids(self.__index)
            return [Album(album_id) for album_id in album_ids]

        App().task_helper.run(load, callback=(on_load,))

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"index": self.__index,
                "view_type": self.view_type & ~ViewType.SMALL}

#######################
# PROTECTED           #
#######################
    def _on_map(self, widget):
        """
            Set initial view state
            @param widget as GtK.Widget
        """
        AlbumsBoxView._on_map(self, widget)
        if self.view_type & ViewType.SCROLLED:
            self.scrolled.grab_focus()
