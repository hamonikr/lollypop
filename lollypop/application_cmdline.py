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

from gi.repository import Gio, GLib, Gdk

from urllib.parse import urlparse

from lollypop.utils import emit_signal
from lollypop.utils_file import get_file_type
from lollypop.define import ScanType, FileType
from lollypop.logger import Logger
from lollypop.objects_track import Track
from lollypop.objects_album import Album


class ApplicationCmdline:
    """
        Handle command line switches
        Need to be inherited by a Gtk.Application
    """

    def __init__(self, version):
        """
            Create cmdline handler
            @param version as str
        """
        self.__debug = False
        self.__version = version
        self.add_main_option("play-ids", b"a", GLib.OptionFlags.NONE,
                             GLib.OptionArg.STRING, "Play ids", None)
        self.add_main_option("debug", b"d", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Debug Lollypop", None)
        self.add_main_option("set-rating", b"r", GLib.OptionFlags.NONE,
                             GLib.OptionArg.STRING, "Rate the current track",
                             None)
        self.add_main_option("play-pause", b"t", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Toggle playback",
                             None)
        self.add_main_option("stop", b"s", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Stop playback",
                             None)
        self.add_main_option("next", b"n", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Go to next track",
                             None)
        self.add_main_option("prev", b"p", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Go to prev track",
                             None)
        self.add_main_option("emulate-phone", b"e", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             "Emulate a Librem phone",
                             None)
        self.add_main_option("version", b"v", GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             "Lollypop version",
                             None)
        self.connect("command-line", self.__on_command_line)
        self.connect("handle-local-options", self.__on_handle_local_options)

    @property
    def version(self):
        """
            Get Lollypop version
            @return srt
        """
        return self.__version

    @property
    def debug(self):
        """
            Get debug state
            @return bool
        """
        return self.__debug

#######################
# PRIVATE             #
#######################
    def __parse_uris(self, playlist_uris, audio_uris):
        """
            Parse playlist uris
            @param playlist_uris as [str]
            @param audio_uris as [str]
        """
        from gi.repository import TotemPlParser
        playlist_uri = playlist_uris.pop(0)
        parser = TotemPlParser.Parser.new()
        parser.connect("entry-parsed",
                       self.__on_entry_parsed,
                       audio_uris)
        parser.parse_async(playlist_uri, True, None,
                           self.__on_parse_finished,
                           playlist_uris, audio_uris)

    def __on_handle_local_options(self, app, options):
        """
            Handle local options
            @param app as Gio.Application
            @param options as GLib.VariantDict
        """
        try:
            if options.contains("version"):
                print(self.__version)
                exit(0)
            self.register(None)
            if self.get_is_remote():
                Gdk.notify_startup_complete()
        except Exception as e:
            Logger.error("Application::__on_handle_local_options(): %s", e)
        return -1

    def __on_command_line(self, app, app_cmd_line):
        """
            Handle command line
            @param app as Gio.Application
            @param options as Gio.ApplicationCommandLine
        """
        try:
            args = app_cmd_line.get_arguments()
            options = app_cmd_line.get_options_dict()
            if options.contains("debug"):
                self.__debug = True
            if options.contains("set-rating"):
                value = options.lookup_value("set-rating").get_string()
                try:
                    value = min(max(0, int(value)), 5)
                    if self.player.current_track.id is not None:
                        self.player.current_track.set_rate(value)
                except Exception as e:
                    Logger.error("Application::__on_command_line(): %s", e)
                    pass
            elif options.contains("play-pause"):
                self.player.play_pause()
            elif options.contains("stop"):
                self.player.stop()
            elif options.contains("play-ids"):
                try:
                    value = options.lookup_value("play-ids").get_string()
                    ids = value.split(";")
                    albums = []
                    for id in ids:
                        if id[0:2] == "a:":
                            album = Album(int(id[2:]))
                            self.player.add_album(album)
                            albums.append(album)
                        else:
                            track = Track(int(id[2:]))
                            self.player.add_album(track.album)
                            albums.append(track.album)
                    if albums and albums[0].tracks:
                        self.player.load(albums[0].tracks[0])
                except Exception as e:
                    Logger.error("Application::__on_command_line(): %s", e)
                    pass
            elif options.contains("next"):
                self.player.next()
            elif options.contains("prev"):
                self.player.prev()
            elif options.contains("emulate-phone"):
                self.window.toolbar.end.devices_popover.add_fake_phone()
            elif len(args) > 1:
                audio_uris = []
                playlist_uris = []
                for uri in args[1:]:
                    parsed = urlparse(uri)
                    if parsed.scheme not in ["http", "https"]:
                        try:
                            uri = GLib.filename_to_uri(uri)
                        except:
                            pass
                        f = Gio.File.new_for_uri(uri)
                        # Try ./filename
                        if not f.query_exists():
                            uri = GLib.filename_to_uri(
                                "%s/%s" % (GLib.get_current_dir(), uri))
                            f = Gio.File.new_for_uri(uri)
                    file_type = get_file_type(uri)
                    if file_type == FileType.PLS:
                        playlist_uris.append(uri)
                    else:
                        audio_uris.append(uri)
                if playlist_uris:
                    self.__parse_uris(playlist_uris, audio_uris)
                else:
                    self.__on_parse_finished(None, None, [], audio_uris)
            elif self.window is not None:
                if not self.window.is_visible():
                    self.window.present()
                    emit_signal(self.player, "status-changed")
                    emit_signal(self.player, "current-changed")
            Gdk.notify_startup_complete()
        except Exception as e:
            Logger.error("Application::__on_command_line(): %s", e)
        return 0

    def __on_parse_finished(self, source, result, playlist_uris, audio_uris):
        """
            Play stream
            @param source as None
            @param result as Gio.AsyncResult
            @param uris as ([str], [str])
        """
        if playlist_uris:
            self.__parse_uris(playlist_uris, audio_uris)
        else:
            self.scanner.update(ScanType.EXTERNAL, audio_uris)

    def __on_entry_parsed(self, parser, uri, metadata, audio_uris):
        """
            Add playlist entry to external files
            @param parser as TotemPlParser.Parser
            @param uri as str
            @param metadata as GLib.HastTable
            @param audio_uris as str
        """
        audio_uris.append(uri)
