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

from lollypop.view import View
from lollypop.define import ViewType, StorageType
from lollypop.widgets_equalizer import EqualizerWidget


class EqualizerView(View):
    """
        Show equalizer widget
    """

    def __init__(self):
        """
            Init view
        """
        View.__init__(self, StorageType.ALL, ViewType.SCROLLED)
        widget = EqualizerWidget()
        widget.show()
        self.add_widget(widget)
