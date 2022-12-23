
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

# Relevant docs:
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_XmlRpc_V1_502__2_.pdf
# - http://www.eq-3.de/Downloads/eq3/download%20bereich/hm_web_ui_doku/hm_devices_Endkunden.pdf

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#import threading

try:
    from builtins import object # pylint:disable=redefined-builtin
except ImportError:
    pass

#from . import params  # @UnusedImport
from . import utils
from .exceptions import PMException


class Entity(object):
    _transform_attributes = {}
    _skip_attributes = []
    _mandatory_attributes = []
    
    def __init__(self, ccu, spec):
        super(Entity, self).__init__()
        self._ccu = ccu
        self._set_attributes(spec)
        super(Entity, self).__init__()


    def _set_attributes(self, obj_dict):
        """Adding provided attributes to this entity.

        Transforming and filtering dictionaries containing attributes for this entity
        by using the configured transform methods for the individual attributes and also
        excluding some attributes which keys are in self._skip_attributes."""
        for key, val in obj_dict.items():
            if key in self._skip_attributes:
                continue

            # Optionally convert values using the given transform functions
            # for the specific object type
            trans_func = self._transform_attributes.get(key)
            if trans_func:
                func_type = type(trans_func).__name__
                if func_type in [ "instancemethod", "function", "method" ]:
                    args = []
                    offset = 1 if func_type in [ "instancemethod", "method" ] else 0
                    argcount = trans_func.__code__.co_argcount
                    for arg_name in trans_func.__code__.co_varnames[offset:argcount]:
                        if arg_name == "api":
                            args.append(self._ccu.api)
                        elif arg_name == "ccu":
                            args.append(self._ccu)
                        elif arg_name == "device":
                            args.append(self)
                        elif arg_name == "obj":
                            args.append(self)
                        else:
                            args.append(val)
                else:
                    args = [val]

                val = trans_func(*args)

            # Transform keys from camel case to our style
            key = utils.decamel(key)

            setattr(self, key, val)


class Channels(dict):
    def __iter__(self):
        return iter(sorted(self.values(), key=lambda x: x.index))


class Channel(utils.LogMixin, Entity):
    _transform_attributes = {
        # ReGa attributes:
        "id"               : int,
        "partner_id"       : lambda x: None if x == "" else int(x),
        # Low level attributes:
        "aes_active"        : bool,
        "link_source_roles" : lambda v: v if isinstance(v, list) else v.split(" "),
        "link_target_roles" : lambda v: v if isinstance(v, list) else v.split(" "),
    }

    # Don't add these keys to the objects attributes
    _skip_attributes = [
        # Low level attributes:
        "parent",
        "parent_type",
    ]

    # These keys have to be set after attribute initialization
    _mandatory_attributes = [
        # Low level attributes:

        # address of channel
        "address",
        # communication direction of channel:
        # 0 = DIRECTION_NONE (Kanal unterstützt keine direkte Verknüpfung)
        # 1 = DIRECTION_SENDER
        # 2 = DIRECTION_RECEIVER
        "direction",
        # see device flags (0x01 visible, 0x02 internal, 0x08 can not be deleted)
        "flags",
        # channel number
        "index",
        # possible roles as sender
        "link_source_roles",
        # possible roles as receiver
        "link_target_roles",
        # list of available parameter sets
        "paramsets",
        # type of this channel
        "type",
        # version of the channel description
        "version",
    ]

    def __init__(self, device, spec):
        if not isinstance(device, Device):
            raise PMException("Device object is not a Device derived class: %r" % device)
        self.device = device
        self._values = {}

        self._callbacks_to_register = {
            "value_updated": [],
            "value_changed": [],
        }

        super(Channel, self).__init__(device._ccu, spec)


    @classmethod
    def from_channel_dicts(cls, device, channel_dicts):
        """Creates channel instances associated with the given *device* instance from the given
        attribute dictionaries.

        Uses the list of channel attribute dictionaries given with *channel_dicts* to create a
        dictionary of specific `Channel` instances (like e.g. :class:`ChannelShutterContact`)
        or the generic :class:`Channel` class. Normally each channel should have a specific
        class. In case an unknown channel needs to be created a debug message is being logged.
        The dictionary uses the index of the channel (the channel id) as key for entries.

        The dictionary of the created channels is then returned."""
        channel_objects = Channels()
        for channel_dict in channel_dicts:
            channel_class = channel_classes_by_type_name.get(channel_dict["type"], Channel)

            if channel_class == Channel:
                cls.cls_logger().debug("Using generic Channel class (Type: %s): %r" %
                                                    (channel_dict["type"], channel_dict))

            channel_objects[channel_dict["index"]] = channel_class(device, channel_dict)
        return channel_objects
    @property
    def values(self):
        return self._values

    @property
    def summary_state(self):
        formated = []
        for title, value in sorted([ (v.name, v) for v in self.values.values() if v.readable ]):
            formated.append("%s: %s" % (title, value))
        return ", ".join(formated)

    def on_value_changed(self, func):
        from . import events
        callback_funcs = events.EventListener.callback_funcs
        if not u"value_changed" in callback_funcs:
            callback_funcs[u"value_changed"] = dict()
        callback_funcs[u"value_changed"][self.address] = func

    def on_value_updated(self, func):
        """Register a function to be called each time a value of this channel parameters has
        been updated."""
        from . import events
        callback_funcs = events.EventListener.callback_funcs
        if not u"value_updated" in callback_funcs:
            callback_funcs[u"value_updated"] = dict()
        callback_funcs[u"value_updated"][self.address] = func


