
# encoding: utf-8

from . import actions

import threading

_lock = threading.RLock()

store_sensor_events = True
store_sensor_trigger_events = True
store_actuator_events = True


def _do_lock_deco(outer_func):

    def inner_func(*args, **kwargs):
        global _lock
        with _lock:
            return outer_func(*args, **kwargs)

    return inner_func


@_do_lock_deco
def add_sensor_trigger_event(param, press_long=False):
    if not store_sensor_trigger_events:
        return
    actions.ActionSensor(param, value=0)
    actions.ActionSensor(param, value=1, time_off=0.001)
    if press_long:
        actions.ActionSensor(param, value=1, time_off=0.5)
        actions.ActionSensor(param, value=0, time_off=0.501)
    else:
        actions.ActionSensor(param, value=1, time_off=0.1)
        actions.ActionSensor(param, value=0, time_off=0.101)


@_do_lock_deco
def add_sensor_event(param, value=None):
    if not store_sensor_events:
        return
    actions.ActionSensor(param, value)


@_do_lock_deco
def add_actuator_event(param):
    if not store_actuator_events:
        return
    actions.ActionActuator(param)


@_do_lock_deco
def add_value_observer(val_name, value):
    oldvals = actions.ActionValueObserver.get_old_vals()
    actions.ActionValueObserver(val_name, value=oldvals.get(val_name, value))
    actions.ActionValueObserver(val_name, value=value, time_off=0.001)
    oldvals[val_name] = value


def get_action_plot_values_grouped_by_channel():
    return actions.get_action_plot_values_grouped_by_channel()


@_do_lock_deco
def set_storage_type(storage_type_new):
    actions.set_storage_type(storage_type_new)


@_do_lock_deco
def set_storage_type_to_main():
    actions.set_storage_type_to_main()


@_do_lock_deco
def set_storage_type_to_byhand():
    actions.set_storage_type_to_byhand()
