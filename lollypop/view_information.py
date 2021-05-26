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

from gi.repository import Gtk, GLib, Gio, Pango

from gettext import gettext as _
import re

from lollypop.define import App, ViewType, MARGIN
from lollypop.define import ARTISTS_PATH
from lollypop.objects_album import Album
from lollypop.information_store import InformationStore
from lollypop.view_albums_list import AlbumsListView
from lollypop.view import View
from lollypop.utils import get_default_storage_type
from lollypop.widgets_banner_information import InformationBannerWidget
from lollypop.helper_signals import SignalsHelper, signals_map


class ArtistRow(Gtk.ListBoxRow):
    """
        Artist row for Wikipedia
    """

    def __init__(self, item):
        """
            Init row
            @param item as (str, str, str)
        """
        Gtk.ListBoxRow.__init__(self)
        self.__locale = item[0]
        self.__page_id = item[2]
        label = Gtk.Label.new("%s: %s" % (item[0], item[1]))
        label.set_property("halign", Gtk.Align.START)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.get_style_context().add_class("padding")
        label.show()
        self.add(label)

    @property
    def locale(self):
        """
            Get locale
            @return str
        """
        return self.__locale

    @property
    def page_id(self):
        """
            Get page id
            @return str
        """
        return self.__page_id


class InformationView(View, SignalsHelper):
    """
        View with artist information
    """

    @signals_map
    def __init__(self, view_type, minimal=False):
        """
            Init artist infos
            @param view_type as ViewType
            @param minimal as bool
        """
        View.__init__(self, get_default_storage_type(),
                      view_type | ViewType.OVERLAY)
        self.__information_store = InformationStore()
        self.__cancellable = Gio.Cancellable()
        self.__minimal = minimal
        self.__artist_name = ""
        if minimal:
            return []
        else:
            return [
                (App().window, "notify::folded", "_on_container_folded"),
            ]

    def populate(self, artist_id=None):
        """
            Show information for artists
            @param artist_id as int
        """
        self.__banner = None
        artist_ids = App().player.current_track.artist_ids\
            if artist_id is None else [artist_id]
        self.__artist_name = App().artists.get_name(artist_ids[0])
        if not self.__minimal:
            storage_type = App().player.current_track.storage_type
            self.__banner = InformationBannerWidget(artist_ids[0])
            self.__banner.show()
            self.__banner.connect("search", self.__on_banner_search)
            self.__albums_view = AlbumsListView([], [],
                                                ViewType.SCROLLED |
                                                ViewType.ARTIST)
            self.__albums_view.set_size_request(350, -1)
            self.__albums_view.show()
            self.__albums_view.set_halign(Gtk.Align.END)
            self.__albums_view.add_widget(self.__albums_view.box)
            albums = []
            storage_type = get_default_storage_type()
            for album_id in App().albums.get_ids([], artist_ids,
                                                 storage_type, True):
                albums.append(Album(album_id))
            if not albums:
                albums = [App().player.current_track.album]
            self.__albums_view.populate(albums)
        self.__listbox = Gtk.ListBox.new()
        self.__listbox.show()
        self.__listbox.get_style_context().add_class("trackswidget")
        self.__listbox.connect("row-activated", self.__on_row_activated)
        self.__listbox.set_hexpand(True)
        self.__listbox.set_halign(Gtk.Align.CENTER)
        self.__label = Gtk.Label.new()
        self.__label.show()
        self.__label.set_justify(Gtk.Justification.FILL)
        self.__label.set_line_wrap(True)
        self.__label.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.__label.set_valign(Gtk.Align.START)
        self.__label.set_margin_top(MARGIN)
        self.__label.set_margin_bottom(MARGIN)
        self.__label.set_margin_start(MARGIN)
        self.__label.set_margin_end(MARGIN)
        self.__label.set_hexpand(True)
        widget = Gtk.Grid()
        widget.show()
        self.__stack = Gtk.Stack.new()
        self.__stack.show()
        self.__stack.add(self.__label)
        self.__stack.add(self.__listbox)
        self.add_widget(widget, self.__banner)
        widget.add(self.__stack)
        if not self.__minimal:
            widget.add(self.__albums_view)
        self._on_container_folded()
        content = self.__information_store.get_information(self.__artist_name,
                                                           ARTISTS_PATH)
        if content is None:
            self.__label.set_text(_("Loading information"))
            from lollypop.information_downloader import InformationDownloader
            downloader = InformationDownloader()
            downloader.get_information(self.__artist_name,
                                       self.__on_artist_information,
                                       self.__artist_name)
        else:
            App().task_helper.run(self.__to_markup, content,
                                  callback=(self.__label.set_markup,))

    @property
    def artist_name(self):
        """
            Get view artist
            @return artist_name as str
        """
        return self.__artist_name