# FIXME: Implement this. The Device() object already has a lot of methods
# related to the maintenance channel. Shouldn't they be moved here and evantually
# only be available as shortcut in the Device object?
class ChannelMaintenance(Channel):
    type_name = "MAINTENANCE"
    name = "Maintenance"
    id = 0

    @property
    def summary_state(self):
        """The maintenance channel does not provide a summary state.

        If you want to get a formated maintenance state, you need to use the property
        :attr:`maintenance_state`."""
        return None


    @property
    def maintenance_state(self):
        """Provides the formated maintenance state of the associated device."""
        return super(ChannelMaintenance, self).summary_state



# FIXME: Handle LOWBAT/ERROR
class ChannelShutterContact(Channel):
    type_name = "SHUTTER_CONTACT"

    @property
    def is_open(self):
        """``True`` when the contact is reported to be open, otherwise ``False``."""
        return self.values["STATE"].value


    @property
    def summary_state(self):
        """Provides a well formated state as string. It is ``open`` when the contact
        is open, otherwise ``closed``."""
        return self.is_open and "open" or "closed"



# FIXME: Handle STOP, INHIBIT, INSTALL_TEST
class ChannelBlind(Channel):
    type_name = "BLIND"

    @property
    def level(self):
        """Look up the level at which the shutter is set."""
        return self.values["LEVEL"].value

    def set_level(self, level):
        """Set the level at which the shutter is to be set."""
        return self.values["LEVEL"].set(level)

    @property
    def working(self):
        """Look up the WORKING value."""
        return self.values["WORKING"].value



# FIXME: Handle INHIBIT, WORKING
class ChannelSwitch(Channel):
    type_name = "SWITCH"

    @property
    def is_on(self):
        """``True`` when the power is on, otherwise ``False``."""
        return self.values["STATE"].value


    @property
    def summary_state(self):
        """Provides the current state as well formated string."""
        return "%s: %s" % (self.values["STATE"].name, self.is_on and "on" or "off")


    def toggle(self):
        """Use this to toggle the switch."""
        if self.is_on:
            return self.switch_off()
        else:
            return self.switch_on()


    def switch_off(self):
        """Power off!"""
        return self.values["STATE"].set(False)


    def switch_on(self):
        """Lights on!"""
        return self.values["STATE"].set(True)



# FIXME: Handle LED_STATUS, ALL_LEDS, LED_SLEEP_MODE, INSTALL_TEST
class ChannelKey(Channel):
    type_name = "KEY"

    def press_short(self):
        """Call this to trigger a short press."""
        return self.values["PRESS_SHORT"].set(True)


    def press_long(self):
        """Triggers a long press."""
        return self.values["PRESS_LONG"].set(True)


    # Not verified working
    def press_long_release(self):
        """Triggers the release of a long press."""
        return self.values["PRESS_LONG_RELEASE"].set(True)


    # Not verified
    def press_cont(self):
        """Unknown. Untested. Please let me know what this is."""
        return self.values["PRESS_CONT"].set(True)


    @property
    def summary_state(self):
        """Has no state info as it's a toggle button. This is only to override the
        default summary_state property."""
        return None



class ChannelVirtualKey(ChannelKey):
    type_name = "VIRTUAL_KEY"



# FIXME: Handle all values:
# {u'POWER': u'3.520000', u'ENERGY_COUNTER': u'501.400000', u'BOOT': u'1',
#  u'CURRENT': u'26.000000', u'FREQUENCY': u'50.010000', u'VOLTAGE': u'228.900000'}
class ChannelPowermeter(Channel):
    type_name = "POWERMETER"


# FIXME: To be implemented.
class ChannelConditionPower(Channel):
    type_name = "CONDITION_POWER"


# FIXME: To be implemented.
class ChannelConditionCurrent(Channel):
    type_name = "CONDITION_CURRENT"


# FIXME: To be implemented.
class ChannelConditionVoltage(Channel):
    type_name = "CONDITION_VOLTAGE"



# FIXME: To be implemented.
class ChannelConditionFrequency(Channel):
    type_name = "CONDITION_FREQUENCY"



# FIXME: To be implemented.
# Devices:
#   HM-Sen-LI-O
class ChannelLuxmeter(Channel):
    type_name = "LUXMETER"


# FIXME: To be implemented.
# Devices:
#   HM-WDS10-TH-O
class ChannelWeather(Channel):
    type_name = "WEATHER"



# FIXME: Handle ERROR
class ChannelClimaVentDrive(Channel):
    type_name = "CLIMATECONTROL_VENT_DRIVE"



