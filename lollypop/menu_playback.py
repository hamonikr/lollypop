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

from gettext import gettext as _

from lollypop.define import App, ViewType, Type, LovedFlags
from lollypop.utils_album import tracks_to_albums
from lollypop.utils import get_default_storage_type, emit_signal
from lollypop.utils import get_network_available
from lollypop.objects_track import Track
from lollypop.objects_album import Album


class PlaybackMenu(Gio.Menu):
    """
        Base class for playback menu
    """

    def __init__(self):
        """
            Init menu
        """
        Gio.Menu.__init__(self)

    @property
    def in_player(self):
        """
            True if current object in player
            return bool
        """
        return False

#######################
# PROTECTED           #
#######################
    def _set_radio_action(self, artist_ids):
        """
            Set radio action
            @param artist_ids as [int]
        """
        radio_action = Gio.SimpleAction(name="radio_action_collection")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        menu_item = Gio.MenuItem.new(_("Play a radio"),
                                     "app.radio_action_collection")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)

    def _set_playback_actions(self):
        """
            Setup playback actions
        """
        if not self.in_player:
            append_playback_action = Gio.SimpleAction(
                name="append_playback_action")
            App().add_action(append_playback_action)
            append_playback_action.connect("activate",
                                           self._append_to_playback)
            menu_item = Gio.MenuItem.new(_("Add to playback"),
                                         "app.append_playback_action")
        else:
            del_playback_action = Gio.SimpleAction(name="del_playback_action")
            App().add_action(del_playback_action)
            del_playback_action.connect("activate",
                                        self._remove_from_playback)
            menu_item = Gio.MenuItem.new(_("Remove from playback"),
                                         "app.del_playback_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)

#######################
# PRIVATE             #
#######################
    def __on_radio_action_activate(self, action, variant, artist_ids):
        """
            Play a radio from storage type
            @param Gio.SimpleAction
            @param GLib.Variant
            @param artist_ids as [int]
        """
        App().player.play_radio_from_collection(artist_ids)


class RadioPlaybackMenu(Gio.Menu):
    """
        Allow to play a radio from artist ids
    """

    def __init__(self, artist_ids):
        """
            Init menu
            @param artist_ids as [int]
        """
        Gio.Menu.__init__(self)
        section = Gio.Menu()
        radio_action = Gio.SimpleAction(name="radio_action_collection")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        menu_item = Gio.MenuItem.new(_("Related tracks"),
                                     "app.radio_action_collection")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        section.append_item(menu_item)
        radio_action = Gio.SimpleAction(name="radio_action_loved")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        menu_item = Gio.MenuItem.new(_("Loved tracks"),
                                     "app.radio_action_loved")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        section.append_item(menu_item)
        radio_action = Gio.SimpleAction(name="radio_action_populars")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        menu_item = Gio.MenuItem.new(_("Popular tracks"),
                                     "app.radio_action_populars")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        section.append_item(menu_item)
        self.append_section(_("From collection"), section)
        section = Gio.Menu()
        radio_action = Gio.SimpleAction(name="radio_action_deezer")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        radio_action.set_enabled(get_network_available("DEEZER"))
        menu_item = Gio.MenuItem.new(_("Deezer"),
                                     "app.radio_action_deezer")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        section.append_item(menu_item)
        radio_action = Gio.SimpleAction(name="radio_action_lastfm")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        radio_action.set_enabled(get_network_available("LASTFM"))
        menu_item = Gio.MenuItem.new(_("Last.fm"),
                                     "app.radio_action_lastfm")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        section.append_item(menu_item)
        radio_action = Gio.SimpleAction(name="radio_action_spotify")
        App().add_action(radio_action)
        radio_action.connect("activate",
                             self.__on_radio_action_activate,
                             artist_ids)
        radio_action.set_enabled(get_network_available("SPOTIFY"))
        menu_item = Gio.MenuItem.new(_("Spotify"),
                                     "app.radio_action_spotify")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        section.append_item(menu_item)
        self.append_section(_("From the Web"), section)

#######################
# PRIVATE             #
#######################
    def __on_radio_action_activate(self, action, variant, artist_ids):
        """
            Play a radio from storage type
            @param Gio.SimpleAction
            @param GLib.Variant
            @param artist_ids as [int]
        """
        def play_radio():
            if action.get_name() == "radio_action_collection":
                App().player.play_radio_from_collection(artist_ids)
            elif action.get_name() == "radio_action_spotify":
                App().player.play_radio_from_spotify(artist_ids)
            elif action.get_name() == "radio_action_lastfm":
                App().player.play_radio_from_lastfm(artist_ids)
            elif action.get_name() == "radio_action_deezer":
                App().player.play_radio_from_deezer(artist_ids)
            elif action.get_name() == "radio_action_loved":
                App().player.play_radio_from_loved(artist_ids)
            elif action.get_name() == "radio_action_populars":
                App().player.play_radio_from_populars(artist_ids)
        App().task_helper.run(play_radio)


class PlaylistPlaybackMenu(Gio.Menu):
    """
        Contextual menu for a playlist
    """

    def __init__(self, playlist_id):
        """
            Init menu
            @param playlist id as int
        """
        Gio.Menu.__init__(self)
        play_action = Gio.SimpleAction(name="playlist_play_action")
        App().add_action(play_action)
        play_action.connect("activate", self.__on_play_action, playlist_id)
        menu_item = Gio.MenuItem.new(_("Play this playlist"),
                                     "app.playlist_play_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)
        add_action = Gio.SimpleAction(name="playlist_add_action")
        App().add_action(add_action)
        add_action.connect("activate", self.__on_add_action, playlist_id)
        menu_item = Gio.MenuItem.new(_("Add this playlist"),
                                     "app.playlist_add_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)

#######################
# PRIVATE             #
#######################
    def __get_albums(self, playlist_id):
        """
            Get albums for playlist_id
            @parma playlist_id as int
        """
        if App().playlists.get_smart(playlist_id):
            request = App().playlists.get_smart_sql(playlist_id)
            # We need to inject skipped/storage_type
            storage_type = get_default_storage_type()
            split = request.split("ORDER BY")
            split[0] += " AND loved != %s" % Type.NONE
            split[0] += " AND tracks.storage_type&%s " % storage_type
            track_ids = App().db.execute("ORDER BY".join(split))
            albums = tracks_to_albums(
                [Track(track_id) for track_id in track_ids])
        else:
            tracks = App().playlists.get_tracks(playlist_id)
            albums = tracks_to_albums(tracks)
        return albums

    def __on_play_action(self, action, variant, playlist_id):
        """
            Play albums
            @param Gio.SimpleAction
            @param GLib.Variant
            @param playlist_id as int
        """
        App().player.play_albums(self.__get_albums(playlist_id))

    def __on_add_action(self, action, variant, playlist_id):
        """
            Add albums to playback
            @param Gio.SimpleAction
            @param GLib.Variant
            @param playlist_id as int
        """
        App().player.add_albums(self.__get_albums(playlist_id))


class ArtistPlaybackMenu(PlaybackMenu):
    """
        Contextual menu for an artist
    """

    def __init__(self, artist_id, storage_type):
        """
            Init menu
            @param artist id as int
            @param storage_type as StorageType
        """
        PlaybackMenu.__init__(self)
        self.__artist_id = artist_id
        self.__storage_type = storage_type
        play_action = Gio.SimpleAction(name="artist_play_action")
        App().add_action(play_action)
        play_action.connect("activate", self.__on_play_action_activate)
        menu_item = Gio.MenuItem.new(_("Play this artist"),
                                     "app.artist_play_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)
        self._set_playback_actions()
        self.__set_skipped_action()
        if get_network_available("SPOTIFY") or\
                get_network_available("LASTFM") or\
                get_network_available("DEEZER"):
            submenu = RadioPlaybackMenu([artist_id])
            self.append_submenu(_("Play a radio"), submenu)
        else:
            self._set_radio_action([artist_id])

    @property
    def in_player(self):
        """
            True if current object in player
            return bool
        """
        album_ids = App().albums.get_ids([], [self.__artist_id],
                                         self.__storage_type, False)
        return set(App().player.album_ids) & set(album_ids) == set(album_ids)

#######################
# PROTECTED           #
#######################
    def _append_to_playback(self, action, variant):
        """
            Append track to playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        from lollypop.utils_artist import add_artist_to_playback
        add_artist_to_playback([self.__artist_id], (), True)

    def _remove_from_playback(self, action, variant):
        """
            Delete track id from playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        from lollypop.utils_artist import add_artist_to_playback
        add_artist_to_playback([self.__artist_id], (), False)

#######################
# PRIVATE             #
#######################
    def __set_skipped_action(self):
        """
            Set skipped action
        """
        album_ids = App().albums.get_ids([], [self.__artist_id],
                                         self.__storage_type, False)
        skipped = True
        for album_id in album_ids:
            album = Album(album_id)
            if not album.loved & LovedFlags.SKIPPED:
                skipped = False
                break
        action = Gio.SimpleAction.new_stateful(
                "skip-artist",
                None,
                GLib.Variant.new_boolean(skipped))
        App().add_action(action)
        action.connect("change-state", self.__on_loved_change_state)
        self.append(_("Ignored"), "app.skip-artist")

    def __on_loved_change_state(self, action, state):
        """
            Update Skipped state
            @param action as Gio.SimpleAction
            @param state as bool
        """
        action.set_state(state)
        album_ids = App().albums.get_ids([], [self.__artist_id],
                                         self.__storage_type, False)
        for album_id in album_ids:
            album = Album(album_id)
            if state:
                album.set_loved(album.loved | LovedFlags.SKIPPED)
            else:
                album.set_loved(album.loved & ~LovedFlags.SKIPPED)

    def __on_play_action_activate(self, action, variant):
        """
            Play albums
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        from lollypop.utils_artist import play_artists
        play_artists([self.__artist_id], [])


class GenrePlaybackMenu(PlaybackMenu):
    """
        Contextual menu for a genre
    """

    def __init__(self, genre_id):
        """
            Init decade menu
            @param genre_id as int
        """
        PlaybackMenu.__init__(self)
        self.__genre_id = genre_id
        play_action = Gio.SimpleAction(name="genre_play_action")
        App().add_action(play_action)
        play_action.connect("activate", self.__play)
        menu_item = Gio.MenuItem.new(_("Play this genre"),
                                     "app.genre_play_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)
        self._set_playback_actions()

    @property
    def in_player(self):
        """
            True if current object in player
            return bool
        """
        album_ids = self.__get_album_ids()
        return set(App().player.album_ids) & set(album_ids) == set(album_ids)

#######################
# PROTECTED           #
#######################
    def _append_to_playback(self, action, variant):
        """
            Append track to playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album_ids = self.__get_album_ids()
        App().player.add_album_ids(album_ids)

    def _remove_from_playback(self, action, variant):
        """
            Delete track id from playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album_ids = self.__get_album_ids()
        if App().player.current_track.album.id in album_ids:
            App().player.skip_album()
        App().player.remove_album_by_ids(album_ids)

#######################
# PRIVATE             #
#######################
    def __get_album_ids(self):
        """
            Get album ids for genre
            @return [int]
        """
        storage_type = get_default_storage_type()
        album_ids = App().albums.get_compilation_ids([self.__genre_id],
                                                     storage_type,
                                                     False)
        album_ids += App().albums.get_ids([self.__genre_id], [],
                                          storage_type,
                                          False)
        return album_ids

    def __play(self, action, variant):
        """
            Play albums
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album_ids = self.__get_album_ids()
        albums = [Album(album_id) for album_id in album_ids]
        App().player.play_albums(albums)


class DecadePlaybackMenu(PlaybackMenu):
    """
        Contextual menu for a decade
    """

    def __init__(self, years):
        """
            Init decade menu
            @param years as [int]
        """
        PlaybackMenu.__init__(self)
        self.__years = years
        play_action = Gio.SimpleAction(name="decade_play_action")
        App().add_action(play_action)
        play_action.connect("activate", self.__play)
        menu_item = Gio.MenuItem.new(_("Play this decade"),
                                     "app.decade_play_action")
        menu_item.set_attribute_value("close", GLib.Variant("b", True))
        self.append_item(menu_item)
        self._set_playback_actions()

    @property
    def in_player(self):
        """
            True if current object in player
            return bool
        """
        album_ids = self.__get_album_ids()
        return set(App().player.album_ids) & set(album_ids) == set(album_ids)

#######################
# PROTECTED           #
#######################
    def _append_to_playback(self, action, variant):
        """
            Append track to playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album_ids = self.__get_album_ids()
        App().player.add_album_ids(album_ids)

    def _remove_from_playback(self, action, variant):
        """
            Delete track id from playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album_ids = self.__get_album_ids()
        if App().player.current_track.album.id in album_ids:
            App().player.skip_album()
        App().player.remove_album_by_ids(album_ids)

#######################
# PRIVATE             #
#######################
    def __get_album_ids(self):
        """
            Get album ids for decade
            @return [int]
        """
        storage_type = get_default_storage_type()
        items = []
        for year in self.__years:
            items += App().tracks.get_compilations_by_disc_for_year(
                year, storage_type, False)
            items += App().tracks.get_albums_by_disc_for_year(
                year, storage_type, False)
        return [item[0] for item in items]

    def __play(self, action, variant):
        """
            Play albums
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album_ids = self.__get_album_ids()
        albums = [Album(album_id) for album_id in album_ids]
        App().player.play_albums(albums)


class AlbumPlaybackMenu(PlaybackMenu):
    """
        Contextual menu for an album
    """

    def __init__(self, album, view_type):
        """
            Init album menu
            @param album as Album
            @param view_type as ViewType
        """
        PlaybackMenu.__init__(self)
        self.__album = album
        if not view_type & ViewType.BANNER:
            play_action = Gio.SimpleAction(name="play_action")
            App().add_action(play_action)
            play_action.connect("activate", self.__on_play_action_activate)
            menu_item = Gio.MenuItem.new(_("Play this album"),
                                         "app.play_action")
            menu_item.set_attribute_value("close", GLib.Variant("b", True))
            self.append_item(menu_item)
            self._set_playback_actions()
        action = Gio.SimpleAction.new_stateful(
                "skip-album",
                None,
                GLib.Variant.new_boolean(
                    self.__album.loved & LovedFlags.SKIPPED))
        App().add_action(action)
        action.connect("change-state", self.__on_loved_change_state)
        self.append(_("Ignored"), "app.skip-album")
        if get_network_available("SPOTIFY") or\
                get_network_available("LASTFM") or\
                get_network_available("DEEZER"):
            submenu = RadioPlaybackMenu(album.artist_ids)
            self.append_submenu(_("Play a radio"), submenu)
        else:
            self._set_radio_action(album.artist_ids)

    @property
    def in_player(self):
        """
            True if current object in player
            return bool
        """
        return self.__album.id in App().player.album_ids

#######################
# PROTECTED           #
#######################
    def _append_to_playback(self, action, variant):
        """
            Append track to playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        App().player.add_album(self.__album)

    def _remove_from_playback(self, action, variant):
        """
            Delete track id from playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        if App().player.current_track.album.id == self.__album.id:
            App().player.skip_album()
        App().player.remove_album_by_id(self.__album.id)

#######################
# PRIVATE             #
#######################
    def __on_loved_change_state(self, action, state):
        """
            Update Skipped state
            @param action as Gio.SimpleAction
            @param state as bool
        """
        action.set_state(state)
        if state:
            self.__album.set_loved(self.__album.loved | LovedFlags.SKIPPED)
        else:
            self.__album.set_loved(self.__album.loved & ~LovedFlags.SKIPPED)

    def __on_play_action_activate(self, action, variant):
        """
            Play album
            @param action as Gio.SimpleAction
            @param variant as GLib.Variant
        """
        App().player.play_album(self.__album.clone(True))


class TrackPlaybackMenu(PlaybackMenu):
    """
        Contextual menu for tracks
    """

    def __init__(self, track, view_type):
        """
            Init track menu
            @param track as Track
            @param view_type as ViewType
        """
        PlaybackMenu.__init__(self)
        self.__track = track
        if not view_type & ViewType.TOOLBAR:
            self._set_playback_actions()
            self.__set_queue_actions()
        self.__set_stop_after_action()
        action = Gio.SimpleAction.new_stateful(
                "skip-track",
                None,
                GLib.Variant.new_boolean(
                    self.__track.loved & LovedFlags.SKIPPED))
        App().add_action(action)
        action.connect("change-state", self.__on_loved_change_state)
        self.append(_("Ignored"), "app.skip-track")

    @property
    def in_player(self):
        """
            True if current object in player
            return bool
        """
        for album in App().player.albums:
            if self.__track.album.id == album.id:
                if self.__track.id in album.track_ids:
                    return True
        return False

#######################
# PROTECTED           #
#######################
    def _append_to_playback(self, action, variant):
        """
            Append track to playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        album = Album(self.__track.album.id)
        album.set_tracks([self.__track])
        App().player.add_album(album)
        if App().player.is_playing:
            App().player.add_album(album)
        else:
            App().player.play_album(album)

    def _remove_from_playback(self, action, variant):
        """
            Delete track from playback
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        for album in App().player.albums:
            if album.id == self.__track.album.id:
                if self.__track.id in album.track_ids:
                    index = album.track_ids.index(self.__track.id)
                    track = album.tracks[index]
                    App().player.remove_track_from_album(track, album)
                    break

#######################
# PRIVATE             #
#######################
    def __set_queue_actions(self):
        """
            Set queue actions
        """
        if self.__track.id not in App().player.queue:
            append_queue_action = Gio.SimpleAction(name="append_queue_action")
            App().add_action(append_queue_action)
            append_queue_action.connect("activate",
                                        self.__append_to_queue)
            self.append(_("Add to queue"), "app.append_queue_action")
        else:
            del_queue_action = Gio.SimpleAction(name="del_queue_action")
            App().add_action(del_queue_action)
            del_queue_action.connect("activate",
                                     self.__remove_from_queue)
            self.append(_("Remove from queue"), "app.del_queue_action")

    def __set_stop_after_action(self):
        """
            Add an action to stop playback after track
        """
        if self.in_player and isinstance(self.__track, Track):
            stop_after_action = Gio.SimpleAction(name="stop_after_action")
            App().add_action(stop_after_action)
            if self.__track.id == App().player.stop_after_track_id:
                stop_after_action.connect("activate", self.__stop_after, None)
                self.append(_("Do not stop after"),
                            "app.stop_after_action")
            else:
                stop_after_action.connect("activate", self.__stop_after,
                                          self.__track.id)
                self.append(_("Stop after"), "app.stop_after_action")

    def __stop_after(self, action, variant, track_id):
        """
            Tell player to stop after track
            @param Gio.SimpleAction
            @param GLib.Variant
            @param track_id as int/None
        """
        App().player.stop_after(track_id)
        if track_id == App().player.current_track.id:
            App().player.set_next()

    def __append_to_queue(self, action, variant):
        """
            Append track to queue
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        App().player.append_to_queue(self.__track.id, False)
        emit_signal(App().player, "queue-changed")

    def __remove_from_queue(self, action, variant):
        """
            Delete track id from queue
            @param Gio.SimpleAction
            @param GLib.Variant
        """
        App().player.remove_from_queue(self.__track.id, False)
        emit_signal(App().player, "queue-changed")

    def __on_loved_change_state(self, action, state):
        """
            Update Skipped state
            @param action as Gio.SimpleAction
            @param state as bool
        """
        action.set_state(state)
        if state:
            self.__track.set_loved(self.__track.loved | LovedFlags.SKIPPED)
        else:
            self.__track.set_loved(self.__track.loved & ~LovedFlags.SKIPPED)
