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

from gi.repository import GLib, Gtk

from lollypop.define import ViewType, App
from lollypop.utils import noaccents
from lollypop.utils_album import tracks_to_albums
from lollypop.logger import Logger


class FilteringHelper():
    """
        Helper for filtering widgets Boxes
    """

    def __init__(self):
        """
            Init helper
        """
        self.__last_scrolled = None

    def search_for_child(self, text):
        """
            Search child and scroll
            @param text as str
        """
        for child in self.filtered:
            style_context = child.get_style_context()
            style_context.remove_class("typeahead")
        if not text:
            return
        for child in self.filtered:
            if noaccents(child.name).find(noaccents(text)) != -1:
                style_context = child.get_style_context()
                style_context.add_class("typeahead")
                GLib.idle_add(self._scroll_to_child, child)
                break

    def search_prev(self, text):
        """
            Search previous child and scroll
            @param text as str
        """
        previous_children = []
        found_child = None
        for child in self.filtered:
            style_context = child.get_style_context()
            if style_context.has_class("typeahead"):
                found_child = child
                break
            previous_children.insert(0, child)
        if previous_children and found_child is not None:
            for child in previous_children:
                if noaccents(child.name).find(noaccents(text)) != -1:
                    found_child.get_style_context().remove_class("typeahead")
                    child.get_style_context().add_class("typeahead")
                    GLib.idle_add(self._scroll_to_child, child)
                    break

    def search_next(self, text):
        """
            Search previous child and scroll
            @param text as str
        """
        found = False
        previous_style_context = None
        for child in self.filtered:
            style_context = child.get_style_context()
            if style_context.has_class("typeahead"):
                previous_style_context = style_context
                found = True
                continue
            if found and noaccents(child.name).find(noaccents(text)) != -1:
                previous_style_context.remove_class("typeahead")
                style_context.add_class("typeahead")
                GLib.idle_add(self._scroll_to_child, child)
                break

    def activate_child(self):
        """
            Activated typeahead row
        """
        def reset_party_mode():
            if App().player.is_party:
                App().lookup_action("party").change_state(
                    GLib.Variant("b", False))

        try:
            # Search typeahead child
            typeahead_child = None
            for child in self.filtered:
                style_context = child.get_style_context()
                if style_context.has_class("typeahead"):
                    typeahead_child = child
                    break
            if typeahead_child is None:
                return
            from lollypop.view_current_albums import CurrentAlbumsView
            from lollypop.view_playlists import PlaylistsView
            # Play child without reseting player
            if isinstance(self, CurrentAlbumsView):
                if hasattr(typeahead_child, "album"):
                    album = typeahead_child.album
                    if album.tracks:
                        track = album.tracks[0]
                        App().player.load(track)
                elif hasattr(typeahead_child, "track"):
                    App().player.load(typeahead_child.track)
            # Play playlist
            elif isinstance(self, PlaylistsView):
                reset_party_mode()
                tracks = []
                for album_row in self.view.children:
                    for track in album_row.album.tracks:
                        tracks.append(track)
                if tracks:
                    albums = tracks_to_albums(tracks)
                    if hasattr(typeahead_child, "album"):
                        if typeahead_child.album.tracks:
                            App().player.play_track_for_albums(
                                typeahead_child.album.tracks[0], albums)
                    elif hasattr(typeahead_child, "track"):
                        App().player.play_track_for_albums(
                            typeahead_child.track, albums)
            elif hasattr(typeahead_child, "data"):
                reset_party_mode()
                typeahead_child.activate()
            elif hasattr(typeahead_child, "album"):
                reset_party_mode()
                album = typeahead_child.album
                App().player.add_album(album)
                App().player.load(album.tracks[0])
            elif hasattr(typeahead_child, "track"):
                reset_party_mode()
                track = typeahead_child.track
                App().player.add_album(track.album)
                App().player.load(track.album.get_track(track.id))
            App().window.container.type_ahead.entry.set_text("")
        except Exception as e:
            Logger.error("View::activate_child: %s" % e)

    @property
    def filtered(self):
        """
            Return widget that we should filter
            @return [Gtk.Widget]
        """
        return self.children

    @property
    def scroll_shift(self):
        """
            Get scroll shift for y axes
            @return int
        """
        return 0

#######################
# PROTECTED           #
#######################
    def _scroll_to_child(self, child):
        """
            Scroll to child
            @param child as Gtk.Widget
        """
        if self.view_type & ViewType.SCROLLED:
            view_widget = self.scrolled.get_child()
            # Filtered children may exists while view is not populated
            if view_widget is None:
                return
            if isinstance(view_widget, Gtk.Viewport):
                view_widget = view_widget.get_child()
            coordinates = child.translate_coordinates(
                view_widget, 0, -self.scroll_shift)
            if coordinates:
                self.scrolled.get_vadjustment().set_value(coordinates[1])

#######################
# PRIVATE             #
#######################
