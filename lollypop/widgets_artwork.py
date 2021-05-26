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

from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf, GObject

from gettext import gettext as _

from lollypop.logger import Logger
from lollypop.utils import emit_signal
from lollypop.define import App, ArtSize, ArtBehaviour


class ArtworkSearchChild(Gtk.FlowBoxChild):
    """
        Child for ArtworkSearch
    """

    __gsignals__ = {
        "hidden": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, api, view_type):
        """
            Init child
            @param api as str
            @param view_type as ViewType
        """
        Gtk.FlowBoxChild.__init__(self)
        self.__bytes = None
        self.__view_type = view_type
        self.__api = api
        self.__image = Gtk.Image()
        self.__image.show()
        self.__label = Gtk.Label()
        self.__label.show()
        grid = Gtk.Grid()
        grid.set_orientation(Gtk.Orientation.VERTICAL)
        grid.show()
        grid.add(self.__image)
        grid.add(self.__label)
        grid.set_row_spacing(5)
        self.__image.get_style_context().add_class("cover-frame")
        self.__image.set_property("halign", Gtk.Align.CENTER)
        self.__image.set_property("valign", Gtk.Align.CENTER)
        self.add(grid)

    def populate(self, bytes, art_manager, art_size):
        """
            Populate images with bytes
            @param bytes as bytes
            @param art_manager as ArtworkManager
            @param art_size as int
            @return bool if success
        """
        try:
            scale_factor = self.get_scale_factor()
            gbytes = GLib.Bytes.new(bytes)
            stream = Gio.MemoryInputStream.new_from_bytes(gbytes)
            if stream is not None:
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
                if self.__api is None:
                    text = "%sx%s" % (pixbuf.get_width(),
                                      pixbuf.get_height())
                else:
                    text = "%s: %sx%s" % (self.__api,
                                          pixbuf.get_width(),
                                          pixbuf.get_height())
                self.__label.set_text(text)
                pixbuf = art_manager.load_behaviour(
                                                pixbuf,
                                                art_size * scale_factor,
                                                art_size * scale_factor,
                                                ArtBehaviour.CROP)
                stream.close()
                self.__bytes = bytes
                surface = Gdk.cairo_surface_create_from_pixbuf(
                                                       pixbuf,
                                                       scale_factor,
                                                       None)
                self.__image.set_from_surface(surface)
                return True
        except Exception as e:
            Logger.error("ArtworkSearchChild::__get_image: %s" % e)
        return False

    @property
    def bytes(self):
        """
            Get bytes associated to widget
            @return bytes
        """
        return self.__bytes


class ArtworkSearchWidget(Gtk.Grid):
    """
        Search for artwork
    """

    def __init__(self, view_type):
        """
            Init widget
            @param view_type as ViewType
        """
        Gtk.Grid.__init__(self)
        self.__view_type = view_type
        self.__timeout_id = None
        self.__uri_artwork_id = None
        self._loaders = 0
        self._cancellable = Gio.Cancellable()
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/ArtworkSearch.ui")
        builder.connect_signals(self)
        widget = builder.get_object("widget")
        self.__stack = builder.get_object("stack")
        self.__entry = builder.get_object("entry")
        self.__spinner = builder.get_object("spinner")

        self._flowbox = Gtk.FlowBox()
        self._flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._flowbox.connect("child-activated", self._on_activate)
        self._flowbox.set_max_children_per_line(100)
        self._flowbox.set_property("row-spacing", 10)
        self._flowbox.set_property("valign", Gtk.Align.START)
        self._flowbox.set_vexpand(True)
        self._flowbox.set_homogeneous(True)
        self._flowbox.show()

        self.__label = builder.get_object("label")
        self.__label.set_text(_("Select artwork"))

        if App().window.folded:
            self._art_size = ArtSize.MEDIUM
            widget.add(self._flowbox)
        else:
            self._art_size = ArtSize.BANNER
            scrolled = Gtk.ScrolledWindow.new()
            scrolled.show()
            scrolled.set_size_request(700, 400)
            scrolled.set_vexpand(True)
            viewport = Gtk.Viewport.new()
            viewport.show()
            viewport.add(self._flowbox)
            scrolled.add(viewport)
            widget.add(scrolled)
        self.add(widget)
        self.connect("unmap", self.__on_unmap)

    def populate(self):
        """
            Populate view
        """
        try:
            grid = Gtk.Grid()
            grid.set_orientation(Gtk.Orientation.VERTICAL)
            grid.show()
            grid.set_row_spacing(5)
            image = Gtk.Image.new_from_icon_name("edit-clear-all-symbolic",
                                                 Gtk.IconSize.INVALID)
            image.set_pixel_size(self._art_size)
            context = image.get_style_context()
            context.add_class("cover-frame")
            padding = context.get_padding(Gtk.StateFlags.NORMAL)
            border = context.get_border(Gtk.StateFlags.NORMAL)
            image.set_size_request(self._art_size + padding.left +
                                   padding.right + border.left + border.right,
                                   self._art_size + padding.top +
                                   padding.bottom + border.top + border.bottom)
            image.show()
            label = Gtk.Label.new(_("Remove"))
            label.show()
            grid.add(image)
            grid.add(label)
            grid.set_property("valign", Gtk.Align.CENTER)
            grid.set_property("halign", Gtk.Align.CENTER)
            self._flowbox.add(grid)
            self._search_for_artwork()
        except Exception as e:
            Logger.error("ArtworkSearchWidget::populate(): %s", e)

    def stop(self):
        """
            Stop loading
        """
        self._cancellable.cancel()

    @property
    def view_type(self):
        """
            Get view type
            @return ViewType
        """
        return self.__view_type

