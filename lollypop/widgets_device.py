# Copyright (c) 2014-2021 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (C) 2010 Jonathan Matthew (replay gain code)
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

from gi.repository import Gtk, GLib, Gio, GObject

from gi.repository.Gio import FILE_ATTRIBUTE_FILESYSTEM_SIZE, \
                              FILE_ATTRIBUTE_FILESYSTEM_FREE

from gettext import gettext as _

from lollypop.logger import Logger
from lollypop.define import App, Type
from lollypop.sync_mtp import MtpSync
from lollypop.utils import emit_signal


class DeviceWidget(Gtk.ListBoxRow):
    """
        A device widget for sync
    """

    __gsignals__ = {
        "syncing": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, name, uri, icon=None):
        """
            Init widget
            @param name as str
            @param uri as str
            @param icon as Gio.Icon
        """
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class("background")
        self.connect("map", self.__on_map)
        self.__name = name
        self.__uri = uri
        self.__progress = 0
        self.__builder = Gtk.Builder()
        self.__builder.add_from_resource("/org/gnome/Lollypop/DeviceWidget.ui")
        self.__progressbar = self.__builder.get_object("progress")
        self.__revealer = self.__builder.get_object("revealer")
        self.__switch_normalize = self.__builder.get_object("switch_normalize")
        self.__builder.get_object("name").set_label(self.__name)
        self.__combobox = self.__builder.get_object("combobox")
        self.__sync_button = self.__builder.get_object("sync_button")
        if icon is not None:
            device_symbolic = self.__builder.get_object("device-symbolic")
            device_symbolic.set_from_gicon(icon, Gtk.IconSize.DND)
        self.add(self.__builder.get_object("widget"))
        self.__builder.connect_signals(self)
        self.__calculate_free_space()
        self.__mtp_sync = MtpSync()
        self.__mtp_sync.connect("sync-finished", self.__on_sync_finished)
        self.__mtp_sync.connect("sync-progress", self.__on_sync_progress)
        for encoder in self.__mtp_sync._GST_ENCODER.keys():
            if not self.__mtp_sync.check_encoder_status(encoder):
                self.__builder.get_object(encoder).set_sensitive(False)
        self.connect("destroy", self.__on_destroy)

    @property
    def uri(self):
        """
            Get device URI
            @return str
        """
        return self.__uri

    @property
    def name(self):
        """
            Get device name
            @return str
        """
        return self.__name

    @property
    def progress(self):
        """
            Get progress status
            @return int
        """
        return self.__progress

#######################
# PROTECTED           #
#######################
    def _on_reveal_button_clicked(self, button):
        """
            Show advanced device options
            @param button as Gtk.Button
        """
        revealed = self.__revealer.get_reveal_child()
        self.__revealer.set_reveal_child(not revealed)
        if revealed:
            button.get_image().get_style_context().remove_class("image-reveal")
        else:
            button.get_image().get_style_context().add_class("image-reveal")

    def _on_content_albums_clicked(self, button):
        """
            Show synced albums
            @param button as Gtk.Button
        """
        index = self.__get_device_index()
        if index is not None:
            App().window.container.show_view([Type.DEVICE_ALBUMS], index)
        else:
            App().notify.send("Lollypop", _("No synchronized albums"))

    def _on_content_playlists_clicked(self, button):
        """
            Show synced playlists
            @param button as Gtk.Button
        """
        index = self.__get_device_index()
        if index is not None:
            App().window.container.show_view([Type.DEVICE_PLAYLISTS], index)
        else:
            App().notify.send("Lollypop", _("No synchronized playlists"))

    def _on_sync_button_clicked(self, button):
        """
            Sync music on device
            @param button as Gtk.Button
        """
        if self.__sync_button.get_label() == _("Synchronize"):
            self.__progress = 0
            uri = self.__get_music_uri()
            index = self.__get_device_index()
            if index is not None:
                App().task_helper.run(self.__mtp_sync.sync, uri, index)
                emit_signal(self, "syncing", True)
                button.set_label(_("Cancel"))
        else:
            self.__mtp_sync.cancel()
            button.set_sensitive(False)

    def _on_convert_toggled(self, widget):
        """
            Save option
            @param widget as Gtk.RadioButton
        """
        if widget.get_active():
            encoder = widget.get_name()
            if encoder == "convert_none":
                self.__switch_normalize.set_sensitive(False)
                self.__mtp_sync.db.set_normalize(False)
                self.__mtp_sync.db.set_encoder("convert_none")
            else:
                self.__switch_normalize.set_sensitive(True)
                self.__mtp_sync.db.set_encoder(encoder)
        self.__mtp_sync.db.save()

    def _on_normalize_state_set(self, widget, state):
        """
            Save option
            @param widget as Gtk.Switch
            @param state as bool
        """
        self.__mtp_sync.db.set_normalize(state)
        self.__mtp_sync.db.save()

    def _on_combobox_changed(self, combobox):
        """
            Update DB
            @param combobox as Gtk.ComboxText
        """
        self.__load_uri_settings(self.__get_music_uri())