# FIXME: Handle ADJUSTING_COMMAND, ADJUSTING_DATA
class ChannelClimaRegulator(Channel):
    type_name = "CLIMATECONTROL_REGULATOR"

    @property
    def summary_state(self):
        """Provides the ventil state."""
        val = self.values["SETPOINT"]
        if val == 0.0:
            return "Ventil closed"
        elif val == 100.0:
            return "Ventil open"
        else:
            return "Ventil: %s" % self.values["SETPOINT"]


# Devices:
#  HM-CC-RT-DN
# FIXME: Values:
# {u'SET_TEMPERATURE': u'21.500000', u'PARTY_START_MONTH': u'1', u'BATTERY_STATE': u'2.400000',
#  u'PARTY_START_DAY': u'1', u'PARTY_STOP_DAY': u'1', u'PARTY_START_YEAR': u'0',
#  u'FAULT_REPORTING': u'0', u'PARTY_STOP_TIME': u'0', u'ACTUAL_TEMPERATURE': u'23.100000',
#  u'BOOST_STATE': u'15', u'PARTY_STOP_YEAR': u'0', u'PARTY_STOP_MONTH': u'1',
#  u'VALVE_STATE': u'10', u'PARTY_START_TIME': u'450', u'PARTY_TEMPERATURE': u'5.000000',
#  u'CONTROL_MODE': u'1'}
class ChannelClimaRTTransceiver(Channel):
    type_name = "CLIMATECONTROL_RT_TRANSCEIVER"

    @property
    def summary_state(self):
        """Provides the actual and target temperature together with the valve state in
        some readable format."""
        return "Temperature: %s (Target: %s, Valve: %s)" % \
                (self.values["ACTUAL_TEMPERATURE"],
                 self.values["SET_TEMPERATURE"],
                 self.values["VALVE_STATE"])


    def _get_class_name_of_param_spec(self, param_spec):
        if param_spec["ID"] == "CONTROL_MODE":
            return "ParameterControlMode"
        else:
            return super(ChannelClimaRTTransceiver, self)._get_class_name_of_param_spec(param_spec)



class ChannelWindowSwitchReceiver(Channel):
    type_name = "WINDOW_SWITCH_RECEIVER"

    @property
    def summary_state(self):
        """Provides ``None`` since the channel has not any values"""
        return None


class ChannelWeatherReceiver(Channel):
    type_name = "WEATHER_RECEIVER"

    @property
    def summary_state(self):
        """Provides ``None`` since the channel has not any values"""
        return None


# Devices:
#  HM-CC-RT-DN
class ChannelClimateControlReceiver(Channel):
    type_name = "CLIMATECONTROL_RECEIVER"

    @property
    def summary_state(self):
        """Provides ``None`` since the channel has not any values"""
        return None


# Devices:
#  HM-CC-RT-DN
class ChannelClimateControlRTReceiver(Channel):
    type_name = "CLIMATECONTROL_RT_RECEIVER"

    @property
    def summary_state(self):
        """Provides ``None`` since the channel has not any values"""
        return None


# Devices:
#  HM-CC-RT-DN
class ChannelRemoteControlReceiver(Channel):
    type_name = "REMOTECONTROL_RECEIVER"

    @property
    def summary_state(self):
        """Provides ``None`` since the channel has not any values"""
        return None


# Devices:
#  HM-TC-IT-WM-W-EU
class ChannelWeatherTransmit(Channel):
    type_name = "WEATHER_TRANSMIT"

    @property
    def summary_state(self):
        """Provides the temperature and humidity in readable format."""
        return "Temperature: %s, Humidity: %s" % \
                (self.values["TEMPERATURE"],
                 self.values["HUMIDITY"])


# Devices:
#  HM-TC-IT-WM-W-EU
class ChannelThermalControlTransmit(Channel):
    type_name = "THERMALCONTROL_TRANSMIT"

    def _init_value_spec(self, value_spec):
        # The value PARTY_MODE_SUBMIT seems to be declared to be readable by
        # the CCU which is wrong. This value can not be read.
        # See <https://github.com/LarsMichelsen/pmatic/issues/7>.
        if value_spec["ID"] == "PARTY_MODE_SUBMIT":
            value_spec["OPERATIONS"] = "2"
        super(ChannelThermalControlTransmit, self)._init_value_spec(value_spec)


    def _get_values(self):
        # This is needed to not let the CCU decide which values to be read from
        # the device because of the bug mentioned above.
        return self._get_values_single()


# Devices:
#  HM-TC-IT-WM-W-EU
class ChannelSwitchTransmit(Channel):
    type_name = "SWITCH_TRANSMIT"

    def _init_value_spec(self, value_spec):
        # The value SWITCH_TRANSMIT seems to be declared to be readable by
        # the CCU which is wrong. This value can not be read.
        # See <https://github.com/LarsMichelsen/pmatic/issues/7>.
        if value_spec["ID"] == "DECISION_VALUE":
            value_spec["OPERATIONS"] = "4" # only supports events
        super(ChannelSwitchTransmit, self)._init_value_spec(value_spec)


    def _get_values(self):
        # This is needed to not let the CCU decide which values to be read from
        # the device because of the bug mentioned above.
        return self._get_values_single()
    

