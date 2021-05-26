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

from gi.repository import Gio, GLib, Gdk, GdkPixbuf, Pango, Gtk

from math import pi
from gettext import gettext as _
from urllib.parse import urlparse
import unicodedata
import cairo
import time
import re
from hashlib import md5
from threading import current_thread
from functools import wraps

from lollypop.logger import Logger
from lollypop.define import App, Type, NetworkAccessACL
from lollypop.define import StorageType
from lollypop.shown import ShownLists


def make_subrequest(value, operand, count):
    """
        Make a subrequest for value and operand
        @param value as str   => SQL
        @param operand as str => OR/AND
        @param count as int => iteration count
    """
    subrequest = "("
    while count != 0:
        if subrequest != "(":
            subrequest += " %s " % operand
        subrequest += value
        count -= 1
    return subrequest + ")"


def ms_to_string(duration):
    """
        Convert milliseconds to a pretty string
        @param duration as int
    """
    hours = duration // 3600000
    if hours == 0:
        minutes = duration // 60000
        seconds = (duration % 60000) // 1000
        return "%i:%02i" % (minutes, seconds)
    else:
        seconds = duration % 3600000
        minutes = seconds // 60000
        seconds = (duration % 60000) // 1000
        return "%i:%02i:%02i" % (hours, minutes, seconds)


def get_human_duration(duration):
    """
        Get human readable duration
        @param duration in milliseconds
        @return str
    """
    hours = duration // 3600000
    minutes = duration // 60000
    if hours > 0:
        seconds = duration % 3600000
        minutes = seconds // 60000
        if minutes > 0:
            return _("%s h  %s m") % (hours, minutes)
        else:
            return _("%s h") % hours
    else:
        return _("%s m") % minutes


def get_round_surface(surface, scale_factor, radius):
    """
        Get rounded surface from surface/pixbuf
        @param surface as GdkPixbuf.Pixbuf/cairo.Surface
        @return surface as cairo.Surface
        @param scale_factor as int
        @param radius as int
        @warning not thread safe!
    """
    width = surface.get_width()
    height = surface.get_height()
    if isinstance(surface, GdkPixbuf.Pixbuf):
        pixbuf = surface
        width = width // scale_factor
        height = height // scale_factor
        radius = radius // scale_factor
        surface = Gdk.cairo_surface_create_from_pixbuf(
            pixbuf, scale_factor, None)
    rounded = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(rounded)
    degrees = pi / 180
    ctx.arc(width - radius, radius, radius, -90 * degrees, 0 * degrees)
    ctx.arc(width - radius, height - radius,
            radius, 0 * degrees, 90 * degrees)
    ctx.arc(radius, height - radius, radius, 90 * degrees, 180 * degrees)
    ctx.arc(radius, radius, radius, 180 * degrees, 270 * degrees)
    ctx.close_path()
    ctx.set_line_width(10)
    ctx.set_source_surface(surface, 0, 0)
    ctx.clip()
    ctx.paint()
    return rounded


def set_cursor_type(widget, name="pointer"):
    """
        Set cursor on widget
        @param widget as Gtk.Widget
        @param name as str
    """
    try:
        window = widget.get_window()
        if window is not None:
            cursor = Gdk.Cursor.new_from_name(Gdk.Display.get_default(),
                                              name)
            window.set_cursor(cursor)
    except:
        pass


def get_default_storage_type():
    """
        Get default collection storage type check
    """
    if get_network_available("YOUTUBE"):
        return StorageType.COLLECTION | StorageType.SAVED
    else:
        return StorageType.COLLECTION


def on_query_tooltip(label, x, y, keyboard, tooltip):
    """
        Show label tooltip if needed
        @param label as Gtk.Label
        @param x as int
        @param y as int
        @param keyboard as bool
        @param tooltip as Gtk.Tooltip
    """
    layout = label.get_layout()
    if layout.is_ellipsized():
        tooltip.set_markup(label.get_label())
        return True


def init_proxy_from_gnome():
    """
        Set proxy settings from GNOME
        @return (host, port) as (str, int) or (None, None)
    """
    try:
        proxy = Gio.Settings.new("org.gnome.system.proxy")
        mode = proxy.get_value("mode").get_string()
        if mode == "manual":
            for name in ["org.gnome.system.proxy.http",
                         "org.gnome.system.proxy.https"]:
                setting = Gio.Settings.new(name)
                host = setting.get_value("host").get_string()
                port = setting.get_value("port").get_int32()
                if host != "" and port != 0:
                    return (host, port)

            # Try with a socks proxy
            # returning host, port not needed as PySocks will override values
            socks = Gio.Settings.new("org.gnome.system.proxy.socks")
            host = socks.get_value("host").get_string()
            port = socks.get_value("port").get_int32()
            proxy = "socks4://%s:%s" % (host, port)
            from os import environ
            environ["all_proxy"] = proxy
            environ["ALL_PROXY"] = proxy
            if host != "" and port != 0:
                import socket
                import socks
                socks.set_default_proxy(socks.SOCKS4, host, port)
                socket.socket = socks.socksocket
    except Exception as e:
        Logger.warning("set_proxy_from_gnome(): %s", e)
    return (None, None)


