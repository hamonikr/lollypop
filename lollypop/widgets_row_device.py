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

from gi.repository import Gtk, GLib, Pango, Handy


from lollypop.define import App


class DeviceRow(Handy.ActionRow):
    """
        A device row
    """

    def __init__(self, name):
        """
            Init row
            @param name as str
        """
        Handy.ActionRow.__init__(self)
        self.__name = name
        label = Gtk.Label.new(name)
        label.set_property("halign", Gtk.Align.START)
        label.set_hexpand(True)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.show()
        button = Gtk.Button.new_from_icon_name("user-trash-symbolic",
                                               Gtk.IconSize.BUTTON)
        button.connect("clicked", self.__on_button_clicked)
        button.get_style_context().add_class("menu-button")
        button.show()
        button.set_valign(Gtk.Align.CENTER)
        self.add(label)
        self.add(button)
        self.show()

#######################
# PRIVATE             #
#######################
    def __on_button_clicked(self, button):
        """
            Remove device
            @param button as Gtk.Button
        """
        if button.get_image().get_style_context().has_class("red"):
            devices = list(App().settings.get_value("devices"))
            if self.__name in devices:
                index = devices.index(self.__name)
                devices.remove(self.__name)
                App().settings.set_value("devices",
                                         GLib.Variant("as", devices))
                App().albums.remove_device(index + 1)
                App().playlists.remove_device(index + 1)
            self.destroy()
        else:
            button.get_image().get_style_context().add_class("red")
