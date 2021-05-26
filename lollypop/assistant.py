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

from gi.repository import Gtk, Gdk, Handy

from gettext import gettext as _

from lollypop.define import App, MARGIN


class Assistant(Handy.Window):
    """
        Dialog showing an assistant
        rules:
        [
            {
                "title": "plop" ,
                "icon_name": "folder",
                "markup": "sdmlqkdsqmkl",
                "uri_label": "flmdks",
                "uri": "http://....."
                "right_button_label": "Cancel",
                "right_button_style": "",
                "left_button_label": "Next",
                "left_button_style: "suggested-action"
            },
        ]
    """

    def __init__(self, rules):
        """
            Init assistant
            @param rules as {}
        """
        Handy.Window.__init__(self)
        self.__rules = rules
        self.__right_button = Gtk.Button.new()
        self.__right_button.show()
        self.__right_button.connect("clicked", self.__on_right_button_clicked)
        self.__left_button = Gtk.Button.new()
        self.__left_button.show()
        self.__left_button.connect("clicked", self.__on_left_button_clicked)
        self.__headerbar = Gtk.HeaderBar()
        self.__headerbar.show()
        self.__headerbar.pack_start(self.__right_button)
        self.__headerbar.pack_end(self.__left_button)
        self.__stack = Gtk.Stack.new()
        self.__stack.show()
        self.__stack.set_property("margin", MARGIN)
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        box.show()
        box.add(self.__headerbar)
        box.add(self.__stack)
        self.add(box)
        for rule in rules:
            page = self.__get_page(rule["icon_name"],
                                   rule["markup"],
                                   rule["uri_label"],
                                   rule["uri"])
            self.__stack.add_named(page, rule["title"])
        self.__set_page_visible(0)

    def update_uri(self, uri, index):
        """
            Update page URI at index
            @param uri as str
            @param index as int
        """
        self.__rules[index]["uri"] = uri

#######################
# PRIVATE             #
#######################
    def __set_page_visible(self, index):
        """
            Set page at index visible
            @param index as int
        """
        # Reset styles
        if index > 0:
            if self.__rules[index - 1]["left_button_style"] is not None:
                self.__left_button.get_style_context().remove_class(
                    self.__rules[index - 1]["left_button_style"])
            if self.__rules[index - 1]["right_button_style"] is not None:
                self.__left_button.get_style_context().remove_class(
                    self.__rules[index - 1]["right_button_style"])

        children = self.__stack.get_children()
        if index < len(children):
            self.__stack.set_visible_child(children[index])
            self.__headerbar.set_title(self.__rules[index]["title"])
            self.__left_button.set_label(
                self.__rules[index]["left_button_label"])
            if self.__rules[index]["right_button_label"] is None:
                self.__right_button.hide()
            else:
                self.__right_button.show()
                self.__right_button.set_label(
                    self.__rules[index]["right_button_label"])
            if self.__rules[index]["left_button_style"] is not None:
                self.__left_button.get_style_context().add_class(
                    self.__rules[index]["left_button_style"])
            if self.__rules[index]["right_button_style"] is not None:
                self.__left_button.get_style_context().add_class(
                    self.__rules[index]["right_button_style"])

    def __on_right_button_clicked(self, button):
        """
            Got back in stack
            @param button as Gtk.Button
        """
        visible = self.__stack.get_visible_child()
        index = self.__stack.get_children().index(visible)
        if index == 0:
            self.destroy()
        else:
            self.__set_page_visible(index - 1)

    def __on_left_button_clicked(self, button):
        """
            Got forward in stack
            @param button as Gtk.Button
        """
        visible = self.__stack.get_visible_child()
        index = self.__stack.get_children().index(visible)
        if index + 1 == len(self.__stack.get_children()):
            self.destroy()
        else:
            self.__set_page_visible(index + 1)

    def __on_uri_button_clicked(self, button):
        """
            Launch URI
            @param button as Gtk.Button
        """
        visible = self.__stack.get_visible_child()
        index = self.__stack.get_children().index(visible)
        uri = self.__rules[index]["uri"]
        if uri == "":
            button.set_label(_("Can't contact this service"))
            button.set_sensitive(False)
            self.__left_button.set_label(_("Finish"))
            self.__right_button.set_sensitive(False)
            for child in self.__stack.get_children()[index + 1:]:
                self.__stack.remove(child)
        Gtk.show_uri_on_window(App().window, uri, Gdk.CURRENT_TIME)

    def __get_page(self, icon_name, markup, uri_label, uri):
        """
            Get a new page
            @param icon_name as str
            @param text as str
            @param uri as str
        """
        grid = Gtk.Grid()
        grid.set_property("expand", True)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_row_spacing(20)
        grid.set_property("margin", 20)
        grid.set_orientation(Gtk.Orientation.VERTICAL)
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        image.set_valign(Gtk.Align.START)
        label = Gtk.Label()
        label.set_markup(markup)
        grid.add(image)
        grid.add(label)
        if uri is not None:
            button = Gtk.Button.new_with_label(uri_label)
            button.connect("clicked", self.__on_uri_button_clicked)
            button.get_style_context().add_class("suggested-action")
            grid.add(button)
        grid.show_all()
        return grid