class Devices(object):
    """Manages a collection of CCU devices."""
    def __init__(self, ccu):
        super(Devices, self).__init__()
        self._ccu = ccu
        self._device_dict = {}

    @property
    def _devices(self):
        """Optional initializer of the devices data structure, called on first access."""
        return self._device_dict

    def get(self, address, deflt=None):
        return self._devices.get(address, deflt)

    def add(self, device):
        self._devices[device.address] = device

    def exists(self, address):
        return address in self._devices

    def addresses(self):
        return self._devices.keys()

    def delete(self, address):
        try:
            del self._devices[address]
        except KeyError:
            pass

    def clear(self):
        self._devices.clear()

    def get_device_or_channel_by_address(self, address):
        if ":" in address:
            device_address = address.split(":", 1)[0]
            return self._devices[device_address].channel_by_address(address)
        else:
            return self._devices[address]

    def on_value_changed(self, func):
        """Register a function to be called each time a value of a device in this
        collection changed."""
        for device in self._devices.values():
            device.on_value_changed(func)

    def on_value_updated(self, func):
        """Register a function to be called each time a value of a device in this
        collection updated."""
        for device in self._devices.values():
            device.on_value_updated(func)

    def __iter__(self):
        """Provides an iterator over the devices of this collection."""
        for value in self._devices.values():
            yield value

    def __len__(self):
        """Is e.g. used by :func:`len`. Returns the number of devices in this collection."""
        return len(self._devices)


# FIXME: self.channels[0]: Provide better access to the channels. e.g. by names or ids or similar
class Device(Entity):

    def __init__(self, ccu, spec):
        super(Device, self).__init__(ccu, spec)


    @classmethod
    def from_dict(self, ccu, spec):
        """Creates a new device object from the attributes given in the *spec* dictionary.

        The *spec* dictionary needs to contain the mandatory attributes with values of the correct
        format. Depending on the device type specified by the *spec* dictionary, either a specific
        device class or the generic :class:`Device` class is used to create the object."""
        device_class = device_classes_by_type_name.get(spec["type"], Device)
        device = device_class(ccu, spec)
        #         del spec["type"]
        #         for k, v in spec:
        #             setattr(device, k, v)
        return device


    # {u'UNREACH': u'1', u'AES_KEY': u'1', u'UPDATE_PENDING': u'1', u'RSSI_PEER': u'-65535',
    #  u'LOWBAT': u'0', u'STICKY_UNREACH': u'1', u'DEVICE_IN_BOOTLOADER': u'0',
    #  u'CONFIG_PENDING': u'0', u'RSSI_DEVICE': u'-65535', u'DUTYCYCLE': u'0'}
    @property
    def maintenance(self):
        """Returns the :class:`ChannelMaintenance` object of this device. It provides
        access to generic maintenance information available on this device."""
        return self.channels[0]


    def set_logic_attributes(self, attrs):
        """Used to update the logic attributes of this device.

        Applying the attributes in the dictionary to this object. Special handling
        for some attributes which are already set by the low level attributes and
        for the channel attributes which are also part of attrs."""
        for channel_attrs in attrs["channels"]:
            self.channels[channel_attrs["index"]].set_logic_attributes(channel_attrs)

        # Skip non needed attributes (already set by low level data)
        attrs = attrs.copy()
        del attrs["channels"]
        del attrs["address"]
        del attrs["interface"]
        del attrs["type"]
        self._set_attributes(attrs)

    @property
    def is_online(self):
        """Is ``True`` when the device is currently reachable. Otherwise it is ``False``."""
        if self.type == "HM-RCV-50":
            return True # CCU is always assumed to be online
        else:
            return not self.maintenance.values["UNREACH"].value

    @property
    def has_pending_config(self):
        """Is ``True`` when the CCU has pending configuration changes for this device.
        Otherwise it is ``False``."""
        if self.type == "HM-RCV-50":
            return False
        else:
            return self.maintenance.values["CONFIG_PENDING"].value

    @property
    def has_pending_update(self):
        """Is ``True`` when the CCU has a pending firmware update for this device.
        Otherwise it is ``False``."""
        try:
            return self.maintenance.values["UPDATE_PENDING"].value
        except KeyError:
            return False

    #{u'CONTROL': u'NONE', u'OPERATIONS': u'7', u'NAME': u'INHIBIT', u'MIN': u'0',
    # u'DEFAULT': u'0', u'MAX': u'1', u'TAB_ORDER': u'6', u'FLAGS': u'1', u'TYPE': u'BOOL',
    # u'ID': u'INHIBIT', u'UNIT': u''}
    @property
    def inhibit(self):
        """The actual inhibit state of the device.

        :getter: Whether or not the device is currently locked, provided as
                 :class:`params.ParameterBOOL`.
        :setter: Specify the new inhibit state as boolean.
        :type: :class:`params.ParameterBOOL`/bool
        """
        return self.maintenance.values["INHIBIT"]

    @inhibit.setter
    def inhibit(self, state):
        self.maintenance.values["INHIBIT"].value = state

    @property
    def summary_state(self):
        return self._get_summary_state()

    def _get_summary_state(self, skip_channel_types=None):
        return self.name

    def channel_by_address(self, address):
        """Returns the channel object having the requested address.

        When the device has no such channel, a KeyError() is raised.
        """
        for channel in self.channels:
            if address == channel.address:
                return channel
        raise KeyError("The channel could not be found on this device.")

    def on_value_changed(self, func):
        """Register a function to be called each time a value of this device has changed."""
        for channel in self.channels:
            channel.on_value_changed(func)

    def on_value_updated(self, func):
        """Register a function to be called each time a value of this device has updated."""
        for channel in self.channels:
            channel.on_value_updated(func)



