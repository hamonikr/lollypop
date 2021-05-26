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

from gi.repository import Gio, GObject, Gtk

from gettext import gettext as _

from lollypop.logger import Logger
from lollypop.utils import emit_signal
from lollypop.widgets_artwork import ArtworkSearchWidget, ArtworkSearchChild
from lollypop.define import App, Type
from lollypop.helper_signals import SignalsHelper, signals_map


class AlbumArtworkSearchWidget(ArtworkSearchWidget, SignalsHelper):
    """
        Search for album artwork
    """

    __gsignals__ = {
        "hidden": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals_map
    def __init__(self, album, view_type, in_menu=False):
        """
            Init search
            @param album as Album
            @param view_type as ViewType
        """
        ArtworkSearchWidget.__init__(self, view_type)
        self.__album = album
        return [
                (App().album_art, "uri-artwork-found", "_on_uri_artwork_found")
        ]

    @property
    def art(self):
        """
            Get related artwork
            @return ArtworkManager
        """
        return App().album_art

    def populate(self):
        """
            Populate view
        """
        try:
            ArtworkSearchWidget.populate(self)
            # First load local files
            uris = App().album_art.get_uris(self.__album)
            # Direct load, not using loopback because not many items
            for uri in uris:
                child = ArtworkSearchChild(_("Local"), self.view_type)
                child.show()
                f = Gio.File.new_for_uri(uri)
                (status, content, tag) = f.load_contents()
                if status:
                    status = child.populate(content, self.art, self._art_size)
                if status:
                    self._flowbox.add(child)
        except Exception as e:
            Logger.error("AlbumArtworkSearchWidget::populate(): %s", e)

#######################
# PROTECTED           #
#######################
    def _save_from_filename(self, filename):
        """
            Save filename as album artwork
            @param button as Gtk.button
        """
        try:
            f = Gio.File.new_for_path(filename)
            (status, data, tag) = f.load_contents()
            if status:
                App().task_helper.run(App().album_art.add,
                                      self.__album, data)
        except Exception as e:
            Logger.error(
                "AlbumArtworkSearchWidget::_save_from_filename(): %s" % e)

    def _get_current_search(self):
        """
            Return current searches
            @return str
        """
        search = ArtworkSearchWidget._get_current_search(self)
        if search.strip() == "":
            is_compilation = self.__album.artist_ids and\
                self.__album.artist_ids[0] == Type.COMPILATIONS
            if is_compilation:
                search = self.__album.name
            else:
                search = "%s+%s" % (self.__album.artists[0], self.__album.name)
        return search

#######################
# PROTECTED           #
#######################
    def _search_for_artwork(self):
        """
            Search artwork on the web
        """
        ArtworkSearchWidget._search_for_artwork(self)
        self._loaders = 3
        search = ArtworkSearchWidget._get_current_search(self)
        App().task_helper.run(App().album_art.search_artwork_from_google,
                              search,
                              self._cancellable)
        App().task_helper.run(App().album_art.search_artwork_from_startpage,
                              search,
                              self._cancellable)
        if search.strip() == "":
            is_compilation = self.__album.artist_ids and\
                self.__album.artist_ids[0] == Type.COMPILATIONS
            if is_compilation:
                artist = "Compilation"
            else:
                artist = self.__album.artists[0]
            App().task_helper.run(
                    App().album_art.search,
                    artist,
                    self.__album.name,
                    self._cancellable)
        else:
            App().task_helper.run(
                    App().album_art.search,
                    "",
                    search,
                    self._cancellable)

    def _on_activate(self, flowbox, child):
        """
            Save artwork
            @param flowbox as Gtk.FlowBox
            @param child as ArtworkSearchChild
        """
        try:
            if isinstance(child, ArtworkSearchChild):
                App().task_helper.run(App().album_art.add,
                                      self.__album, child.bytes)
            else:
                App().task_helper.run(App().album_art.add, self.__album, None)
            emit_signal(self, "hidden", True)
        except Exception as e:
            Logger.error("AlbumArtworkSearchWidget::_on_activate(): %s", e)

    def __on_album_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if surface is None:
            self.__artwork.set_from_icon_name("folder-music-symbolic",
                                              Gtk.IconSize.BUTTON)
        else:
            self.__artwork.set_from_surface(surface)
