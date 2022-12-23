
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Realizes an event listener to receive events from the CCU XML-RPC API"""

# Relevant docs:
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_XmlRpc_V1_502__2_.pdf

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import, division, print_function, unicode_literals

from . import utils
from .. import actionstorage


class EventListener(utils.LogMixin, utils.CallbackMixin):

    callback_funcs = dict()

    @classmethod
    def callback(cls, cb_name, param, add_sensor_event=True):
        if add_sensor_event:
            if getattr(param, 'id', "").upper() == u"PRESS_SHORT":
                actionstorage.add_sensor_trigger_event(param)
            if getattr(param, u'id', "").upper() == u"PRESS_LONG":
                actionstorage.add_sensor_trigger_event(param, press_long=True)
            else:
                value = getattr(param, u'VALUEX', None)
                actionstorage.add_sensor_event(param, value)
        cls.callback_funcs[cb_name][param.channel.address](param)