# Funk-Heizkörperthermostat
# TODO:
#{u'CONTROL': u'NONE', u'OPERATIONS': u'5', u'NAME': u'FAULT_REPORTING', u'MIN': u'0',
# u'DEFAULT': u'0', u'MAX': u'7', u'VALUE_LIST': u'NO_FAULT VALVE_TIGHT
# ADJUSTING_RANGE_TOO_LARGE ADJUSTING_RANGE_TOO_SMALL COMMUNICATION_ERROR {}
# LOWBAT VALVE_ERROR_POSITION', u'TAB_ORDER': u'1', u'FLAGS': u'9',
# u'TYPE': u'ENUM', u'ID': u'FAULT_REPORTING', u'UNIT': u''}

#{u'CONTROL': u'HEATING_CONTROL.PARTY_TEMP', u'OPERATIONS': u'3', u'NAME': u'PARTY_TEMPERATURE',
# u'MIN': u'5.000000', u'DEFAULT': u'20.000000', u'MAX': u'30.000000', u'TAB_ORDER': u'13',
# u'FLAGS': u'1', u'TYPE': u'FLOAT', u'ID': u'PARTY_TEMPERATURE', u'UNIT': u'\xb0C'}
#{u'CONTROL': u'NONE', u'OPERATIONS': u'2', u'NAME': u'PARTY_MODE_SUBMIT', u'MIN': u'',
# u'DEFAULT': u'', u'MAX': u'', u'TAB_ORDER': u'12', u'FLAGS': u'1', u'TYPE': u'STRING',
# u'ID': u'PARTY_MODE_SUBMIT', u'UNIT': u''}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_START_TIME', u'OPERATIONS': u'3',
# u'NAME': u'PARTY_START_TIME', u'MIN': u'0', u'DEFAULT': u'0', u'MAX': u'1410',
# u'TAB_ORDER': u'14', u'FLAGS': u'1', u'TYPE': u'INTEGER', u'ID': u'PARTY_START_TIME',
# u'UNIT': u'minutes'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_START_DAY', u'OPERATIONS': u'3', u'NAME': u'PARTY_START_DAY',
# u'MIN': u'1', u'DEFAULT': u'1', u'MAX': u'31', u'TAB_ORDER': u'15', u'FLAGS': u'1',
# u'TYPE': u'INTEGER', u'ID': u'PARTY_START_DAY', u'UNIT': u'day'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_START_MONTH', u'OPERATIONS': u'3',
# u'NAME': u'PARTY_START_MONTH', u'MIN': u'1', u'DEFAULT': u'1', u'MAX': u'12',
# u'TAB_ORDER': u'16', u'FLAGS': u'1', u'TYPE': u'INTEGER', u'ID':
# u'PARTY_START_MONTH', u'UNIT': u'month'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_START_YEAR', u'OPERATIONS': u'3',
# u'NAME': u'PARTY_START_YEAR', u'MIN': u'0', u'DEFAULT': u'12', u'MAX': u'99',
# u'TAB_ORDER': u'17', u'FLAGS': u'1', u'TYPE': u'INTEGER', u'ID': u'PARTY_START_YEAR',
# u'UNIT': u'year'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_STOP_TIME', u'OPERATIONS': u'3',
# u'NAME': u'PARTY_STOP_TIME', u'MIN': u'0', u'DEFAULT': u'0', u'MAX': u'1410',
# u'TAB_ORDER': u'18', u'FLAGS': u'1', u'TYPE': u'INTEGER', u'ID': u'PARTY_STOP_TIME',
# u'UNIT': u'minutes'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_STOP_DAY', u'OPERATIONS': u'3', u'NAME': u'PARTY_STOP_DAY',
# u'MIN': u'1', u'DEFAULT': u'1', u'MAX': u'31', u'TAB_ORDER': u'19', u'FLAGS': u'1',
# u'TYPE': u'INTEGER', u'ID': u'PARTY_STOP_DAY', u'UNIT': u'day'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_STOP_MONTH', u'OPERATIONS': u'3', u'NAME': u'PARTY_STOP_MONTH',
# u'MIN': u'1', u'DEFAULT': u'1', u'MAX': u'12', u'TAB_ORDER': u'20', u'FLAGS': u'1',
# u'TYPE': u'INTEGER', u'ID': u'PARTY_STOP_MONTH', u'UNIT': u'month'}
#{u'CONTROL': u'HEATING_CONTROL.PARTY_STOP_YEAR', u'OPERATIONS': u'3', u'NAME': u'PARTY_STOP_YEAR',
# u'MIN': u'0', u'DEFAULT': u'12', u'MAX': u'99', u'TAB_ORDER': u'21', u'FLAGS': u'1',
# u'TYPE': u'INTEGER', u'ID': u'PARTY_STOP_YEAR', u'UNIT': u'year'}
class HM_CC_RT_DN(Device):
    type_name = "HM-CC-RT-DN"

    @property
    def temperature(self):
        """Provides the current temperature.

        Returns an instance of :class:`ParameterFLOAT`.
        """
        return self.channels[4].values["ACTUAL_TEMPERATURE"]


    #{u'CONTROL': u'NONE', u'OPERATIONS': u'5', u'NAME': u'VALVE_STATE', u'MIN': u'0',
    # u'DEFAULT': u'0', u'MAX': u'99', u'TAB_ORDER': u'3', u'FLAGS': u'1', u'TYPE': u'INTEGER',
    # u'ID': u'VALVE_STATE', u'UNIT': u'%'}
    @property
    def valve_state(self):
        """Provides the current valve state in percentage.

        Returns an instance of :class:`ParameterINTEGER`.
        """
        return self.channels[4].values["VALVE_STATE"]


    @property
    def set_temperature(self):
        """The actual set temperature of the device.

        :getter: Provides the actual target temperature as :class:`ParameterFLOAT`.
        :setter: Specify the new set temperature as float. Please note that the CCU rounds
                 this values to
                 .0 or .5 after the comma. So if you provide .e.g 22.1 as new set temperature,
                 the CCU will convert this to 22.0. This is totally equal to the control on the
                 device.
        :type: ParameterFloat/float
        """
        return self.channels[4].values["SET_TEMPERATURE"]


    @set_temperature.setter
    def set_temperature(self, target):
        self.channels[4].values["SET_TEMPERATURE"].value = target


    # {u'CONTROL': u'HEATING_CONTROL.COMFORT', u'OPERATIONS': u'2', u'NAME': u'COMFORT_MODE',
    #  u'MIN': u'0', u'DEFAULT': u'0', u'MAX': u'1', u'TAB_ORDER': u'10', u'FLAGS': u'1',
    #  u'TYPE': u'ACTION', u'ID': u'COMFORT_MODE', u'UNIT': u''}
    def set_temperature_comfort(self):
        """Sets the :attr:`set_temperature` to the configured comfort temperature"""
        self.channels[4].values["COMFORT_MODE"].value = True


    #{u'CONTROL': u'HEATING_CONTROL.LOWERING', u'OPERATIONS': u'2', u'NAME': u'LOWERING_MODE',
    # u'MIN': u'0', u'DEFAULT': u'0', u'MAX': u'1', u'TAB_ORDER': u'11', u'FLAGS': u'1',
    # u'TYPE': u'ACTION', u'ID': u'LOWERING_MODE', u'UNIT': u''}
    def set_temperature_lowering(self):
        """Sets the :attr:`set_temperature` to the configured lowering temperature"""
        self.channels[4].values["LOWERING_MODE"].value = True


    @property
    def is_off(self):
        """Is set to `True` when the device is not enabled to heat."""
        return self.channels[4].values["SET_TEMPERATURE"].value == 4.5


    def turn_off(self):
        """Call this method to tell the thermostat that it should not heat."""
        self.set_temperature = 4.5


    @property
    def control_mode(self):
        """
        The actual control mode of the device. This is either ``AUTO``, ``MANUAL``,
        ``PARTY`` or ``BOOST``.

        :getter: Provides the current control mode as :class:`ParameterENUM`.
        :setter: Set the control mode by the name of the mode (see above). When setting
                 to ``MANUAL`` it uses either the current set temperature as target
                 temperature or the default temperature when the
                 device is currently turned off.
        :type: ParameterENUM/string
        """
        return self.channels[4].values["CONTROL_MODE"]


    @control_mode.setter
    def control_mode(self, mode):
        modes = ["AUTO", "MANUAL", "PARTY", "BOOST"]
        if mode not in modes:
            raise PMException("The control mode must be one of: %s" % ", ".join(modes))

        if mode == "MANUAL":
            mode = "MANU"

        value = True

        # In manual mode the set temperature needs to be provided. Set it to the
        # current set temperature. When the set temperature is "off", use the default
        # value.
        if mode == "MANU":
            if self.is_off:
                value = self.set_temperature.default
                # Also set the set_temperature attribute
                self.set_temperature = value
            else:
                value = self.set_temperature.value

        self.channels[4].values["%s_MODE" % mode].value = value


    @property
    def is_battery_low(self):
        """Is ``True`` when the battery is reported to be low, otherwise ``False``.
        If you want more details about the current battery, use :meth:`battery_state` to get
        the current reported voltage."""
        return self.channels[4].values["FAULT_REPORTING"].formated() == "LOWBAT"


    @property
    def battery_state(self):
        """Provides the actual battery voltage reported by the device."""
        return self.channels[4].values["BATTERY_STATE"]


    # {u'CONTROL': u'NONE', u'OPERATIONS': u'5', u'NAME': u'BOOST_STATE', u'MIN': u'0',
    #  u'DEFAULT': u'0', u'MAX': u'30', u'TAB_ORDER': u'4', u'FLAGS': u'1',
    #  u'TYPE': u'INTEGER', u'ID': u'BOOST_STATE', u'UNIT': u'min'}
    @property
    def boost_duration(self):
        """When boost mode is currently active this returns the number of minutes left
        in boost mode. Otherwise it returns ``None``.

        Provides the configured boost duration as :class:`ParameterINTEGER`.
        """
        if self.control_mode == "BOOST":
            return self.channels[4].values["BOOST_STATE"]



