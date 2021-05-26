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

from gi.repository import Gtk


class GesturesHelper():
    """
        Helper for gesture on widgets
    """

    def __init__(self, widget, primary_long_callback=None,
                 secondary_long_callback=None,
                 primary_press_callback=None,
                 secondary_press_callback=None,
                 tertiary_press_callback=None):
        """
            Init helper
            @param widget as Gtk.Widget
            @params as callbacks
        """
        self.__widget = widget
        self.__allow_multi_released = False
        widget.connect("destroy", self.__on_destroy)
        self.__primary_long_callback = primary_long_callback
        self.__secondary_long_callback = secondary_long_callback
        self.__primary_press_callback = primary_press_callback
        self.__secondary_press_callback = secondary_press_callback
        self.__tertiary_press_callback = tertiary_press_callback
        self.__long_press = Gtk.GestureLongPress.new(widget)
        self.__long_press.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.__long_press.connect("pressed", self.__on_long_pressed)
        self.__long_press.connect("cancelled", self.__on_long_cancelled)
        self.__long_press.set_button(0)
        self.__multi_press = Gtk.GestureMultiPress.new(widget)
        self.__multi_press.connect("released", self.__on_multi_released)
        self.__multi_press.set_propagation_phase(Gtk.PropagationPhase.TARGET)
        self.__multi_press.set_button(0)

    def special_headerbar_hack(self):
        """
            Enable a special header bar hack to block mutter
        """
        self.__multi_press.connect("pressed", self.__on_multi_pressed)

    @property
    def widget(self):
        """
            Get widget
            @return Gtk.Widget
        """
        return self.__widget

    @property
    def multi_press_gesture(self):
        """
            Get multi press gesture
            @return Gtk.GestureMultiPress
        """
        return self.__multi_press

#######################
# PROTECTED           #
#######################
    def _on_primary_long_press_gesture(self, x, y):
        if self.__primary_long_callback is not None:
            self.__primary_long_callback(x, y)

    def _on_secondary_long_press_gesture(self, x, y):
        if self.__secondary_long_callback is not None:
            self.__secondary_long_callback(x, y)

    def _on_primary_press_gesture(self, x, y, event):
        if self.__primary_press_callback is not None:
            self.__primary_press_callback(x, y, event)

    def _on_secondary_press_gesture(self, x, y, event):
        if self.__secondary_press_callback is not None:
            self.__secondary_press_callback(x, y, event)

    def _on_tertiary_press_gesture(self, x, y, event):
        if self.__tertiary_press_callback is not None:
            self.__tertiary_press_callback(x, y, event)

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, widget):
        """
            Remove ref cycle
            @param widget as Gtk.Widget
        """
        self.__primary_long_callback = None
        self.__secondary_long_callback = None
        self.__primary_press_callback = None
        self.__secondary_press_callback = None
        self.__tertiary_press_callback = None
        self.__long_press = None
        self.__multi_press = None
        self.__widget = None

    def __on_long_pressed(self, gesture, x, y):
        """
            Run callback for long pressed
            @param gesture as Gtk.Gesture
            @param x as int
            @param y as int
        """
        if gesture.get_current_button() == 1:
            self._on_primary_long_press_gesture(x, y)
        else:
            self._on_secondary_long_press_gesture(x, y)

    def __on_long_cancelled(self, gesture):
        """
            Allow multi released
            @param gesture as Gtk.Gesture
        """
        self.__allow_multi_released = True

    def __on_multi_pressed(self, gesture, n_press, x, y):
        """
            For headerbar hack
            @param gesture as Gtk.Gesture
            @param n_press as int
            @param x as int
            @param y as int
        """
        if gesture.get_current_button() == 3:
            sequence = gesture.get_current_sequence()
            event = gesture.get_last_event(sequence)
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
            self._on_secondary_press_gesture(x, y, event)

    def __on_multi_released(self, gesture, n_press, x, y):
        """
            Check released button
            @param gesture as Gtk.Gesture
            @param n_press as int
            @param x as int
            @param y as int
        """
        if not self.__allow_multi_released:
            return
        self.__allow_multi_released = False
        sequence = gesture.get_current_sequence()
        event = gesture.get_last_event(sequence)
        if gesture.get_current_button() == 1:
            self._on_primary_press_gesture(x, y, event)
        elif gesture.get_current_button() == 2:
            self._on_tertiary_press_gesture(x, y, event)
        else:
            self._on_secondary_press_gesture(x, y, event)
