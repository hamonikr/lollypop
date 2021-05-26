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

from gi.repository import Gtk, Gio, GObject, GLib

from lollypop.define import App
from lollypop.utils import is_device, emit_signal
from lollypop.widgets_popover import Popover


class DevicesPopover(Popover):
    """
        Popover with connected devices
    """

    __gsignals__ = {
        "content-changed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, progressbar):
        """
            Init popover
            @param progressbar Gtk.ProgressBar
        """
        Popover.__init__(self, False)
        self.__syncing = 0
        self.__timeout_id = None
        self.__progressbar = progressbar
        self.__scrolled = Gtk.ScrolledWindow()
        self.__scrolled.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)
        self.__scrolled.show()
        self.__viewport = Gtk.Viewport()
        self.__viewport.set_margin_start(5)
        self.__viewport.set_margin_end(5)
        self.__viewport.set_margin_top(5)
        self.__viewport.set_margin_bottom(5)
        self.__scrolled.add(self.__viewport)
        self.__viewport.show()
        self.__listbox = Gtk.ListBox()
        self.__listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        # Volume manager
        self.__vm = Gio.VolumeMonitor.get()
        self.__vm.connect("mount-added", self.__on_mount_added)
        self.__vm.connect("mount-removed", self.__on_mount_removed)
        self.__viewport.add(self.__listbox)
        self.add(self.__scrolled)

    def populate(self):
        """
            Populate widget with current available devices
        """
        for mount in self.__vm.get_mounts():
            self.__add_device(mount)

    def add_fake_phone(self):
        """
            Add a fake phone device
        """
        from lollypop.widgets_device import DeviceWidget
        name = "Librem phone"
        uri = "file:///tmp/librem/"
        d = Gio.File.new_for_uri(uri + "Internal Memory")
        if not d.query_exists():
            d.make_directory_with_parents()
        d = Gio.File.new_for_uri(uri + "SD Card")
        if not d.query_exists():
            d.make_directory_with_parents()
        widget = DeviceWidget(name, uri)
        widget.connect("syncing", self.__on_syncing)
        widget.connect("size-allocate", self.__on_size_allocate)
        widget.show()
        self.__listbox.add(widget)
        self.__listbox.show()
        emit_signal(self, "content-changed",
                    len(self.__listbox.get_children()))

    @property
    def devices(self):
        """
            Get current devices
            @return [str]
        """
        return [child.name for child in self.__listbox.get_children()]

#######################
# PROTECTED           #
#######################
    def _on_button_clicked(self, button):
        """
            Hide popover
            @param button as Gtk.Button
        """
        self.hide()

    def _on_volume_value_changed(self, scale):
        """
            Set volume
            @param scale as Gtk.Scale
        """
        new_volume = scale.get_value()
        if new_volume != App().player.volume:
            App().player.set_volume(scale.get_value())

#######################
# PRIVATE             #
#######################
    def __add_device(self, mount):
        """
            Add a device
            @param mount as Gio.Mount
        """
        if is_device(mount):
            from lollypop.widgets_device import DeviceWidget
            name = mount.get_name()
            uri = mount.get_default_location().get_uri()
            if mount.get_volume() is not None:
                icon = mount.get_volume().get_symbolic_icon()
            else:
                icon = None
            widget = DeviceWidget(name, uri, icon)
            widget.connect("syncing", self.__on_syncing)
            widget.connect("size-allocate", self.__on_size_allocate)
            widget.show()
            self.__listbox.add(widget)
            self.__listbox.show()
        emit_signal(self, "content-changed",
                    len(self.__listbox.get_children()))

    def __remove_device(self, mount):
        """
            Remove volume from device list
            @param mount as Gio.Mount
        """
        uri = mount.get_default_location().get_uri()
        for widget in self.__listbox.get_children():
            if widget.uri == uri:
                widget.disconnect_by_func(self.__on_syncing)
                widget.destroy()
        emit_signal(self, "content-changed",
                    len(self.__listbox.get_children()))

    def __update_progress(self):
        """
            Update progressbar
        """
        progress = 0.0
        nb_syncs = 0
        for row in self.__listbox.get_children():
            nb_syncs += 1
            progress += row.progress
        if nb_syncs:
            value = progress / nb_syncs
            self.__progressbar.set_fraction(value)
        return True

    def __on_mount_added(self, vm, mount):
        """
            On volume mounter
            @param vm as Gio.VolumeMonitor
            @param mount as Gio.Mount
        """
        self.__add_device(mount)

    def __on_mount_removed(self, vm, mount):
        """
            On volume removed, clean selection list
            @param vm as Gio.VolumeMonitor
            @param mount as Gio.Mount
        """
        self.__remove_device(mount)

    def __on_size_allocate(self, widget, allocation):
        """
            Show scrollbar if needed
            @param widget as Gtk.Widget
            @param allocation as Gtk.Allocation
        """
        height = 10
        for child in self.__listbox.get_children():
            if child.is_visible():
                height += child.get_allocated_height()
        self.__scrolled.set_size_request(300, min(400, height))

    def __on_syncing(self, widget, status):
        """
            Start/stop progress status
            @param widget as Gtk.Widget
            @param status as bool
        """
        def hide_progress():
            if self.__timeout_id is None:
                self.__progressbar.hide()

        if status:
            self.__syncing += 1
        else:
            self.__syncing -= 1
        if self.__syncing > 0 and self.__timeout_id is None:
            self.__progressbar.set_fraction(0)
            self.__progressbar.show()
            self.__timeout_id = GLib.timeout_add(1000,
                                                 self.__update_progress)
        elif self.__syncing == 0 and self.__timeout_id is not None:
            GLib.timeout_add(1000, hide_progress)
            GLib.source_remove(self.__timeout_id)
            self.__timeout_id = None
            self.__progressbar.set_fraction(1)