# Funk-Temperatur-/Luftfeuchtesensor OTH
class HM_WDS10_TH_O(Device):
    type_name = "HM-WDS10-TH-O"

    @property
    def temperature(self):
        """Provides the current temperature.

        Returns an instance of :class:`ParameterFLOAT`.
        """
        return self.channels[1].values["TEMPERATURE"]


    @property
    def humidity(self):
        """Provides the current humidity.

        Returns an instance of :class:`ParameterFLOAT`.
        """
        return self.channels[1].values["HUMIDITY"]



# Funk-Temperatur-/Luftfeuchtesensor ITH
class HM_WDS40_TH_I_2(Device):
    type_name = "HM-WDS40-TH-I-2"

    @property
    def temperature(self):
        """Provides the current temperature.

        Returns an instance of :class:`ParameterFLOAT`.
        """
        return self.channels[1].values["TEMPERATURE"]


    @property
    def humidity(self):
        """Provides the current humidity.

        Returns an instance of :class:`ParameterFLOAT`.
        """
        return self.channels[1].values["HUMIDITY"]



# Funk-Außen-Helligkeitssensor OLI
class HM_Sen_LI_O(Device):
    type_name = "HM-Sen-LI-O"

    @property
    def brightness(self):
        """Provides the current brightness.

        Returns an instance of :class:`ParameterFLOAT`.
        """
        return self.channels[1].values["LUX"]



