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

from random import shuffle
from gettext import gettext as _
from time import time

from lollypop.view_flowbox import FlowBoxView
from lollypop.define import App, Type, ViewType, OrderBy, ScanUpdate
from lollypop.widgets_artist_rounded import RoundedArtistWidget
from lollypop.objects_album import Album
from lollypop.utils import get_icon_name
from lollypop.helper_signals import SignalsHelper, signals_map


class RoundedArtistsView(FlowBoxView, SignalsHelper):
    """
        Show artists in a FlowBox
    """

    @signals_map
    def __init__(self, storage_type, view_type):
        """
            Init artist view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        FlowBoxView.__init__(self, storage_type, view_type)
        self.__time = time() + 10
        self.connect("destroy", self.__on_destroy)
        self._empty_icon_name = get_icon_name(Type.ARTISTS)
        return [
            (App().artist_art, "artist-artwork-changed",
             "_on_artist_artwork_changed"),
            (App().scanner, "updated", "_on_collection_updated")
        ]

    def populate(self, artist_ids=[]):
        """
            Populate view with artist id
            Show all artists if empty
            @param artist_ids as [int]
        """
        def on_load(artist_ids):
            FlowBoxView.populate(self, artist_ids)

        def load():
            return App().artists.get([], self.storage_type)

        if artist_ids:
            FlowBoxView.populate(self, artist_ids)
        else:
            App().task_helper.run(load, callback=(on_load,))

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"storage_type": self.storage_type,
                "view_type": self.view_type}

#######################
# PROTECTED           #
#######################
    def _get_child(self, item):
        """
            Get a child for view
            @param item as (int, str, str)
            @return row as SelectionListRow
        """
        if self.destroyed:
            return None
        widget = RoundedArtistWidget(item, self.view_type, self.font_height)
        self._box.insert(widget, -1)
        widget.show()
        return widget

    def _get_menu_widget(self, child):
        """
            Get menu widget
            @param child as AlbumSimpleWidget
            @return Gtk.Widget
        """
        from lollypop.widgets_menu import MenuBuilder
        from lollypop.menu_artist import ArtistMenu
        from lollypop.menu_similars import SimilarsMenu
        menu = ArtistMenu(child.data, self.storage_type, self.view_type,
                          App().window.folded)
        menu_widget = MenuBuilder(menu, False)
        menu_widget.show()
        menu_ext = SimilarsMenu(child.data)
        menu_ext.show()
        menu_widget.add_widget(menu_ext)
        return menu_widget

    def _on_child_activated(self, flowbox, child):
        """
            Navigate into child
            @param flowbox as Gtk.FlowBox
            @param child as Gtk.FlowBoxChild
        """
        App().window.container.show_view([Type.ARTISTS], [child.data],
                                         self.storage_type)

    def _on_tertiary_press_gesture(self, x, y, event):
        """
            Play artist
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        child = self._box.get_child_at_pos(x, y)
        if child is None or child.artwork is None:
            return
        album_ids = App().albums.get_ids([], [child.data],
                                         self.storage_type, False)
        albums = [Album(album_id) for album_id in album_ids]
        if albums:
            App().player.play_album_for_albums(albums[0], albums)

    def _on_artist_artwork_changed(self, art, prefix):
        """
            Update artwork if needed
            @param art as Art
            @param prefix as str
        """
        for child in self._box.get_children():
            if child.name == prefix:
                child.set_artwork()

    def _on_collection_updated(self, scanner, item, scan_update):
        """
            Add/remove artist to/from list
            @param scanner as CollectionScanner
            @param item as CollectionItem
            @param scan_update as ScanUpdate
        """
        # On first update, ignore notifications for 10 seconds
        # Next, ignore notifications for 120 seconds
        if scan_update == ScanUpdate.ADDED and time() > self.__time:
            self.__time = time() + 120
            App().window.container.show_notification(
                    _("New artists available"),
                    [_("Refresh")],
                    [App().window.container.reload_view])
        elif scan_update == ScanUpdate.REMOVED:
            for child in self._box.get_children():
                if child.data in item.new_album_artist_ids:
                    child.destroy()
                    break

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, widget):
        """
            Stop loading
            @param widget as Gtk.Widget
        """
        RoundedArtistsView.stop(self)


class RoundedArtistsViewWithBanner(RoundedArtistsView):
    """
        Show rounded artist view with a banner
    """

    def __init__(self, storage_type, view_type):
        """
            Init artist view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        from lollypop.widgets_banner_flowbox import FlowboxBannerWidget
        RoundedArtistsView.__init__(self, storage_type,
                                    view_type | ViewType.OVERLAY)
        self.__banner = FlowboxBannerWidget([Type.ARTISTS], [], self.view_type)
        self.__banner.show()
        self.__banner.connect("play-all", self.__on_banner_play_all)
        self.add_widget(self._box, self.__banner)

#######################
# PROTECTED           #
#######################
    def _on_map(self, widget):
        """
            Set initial view state
            @param widget as GtK.Widget
        """
        RoundedArtistsView._on_map(self, widget)
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
        album_ids = App().albums.get_ids([], [], self.storage_type,
                                         False, OrderBy.ARTIST_YEAR)
        if not album_ids:
            return
        albums = [Album(album_id) for album_id in album_ids]
        if random:
            shuffle(albums)
            App().player.play_album_for_albums(albums[0], albums)
        else:
            App().player.play_album_for_albums(albums[0], albums)
