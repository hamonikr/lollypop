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


from lollypop.define import App, Type


def tracks_to_albums(tracks, skipped=True):
    """
        Convert tracks list to albums list
        @param tracks as [Track]
        @param skipped as bool
        @return [Album]
    """
    albums = []
    for track in tracks:
        if albums and albums[-1].id == track.album.id:
            albums[-1].append_track(track, False)
        else:
            album = track.album
            if album.loved == -1 and not skipped:
                continue
            album.set_tracks([track], False)
            albums.append(album)
    return albums


def get_album_ids_for(genre_ids, artist_ids, storage_type, skipped):
    """
        Get album ids view for genres/artists
        @param genre_ids as [int]
        @param artist_ids as [int]
        @param storage_type as StorageType
        @return [int]
    """
    items = []
    limit = App().settings.get_value("view-limit").get_int32()
    if genre_ids and genre_ids[0] == Type.POPULARS:
        items = App().albums.get_rated(storage_type, skipped, limit)
        count = limit - len(items)
        for album in App().albums.get_populars(storage_type, skipped, count):
            if album not in items:
                items.append(album)
    elif genre_ids and genre_ids[0] == Type.LOVED:
        items = App().albums.get_loved_albums(storage_type)
    elif genre_ids and genre_ids[0] == Type.RECENTS:
        items = App().albums.get_recents(storage_type, skipped, limit)
    elif genre_ids and genre_ids[0] == Type.LITTLE:
        items = App().albums.get_little_played(storage_type, skipped, limit)
    elif genre_ids and genre_ids[0] == Type.RANDOMS:
        items = App().albums.get_randoms(storage_type, None, skipped, limit)
    elif genre_ids and genre_ids[0] == Type.COMPILATIONS:
        items = App().albums.get_compilation_ids([], storage_type, skipped)
    elif genre_ids and not artist_ids:
        if Type.WEB in genre_ids or\
                App().settings.get_value("show-compilations-in-album-view"):
            items = App().albums.get_compilation_ids(genre_ids, storage_type,
                                                     skipped)
        items += App().albums.get_ids(genre_ids, [], storage_type, skipped)
    else:
        items = App().albums.get_ids(genre_ids, artist_ids,
                                     storage_type, skipped)
    return items
