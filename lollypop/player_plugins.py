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

from gi.repository import Gst

from lollypop.define import App, ReplayGain
from lollypop.logger import Logger


class PluginsPlayer:
    """
        Replay gain player
    """

    __EQUALIZER = [55, 77, 110, 156, 220, 311, 440, 622,
                   880, 1200, 1800, 2500, 3500, 5000, 7000,
                   10000, 14000, 20000]

    def __init__(self, playbin):
        """
            Init playbin
            @param playbin as Gst.bin
        """
        self.__equalizer = None
        self.__playbin = playbin
        self.build_audiofilter()

    def build_audiofilter(self):
        """
            Build audio filter
            audioconvert ! (rgvolume ! rglimiter ! audioconvert) !
            (equalizer) ! volume ! audioconvert ! audiosink
        """
        try:
            audiobin = Gst.ElementFactory.make("bin", None)
            audioconvert_in = Gst.ElementFactory.make("audioconvert", None)
            audiobin.add(audioconvert_in)
            # Replay gain
            replay_gain = App().settings.get_enum(
                "replay-gain") != ReplayGain.NONE
            if replay_gain:
                rgvolume = Gst.ElementFactory.make("rgvolume", None)
                rglimiter = Gst.ElementFactory.make("rglimiter", None)
                audioconvert_rg = Gst.ElementFactory.make("audioconvert", None)
                audiobin.add(rgvolume)
                audiobin.add(rglimiter)
                audiobin.add(audioconvert_rg)
                audioconvert_in.link(rgvolume)
                rgvolume.link(rglimiter)
                rglimiter.link(audioconvert_rg)
                if replay_gain == ReplayGain.ALBUM:
                    rgvolume.props.album_mode = 1
                else:
                    rgvolume.props.album_mode = 0
                rgvolume.props.pre_amp = App().settings.get_value(
                    "replay-gain-db").get_double()
                rglimiter.props.enabled = App().settings.get_value(
                    "replay-gain-limiter")

            # Equalizer
            self.__equalizer = None
            if App().settings.get_value("equalizer-enabled"):
                self.__equalizer = Gst.ElementFactory.make("equalizer-nbands",
                                                           None)
# GStreamer's GstIirEqualizerNBands sets up shelve filters for the first and
# last bands as corner cases. That was causing the "inverted slider" bug.
# As a workaround, we create two dummy bands at both ends of the spectrum.
# This causes the actual first and last adjustable bands to be
# implemented using band-pass filters.
# Comment from Clementine source code, thanks Clementine devs!
                self.__equalizer.set_property("num-bands", 18 + 2)
                for idx in [0, 19]:
                    band = self.__equalizer.get_child_by_index(idx)
                    band.set_property("freq", 0)
                    band.set_property("bandwidth", 0)
                    band.set_property("gain", 0)
                # Setup bandwidth, thanks again to Clementine project
                last_band_freq = 0
                for idx in range(1, 19):
                    band = self.__equalizer.get_child_by_index(idx)
                    freq = self.__EQUALIZER[idx - 1]
                    bandwidth = freq - last_band_freq
                    last_band_freq = freq
                    band.set_property("bandwidth", bandwidth)
                audiobin.add(self.__equalizer)
                if replay_gain:
                    audioconvert_rg.link(self.__equalizer)
                else:
                    audioconvert_in.link(self.__equalizer)

            # Internal volume manager
            self.volume = Gst.ElementFactory.make("volume", None)
            self.volume.props.volume = 1.0
            audiobin.add(self.volume)
            if self.__equalizer is not None:
                self.__equalizer.link(self.volume)
            elif replay_gain:
                audioconvert_rg.link(self.volume)
            else:
                audioconvert_in.link(self.volume)

            audiosink = Gst.ElementFactory.make("autoaudiosink", None)
            audiobin.add(audiosink)
            self.volume.link(audiosink)
            audiobin.add_pad(Gst.GhostPad.new(
                "sink",
                audioconvert_in.get_static_pad("sink")))
            self.__playbin.set_property("audio-sink", audiobin)
            if self.__equalizer is not None:
                self.update_equalizer()
        except Exception as e:
            Logger.error("PluginsPlayer::init():", e)

    def update_equalizer(self):
        """
            Update equalizer based on current settings
        """
        i = 0
        for value in App().settings.get_value("equalizer"):
            self.set_equalizer(i, value)
            i += 1

    def set_equalizer(self, index, value):
        """
            Set band value
            @param index as int
            @param value as int
        """
        try:
            if self.__equalizer is not None:
                band = self.__equalizer.get_child_by_index(index + 1)
                band.set_property("freq", self.__EQUALIZER[index])
                band.set_property("gain", value)
        except Exception as e:
            Logger.error("PluginsPlayer::set_equalizer():", e)

#######################
# PRIVATE             #
#######################