# Virtuelle Fernbedienung der CCU
class HM_RCV_50(Device):
    type_name = "HM-RCV-50"



# Funk-Tür-/ Fensterkontakt
class HM_Sec_SC(Device):
    type_name = "HM-Sec-SC"


    # Make methods of ChannelShutterContact() available
    def __getattr__(self, attr):
        return getattr(self.channels[1], attr)



# Optischer Funk-Tür-/ Fensterkontakt
class HM_Sec_SCo(HM_Sec_SC):
    type_name = "HM-Sec-SCo"



# Funk-Schaltaktor mit Leistungsmessung
class HM_ES_PMSw1_Pl(Device):
    type_name = "HM-ES-PMSw1-Pl"


    # Make methods of ChannelSwitch() available
    def __getattr__(self, attr):
        return getattr(self.channels[1], attr)


    @property
    def summary_state(self):
        return super(HM_ES_PMSw1_Pl, self)._get_summary_state(
            skip_channel_types=["ChannelConditionPower", "ChannelConditionCurrent",
                                "ChannelConditionVoltage", "ChannelConditionFrequency"])



# Funk-Schaltaktor ohne Leistungsmessung
class HM_LC_Sw1_Pl_DN_R1(Device):
    type_name = "HM-LC-Sw1-Pl-DN-R1"


    # Make methods of ChannelSwitch() available
    def __getattr__(self, attr):
        return getattr(self.channels[1], attr)


    @property
    def summary_state(self):
        return super(HM_LC_Sw1_Pl_DN_R1, self)._get_summary_state()

    @property
    def switch(self):
        """Provides to the :class:`.ChannelKey` object of the switch.

        You can do something like ``self.switch.switch_on()`` with this. For details take
        a look at the methods provided by the :class:``.ChannelKey`` class."""
        return self.channels[1]



# Funk-Rolladenaktor
class HM_LC_Bl1PBU_FM(Device):
    type_name = "HM-LC-Bl1PBU-FM"


    # Make methods of ChannelBlind() available
    def __getattr__(self, attr):
        return getattr(self.channels[1], attr)

    @property
    def blind(self):
        """Provides to the :class:`.ChannelKey` object of the blind channel.

        You can do something like ``self.blind.set_level(0.6)`` with this. For details take
        a look at the methods provided by the :class:``.ChannelKey`` class."""
        return self.channels[1]



class HM_PBI_4_FM(Device):
    type_name = "HM-PBI-4-FM"

    @property
    def switch1(self):
        """Provides to the :class:`.ChannelKey` object of the first switch.

        You can do something like ``self.switch1.press_short()`` with this. For details take
        a look at the methods provided by the :class:``.ChannelKey`` class."""
        return self.channels[1]


    @property
    def switch2(self):
        """Provides to the :class:`.ChannelKey` object of the second switch."""
        return self.channels[2]


    @property
    def switch3(self):
        """Provides to the :class:`.ChannelKey` object of the third switch."""
        return self.channels[3]


    @property
    def switch4(self):
        """Provides to the :class:`.ChannelKey` object of the fourth switch."""
        return self.channels[4]