def debug(str):
    """
        Print debug
        @param str as str
    """
    if App().debug is True:
        print(str)


def get_network_available(acl_name=""):
    """
        Return True if network available
        @param acl_name as str
        @return bool
    """
    if not App().settings.get_value("network-access"):
        return False
    elif acl_name == "":
        return Gio.NetworkMonitor.get_default().get_network_available()
    else:
        acl = App().settings.get_value("network-access-acl").get_int32()
        if acl & NetworkAccessACL[acl_name]:
            return Gio.NetworkMonitor.get_default().get_network_available()
    return False


def noaccents(string):
    """
        Return string without accents lowered
        @param string as str
        @return str
    """
    nfkd_form = unicodedata.normalize("NFKD", string)
    v = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return v.lower()


def sql_escape(string):
    """
        Escape string for SQL request
        @param string as str
        @param ignore as [str]
    """
    nfkd_form = unicodedata.normalize("NFKD", string)
    v = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return "".join([c for c in v if
                    c.isalpha() or
                    c.isdigit()]).rstrip().lower()


def escape(str, ignore=["_", "-", " ", "."]):
    """
        Escape string
        @param str as str
        @param ignore as [str]
    """
    return "".join([c for c in str if
                    c.isalpha() or
                    c.isdigit() or c in ignore]).rstrip()


def get_lollypop_album_id(name, artists, year=None):
    """
        Calculate Lollypop album id
        @param name as str
        @param artists as [str]
        @param year as int/None
    """
    if year is None:
        name = "%s_%s" % (sql_escape(" ".join(artists)), sql_escape(name))
    else:
        name = "%s_%s_%s" % (
            sql_escape(" ".join(artists)), sql_escape(name), year)
    return md5(name.encode("utf-8")).hexdigest()


def get_lollypop_track_id(name, artists, album_name):
    """
        Calculate Lollypop track id
        @param name as str
        @param artists as [str]
        @param year as str
        @param album_name as str
    """
    name = "%s_%s_%s" % (sql_escape(" ".join(artists)), sql_escape(name),
                         sql_escape(album_name))
    return md5(name.encode("utf-8")).hexdigest()


def get_iso_date_from_string(string):
    """
        Convert any string to an iso date
        @param string as str
        @return str/None
    """
    model = ["1970", "01", "01", "00", "00", "00"]
    try:
        split = re.split('[-:TZ]', string)
        length = len(split)
        while length < 6:
            split.append(model[length])
            length = len(split)
        return "%s-%s-%sT%s:%s:%sZ" % (split[0], split[1], split[2],
                                       split[3], split[4], split[5])
    except Exception as e:
        Logger.error("get_iso_date_from_string(): %s -> %s", string, e)
        return None


def format_artist_name(name):
    """
        Return formated artist name
        @param name as str
    """
    if not App().settings.get_value("smart-artist-sort"):
        return name
    # Handle language ordering
    # Translators: Add here words that shoud be ignored for artist sort order
    # Translators: Add The the too
    for special in _("The the").split():
        if name.startswith(special + " "):
            strlen = len(special) + 1
            name = name[strlen:] + ", " + special
    return name


def emit_signal(obj, signal, *args):
    """
        Emit signal
        @param obj as GObject.Object
        @param signal as str
        @thread safe
    """
    if current_thread().getName() == "MainThread":
        obj.emit(signal, *args)
    else:
        GLib.idle_add(obj.emit, signal, *args)


def translate_artist_name(name):
    """
        Return translate formated artist name
        @param name as str
    """
    split = name.split("@@@@")
    if len(split) == 2:
        name = split[1] + " " + split[0]
    return name


def get_page_score(page_title, title, artist, album):
    """
        Calculate web page score
        if page_title looks like (title, artist, album), score is lower
        @return int/None
    """
    page_title = escape(page_title.lower(), [])
    artist = escape(artist.lower(), [])
    album = escape(album.lower(), [])
    title = escape(title.lower(), [])
    # YouTube page title should be at least as long as wanted title
    if len(page_title) < len(title):
        return -1
    # Remove common word for a valid track
    page_title = page_title.replace("official", "")
    page_title = page_title.replace("video", "")
    page_title = page_title.replace("audio", "")
    # Remove artist name
    page_title = page_title.replace(artist, "")
    # Remove album name
    page_title = page_title.replace(album, "")
    # Remove title
    page_title = page_title.replace(title, "")
    return len(page_title)


def remove_static(ids):
    """
        Remove static ids
        @param ids as [int]
        @return [int]
    """
    # Special case for Type.WEB, only static item present in DB
    return [item for item in ids if item >= 0 or item == Type.WEB]


def get_font_height():
    """
        Get current font height
        @return int
    """
    ctx = App().window.get_pango_context()
    layout = Pango.Layout.new(ctx)
    layout.set_text("A", 1)
    return int(layout.get_pixel_size()[1])


