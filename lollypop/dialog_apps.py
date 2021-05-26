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

from gi.repository import Gtk, Gio, GLib
from gi.repository.Gio import FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE

import json
from gettext import gettext as _

from lollypop.define import App, MARGIN_MEDIUM, MARGIN
from lollypop.logger import Logger


class AppListBoxRow(Gtk.ListBoxRow):
    """
        An application row
    """

    def __init__(self, app):
        """
            Init row
            @param app as Gio.AppInfo
        """
        Gtk.ListBoxRow.__init__(self)
        self.__app = app
        label = Gtk.Label.new(app.get_name())
        label.show()
        artwork = Gtk.Image.new_from_gicon(app.get_icon(), Gtk.IconSize.DIALOG)
        artwork.show()
        grid = Gtk.Grid.new()
        grid.show()
        grid.set_column_spacing(MARGIN)
        grid.add(artwork)
        grid.add(label)
        self.add(grid)

    @property
    def app(self):
        """
            Get app
            @return Gio.AppInfo
        """
        return self.__app


class AppsDialog(Gtk.Dialog):
    """
        Dialog showing apps for file
    """

    def __init__(self, f):
        """
            Init dialog
            @param f as Gio.File
        """
        Gtk.Dialog.__init__(self)
        self.__commandline = None
        self.__open_with = {}
        self.set_size_request(300, 300)
        self.set_transient_for(App().window)
        cancel_button = Gtk.Button.new_with_label(_("Cancel"))
        cancel_button.show()
        cancel_button.get_style_context().add_class("text-label")
        select_button = Gtk.Button.new_with_label(_("Select"))
        select_button.show()
        select_button.get_style_context().add_class("text-label")
        select_button.get_style_context().add_class("suggested-action")
        headerbar = Gtk.HeaderBar.new()
        headerbar.show()
        headerbar.pack_start(cancel_button)
        headerbar.pack_end(select_button)
        headerbar.set_title(_("Select an application"))
        self.set_titlebar(headerbar)
        self.__listbox = Gtk.ListBox.new()
        self.__listbox.show()
        self.__listbox.set_activate_on_single_click(False)
        self.__listbox.connect("row-selected", self.__on_row_selected)
        self.__listbox.set_sort_func(self.__sort)
        scrolled = Gtk.ScrolledWindow.new()
        scrolled.show()
        scrolled.add(self.__listbox)
        scrolled.set_property("expand", True)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        self.get_content_area().set_property("margin", MARGIN_MEDIUM)
        self.get_content_area().add(scrolled)
        cancel_button.connect("clicked",
                              lambda x: self.response(Gtk.ResponseType.CLOSE))
        select_button.connect("clicked",
                              lambda x: self.response(Gtk.ResponseType.OK))
        self.__listbox.connect("row-activated",
                               lambda x, y: self.response(Gtk.ResponseType.OK))

        try:
            info = f.query_info("%s" % FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
                                Gio.FileQueryInfoFlags.NONE,
                                None)
            content_type = info.get_content_type()
            self.__last_app = self.__get_last_app(content_type)
            self.connect("response", self.__on_response, content_type)
            # Set apps
            for app in Gio.AppInfo.get_all_for_type(content_type):
                if not app.get_commandline().startswith("lollypop"):
                    row = AppListBoxRow(app)
                    row.show()
                    self.__listbox.add(row)
        except Exception as e:
            Logger.error("AppsDialog::__init__(): %s", e)

    @property
    def commandline(self):
        """
            Get current commandline for dialog
            @return str/None
        """
        return self.__commandline

#######################
# PRIVATE             #
#######################
    def __get_last_app(self, content_type):
        """
            Get last application for content_type
            @param content_type as str
            @return str/None
        """
        try:
            json_data = App().settings.get_value("open-with").get_string()
            if json_data:
                self.__open_with = json.loads(json_data)
                return self.__open_with[content_type]
        except Exception as e:
            Logger.error("AppsDialog::__get_last_app(): %s", e)
            App().settings.set_value("open-with", GLib.Variant("s", ""))
        return None

    def __sort(self, row_a, row_b):
        """
            Sort function to always show last selected item
            @param row_a as AppListBoxRow
            @param row_b as AppListBoxRow
            @return bool
        """
        if row_b.app.get_commandline() == self.__last_app:
            return True
        return False

    def __on_response(self, dialog, response_id, content_type):
        """
            Save currently selected item
            @param dialog as Gtk.Dialog
            @param response_id as Gtk.ResponseType
            @param content_type as str
        """
        if response_id == Gtk.ResponseType.OK:
            if dialog.commandline is not None:
                self.__open_with[content_type] = dialog.commandline
                data = json.dumps(self.__open_with)
                App().settings.set_value("open-with",
                                         GLib.Variant("s", data))

    def __on_row_selected(self, listbox, row):
        """
            Set current commandline
            @param listbox as Gtk.ListBox
            @param row as AppListBoxRow
        """
        if row is None:
            self.__commandline = None
        else:
            self.__commandline = row.app.get_commandline()
