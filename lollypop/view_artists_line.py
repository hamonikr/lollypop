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

from gi.repository import Gtk, Pango, GLib

from gettext import gettext as _

from lollypop.utils import get_default_storage_type
from lollypop.define import App, MARGIN, ViewType
from lollypop.helper_horizontal_scrolling import HorizontalScrollingHelper
from lollypop.view_artists_rounded import RoundedArtistsView


class ArtistsLineView(RoundedArtistsView, HorizontalScrollingHelper):
    """
        Show artist in an horizontal flowbox
    """

    def __init__(self, storage_type, view_type):
        """
            Init artist view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        RoundedArtistsView.__init__(self, storage_type, view_type)
        self.__artist_ids = []
        self.set_row_spacing(5)
        self._label = Gtk.Label.new()
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._label.get_style_context().add_class("dim-label")
        self.__update_label(App().window.folded)
        self._label.set_hexpand(True)
        self._label.set_property("halign", Gtk.Align.START)
        self._backward_button = Gtk.Button.new_from_icon_name(
                                                    "go-previous-symbolic",
                                                    Gtk.IconSize.BUTTON)
        self._forward_button = Gtk.Button.new_from_icon_name(
                                                   "go-next-symbolic",
                                                   Gtk.IconSize.BUTTON)
        self._backward_button.get_style_context().add_class("menu-button")
        self._forward_button.get_style_context().add_class("menu-button")
        header = Gtk.Grid()
        header.set_column_spacing(10)
        header.add(self._label)
        header.add(self._backward_button)
        header.add(self._forward_button)
        header.set_margin_end(MARGIN)
        header.show_all()
        HorizontalScrollingHelper.__init__(self)
        self.add(header)
        self._label.set_property("halign", Gtk.Align.START)
        self.add_widget(self._box)

    def add_value(self, artist_id):
        """
            Insert item if not exists
            @param artist_id as int
        """
        if artist_id not in self.__artist_ids:
            self.__artist_ids.append(artist_id)
            RoundedArtistsView.add_value(self, artist_id)
            self.update_buttons()

    def clear(self):
        """
            Clear children
        """
        self.__artist_ids = []
        RoundedArtistsView.clear(self)

    @property
    def args(self):
        return None

#######################
# PROTECTED           #
#######################
    def _on_container_folded(self, leaflet, folded):
        """
            Handle libhandy folded status
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        RoundedArtistsView._on_container_folded(self, leaflet, folded)
        self.__update_label(folded)

    def _on_collection_updated(self, scanner, item, scan_update):
        pass

    def _on_populated(self, widget):
        """
            Update buttons
            @param widget as Gtk.Widget
        """
        self.update_buttons()
        RoundedArtistsView._on_populated(self, widget)

#######################
# PRIVATE             #
#######################
    def __update_label(self, folded):
        """
            Update label style based on current adaptive state
            @param folded as bool
        """
        style_context = self._label.get_style_context()
        if folded:
            style_context.remove_class("text-x-large")
        else:
            style_context.add_class("text-x-large")


class ArtistsRandomLineView(ArtistsLineView):
    """
        Line view showing 6 random artists
    """
    def __init__(self, storage_type, view_type):
        """
            Init artist view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        ArtistsLineView.__init__(self, storage_type, view_type)
        self._label.set_text(_("Why not listen to?"))

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            self._box.set_min_children_per_line(len(items))
            ArtistsLineView.populate(self, items)
            if items:
                self.show()

        def load():
            storage_type = get_default_storage_type()
            ids = App().artists.get_randoms(15, storage_type)
            return ids

        App().task_helper.run(load, callback=(on_load,))


class ArtistsSearchLineView(ArtistsLineView):
    """
        Line view for search
    """
    def __init__(self, storage_type):
        """
            Init artist view
            @param storage_type as StorageType
        """
        ArtistsLineView.__init__(self, storage_type,
                                 ViewType.SEARCH | ViewType.SCROLLED)
        self.__artist_ids = []
        self._label.set_text(_("Artists"))

    def add_value(self, item_id):
        """
            Insert item
            @param item_id as int
        """
        if item_id in self.__artist_ids:
            return
        self.__artist_ids.append(item_id)
        ArtistsLineView.populate(self, [item_id])
        self._box.set_min_children_per_line(len(self._box.get_children()))

    def clear(self):
        """
            Clear and hide the view
        """
        self.__artist_ids = []
        ArtistsLineView.clear(self)
        GLib.idle_add(self.hide)
