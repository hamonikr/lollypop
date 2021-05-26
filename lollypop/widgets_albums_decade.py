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
from lollypop.utils import get_default_storage_type
from lollypop.widgets_albums_rounded import RoundedAlbumsWidget


class AlbumsDecadeWidget(RoundedAlbumsWidget):
    """
        Decade widget showing cover for 4 albums
    """

    def __init__(self, item_ids, view_type, font_height):
        """
            Init widget
            @param decade as [int]
            @param view_type as ViewType
            @param font_height as int
        """
        decade_str = "%s - %s" % (item_ids[0], item_ids[-1])
        RoundedAlbumsWidget.__init__(self, item_ids, decade_str,
                                     decade_str, view_type, font_height)
        self._genre = Type.YEARS

    def populate(self):
        """
            Populate widget content
        """
        if self._artwork is None:
            RoundedAlbumsWidget.populate(self)
        else:
            self.set_artwork()

    @property
    def artwork_name(self):
        """
            Get artwork name
            return str
        """
        return "decade_" + self.name

#######################
# PROTECTED           #
#######################
    def _get_album_ids(self):
        """
            Get album ids
            @return [int]
        """
        storage_type = get_default_storage_type()
        items = []
        for year in self._data:
            items += App().tracks.get_albums_by_disc_for_year(
                                                       year,
                                                       storage_type, True,
                                                       self._ALBUMS_COUNT)
            l = len(items)
            if l < self._ALBUMS_COUNT:
                items += App().tracks.get_compilations_by_disc_for_year(
                                                       year,
                                                       storage_type, True,
                                                       self._ALBUMS_COUNT)
        return [item[0] for item in items]

#######################
# PRIVATE             #
#######################
