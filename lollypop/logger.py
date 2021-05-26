# Copyright (c) 2017-2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (c) 2017 Bilal Elmoussaoui <bil.elmoussaoui@gmail.com>
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

import logging
import sys

from lollypop.define import App


class Logger:
    """
        Logger class.
    """
    FORMAT = "[%(levelname)-s] %(asctime)s %(message)s"
    DATE = "%Y-%m-%d %H:%M:%S"
    __log = None
    APP = "org.gnome.Lollypop"

    @staticmethod
    def get_default():
        """
            Return default instance of Logger
            @return Logger
        """
        if Logger.__log is None:
            logger = logging.getLogger(Logger.APP)

            handler = logging.StreamHandler(sys.stdout)
            formater = logging.Formatter(Logger.FORMAT, Logger.DATE)
            handler.setFormatter(formater)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)

            Logger.__log = logging.getLogger(Logger.APP)
        return Logger.__log

    @staticmethod
    def warning(msg, *args):
        """
            Log warning message
            @parma msg as str
        """
        Logger.get_default().warning(msg, *args)

    @staticmethod
    def debug(msg, *args):
        """
            Log debug message
            @parma msg as str
        """
        if App().debug:
            Logger.get_default().debug(msg, *args)

    @staticmethod
    def info(msg, *args):
        """
            Log info message
            @parma msg as str
        """
        Logger.get_default().info(msg, *args)

    @staticmethod
    def error(msg, *args):
        """
            Log error message
            @parma msg as str
        """
        Logger.get_default().error(msg, *args)
