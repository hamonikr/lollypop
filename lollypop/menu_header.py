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

from gi.repository import Gio, GLib

from lollypop.objects_album import Album
from lollypop.define import App


class HeaderType:
    DEFAULT = 1
    ARTIST = 2
    ALBUM = 3
    ROUNDED = 4


class MenuHeader(Gio.MenuItem):
    """
        A simple menu header with label and icon
    """

    def __init__(self, label, icon_name):
        """
            Init menu
            @param label as str
            @param icon_name as str
        """
        Gio.MenuItem.__init__(self)
        header_type = GLib.Variant("i", HeaderType.DEFAULT)
        vlabel = GLib.Variant("s", label)
        vicon_name = GLib.Variant("s", icon_name)
        header = [header_type, vlabel, vicon_name]
        self.set_attribute_value("header", GLib.Variant("av", header))


class ArtistMenuHeader(Gio.MenuItem):
    """
        A menu header item for an artist
    """

    def __init__(self, artist_id):
        """
            Init menu
            @param artist_id as int
        """
        Gio.MenuItem.__init__(self)
        header_type = GLib.Variant("i", HeaderType.ARTIST)
        name = App().artists.get_name(artist_id)
        label = "<span alpha='40000'>%s</span>" % GLib.markup_escape_text(name)
        vlabel = GLib.Variant("s", label)
        vartist_id = GLib.Variant("i", artist_id)
        header = [header_type, vlabel, vartist_id]
        self.set_attribute_value("header", GLib.Variant("av", header))


class RoundedMenuHeader(Gio.MenuItem):
    """
        A menu header item for a playlist
    """

    def __init__(self, name, artwork_name):
        """
            Init menu
            @param name as str
            @param artwork_name as str
        """
        Gio.MenuItem.__init__(self)
        header_type = GLib.Variant("i", HeaderType.ROUNDED)
        label = "<span alpha='40000'>%s</span>" % GLib.markup_escape_text(name)
        vlabel = GLib.Variant("s", label)
        vartwork_name = GLib.Variant("s", artwork_name)
        header = [header_type, vlabel, vartwork_name]
        self.set_attribute_value("header", GLib.Variant("av", header))


class AlbumMenuHeader(Gio.MenuItem):
    """
        A menu header item for Albums/Tracks
    """

    def __init__(self, object):
        """
            Init menu
            @param object as Album/Track
        """
        Gio.MenuItem.__init__(self)
        header_type = GLib.Variant("i", HeaderType.ALBUM)
        if isinstance(object, Album):
            label = "<span alpha='40000'>%s</span>" % GLib.markup_escape_text(
                object.name)
            album_id = object.id
        else:
            label = "<b>%s</b>\n<span alpha='40000'>%s</span>" % (
                GLib.markup_escape_text(", ".join(object.artists)),
                GLib.markup_escape_text(object.name))
            album_id = object.album.id
        vlabel = GLib.Variant("s", label)
        valbum_id = GLib.Variant("i", album_id)
        header = [header_type, vlabel, valbum_id]
        self.set_attribute_value("header", GLib.Variant("av", header))
