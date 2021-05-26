# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2015 Jean-Philippe Braun <eon@patapon.info>
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

from lollypop.logger import Logger
from lollypop.define import App
from lollypop.utils import emit_signal


class Base:
    """
        Base for album and track objects
    """

    def __init__(self, db):
        self.db = db

    def __dir__(self, *args, **kwargs):
        """
            Concatenate base class"s fields with child class"s fields
        """
        return super(Base, self).__dir__(*args, **kwargs) +\
            list(self.DEFAULTS.keys())

    def __getattr__(self, attr):
        # Lazy DB calls of attributes
        if attr in list(self.DEFAULTS.keys()):
            if self.id is None or self.id < 0:
                return self.DEFAULTS[attr]
            # Actual value of "attr_name" is stored in "_attr_name"
            attr_name = "_" + attr
            attr_value = getattr(self, attr_name)
            if attr_value is None:
                attr_value = getattr(self.db, "get_" + attr)(self.id)
                setattr(self, attr_name, attr_value)
            # Return default value if None
            if attr_value is None:
                return self.DEFAULTS[attr]
            else:
                return attr_value

    def reset(self, attr):
        """
            Reset attr
            @param attr as str
        """
        attr_name = "_" + attr
        attr_value = getattr(self.db, "get_" + attr)(self.id)
        setattr(self, attr_name, attr_value)

    def get_popularity(self):
        """
            Get popularity
            @return int between 0 and 5
        """
        if self.id is None:
            return 0

        popularity = 0
        avg_popularity = self.db.get_avg_popularity()
        if avg_popularity > 0:
            popularity = self.db.get_popularity(self.id)
        return popularity * 5 / avg_popularity + 0.5

    def set_popularity(self, new_rate):
        """
            Set popularity
            @param new_rate as int between 0 and 5
        """
        if self.id is None:
            return
        try:
            avg_popularity = self.db.get_avg_popularity()
            popularity = int((new_rate * avg_popularity / 5) + 0.5)
            best_popularity = self.db.get_higher_popularity()
            if new_rate == 5:
                popularity = (popularity + best_popularity) / 2
            self.db.set_popularity(self.id, popularity)
            self.reset("popularity")
        except Exception as e:
            Logger.error("Base::set_popularity(): %s" % e)

    def set_rate(self, rate):
        """
            Set rate
            @param rate as int between -1 and 5
        """
        self.db.set_rate(self.id, rate)
        self.reset("rate")
        emit_signal(App().player, "rate-changed", self.id, rate)
