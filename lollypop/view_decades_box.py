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

from lollypop.view_flowbox import FlowBoxView
from lollypop.widgets_albums_decade import AlbumsDecadeWidget
from lollypop.define import App, Type, ViewType, OrderBy
from lollypop.utils import get_icon_name
from lollypop.objects_album import Album


class DecadesBoxView(FlowBoxView):
    """
        Show decades in a FlowBox
    """

    def __init__(self, storage_type, view_type):
        """
            Init decade view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        from lollypop.widgets_banner_flowbox import FlowboxBannerWidget
        FlowBoxView.__init__(self, storage_type, view_type | ViewType.OVERLAY)
        self._empty_icon_name = get_icon_name(Type.YEARS)
        self.__banner = FlowboxBannerWidget([Type.YEARS], [], self.view_type)
        self.__banner.show()
        self.__banner.connect("play-all", self.__on_banner_play_all)
        self.add_widget(self._box, self.__banner)

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            FlowBoxView.populate(self, items)

        def load():
            (years, unknown) = App().tracks.get_years(self.storage_type)
            decades = []
            decade = []
            current_d = None
            for year in sorted(years):
                d = year // 10
                if current_d is not None and current_d != d:
                    current_d = d
                    decades.append(decade)
                    decade = []
                current_d = d
                decade.append(year)
            if decade:
                decades.append(decade)
            return decades

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
    def _get_child(self, value):
        """
            Get a child for view
            @param value as object
            @return row as SelectionListRow
        """
        if self.destroyed:
            return None
        widget = AlbumsDecadeWidget(value, self.view_type, self.font_height)
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
        from lollypop.menu_decade import DecadeMenu
        menu = DecadeMenu(child.data, self.view_type,
                          App().window.folded)
        return MenuBuilder(menu)

    def _on_child_activated(self, flowbox, child):
        """
            Navigate into child
            @param flowbox as Gtk.FlowBox
            @param child as Gtk.FlowBoxChild
        """
        App().window.container.show_view([Type.YEARS], child.data)

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
        items = []
        for year in child.data:
            items += App().tracks.get_albums_by_disc_for_year(
                year, self.storage_type, False)
            items += App().tracks.get_compilations_by_disc_for_year(
                year, self.storage_type, False)
        album_ids = [item[0] for item in items]
        albums = [Album(album_id, [], [], False) for album_id in album_ids]
        if albums:
            App().player.play_album_for_albums(albums[0], albums)

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
                                         False, OrderBy.YEAR_ASC)
        if not album_ids:
            return
        albums = [Album(album_id, [], [], False) for album_id in album_ids]
        if random:
            shuffle(albums)
            App().player.play_album_for_albums(albums[0], albums)
        else:
            App().player.play_album_for_albums(albums[0], albums)
