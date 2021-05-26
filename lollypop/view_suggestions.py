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

from gi.repository import Gtk, GLib, Pango

from gettext import gettext as _

from lollypop.view import View
from lollypop.utils import get_network_available
from lollypop.define import ViewType, StorageType, Size, App
from lollypop.view_albums_line import AlbumsPopularsLineView
from lollypop.view_albums_line import AlbumsRandomGenresLineView
from lollypop.view_artists_line import ArtistsRandomLineView
from lollypop.widgets_banner_today import TodayBannerWidget
from lollypop.helper_signals import signals_map


class SuggestionsView(View):
    """
        View showing suggestions to user
    """

    @signals_map
    def __init__(self, storage_type, view_type):
        """
            Init view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        View.__init__(self, storage_type, view_type | ViewType.OVERLAY)
        self.__grid = Gtk.Grid()
        self.__grid.get_style_context().add_class("padding")
        self.__grid.set_row_spacing(5)
        self.__grid.set_orientation(Gtk.Orientation.VERTICAL)
        self.__grid.show()
        if App().tracks.count() == 0:
            self.__welcome_screen()
            self.add_widget(self.__grid, None)
        else:
            album = TodayBannerWidget.get_today_album()
            if album is not None:
                self.__banner = TodayBannerWidget(album, self.view_type)
                self.__banner.show()
            else:
                self.__banner = None
            self.add_widget(self.__grid, self.__banner)
        return [
            (App().settings, "changed::suggestions-mask", "_on_mask_changed"),
        ]

    def populate(self):
        """
            Populate view
        """
        for cls in [AlbumsPopularsLineView,
                    ArtistsRandomLineView,
                    AlbumsRandomGenresLineView]:
            view = cls(self.storage_type, self.view_type)
            view.populate()
            self.__grid.add(view)
        self.__add_web_views()

    @property
    def filtered(self):
        """
            Get filtered widgets
            @return [Gtk.Widget]
        """
        children = []
        for child in reversed(self.__grid.get_children()):
            children += child.children
        return children

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
    def _on_mask_changed(self, settings, value):
        """
            Reload web views
            @param settings as Gio.Settings
            @param value as str
        """
        self.__add_web_views()

    def _on_map(self, widget):
        """
            Set initial view state
            @param widget as GtK.Widget
        """
        View._on_map(self, widget)
        if self.view_type & ViewType.SCROLLED:
            self.scrolled.grab_focus()

#######################
# PRIVATE             #
#######################
    def __add_web_views(self):
        """
            Add web views
        """
        from lollypop.view_albums_line import AlbumsStorageTypeLineView
        for child in self.__grid.get_children():
            if isinstance(child, AlbumsStorageTypeLineView):
                child.destroy()

        mask = App().settings.get_value("suggestions-mask").get_int32()
        if get_network_available("YOUTUBE"):
            for (title, storage_type) in [
                   (_("Suggestions from Spotify"),
                    StorageType.SPOTIFY_SIMILARS),
                   (_("New releases on Spotify"),
                    StorageType.SPOTIFY_NEW_RELEASES),
                   (_("Top albums on Deezer"),
                    StorageType.DEEZER_CHARTS)]:
                if not storage_type & mask:
                    continue
                view = AlbumsStorageTypeLineView(title,
                                                 self.storage_type,
                                                 self.view_type)
                view.populate(storage_type)
                self.__grid.add(view)

    def __welcome_screen(self):
        """
            Show welcome screen if view empty
        """
        label = Gtk.Label.new(_("Welcome to Lollypop"))
        label.get_style_context().add_class("text-xx-large")
        label.set_property("valign", Gtk.Align.END)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_vexpand(True)
        label.show()
        label.get_style_context().add_class("opacity-transition")
        image = Gtk.Image.new_from_icon_name("org.gnome.Lollypop",
                                             Gtk.IconSize.INVALID)
        image.set_pixel_size(Size.MINI)
        image.show()
        image.get_style_context().add_class("image-rotate-fast")
        image.get_style_context().add_class("opacity-transition")
        image.set_hexpand(True)
        image.set_vexpand(True)
        image.set_property("valign", Gtk.Align.START)
        self.__grid.add(label)
        self.__grid.add(image)
        GLib.idle_add(label.set_state_flags, Gtk.StateFlags.VISITED, True)
        GLib.idle_add(image.set_state_flags, Gtk.StateFlags.VISITED, True)
