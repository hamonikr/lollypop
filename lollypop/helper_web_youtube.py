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

from gi.repository import GLib, Gio

from re import sub

from lollypop.helper_web_base import BaseWebHelper
from lollypop.utils import emit_signal
from lollypop.utils_file import get_youtube_dl
from lollypop.logger import Logger


class YouTubeWebHelper(BaseWebHelper):
    """
        YoutTube helper
    """

    __BAD_SCORE = 1000000

    def __init__(self):
        """
            Init heApper
        """
        BaseWebHelper.__init__(self)

    def get_uri_content(self, uri, cancellable):
        """
            Get content uri
            @param uri as str
            @param cancellable as Gio.Cancellable
            @return content uri as str/None
        """
        Logger.info("Loading %s with YouTube", uri)
        try:
            proxy = GLib.environ_getenv(GLib.get_environ(), "all_proxy")
            if proxy is not None and proxy.startswith("socks://"):
                proxy = proxy.replace("socks://", "socks4://")
            (path, env) = get_youtube_dl()
            # Remove playlist args
            uri = sub("list=.*", "", uri)
            argv = [path, "--no-cache-dir", "-g", "-f", "bestaudio", uri]
            if proxy is not None:
                argv += ["--proxy", proxy, None]
            else:
                argv.append(None)
            process = Gio.Subprocess.new(argv, Gio.SubprocessFlags.STDOUT_PIPE)
            process.wait_async(cancellable, self.__on_youtube_dl, cancellable)
        except Exception as e:
            Logger.error("YouTubeWebHelper::get_uri_content(): %s", e)

#######################
# PRIVATE             #
#######################
    def __on_youtube_dl(self, process, result, cancellable):
        """
            Emit signal for content
            @param process as Gio.Subprocess.
            @param result as Gio.AsyncResult
            @param cancellable as Gio.Cancellable
        """
        try:
            content = ""
            status = process.wait_check_finish(result)
            if status:
                stream = process.get_stdout_pipe()
                bytes = bytearray(0)
                buf = stream.read_bytes(1024, cancellable).get_data()
                while buf:
                    bytes += buf
                    buf = stream.read_bytes(1024, cancellable).get_data()
                stream.close()
                content = bytes.decode("utf-8")
        except Exception as e:
            Logger.warning("YouTubeWebHelper::__on_youtube_dl(): %s", e)
        emit_signal(self, "uri-content-loaded", content)