#######################
# PROTECTED           #
#######################
    def _on_unmap(self, widget):
        """
            Cancel operations
            @param widget as Gtk.Widget
        """
        self.__cancellable.cancel()

    def _on_container_folded(self, *ignore):
        """
            Handle libhandy folded status
        """
        if not self.__minimal:
            if App().window.folded:
                if not self.view_type & ViewType.SMALL:
                    self.__label.set_margin_start(MARGIN)
                    self.__label.set_margin_end(MARGIN)
                    self.__label.get_style_context().remove_class("text-large")
                self.__albums_view.hide()
            else:
                if not self.view_type & ViewType.SMALL:
                    self.__label.set_margin_start(100)
                    self.__label.set_margin_end(100)
                    self.__label.get_style_context().add_class("text-large")
                self.__albums_view.show()

#######################
# PRIVATE             #
#######################
    def __show_main_widget(self):
        """
            Show main widget in stack
        """
        self.__listbox.hide()
        self.__label.show()
        self.__stack.set_visible_child(self.__label)

    def __to_markup(self, data):
        """
            Transform message to markup
            @param data as bytes
            @return str
        """
        pango = ["large", "x-large", "xx-large"]
        start = ["^===*", "^==", "^="]
        end = ["===*$", "==$", "=$"]
        i = 0
        text = GLib.markup_escape_text(data.decode("utf-8"))
        while i < len(pango):
            text = re.sub(start[i], "<b><span size='%s'>" % pango[i],
                          text, flags=re.M)
            text = re.sub(end[i], "</span></b>", text, flags=re.M)
            i += 1
        return text

    def __on_banner_search(self, banner, status):
        """
            Search for artist
            @param banner as InformationBannerwidget
            @param status as bool
        """
        if status:
            from lollypop.helper_web_wikipedia import WikipediaHelper
            wikipedia = WikipediaHelper()
            self.__label.hide()
            self.__listbox.show()
            self.__stack.set_visible_child(self.__listbox)
            App().task_helper.run(
                wikipedia.get_search_list,
                self.__artist_name,
                callback=(self.__on_wikipedia_search_list,))
        else:
            self.__show_main_widget()

    def __on_wikipedia_search_list(self, items):
        """
            Populate view with items
            @param items as [(str, str)]
        """
        if items:
            for item in items:
                row = ArtistRow(item)
                row.show()
                self.__listbox.add(row)
        else:
            self.__show_main_widget()
            self.__label.set_text(
                _("No information for %s") % self.__artist_name)

    def __on_wikipedia_get_content(self, content):
        """
            Update label and save to cache
            @param content as str
        """
        if content is not None:
            App().task_helper.run(self.__to_markup, content,
                                  callback=(self.__label.set_markup,))
            self.__information_store.save_information(
                self.__artist_name, ARTISTS_PATH, content)

    def __on_artist_artwork(self, surface):
        """
            Finish widget initialisation
            @param surface as cairo.Surface
        """
        if surface is None:
            self.__artist_artwork.hide()
        else:
            self.__artist_artwork.set_from_surface(surface)

    def __on_artist_information(self, content, artist_name):
        """
            Set label
            @param content as bytes
            @param artist_name as str
        """
        if content is None:
            self.__show_main_widget()
            self.__label.set_text(
                _("No information for %s") % self.__artist_name)
        else:
            App().task_helper.run(self.__to_markup, content,
                                  callback=(self.__label.set_markup,))
            self.__information_store.save_information(self.__artist_name,
                                                      ARTISTS_PATH,
                                                      content)

    def __on_row_activated(self, listbox, row):
        """
            Update artist information
            @param listbox as Gtk.ListBox
            @param row as Gtk.ListBoxRow
        """
        self.__show_main_widget()
        self.__banner.button.set_active(False)
        from lollypop.helper_web_wikipedia import WikipediaHelper
        wikipedia = WikipediaHelper()
        App().task_helper.run(wikipedia.get_content_for_page_id,
                              row.page_id, row.locale,
                              callback=(self.__on_wikipedia_get_content,))
