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

from locale import getlocale, strcoll
from importlib import import_module

# Ugly magic to dynamically adapt to the current locale...
try:
    # Try loading 'index_of' function of the current locale
    _module = import_module('lollypop.locales.%s' % getlocale()[0].lower())
    index_of = _module.index_of
except:
    # In case the locale doesn't need special care, fall back to a naive
    # implementation
    def index_of(string):
        """
            Get index of a string in a locale-aware manner.
            This is the fallback, which simply returns the first character.
            @param string as str
            @return str
        """
        if string:
            return string[0]
        else:
            return ""


class LocalizedCollation(object):
    """
        COLLATE LOCALIZED missing from default sqlite installation
        Android only
    """

    def __init__(self):
        pass

    def __call__(self, v1, v2):
        i1 = index_of(v1).upper()
        i2 = index_of(v2).upper()
        if strcoll(i1, i2) < 0:
            return -1
        elif strcoll(i1, i2) == 0:
            return strcoll(v1, v2)
        else:
            return 1