def get_icon_name(object_id):
    """
        Return icon name for id
        @param object_id as int
    """
    icon = ""
    if object_id == Type.SUGGESTIONS:
        icon = "org.gnome.Lollypop-suggestions-symbolic"
    elif object_id == Type.POPULARS:
        icon = "starred-symbolic"
    elif object_id == Type.PLAYLISTS:
        icon = "emblem-documents-symbolic"
    elif object_id == Type.ALL:
        icon = "media-optical-cd-audio-symbolic"
    elif object_id == Type.ARTISTS:
        icon = "avatar-default-symbolic"
    elif object_id == Type.ARTISTS_LIST:
        icon = "org.gnome.Lollypop-artists-list-symbolic"
    elif object_id == Type.COMPILATIONS:
        icon = "system-users-symbolic"
    elif object_id == Type.RECENTS:
        icon = "document-open-recent-symbolic"
    elif object_id == Type.RANDOMS:
        icon = "media-playlist-shuffle-symbolic"
    elif object_id == Type.LOVED:
        icon = "emblem-favorite-symbolic"
    elif object_id == Type.LITTLE:
        icon = "org.gnome.Lollypop-unplayed-albums-symbolic"
    elif object_id == Type.YEARS:
        icon = "x-office-calendar-symbolic"
    elif object_id == Type.CURRENT:
        icon = "org.gnome.Lollypop-play-queue-symbolic"
    elif object_id == Type.LYRICS:
        icon = "audio-input-microphone-symbolic"
    elif object_id == Type.SEARCH:
        icon = "edit-find-symbolic"
    elif object_id == Type.GENRES:
        icon = "org.gnome.Lollypop-tag-symbolic"
    elif object_id == Type.GENRES_LIST:
        icon = "org.gnome.Lollypop-tag-list-symbolic"
    elif object_id == Type.WEB:
        icon = "goa-panel-symbolic"
    elif object_id == Type.INFO:
        icon = "dialog-information-symbolic"
    return icon


def get_title_for_genres_artists(genre_ids, artist_ids):
    """
        Return title for genres/artists
        @param genre_ids as [int]
        @param artist_ids as [int]
        @return str
    """
    if genre_ids and genre_ids[0] == Type.YEARS and artist_ids:
        title_str = "%s - %s" % (artist_ids[0], artist_ids[-1])
    else:
        genres = []
        for genre_id in genre_ids:
            if genre_id < 0:
                genres.append(ShownLists.IDS[genre_id])
            else:
                genre = App().genres.get_name(genre_id)
                if genre is not None:
                    genres.append(genre)
        title_str = ",".join(genres)
    return title_str


def popup_widget(widget, parent, x, y, state_widget):
    """
        Popup menu on widget as x, y
        @param widget as Gtk.Widget
        @param parent as Gtk.Widget
        @param x as int
        @param y as int
        @param state_widget as Gtk.Widget
        @return Gtk.Popover/None
    """
    def on_hidden(widget, hide, popover):
        popover.popdown()

    def on_unmap(popover, parent):
        parent.unset_state_flags(Gtk.StateFlags.VISITED)

    if App().window.folded:
        App().window.container.show_menu(widget)
        return None
    else:
        from lollypop.widgets_popover import Popover
        popover = Popover()
        popover.add(widget)
        widget.connect("hidden", on_hidden, popover)
        if state_widget is not None:
            if not state_widget.get_state_flags() & Gtk.StateFlags.VISITED:
                popover.connect("unmap", on_unmap, state_widget)
                state_widget.set_state_flags(Gtk.StateFlags.VISITED, False)
        popover.set_relative_to(parent)
        # Workaround a GTK autoscrolling issue in Gtk.ListBox
        # Gtk autoscroll to last focused widget on popover close
        if state_widget is not None:
            state_widget.grab_focus()
        if x is not None and y is not None:
            rect = Gdk.Rectangle()
            rect.x = x
            rect.y = y
            rect.width = rect.height = 1
            popover.set_pointing_to(rect)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.popup()
        return popover


def is_device(mount):
    """
        True if mount is a Lollypop device
        @param mount as Gio.Mount
        @return bool
    """
    if mount.get_volume() is None:
        return False
    uri = mount.get_default_location().get_uri()
    if uri is None:
        return False
    parsed = urlparse(uri)
    if parsed.scheme == "mtp":
        return True
    elif not App().settings.get_value("sync-usb-disks"):
        return False
    drive = mount.get_drive()
    return drive is not None and drive.is_removable()


def profile(f):
    """
        Decorator to get execution time of a function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()

        ret = f(*args, **kwargs)

        elapsed_time = time.perf_counter() - start_time
        Logger.info("%s::%s: execution time %d:%f" % (
            f.__module__, f.__name__, elapsed_time / 60, elapsed_time % 60))

        return ret

    return wrapper


def split_list(l, n=1):
    """
        Split list in n parts
        @param l as []
        @param n as int
    """
    length = len(l)
    split = [l[i * length // n: (i + 1) * length // n] for i in range(n)]
    return [l for l in split if l]
