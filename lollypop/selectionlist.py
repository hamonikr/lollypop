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

from gi.repository import Gtk, Gdk, GLib, GObject, Pango

from locale import strcoll

from lollypop.view_lazyloading import LazyLoadingView
from lollypop.helper_gestures import GesturesHelper
from lollypop.fastscroll import FastScroll
from lollypop.define import Type, App, ArtSize, SelectionListMask
from lollypop.define import ArtBehaviour, ViewType, StorageType
from lollypop.logger import Logger
from lollypop.utils import get_icon_name, on_query_tooltip, popup_widget
from lollypop.utils import emit_signal


class SelectionListRow(Gtk.ListBoxRow):
    """
        A selection list row
    """

    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def get_best_height(widget):
        """
            Calculate widget height
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(layout.get_pixel_size()[1])
        return font_height

    def __init__(self, rowid, name, sortname, mask, height):
        """
            Init row
            @param rowid as int
            @param name as str
            @param sortname as str
            @param mask as SelectionListMask
            @param height as str
        """
        Gtk.ListBoxRow.__init__(self)
        self.__artwork = None
        self.__rowid = rowid
        self.__name = name
        self.__sortname = sortname
        self.__mask = mask
        self.set_style(height)

    def populate(self):
        """
            Populate widget
        """
        if self.__rowid == Type.SEPARATOR:
            separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
            separator.show()
            self.add(separator)
            self.set_sensitive(False)
            emit_signal(self, "populated")
        else:
            self.__grid = Gtk.Grid()
            self.__grid.set_column_spacing(7)
            self.__grid.show()
            self.__artwork = Gtk.Image.new()
            self.__grid.add(self.__artwork)
            self.__label = Gtk.Label.new()
            self.__label.set_markup(GLib.markup_escape_text(self.__name))
            self.__label.set_property("has-tooltip", True)
            self.__label.connect("query-tooltip", on_query_tooltip)
            self.__label.set_xalign(0)
            self.__grid.add(self.__label)
            if self.__mask & SelectionListMask.ARTISTS:
                self.__grid.set_margin_end(20)
            self.add(self.__grid)
            self.set_artwork()
            self.set_mask()

    def set_label(self, string):
        """
            Set label for row
            @param string as str
        """
        self.__name = string
        if not self.__mask & SelectionListMask.SIDEBAR:
            self.__label.set_markup(GLib.markup_escape_text(string))

    def set_artwork(self):
        """
            set_artwork widget
        """
        if self.__artwork is None:
            return
        if self.__rowid == Type.SEPARATOR:
            pass
        elif self.__mask & SelectionListMask.ARTISTS and\
                self.__rowid >= 0 and\
                App().settings.get_value("artist-artwork"):
            App().art_helper.set_artist_artwork(
                                    self.__name,
                                    ArtSize.SMALL,
                                    ArtSize.SMALL,
                                    self.get_scale_factor(),
                                    ArtBehaviour.ROUNDED |
                                    ArtBehaviour.CROP_SQUARE |
                                    ArtBehaviour.CACHE,
                                    self.__on_artist_artwork)
            self.__artwork.show()
        elif self.__rowid < 0:
            icon_name = get_icon_name(self.__rowid)
            self.__artwork.set_from_icon_name(icon_name, Gtk.IconSize.INVALID)
            self.__artwork.set_pixel_size(20)
            self.__artwork.show()
            emit_signal(self, "populated")
        else:
            self.__artwork.hide()
            emit_signal(self, "populated")

    def set_mask(self, mask=None):
        """
            Set row mask
            @param mask as SelectionListMask
        """
        # Do nothing if widget not populated
        if self.__artwork is None:
            self.__mask = mask
            return
        # Do not update widget if mask does not changed
        elif mask == self.__mask:
            return
        # If no mask, use current one
        elif mask is None:
            mask = self.__mask
        # Else use new mask
        else:
            self.__mask = mask

        if mask & (SelectionListMask.LABEL |
                   SelectionListMask.ARTISTS |
                   SelectionListMask.GENRES):
            self.__artwork.set_property("halign", Gtk.Align.FILL)
            self.__artwork.set_hexpand(False)
            self.__label.show()
            self.set_tooltip_text("")
            self.set_has_tooltip(False)
        else:
            self.__artwork.set_property("halign", Gtk.Align.CENTER)
            self.__artwork.set_hexpand(True)
            self.__label.hide()
            self.set_tooltip_text(self.__label.get_text())
            self.set_has_tooltip(True)
        if mask & SelectionListMask.ELLIPSIZE:
            self.__label.set_ellipsize(Pango.EllipsizeMode.END)
        else:
            self.__label.set_ellipsize(Pango.EllipsizeMode.NONE)

    def set_style(self, height):
        """
            Set internal sizing
        """
        if self.__rowid == Type.SEPARATOR:
            height = -1
            self.set_sensitive(False)
        elif self.__mask & SelectionListMask.ARTISTS and\
                self.__rowid >= 0 and\
                App().settings.get_value("artist-artwork"):
            self.get_style_context().add_class("row")
            if height < ArtSize.SMALL:
                height = ArtSize.SMALL
            # Padding => application.css
            height += 12
        elif self.__mask & SelectionListMask.SIDEBAR:
            self.get_style_context().add_class("row-big")
            # Padding => application.css
            height += 30
        else:
            self.get_style_context().add_class("row")
        self.set_size_request(-1, height)

    @property
    def is_populated(self):
        """
            Return True if populated
            @return bool
        """
        return self.get_child() is not None

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        return self.__name

    @property
    def sortname(self):
        """
            Get row sortname
            @return str
        """
        return self.__sortname

    @property
    def id(self):
        """
            Get row id
            @return int
        """
        return self.__rowid

#######################
# PRIVATE             #
#######################
    def __on_artist_artwork(self, surface):
        """
            Set artist artwork
            @param surface as cairo.Surface
        """
        if surface is None:
            self.__artwork.get_style_context().add_class("circle-icon")
            self.__artwork.set_size_request(ArtSize.SMALL,
                                            ArtSize.SMALL)
            self.__artwork.set_from_icon_name(
                                              "avatar-default-symbolic",
                                              Gtk.IconSize.DND)
        else:
            self.__artwork.get_style_context().remove_class("circle-icon")
            self.__artwork.set_from_surface(surface)
        emit_signal(self, "populated")


class SelectionList(LazyLoadingView, GesturesHelper):
    """
        A list for artists/genres
    """
    __gsignals__ = {
        "expanded": (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }

    def __init__(self, base_mask):
        """
            Init Selection list ui
            @param base_mask as SelectionListMask
        """
        LazyLoadingView.__init__(self, StorageType.ALL, ViewType.DEFAULT)
        self.__selection_pending_ids = []
        self.__base_mask = base_mask
        self.__mask = SelectionListMask.NONE
        self.__animation_timeout_id = None
        self.__height = SelectionListRow.get_best_height(self)
        self._box = Gtk.ListBox()
        self._box.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self._box.show()
        GesturesHelper.__init__(self, self._box)
        self.__scrolled = Gtk.ScrolledWindow()
        self.__scrolled.show()
        self.__scrolled.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)
        self.__viewport = Gtk.Viewport()
        self.__scrolled.add(self.__viewport)
        self.__viewport.show()
        self.__viewport.add(self._box)
        self.connect("initialized", self.__on_initialized)
        self.get_style_context().add_class("sidebar")
        self.__scrolled.set_vexpand(True)
        if base_mask & SelectionListMask.FASTSCROLL:
            self.__overlay = Gtk.Overlay.new()
            self.__overlay.show()
            self.__overlay.add(self.__scrolled)
            self.__fastscroll = FastScroll(self._box,
                                           self.__scrolled)
            self.__overlay.add_overlay(self.__fastscroll)
            self.add(self.__overlay)
            App().settings.connect("changed::artist-artwork",
                                   self.__on_artist_artwork_changed)
            App().artist_art.connect("artist-artwork-changed",
                                     self.__on_artist_artwork_changed)
        else:
            self.__overlay = None
            App().settings.connect("changed::show-sidebar-labels",
                                   self.__on_show_sidebar_labels_changed)
            self.add(self.__scrolled)
            self.__menu_button = Gtk.Button.new_from_icon_name(
                "view-more-horizontal-symbolic", Gtk.IconSize.BUTTON)
            self.__menu_button.set_property("halign", Gtk.Align.CENTER)
            self.__menu_button.get_style_context().add_class("no-border")
            self.__menu_button.connect("clicked",
                                       lambda x: self.__popup_menu(None, x))
            self.__menu_button.show()
            self.add(self.__menu_button)
        if base_mask & SelectionListMask.SIDEBAR:
            App().window.container.widget.connect("notify::folded",
                                                  self.__on_container_folded)
            self.__on_container_folded(None, App().window.folded)
        else:
            self.__base_mask |= SelectionListMask.LABEL
            self.__base_mask |= SelectionListMask.ELLIPSIZE
            self.__set_rows_mask(self.__base_mask | self.__mask)

    def set_mask(self, mask):
        """
            Mark list as artists list
            @param mask as SelectionListMask
        """
        self.__mask = mask

    def add_mask(self, mask):
        """
            Mark list as artists list
            @param mask as SelectionListMask
        """
        self.__mask |= mask

    def populate(self, values):
        """
            Populate view with values
            @param [(int, str, optional str)], will be deleted
        """
        self._box.set_sort_func(None)
        self.__scrolled.get_vadjustment().set_value(0)
        self.clear()
        LazyLoadingView.populate(self, values)

    def remove_value(self, object_id):
        """
            Remove id from list
            @param object_id as int
        """
        for child in self._box.get_children():
            if child.id == object_id:
                child.destroy()
                break

    def add_value(self, value):
        """
            Add item to list
            @param value as (int, str, optional str)
        """
        self._box.set_sort_func(self.__sort_func)
        ids = [row.id for row in self._box.get_children()]
        if value[0] not in ids:
            child = self._get_child(value)
            child.populate()
            if self.mask & SelectionListMask.ARTISTS:
                self.__fastscroll.clear()
                self.__fastscroll.populate()

    def update_value(self, object_id, name):
        """
            Update object with new name
            @param object_id as int
            @param name as str
        """
        found = False
        for child in self._box.get_children():
            if child.id == object_id:
                child.set_label(name)
                found = True
                break
        if not found:
            if self.__base_mask & SelectionListMask.FASTSCROLL:
                self.__fastscroll.clear()
            self.add_value((object_id, name, name))

    def update_values(self, values):
        """
            Update view with values
            @param [(int, str, optional str)]
        """
        if self.mask & SelectionListMask.FASTSCROLL:
            self.__fastscroll.clear()
        # Remove not found items
        value_ids = set([v[0] for v in values])
        for child in self._box.get_children():
            if child.id not in value_ids:
                self.remove_value(child.id)
        # Add items which are not already in the list
        item_ids = set([child.id for child in self._box.get_children()])
        for value in values:
            if not value[0] in item_ids:
                row = self._get_child(value)
                row.populate()
        if self.mask & SelectionListMask.ARTISTS:
            self.__fastscroll.populate()

    def select_ids(self, ids=[], activate=True):
        """
            Select listbox items
            @param ids as [int]
            @param activate as bool
        """
        if ids:
            rows = []
            for row in self._box.get_children():
                if row.id in ids:
                    rows.append(row)
            if rows:
                self._box.unselect_all()
                for row in rows:
                    self._box.select_row(row)
                if activate:
                    rows[0].activate()
        else:
            self._box.unselect_all()

    def clear(self):
        """
            Clear treeview
        """
        self.stop()
        for child in self._box.get_children():
            child.destroy()
        if self.__base_mask & SelectionListMask.FASTSCROLL:
            self.__fastscroll.clear()
            self.__fastscroll.clear_chars()

    def select_first(self):
        """
            Select first available item
        """
        try:
            self._box.unselect_all()
            row = self._box.get_children()[0]
            self._box.select_row(row)
            row.activate()
        except Exception as e:
            Logger.warning("SelectionList::select_first(): %s", e)

    def set_selection_pending_ids(self, pending_ids):
        """
            Set selection pending ids
            @param pending_ids
        """
        self.__selection_pending_ids = pending_ids

    def select_pending_ids(self):
        """
            Select pending ids
        """
        self.select_ids(self.__selection_pending_ids)
        self.__selection_pending_ids = []

    def activate_child(self):
        """
            Activated typeahead row
        """
        self._box.unselect_all()
        for row in self._box.get_children():
            style_context = row.get_style_context()
            if style_context.has_class("typeahead"):
                row.activate()
            style_context.remove_class("typeahead")

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        filtered = []
        for child in self._box.get_children():
            if isinstance(child, SelectionListRow):
                filtered.append(child)
        return filtered

    @property
    def overlay(self):
        """
            Get list overlay
            @return overlay as Gtk.Overlay
        """
        return self.__overlay

    @property
    def listbox(self):
        """
            Get listbox
            @return Gtk.ListBox
        """
        return self._box

    @property
    def mask(self):
        """
            Get selection list type
            @return bit mask
        """
        return self.__mask | self.__base_mask

    @property
    def args(self):
        return None

    @property
    def count(self):
        """
            Get items count in list
            @return int
        """
        return len(self._box.get_children())

    @property
    def selected_ids(self):
        """
            Get selected ids
            @return [int]
        """
        return [row.id for row in self._box.get_selected_rows()]

    @property
    def scrolled(self):
        """
            Get scrolled window
            @return Gtk.ScrolledWindow
        """
        return self.__scrolled

    @property
    def selected_id(self):
        """
            Get selected id
            @return int
        """
        selected_row = self._box.get_selected_row()
        return None if selected_row is None else selected_row.id

#######################
# PROTECTED           #
#######################
    def _get_child(self, value):
        """
            Get a child for view
            @param value as [(int, str, optional str)]
            @return row as SelectionListRow
        """
        (rowid, name, sortname) = value
        if rowid > 0 and self.mask & SelectionListMask.ARTISTS:
            used = sortname if sortname else name
            self.__fastscroll.add_char(used[0])
        row = SelectionListRow(rowid, name, sortname,
                               self.mask, self.__height)
        row.show()
        self._box.add(row)
        return row

    def _scroll_to_child(self, row):
        """
            Scroll to row
            @param row as SelectionListRow
        """
        coordinates = row.translate_coordinates(self._box, 0, 0)
        if coordinates:
            self.__scrolled.get_vadjustment().set_value(coordinates[1])

    def _on_primary_long_press_gesture(self, x, y):
        """
            Show row menu
            @param x as int
            @param y as int
        """
        self.__popup_menu(y)

    def _on_primary_press_gesture(self, x, y, event):
        """
            Activate current row
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        row = self._box.get_row_at_y(y)
        if row is not None:
            (exists, state) = event.get_state()
            if state & Gdk.ModifierType.CONTROL_MASK or\
                    state & Gdk.ModifierType.SHIFT_MASK:
                pass
            else:
                self._box.unselect_all()

    def _on_secondary_press_gesture(self, x, y, event):
        """
            Show row menu
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        self.__popup_menu(y)

#######################
# PRIVATE             #
#######################
    def __set_rows_mask(self, mask):
        """
            Show labels on child
            @param status as bool
        """
        for row in self._box.get_children():
            row.set_mask(mask)

    def __sort_func(self, row_a, row_b):
        """
            Sort rows
            @param row_a as SelectionListRow
            @param row_b as SelectionListRow
        """
        a_index = row_a.id
        b_index = row_b.id

        # Static vs static
        if a_index < 0 and b_index < 0:
            return a_index < b_index
        # Static entries always on top
        elif b_index < 0:
            return True
        # Static entries always on top
        if a_index < 0:
            return False
        # String comparaison for non static
        else:
            if self.mask & SelectionListMask.ARTISTS:
                a = row_a.sortname
                b = row_b.sortname
            else:
                a = row_a.name
                b = row_b.name
            return strcoll(a, b)

    def __popup_menu(self, y=None, relative=None):
        """
            Show menu at y or row
            @param y as int
            @param relative as Gtk.Widget
        """
        if self.__base_mask & SelectionListMask.SIDEBAR:
            menu = None
            row_id = None
            if relative is None:
                relative = self._box.get_row_at_y(y)
                if relative is not None:
                    row_id = relative.id
            if row_id is None:
                from lollypop.menu_selectionlist import SelectionListMenu
                menu = SelectionListMenu(self,
                                         self.mask,
                                         App().window.folded)
            elif not App().settings.get_value("save-state"):
                from lollypop.menu_selectionlist import SelectionListRowMenu
                menu = SelectionListRowMenu(row_id,
                                            App().window.folded)
            if menu is not None:
                from lollypop.widgets_menu import MenuBuilder
                menu_widget = MenuBuilder(menu)
                menu_widget.show()
                popup_widget(menu_widget, relative, None, None, None)

    def __on_artist_artwork_changed(self, object, value):
        """
            Update row artwork
            @param object as GObject.Object
            @param value as str
        """
        artist = value if object == App().art else None
        if self.mask & SelectionListMask.ARTISTS:
            for row in self._box.get_children():
                if artist is None:
                    row.set_style(self.__height)
                    row.set_artwork()
                elif row.name == artist:
                    row.set_artwork()
                    break

    def __on_show_sidebar_labels_changed(self, settings, value):
        """
            Show/hide labels
            @param settings as Gio.Settings
            @param value as str
        """
        self.__on_container_folded(None, App().window.folded)

    def __on_initialized(self, selectionlist):
        """
            Update fastscroll
            @param selectionlist as SelectionList
        """
        if self.mask & SelectionListMask.ARTISTS:
            self.__fastscroll.populate()
        # Scroll to first selected item
        for row in self._box.get_selected_rows():
            GLib.idle_add(self._scroll_to_child, row)
            break

    def __on_container_folded(self, leaflet, folded):
        """
            Update internals
            @param leaflet as Handy.Leaflet
            @param folded as Gparam
        """
        folded = App().window.folded
        self.__base_mask &= ~SelectionListMask.LABEL
        self.__scrolled.set_hexpand(folded)
        if folded or App().settings.get_value("show-sidebar-labels"):
            self.__base_mask |= SelectionListMask.LABEL
        self.__set_rows_mask(self.__base_mask | self.__mask)
