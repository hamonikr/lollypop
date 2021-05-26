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

from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, GLib, Pango

from lollypop.objects_album import Album
from lollypop.define import App, ArtSize, ArtBehaviour, MARGIN
from lollypop.utils import get_round_surface, emit_signal
from lollypop.menu_header import HeaderType
from lollypop.helper_signals import SignalsHelper, signals_map


class MenuBuilder(Gtk.Stack, SignalsHelper):
    """
        Advanced menu model constructor
        Does not support submenus
    """

    __gsignals__ = {
        "hidden": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @signals_map
    def __init__(self, menu, scrolled=False):
        """
            Init menu
            @param menu as Gio.Menu
            @param scrolled as bool
        """
        Gtk.Stack.__init__(self)
        self.__built = False
        self.__grids = {}
        self.__menu_queue = []
        self.__submenu_queue = []
        self.__widgets_queue = []
        self.__add_menu(menu, "main", False, scrolled)
        return [
            (App().window.container.widget, "notify::folded",
             "_on_container_folded")
        ]

    def add_widget(self, widget, position=-1):
        """
            Append widget to menu
            @param widget as Gtk.Widget
            @param position as negative int
        """
        self.__widgets_queue.append((widget, position))
        if self.__built:
            self.__add_widgets()

#######################
# PROTECTED           #
#######################
    def _on_container_folded(self, leaflet, folded):
        """
            Destroy self if adaptive off
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        if not App().window.folded:
            self.destroy()

#######################
# PRIVATE             #
#######################
    def __add_widgets(self):
        """
            Add pending widget to menu
        """
        while self.__widgets_queue:
            (widget, position) = self.__widgets_queue.pop(0)
            if widget.submenu_name is not None:
                self.__add_menu_container(widget.submenu_name, True, True)
                self.__grids[widget.submenu_name].add(widget)
                button = Gtk.ModelButton.new()
                button.set_label(widget.submenu_name)
                button.get_child().set_halign(Gtk.Align.START)
                button.set_property("menu-name", widget.submenu_name)
                button.show()
                parent = self.__grids["main"]
                if widget.section is not None:
                    self.__add_section(widget.section, "main")
                widget = button
            else:
                parent = self.get_child_by_name("main")
                if isinstance(parent, Gtk.ScrolledWindow):
                    # scrolled -> viewport -> grid
                    parent = parent.get_child().get_child()
            if position < -1:
                position = len(parent) + position + 1
                parent.insert_row(position)
                parent.attach(widget, 0, position, 1, 1)
            else:
                parent.add(widget)

    def __add_menu_container(self, menu_name, submenu, scrolled, margin=10):
        """
            Add menu container
            @param menu_name as str
            @param submenu as bool
            @param scrolled as bool
            @param margin as int
        """
        grid = self.get_child_by_name(menu_name)
        if grid is None:
            grid = Gtk.Grid.new()
            grid.set_orientation(Gtk.Orientation.VERTICAL)
            grid.connect("map", self.__on_grid_map, menu_name)
            self.__grids[menu_name] = grid
            grid.set_property("margin", margin)
            grid.show()
            if scrolled:
                scrolled = Gtk.ScrolledWindow()
                scrolled.set_policy(Gtk.PolicyType.NEVER,
                                    Gtk.PolicyType.AUTOMATIC)
                scrolled.show()
                scrolled.add(grid)
                self.add_named(scrolled, menu_name)
            else:
                self.add_named(grid, menu_name)
            if submenu:
                button = Gtk.ModelButton.new()
                button.get_style_context().add_class("padding")
                button.set_property("menu-name", "main")
                button.set_property("inverted", True)
                button.set_label(menu_name)
                button.get_child().set_halign(Gtk.Align.START)
                button.show()
                grid.add(button)

    def __add_menu(self, menu, menu_name, submenu, scrolled):
        """
            Create container and add menu
            @param menu as Gio.Menu
            @param menu_name as str
            @param submenu as bool
            @param scrolled as bool
        """
        n_items = menu.get_n_items()
        if n_items:
            self.__add_menu_container(menu_name, submenu, scrolled, 10)
            menu_range = list(range(0, n_items))
            if submenu:
                self.__submenu_queue.append((menu, menu_name, menu_range))
            else:
                self.__add_menu_items(menu, menu_name, menu_range)
        else:
            self.__add_menu_container(menu_name, submenu, scrolled, 0)
            self.__built = True
            self.__add_widgets()

    def __add_menu_items(self, menu, menu_name, indexes):
        """
            Add menu items present in indexes
            @param menu as Gio.Menu
            @param menu_name as str
            @param indexes as [int]
        """
        if indexes:
            i = indexes.pop(0)
            header = menu.get_item_attribute_value(i, "header")
            action = menu.get_item_attribute_value(i, "action")
            label = menu.get_item_attribute_value(i, "label")
            tooltip = menu.get_item_attribute_value(i, "tooltip")
            close = menu.get_item_attribute_value(i, "close") is not None
            if header is not None:
                header_type = header[0]
                header_label = header[1]
                if header_type == HeaderType.ALBUM:
                    album_id = header[2]
                    self.__add_album_header(header_label,
                                            album_id,
                                            menu_name)
                elif header_type == HeaderType.ARTIST:
                    artist_id = header[2]
                    self.__add_artist_header(header_label, artist_id,
                                             menu_name)
                elif header_type == HeaderType.ROUNDED:
                    artwork_name = header[2]
                    self.__add_rounded_header(header_label, artwork_name,
                                              menu_name)
                else:
                    icon_name = header[2]
                    self.__add_header(header_label, icon_name, menu_name)
                GLib.idle_add(self.__add_menu_items, menu, menu_name, indexes)
            elif action is None:
                link = menu.get_item_link(i, "section")
                submenu = menu.get_item_link(i, "submenu")
                if link is not None:
                    self.__menu_queue.append((menu, menu_name, indexes))
                    self.__add_section(label, menu_name)
                    self.__add_menu(link, menu_name, False, False)
                elif submenu is not None:
                    self.__add_submenu(label, submenu, menu_name)
                    GLib.idle_add(self.__add_menu_items, menu,
                                  menu_name, indexes)
            else:
                target = menu.get_item_attribute_value(i, "target")
                self.__add_item(label, action, target,
                                tooltip, close, menu_name)
                GLib.idle_add(self.__add_menu_items, menu, menu_name, indexes)
        # Continue to populate queued menu
        elif self.__menu_queue:
            (menu, menu_name, indexes) = self.__menu_queue.pop(-1)
            GLib.idle_add(self.__add_menu_items, menu, menu_name, indexes)
        # Finish with submenus
        elif self.__submenu_queue:
            (menu, menu_name, indexes) = self.__submenu_queue.pop(-1)
            GLib.idle_add(self.__add_menu_items, menu, menu_name, indexes)
        else:
            self.__built = True
            self.__add_widgets()

    def __add_item(self, text, action, target, tooltip, close, menu_name):
        """
            Add a Menu item
            @param text as GLib.Variant
            @param action as Gio.Action
            @param target as GLib.Variant
            @parmam tooltip as GLib.Variant
            @param close as bool
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_hexpand(True)
        button.set_action_name(action.get_string())
        button.set_label(text.get_string())
        button.get_child().set_halign(Gtk.Align.START)
        if close:
            button.connect("clicked",
                           lambda x: emit_signal(self, "hidden", True))
        if tooltip is not None:
            button.set_tooltip_markup(tooltip.get_string())
            button.set_has_tooltip(True)
        if target is not None:
            button.set_action_target_value(target)
        button.show()
        self.__grids[menu_name].add(button)

    def __add_section(self, text, menu_name):
        """
            Add section to menu
            @param text as as GLib.Variant
            @param menu_name as str
        """
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
        sep1 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep1.set_hexpand(True)
        sep1.set_property("valign", Gtk.Align.CENTER)
        box.add(sep1)
        label = Gtk.Label.new(text.get_string())
        label.get_style_context().add_class("dim-label")
        if App().window.folded:
            label.get_style_context().add_class("padding")
        box.add(label)
        sep2 = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep2.set_property("valign", Gtk.Align.CENTER)
        sep2.set_hexpand(True)
        box.add(sep2)
        box.show_all()
        self.__grids[menu_name].add(box)

    def __add_submenu(self, text, menu, menu_name):
        """
            Add submenu
            @param text as GLib.Variant
            @param menu as Gio.Menu
            @param menu_name as str
        """
        submenu_name = text.get_string()
        self.__add_menu(menu, submenu_name, True, True)
        button = Gtk.ModelButton.new()
        button.set_hexpand(True)
        button.set_property("menu-name", submenu_name)
        button.set_label(text.get_string())
        button.get_child().set_halign(Gtk.Align.START)
        button.show()
        self.__grids[menu_name].add(button)

    def __add_header(self, text, icon_name, menu_name):
        """
            Add an header for albums to close menu
            @param text as GLib.Variant
            @param icon_name as GLib.Variant
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_hexpand(True)
        button.connect("clicked", lambda x: emit_signal(self, "hidden", True))
        button.show()
        label = Gtk.Label.new()
        label.set_markup(text)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.show()
        artwork = Gtk.Image.new_from_icon_name(icon_name,
                                               Gtk.IconSize.INVALID)
        artwork.set_pixel_size(ArtSize.SMALL)
        artwork.show()
        close_image = Gtk.Image.new_from_icon_name("pan-up-symbolic",
                                                   Gtk.IconSize.BUTTON)
        close_image.show()
        grid = Gtk.Grid()
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        grid.add(close_image)
        button.set_image(grid)
        button.get_style_context().add_class("padding")
        self.__grids[menu_name].add(button)

    def __add_album_header(self, text, album_id, menu_name):
        """
            Add an header for album to close menu
            @param text as str
            @param album_id as int
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_hexpand(True)
        button.connect("clicked", lambda x: emit_signal(self, "hidden", True))
        button.show()
        label = Gtk.Label.new()
        label.set_markup(text)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.show()
        artwork = Gtk.Image.new()
        close_image = Gtk.Image.new_from_icon_name("pan-up-symbolic",
                                                   Gtk.IconSize.BUTTON)
        close_image.show()
        grid = Gtk.Grid()
        grid.set_halign(Gtk.Align.START)
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        grid.add(close_image)
        button.set_image(grid)
        button.get_style_context().add_class("padding")
        App().art_helper.set_album_artwork(
                Album(album_id),
                ArtSize.SMALL,
                ArtSize.SMALL,
                artwork.get_scale_factor(),
                ArtBehaviour.CACHE | ArtBehaviour.CROP_SQUARE,
                self.__on_artwork,
                artwork)
        self.__grids[menu_name].add(button)

    def __add_artist_header(self, text, artist_id, menu_name):
        """
            Add an header for artist to close menu
            @param text as str
            @param artist_id as int
            @param menu_name as str
        """
        button = Gtk.ModelButton.new()
        button.set_hexpand(True)
        button.connect("clicked", lambda x: emit_signal(self, "hidden", True))
        button.show()
        label = Gtk.Label.new()
        label.set_markup(text)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.show()
        artwork = Gtk.Image.new()
        close_image = Gtk.Image.new_from_icon_name("pan-up-symbolic",
                                                   Gtk.IconSize.BUTTON)
        close_image.show()
        grid = Gtk.Grid()
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        grid.add(close_image)
        button.set_image(grid)
        button.get_style_context().add_class("padding")
        artist_name = App().artists.get_name(artist_id)
        App().art_helper.set_artist_artwork(
                artist_name,
                ArtSize.SMALL,
                ArtSize.SMALL,
                artwork.get_scale_factor(),
                ArtBehaviour.CACHE |
                ArtBehaviour.CROP_SQUARE |
                ArtBehaviour.ROUNDED,
                self.__on_artwork,
                artwork)
        self.__grids[menu_name].add(button)

    def __add_rounded_header(self, text, artwork_name, menu_name):
        """
            Add an header for rounded widgets to close menu
            @param text as str
            @param artwork_name as str
            @param menu_name as str
        """
        def on_load_from_cache(pixbuf, artwork):
            if pixbuf is not None:
                scale_factor = artwork.get_scale_factor()
                surface = Gdk.cairo_surface_create_from_pixbuf(
                    pixbuf.scale_simple(ArtSize.MEDIUM, ArtSize.MEDIUM,
                                        GdkPixbuf.InterpType.BILINEAR),
                    scale_factor, None)
                rounded = get_round_surface(surface, scale_factor,
                                            ArtSize.MEDIUM / 4)
                artwork.set_from_surface(rounded)
                artwork.show()
        button = Gtk.ModelButton.new()
        button.set_hexpand(True)
        button.connect("clicked", lambda x: emit_signal(self, "hidden", True))
        button.show()
        label = Gtk.Label.new()
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_markup(text)
        label.show()
        artwork = Gtk.Image.new()
        artwork.get_style_context().add_class("light-background")
        close_image = Gtk.Image.new_from_icon_name("pan-up-symbolic",
                                                   Gtk.IconSize.BUTTON)
        close_image.show()
        grid = Gtk.Grid()
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        grid.add(close_image)
        button.set_image(grid)
        button.get_style_context().add_class("padding")
        App().task_helper.run(
                App().art.get_from_cache,
                artwork_name,
                "ROUNDED",
                ArtSize.BANNER, ArtSize.BANNER,
                callback=(on_load_from_cache, artwork))
        self.__grids[menu_name].add(button)

    def __on_artwork(self, surface, artwork):
        """
            Set artwork
            @param surface as str
            @param artwork as Gtk.Image
        """
        if surface is None:
            artwork.set_from_icon_name("folder-music-symbolic",
                                       Gtk.IconSize.BUTTON)
        else:
            artwork.set_from_surface(surface)
        artwork.show()

    def __on_grid_map(self, widget, menu_name):
        """
            On map, set stack order
            @param widget as Gtk.Widget
            @param menu_name as str
        """
        if menu_name == "main":
            self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
            self.set_size_request(-1, -1)
        else:
            self.set_size_request(300, 400)
            self.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