# #HENNING BEGINN
# class HM_PB_2_WM55_2(Device):
#     type_name = "HM-PB-2-WM55-2"
# 
#     @property
#     def switch_top(self):
#         """Provides to the :class:`.ChannelKey` object of the first switch.
# 
#         You can do something like ``self.switch1.press_short()`` with this. For details take
#         a look at the methods provided by the :class:``.ChannelKey`` class."""
#         return self.channels[1]
# 
#     @property
#     def switch_bottom(self):
#         """Provides to the :class:`.ChannelKey` object of the second switch."""
#         return self.channels[2]
# 
# 
# # Funk-Schaltaktor 4-fach
# class HM_LC_Sw4_DR(Device):
#     type_name = "HM-LC-Sw4-DR"
# 
#     # Make methods of ChannelSwitch() available
#     def __getattr__(self, attr):
#         return getattr(self.channels[1], attr)
# 
#     @property
#     def summary_state(self):
#         return super(HM_LC_Sw4_DR, self)._get_summary_state()
# 
#     @property
#     def switch1(self):
#         return self.channels[1]
# 
#     @property
#     def switch2(self):
#         return self.channels[2]
# 
#     @property
#     def switch3(self):
#         return self.channels[3]
# 
#     @property
#     def switch4(self):
#         return self.channels[4]
# #HENNING ENDE



class Rooms(object):
    """Manages a collection of rooms."""

    def __init__(self, ccu):
        super(Rooms, self).__init__()
        if not isinstance(ccu, ccu.CCU):
            raise PMException("Invalid ccu object provided: %r" % ccu)
        self._ccu = ccu
        self._room_dict = {}


    @property
    def _rooms(self):
        """Optional initializer of the rooms data structure, called on first access."""
        return self._room_dict


    def get(self, room_id, deflt=None):
        """Returns the :class:`Room` matching the given room id.

        If there is none matching the given ID either None or the value
        specified by the optional attribute *deflt* is returned."""
        return self._rooms.get(room_id, deflt)


    @property
    def ids(self):
        """Provides a sorted list of all ids of all initialized room."""
        return sorted(self._rooms.keys())


    def add(self, room):
        """Add a :class:`Room` to the collection."""
        if not isinstance(room, Room):
            raise PMException("You can only add Room objects.")
        self._rooms[room.id] = room


    def exists(self, room_id):
        """Check whether or not a :class:`Room` with the given id is in this collection."""
        return room_id in self._rooms


    def delete(self, room_id):
        """Deletes the :class:`Room` with the given id from the pmatic runtime.

        The room is not deleted from the CCU. When the room is not known, the method is
        tollerating that."""
        try:
            del self._rooms[room_id]
        except KeyError:
            pass


    def clear(self):
        """Remove all :class:`Room` objects from this collection."""
        self._rooms.clear()


    def __iter__(self):
        """Provides an iterator over the rooms of this collection."""
        for value in self._rooms.values():
            yield value


    def __len__(self):
        """Is e.g. used by :func:`len`. Returns the number of rooms in this collection."""
        return len(self._rooms)



class Room(Entity):
    _transform_attributes = {
        "id"               : int,
        "channelIds"       : lambda x: list(map(int, x)),
    }

    def __init__(self, ccu, spec):
        self._values = {}
        self._devices = None
        super(Room, self).__init__(ccu, spec)


    #@classmethod
    #def get_rooms(self, api):
    #    """Returns a list of all currently configured :class:`.Room` instances."""
    #    rooms = []
    #    for room_dict in api.room_get_all():
    #        rooms.append(Room(api, room_dict))
    #    return rooms


    @property
    def devices(self):
        """Provides access to a collection of :class:`.Device` objects which have at least one
        channel associated with this room.

        The collections is a :class:`.Devices` instance."""
        if not self._devices:
            self._devices = self._ccu.devices.query(has_channel_ids=self.channel_ids)
        return self._devices


    @property
    def channels(self):
        """Holds a list of channel objects associated with this room."""
        # FIXME: Cache this?
        room_channels = []
        for device in self.devices:
            for channel in device.channels:
                if channel.id in self.channel_ids:
                    room_channels.append(channel)
        return room_channels


#    @property
#    def programs(self):
#        """Returns list of program objects which use at least one channel associated
#        with this room."""
#        # FIXME: Implement!
#        # FIXME: Cache this?
#        return []
#
#
#    def add(self, channel):
#        """Adds a channel to this room."""
#        # FIXME: Implement!
#
#
#    def remove(self, channel):
#        """Removes a channel to this room."""
#        # FIXME: Implement!


# Build a list of all specific product classes. If a device is initialized
# Device() checks whether or not a specific class or the generic Device()
# class should be used to initialize an object.
device_classes_by_type_name = {}
for key, val in list(globals().items()):
    if isinstance(val, type):
        if issubclass(val, Device) and key != "Device":
            device_classes_by_type_name[val.type_name] = val

channel_classes_by_type_name = {}
for key, val in list(globals().items()):
    if isinstance(val, type):
        if issubclass(val, Channel) and val != Channel:
            channel_classes_by_type_name[val.type_name] = val