#######################
# PROTECTED           #
#######################
    def _search_for_artwork(self):
        """
            Search artwork on the web
        """
        self._loaders = 0
        self._cancellable = Gio.Cancellable()
        self.__spinner.start()

    def _save_from_filename(self, filename):
        pass

    def _on_button_clicked(self, button):
        """
            Show file chooser
            @param button as Gtk.button
        """
        dialog = Gtk.FileChooserDialog()
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_buttons(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_transient_for(App().window)
        file_filter = Gtk.FileFilter.new()
        file_filter.add_pixbuf_formats()
        dialog.set_filter(file_filter)
        emit_signal(self, "hidden", True)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self._save_from_filename(dialog.get_filename())
        dialog.destroy()

    def _get_current_search(self):
        """
            Return current searches
            @return str
        """
        return self.__entry.get_text()

    def _on_search_changed(self, entry):
        """
            Launch search based on current text
            @param entry as Gtk.Entry
        """
        if self.__timeout_id is not None:
            GLib.source_remove(self.__timeout_id)
        self.__timeout_id = GLib.timeout_add(1000,
                                             self.__on_search_timeout)

    def _on_activate(self, flowbox, child):
        pass

    def _on_uri_artwork_found(self, art, uris):
        """
            Load content in view
            @param art as Art
            @param uris as (str, str)/None
        """
        if uris:
            (uri, api) = uris.pop(0)
            App().task_helper.load_uri_content(uri,
                                               self._cancellable,
                                               self.__on_load_uri_content,
                                               api,
                                               uris,
                                               self._cancellable)
        else:
            self._loaders -= 1
            if self._loaders == 0:
                self.__spinner.stop()

#######################
# PRIVATE             #
#######################
    def __add_pixbuf(self, content, api):
        """
            Add content to view
            @param content as bytes
            @param api as str
        """
        child = ArtworkSearchChild(api, self.__view_type)
        child.show()
        status = child.populate(content, self.art, self._art_size)
        if status:
            child.set_name("web")
            self._flowbox.add(child)
        else:
            child.destroy()

    def __on_unmap(self, widget):
        """
            Cancel loading
            @param widget as Gtk.Widget
        """
        self._cancellable.cancel()

    def __on_load_uri_content(self, uri, loaded, content,
                              api, uris, cancellable):
        """
            Add loaded pixbuf
            @param uri as str
            @param loaded as bool
            @param content as bytes
            @param api as str
            @param uris as [str]
            @param cancellable as Gio.Cancellable
        """
        try:
            if loaded:
                self.__add_pixbuf(content, api)
            if uris and not cancellable.is_cancelled():
                (uri, api) = uris.pop(0)
                App().task_helper.load_uri_content(uri,
                                                   cancellable,
                                                   self.__on_load_uri_content,
                                                   api,
                                                   uris,
                                                   cancellable)
            else:
                self._loaders -= 1
        except Exception as e:
            self._loaders -= 1
            Logger.warning(
                "ArtworkSearchWidget::__on_load_uri_content(): %s", e)
        if self._loaders == 0:
            self.__spinner.stop()

    def __on_search_timeout(self):
        """
            Populate widget
        """
        self.__timeout_id = None
        self._cancellable.cancel()
        self._cancellable = Gio.Cancellable()
        for child in self._flowbox.get_children():
            if child.get_name() == "web":
                child.destroy()
        GLib.timeout_add(500, self._search_for_artwork)