#######################
# PRIVATE             #
#######################
    def __get_device_index(self):
        """
            Get current device index
            @return int/None
        """
        try:
            devices = list(App().settings.get_value("devices"))
            index = devices.index(self.__name) + 1
        except Exception as e:
            Logger.warning("DeviceWidget::__get_device_index(): %s",
                           e)
            index = None
        return index

    def __get_music_uri(self):
        """
            Get music URI on device
            @return str
        """
        if self.__combobox.get_visible():
            if self.__uri.endswith("/"):
                uri = "%s%s/Music" % (self.__uri,
                                      self.__combobox.get_active_text())
            else:
                uri = "%s/%s/Music" % (self.__uri,
                                       self.__combobox.get_active_text())
        else:
            uri = "%s/Music" % self.__uri
        return uri

    def __get_basename_for_sync(self):
        """
            Get basename base on device content
            @return str
        """
        names = []
        try:
            if not self.__uri.startswith("mtp://") and\
                    self.__name != "Librem phone":
                return None

            # Search for previous sync
            d = Gio.File.new_for_uri(self.__uri)
            infos = d.enumerate_children(
                "standard::name,standard::type",
                Gio.FileQueryInfoFlags.NONE,
                None)

            for info in infos:
                if info.get_file_type() != Gio.FileType.DIRECTORY:
                    continue
                f = infos.get_child(info)
                uri = f.get_uri() + "/Music"
                previous_sync = Gio.File.new_for_uri("%s/unsync" % uri)
                if previous_sync.query_exists():
                    names.insert(0, info.get_name())
                else:
                    names.append(info.get_name())
            infos.close(None)
        except Exception as e:
            Logger.error("DeviceWidget::__get_best_uri_for_sync: %s: %s"
                         % (self.__uri, e))
        return names

    def __set_combobox_content(self, names):
        """
            Set combobox content based on names
            @param names as [str]
        """
        if self.__combobox.get_active_text():
            return
        self.__sync_button.set_sensitive(True)
        if names is None:
            self.__load_uri_settings(self.__get_music_uri())
            self.__combobox.hide()
        elif names:
            self.__combobox.show()
            for name in names:
                self.__combobox.append_text(name)
            self.__combobox.set_active(0)
        else:
            self.__sync_button.set_sensitive(False)
            self.__combobox.hide()

    def __load_uri_settings(self, uri):
        """
            Load settings at URI
            @param uri as str
        """
        self.__mtp_sync.db.load(uri)
        encoder = self.__mtp_sync.db.encoder
        normalize = self.__mtp_sync.db.normalize
        self.__switch_normalize.set_sensitive(False)
        self.__switch_normalize.set_active(normalize)
        self.__builder.get_object(encoder).set_active(True)
        for encoder in self.__mtp_sync._GST_ENCODER.keys():
            if not self.__mtp_sync.check_encoder_status(encoder):
                self.__builder.get_object(encoder).set_sensitive(False)

    def __calculate_free_space(self):
        """
            Calculate free space on device
        """
        f = Gio.File.new_for_uri(self.__uri)
        f.query_filesystem_info_async("{},{}".format(
                                       FILE_ATTRIBUTE_FILESYSTEM_SIZE,
                                       FILE_ATTRIBUTE_FILESYSTEM_FREE),
                                      GLib.PRIORITY_DEFAULT,
                                      None,
                                      self.__on_filesystem_info)

    def __on_filesystem_info(self, source, result):
        """
            Show available space on disk
            @param source as GObject.Object
            @param result as Gio.AsyncResult
        """
        try:
            info = source.query_filesystem_info_finish(result)
            size = info.get_attribute_uint64(FILE_ATTRIBUTE_FILESYSTEM_SIZE)
            free = info.get_attribute_uint64(FILE_ATTRIBUTE_FILESYSTEM_FREE)
            if size == 0:
                return
            used = size - free
            fraction = 1 * used / size
            self.__progressbar.set_fraction(fraction)
            style_context = self.__progressbar.get_style_context()
            style_context.remove_class("usagebar-green")
            style_context.remove_class("usagebar-orange")
            style_context.remove_class("usagebar-red")
            if fraction < 0.6:
                style_context.add_class("usagebar-green")
            elif fraction < 0.8:
                style_context.add_class("usagebar-orange")
            else:
                style_context.add_class("usagebar-red")
        except Exception as e:
            Logger.error("DeviceWiget::__on_filesystem_info(): %s", e)

    def __on_sync_progress(self, mtp_sync, value):
        """
            Update progress bar
            @param mtp_sync as MtpSync
            @param value as float
        """
        self.__progress = value

    def __on_sync_finished(self, mtp_sync):
        """
            Emit finished signal
            @param mtp_sync as MtpSync
        """
        emit_signal(self, "syncing", False)
        self.__progress = 0
        self.__sync_button.set_label(_("Synchronize"))
        self.__sync_button.set_sensitive(True)
        self.__calculate_free_space()

    def __on_map(self, widget):
        """
            Setup combobox
            @param widget as Gtk.Widget
        """
        App().task_helper.run(self.__get_basename_for_sync,
                              callback=(self.__set_combobox_content,))

    def __on_destroy(self, widget):
        """
            Remove ref cycle
            @param widget as Gtk.Widget
        """
        self.__builder = None
