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

from gi.repository import Gtk, Gio, GLib, GObject, Pango

from gettext import gettext as _

from lollypop.view_tracks_album import AlbumTracksView
from lollypop.define import ArtSize, App, ViewType, MARGIN_SMALL
from lollypop.define import ArtBehaviour
from lollypop.utils import emit_signal


class AlbumRow(Gtk.ListBoxRow):
    """
        Album row
    """

    __gsignals__ = {
        "activated": (GObject.SignalFlags.RUN_FIRST,
                      None, (GObject.TYPE_PYOBJECT,)),
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "track-removed": (GObject.SignalFlags.RUN_FIRST, None,
                          (GObject.TYPE_PYOBJECT,)),
    }

    def get_best_height(widget):
        """
            Helper to pass object it's height request
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(MARGIN_SMALL * 2 +
                          2 * layout.get_pixel_size()[1])
        cover_height = MARGIN_SMALL * 2 + ArtSize.SMALL
        # Don't understand what is this magic value
        # May not work properly without Adwaita
        if font_height > cover_height:
            return font_height + 4
        else:
            return cover_height + 4

    def __init__(self, album, height, view_type):
        """
            Init row widgets
            @param album as Album
            @param height as int
            @param view_type as ViewType
            @param parent as AlbumListView
        """
        Gtk.ListBoxRow.__init__(self)
        self.__view_type = view_type
        self.__revealer = None
        self.__artwork = None
        self.__gesture_list = None
        self.__album = album
        self.__cancellable = Gio.Cancellable()
        self.set_sensitive(False)
        context_style = self.get_style_context()
        context_style.add_class("albumrow")
        context_style.add_class("albumrow-collapsed")
        self.set_property("height-request", height)
        self.connect("destroy", self.__on_destroy)
        self.__tracks_view = self.__get_new_tracks_view()

    def populate(self):
        """
            Populate widget content
        """
        if self.__artwork is not None:
            self.emit("populated")
            return
        self.__artwork = Gtk.Image.new()
        App().art_helper.set_frame(self.__artwork, "small-cover-frame",
                                   ArtSize.SMALL, ArtSize.SMALL)
        self.set_sensitive(True)
        # Issue with gtk3-3.24.24, tooltip is flashing when in
        # information popover
        self.set_property("has-tooltip",
                          self.get_ancestor(Gtk.Popover) is None)
        self.connect("query-tooltip", self.__on_query_tooltip)
        if self.__album.artists:
            artists = GLib.markup_escape_text(", ".join(self.__album.artists))
        else:
            artists = _("Compilation")
        self.__artist_label = Gtk.Label.new("<b>%s</b>" % artists)
        self.__artist_label.set_use_markup(True)
        self.__artist_label.set_property("halign", Gtk.Align.START)
        self.__artist_label.set_hexpand(True)
        self.__artist_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label = Gtk.Label.new(self.__album.name)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.set_property("halign", Gtk.Align.START)
        self.__title_label.get_style_context().add_class("dim-label")
        if self.__view_type & (ViewType.PLAYBACK | ViewType.PLAYLISTS):
            button = Gtk.Button.new_from_icon_name("list-remove-symbolic",
                                                   Gtk.IconSize.BUTTON)
            if self.__view_type & ViewType.PLAYBACK:
                button.set_tooltip_text(_("Remove from playback"))
            else:
                button.set_tooltip_text(_("Remove from playlist"))
            button.connect("clicked", self.__on_remove_clicked)
        else:
            button = Gtk.Button.new_from_icon_name(
                    "media-playback-start-symbolic",
                    Gtk.IconSize.MENU)
            button.set_tooltip_text(_("Play this album"))
            button.connect("clicked", self.__on_play_clicked)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.get_style_context().add_class("menu-button")
        button.set_property("valign", Gtk.Align.CENTER)
        header = Gtk.Grid.new()
        header.set_column_spacing(MARGIN_SMALL)
        header.show()
        header.set_margin_start(MARGIN_SMALL)
        # This to align button with row button
        header.set_margin_end(MARGIN_SMALL * 2 + 3)
        header.set_margin_top(2)
        header.set_margin_bottom(2)
        header.attach(self.__artwork, 0, 0, 1, 2)
        header.attach(self.__artist_label, 1, 0, 1, 1)
        header.attach(self.__title_label, 1, 1, 1, 1)
        header.attach(button, 2, 0, 1, 2)

        self.__revealer = Gtk.Revealer.new()
        self.__revealer.show()
        self.__revealer.add(self.__tracks_view)

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        box.pack_start(header, 0, True, True)
        box.pack_start(self.__revealer, 1, False, False)
        self.add(box)
        self.set_artwork()
        self.set_selection()

    def reveal(self, reveal=None):
        """
            Reveal/Unreveal tracks
            @param reveal as bool or None to just change state
        """
        if self.__artwork is None:
            self.populate()
        if self.__revealer.get_reveal_child() and reveal is not True:
            self.__revealer.set_reveal_child(False)
            self.get_style_context().add_class("albumrow-collapsed")
            if self.album.id == App().player.current_track.album.id:
                self.set_state_flags(Gtk.StateFlags.VISITED, True)
        else:
            if not self.__tracks_view.is_populated:
                self.__tracks_view.populate()
            self.__revealer.set_reveal_child(True)
            self.get_style_context().remove_class("albumrow-collapsed")
            self.unset_state_flags(Gtk.StateFlags.VISITED)

    def set_selection(self):
        """
            Show play indicator
        """
        if self.__artwork is None:
            return
        selected = self.album.id == App().player.current_track.album.id and\
            App().player.current_track.id in self.album.track_ids
        if self.__revealer.get_reveal_child():
            self.set_state_flags(Gtk.StateFlags.NORMAL, True)
        elif selected:
            self.set_state_flags(Gtk.StateFlags.VISITED, True)
        else:
            self.set_state_flags(Gtk.StateFlags.NORMAL, True)

    def reset(self):
        """
            Get a new track view
        """
        if self.__artwork is None:
            return
        self.__tracks_view.destroy()
        self.__tracks_view = self.__get_new_tracks_view()
        self.__tracks_view.populate()
        self.__revealer.add(self.__tracks_view)

    def set_artwork(self):
        """
            Set album artwork
        """
        if self.__artwork is None:
            return
        App().art_helper.set_album_artwork(self.__album,
                                           ArtSize.SMALL,
                                           ArtSize.SMALL,
                                           self.__artwork.get_scale_factor(),
                                           ArtBehaviour.CACHE |
                                           ArtBehaviour.CROP_SQUARE,
                                           self.__on_album_artwork)

    @property
    def revealed(self):
        """
            True if revealed
            @return bool
        """
        return self.__revealer is not None and\
            self.__revealer.get_reveal_child()

    @property
    def tracks_view(self):
        """
            Get tracks view
            @return TracksView
        """
        return self.__tracks_view

    @property
    def listbox(self):
        """
            Get listbox
            @return Gtk.ListBox
        """
        if self.__tracks_view.boxes:
            return self.__tracks_view.boxes[0]
        else:
            return Gtk.ListBox.new()

    @property
    def children(self):
        """
            Get track rows
            @return [TrackRow]
        """
        if self.__tracks_view.boxes:
            return self.__tracks_view.boxes[0].get_children()
        else:
            return []

    @property
    def is_populated(self):
        """
            Return True if populated
            @return bool
        """
        return not self.revealed or self.__tracks_view.is_populated

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        if self.__artwork is None:
            return ""
        else:
            return self.__title_label.get_text() +\
                self.__artist_label.get_text()

    @property
    def album(self):
        """
            Get album
            @return Album
        """
        return self.__album

#######################
# PRIVATE             #
#######################
    def __get_new_tracks_view(self):
        """
            Get a new track view
            @return AlbumTracksView
        """
        tracks_view = AlbumTracksView(self.__album,
                                      self.__view_type |
                                      ViewType.SINGLE_COLUMN)
        tracks_view.connect("activated",
                            self.__on_tracks_view_activated)
        tracks_view.connect("populated",
                            self.__on_tracks_view_populated)
        tracks_view.connect("track-removed",
                            self.__on_tracks_view_track_removed)
        tracks_view.show()
        return tracks_view

    def __on_album_artwork(self, surface):
        """
            Set album artwork
            @param surface as str
        """
        if self.__artwork is None:
            return
        if surface is None:
            self.__artwork.set_from_icon_name("folder-music-symbolic",
                                              Gtk.IconSize.BUTTON)
        else:
            self.__artwork.set_from_surface(surface)
        self.show_all()
        # TracksView will emit populated
        if not self.revealed:
            emit_signal(self, "populated")

    def __on_query_tooltip(self, widget, x, y, keyboard, tooltip):
        """
            Show tooltip if needed
            @param widget as Gtk.Widget
            @param x as int
            @param y as int
            @param keyboard as bool
            @param tooltip as Gtk.Tooltip
        """
        layout_title = self.__title_label.get_layout()
        layout_artist = self.__artist_label.get_layout()
        if layout_title.is_ellipsized() or layout_artist.is_ellipsized():
            artist = GLib.markup_escape_text(self.__artist_label.get_text())
            title = GLib.markup_escape_text(self.__title_label.get_text())
            self.set_tooltip_markup("<b>%s</b>\n%s" % (artist, title))
        else:
            self.set_tooltip_text("")

    def __on_destroy(self, widget):
        """
            Destroyed widget
            @param widget as Gtk.Widget
        """
        self.__cancellable.cancel()
        self.__artwork = None

    def __on_tracks_view_activated(self, view, track):
        """
            Pass signal
        """
        emit_signal(self, "activated", track)

    def __on_tracks_view_track_removed(self, view, row):
        """
            Remove row
            @param view as TracksView
            @param row as TrackRow
        """
        row.destroy()
        emit_signal(self, "track-removed", row.track)

    def __on_tracks_view_populated(self, view):
        """
            Populate remaining discs
            @param view as TracksView
            @param disc_number as int
        """
        if self.revealed and not self.__tracks_view.is_populated:
            self.__tracks_view.populate()
        else:
            emit_signal(self, "populated")

    def __on_remove_clicked(self, button):
        """
            Remove album from playback/playlist
            @param button as Gtk.Button
        """
        if not self.get_state_flags() & Gtk.StateFlags.PRELIGHT:
            return True
        self.destroy()

    def __on_play_clicked(self, button):
        """
            Play album
            @param button as Gtk.Button
        """
        if not self.get_state_flags() & Gtk.StateFlags.PRELIGHT:
            return True
        App().player.play_album(self.__album)
