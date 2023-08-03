# encoding: utf-8

from __future__ import unicode_literals

from ..pmaticpatched import params, events


# @simthread.run_threaded_deco
def trigger_event_but_short(channel):
    param = params.Parameter(channel, {u'CONTROL': u"BUTTON.SHORT",
                                       u'ID': u"PRESS_SHORT",
                                       u'DEFAULT': 0,
                                       u'FLAGS': 1,
                                       u'OPERATIONS': 7,
                                       u'UNIT': u"",
                                       u'NAME': u"CCU2",
                                       })
    print("trigger_event_but_short")
    events.EventListener.callback(u"value_updated", param)


# @simthread.run_threaded_deco
def trigger_event_but_long(channel):
    param = params.Parameter(channel, {u'CONTROL': u"BUTTON.LONG",
                                       u'ID': u"PRESS_LONG",
                                       u'DEFAULT': 0,
                                       u'FLAGS': 1,
                                       u'OPERATIONS': 7,
                                       u'UNIT': u"",
                                       u'NAME': u"CCU2",
                                       })
    print("trigger_event_but_long")
    events.EventListener.callback(u"value_updated", param)


# @simthread.run_threaded_deco
def trigger_event_shutter_contact(channel, is_open, add_sensor_event=True):
    param = params.Parameter(channel, {u'DEFAULT': 0,
                                       u'ID': u"OPEN",
                                       u'FLAGS': 1,
                                       u'OPERATIONS': 7,
                                       u'UNIT': u"",
                                       u'NAME': u"CCU2",
                                       u'STATE': 1,
                                       u'DEFAULT': is_open,
                                       })
    channel.values["STATE"] = param
    events.EventListener.callback(u"value_updated", param, add_sensor_event)


def set_water_level_sensor_is_full(sensor):
    _set_water_level_sensor_temperature(sensor.temperature1_channel, 5)
    _set_water_level_sensor_temperature(sensor.temperature2_channel, 5)


def set_water_level_sensor_is_empty(sensor):
    _set_water_level_sensor_temperature(sensor.temperature1_channel, 150)
    _set_water_level_sensor_temperature(sensor.temperature2_channel, 150)


def _set_water_level_sensor_temperature(channel, temperature):
    channel.temperature = temperature
    # events.EventListener.callback(u"value_updated", channel.temperature_param)

