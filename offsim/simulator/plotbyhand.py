
# encoding: utf-8

from .. import actionstorage
from ..pmaticpatched import params


def add_sensor_event(channel):
    param = params.Parameter(channel, {u"control": u"BUTTON.LONG",
                                       u"default": 0, u"operations": 7})
    actionstorage.add_sensor_event(param)


def add_actuator_switch_on(channel):
    param = params.Parameter(channel, {u"default": 0, u"operations": 7})
    param.set(True)
#     param._value = (True if value_invert else False)
#     actionstorage.add_actuator_event(u"value_updated", param,
#                                      storage_type=u"byhand")
#     param = params.Parameter(channel, {u"default": 1, u"operations": 7})
#     param._value = (False if value_invert else True)
#     actionstorage.add_actuator_event(u"value_updated", param,
#                                      storage_type=u"byhand")


def add_actuator_switch_off(channel):
    param = params.Parameter(channel, {u"default": 1, u"operations": 7})
    param.set(False)
    # ime_stamp = add_actuator_switch_on(channel, time_stamp, value_invert=True)
    # return time_stamp
