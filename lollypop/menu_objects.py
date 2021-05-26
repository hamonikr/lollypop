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

from gi.repository import Gio, Gtk, GLib

from gettext import gettext as _

from lollypop.define import StorageType, MARGIN_SMALL, App
from lollypop.define import ViewType, Type
from lollypop.menu_playlists import PlaylistsMenu
from lollypop.menu_actions import ActionsMenu
from lollypop.menu_playback import TrackPlaybackMenu, AlbumPlaybackMenu
from lollypop.menu_sync import SyncAlbumsMenu
from lollypop.widgets_rating import RatingWidget
from lollypop.widgets_loved import LovedWidget


class AlbumMenu(Gio.Menu):
    """
        Contextual menu for album
    """

    def __init__(self, album, storage_type, view_type):
        """
            Init menu model
            @param album as Album
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        Gio.Menu.__init__(self)
        if App().window.folded:
            from lollypop.menu_header import AlbumMenuHeader
            self.append_item(AlbumMenuHeader(album))
        self.append_section(_("Playback"),
                            AlbumPlaybackMenu(album, view_type))
        if view_type & ViewType.ALBUM:
            from lollypop.menu_artist import ArtistAlbumsMenu
            menu = ArtistAlbumsMenu(album.artist_ids[0], album.storage_type)
            self.append_section(_("Artist"), menu)
        section = Gio.Menu()
        if album.storage_type & (StorageType.COLLECTION | StorageType.SAVED):
            section.append_submenu(_("Playlists"), PlaylistsMenu([album]))
        if album.storage_type & StorageType.COLLECTION:
            section.append_submenu(_("Devices"), SyncAlbumsMenu([album]))
        if section.get_n_items() != 0:
            self.append_section(_("Add to"), section)
        actions_menu = ActionsMenu(album)
        # Allow user to show album if not in album view
        if not view_type & ViewType.ALBUM:
            show_album_action = Gio.SimpleAction(name="show_album_action")
            App().add_action(show_album_action)
            show_album_action.connect(
                "activate",
                lambda x, y:
                App().window.container.show_view(
                   [Type.ALBUM], album, storage_type))
            menu_item = Gio.MenuItem.new(_("Show album"),
                                         "app.show_album_action")
            menu_item.set_attribute_value("close", GLib.Variant("b", True))
            actions_menu.prepend_item(menu_item)
        if actions_menu.get_n_items() != 0:
            self.append_section(_("Others"), actions_menu)


class AlbumsMenu(Gio.Menu):
    """
        Contextual menu for albums
    """

    def __init__(self, title, albums, view_type):
        """
            Init menu model
            @param title as str
            @param albums as [Album]
            @param view_type as ViewType
        """
        Gio.Menu.__init__(self)
        if App().window.folded:
            from lollypop.menu_header import MenuHeader
            self.append_item(MenuHeader(title,
                                        "media-optical-cd-audio-symbolic"))
        self.append_section(_("Devices"), SyncAlbumsMenu(albums))


class TrackMenu(Gio.Menu):
    """
        Full Contextual menu for a track
    """

    def __init__(self, track, view_type):
        """
            Init menu model
            @param track as Track
            @param view_type as ViewType

        """
        Gio.Menu.__init__(self)
        if App().window.folded:
            from lollypop.menu_header import AlbumMenuHeader
            self.append_item(AlbumMenuHeader(track))
        self.append_section(_("Playback"), TrackPlaybackMenu(track, view_type))
        if view_type & ViewType.SEARCH:
            from lollypop.menu_artist import ArtistAlbumsMenu
            menu = ArtistAlbumsMenu(track.artist_ids[0], track.storage_type)
            if menu.get_n_items() != 0:
                self.append_section(_("Artist"), menu)
        if not track.storage_type & StorageType.EPHEMERAL:
            section = Gio.Menu()
            section.append_submenu(_("Playlists"), PlaylistsMenu([track]))
            self.append_section(_("Add to"), section)
        actions_menu = ActionsMenu(track)
        if actions_menu.get_n_items() != 0:
            self.append_section(_("Others"), actions_menu)


class TrackMenuExt(Gtk.Grid):
    """
        Additional widgets for track menu
    """

    def __init__(self, track):
        """
            Init widget
            @param track as Track
        """
        Gtk.Grid.__init__(self)
        self.set_margin_top(MARGIN_SMALL)
        self.set_row_spacing(MARGIN_SMALL)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        if track.year is not None:
            year_label = Gtk.Label.new()
            year_label.set_text(str(track.year))
            dt = GLib.DateTime.new_from_unix_local(track.timestamp)
            year_label.set_tooltip_text(dt.format(_("%Y-%m-%d")))
            year_label.set_margin_end(5)
            year_label.get_style_context().add_class("dim-label")
            year_label.set_property("halign", Gtk.Align.START)
            year_label.set_property("hexpand", True)
            year_label.show()

        hgrid = Gtk.Grid()
        rating = RatingWidget(track)
        rating.set_property("halign", Gtk.Align.START)
        if App().window.folded:
            rating.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        rating.show()

        loved = LovedWidget(track)
        loved.set_property("halign", Gtk.Align.START)
        if App().window.folded:
            loved.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        loved.show()

        if track.year is not None:
            hgrid.add(year_label)
        hgrid.add(loved)
        hgrid.add(rating)
        hgrid.show()

        if track.is_web:
            from lollypop.helper_web import WebHelper
            helper = WebHelper(track, None)
            edit = Gtk.Entry()
            edit.set_placeholder_text(_("YouTube page address"))
            edit.set_margin_top(MARGIN_SMALL)
            edit.set_margin_start(MARGIN_SMALL)
            edit.set_margin_end(MARGIN_SMALL)
            edit.set_margin_bottom(MARGIN_SMALL)
            edit.set_property("hexpand", True)
            if helper.uri is not None:
                edit.set_text(helper.uri)
            edit.connect("changed", self.__on_edit_changed, track)
            edit.show()
            self.add(edit)

        separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        separator.show()
        self.add(separator)
        self.add(hgrid)

    @property
    def section(self):
        return None

    @property
    def submenu_name(self):
        return None

#######################
# PRIVATE             #
#######################
    def __on_edit_changed(self, edit, track):
        """
            Update track uri
            @param edit as Gtk.Edit
            @param track as Track
        """
        from urllib.parse import urlparse
        uri = edit.get_text()
        parsed = urlparse(uri)
        if parsed.scheme not in ["http", "https"]:
            return
        from lollypop.helper_web import WebHelper
        helper = WebHelper(track, None)
        helper.save(uri)
