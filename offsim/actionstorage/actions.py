
# encoding: utf-8

from collections import defaultdict
import copy

from .. import simtime as time


class ActionType(object):
    sensor = u"sensor"
    actuator = u"actuator"
    value = u"value"


class StorageType(object):
    main = u"main"
    byhand = u"byhand"
    value = u"value"


storage_type = StorageType.main
_actions = {StorageType.main: list(),
            StorageType.byhand: list(),
            StorageType.value: list()}


def set_storage_type(storage_type_new):
    global storage_type
    storage_type = storage_type_new


def set_storage_type_to_main():
    global storage_type
    storage_type = StorageType.main


def set_storage_type_to_byhand():
    global storage_type
    storage_type = StorageType.byhand


def get_actions():
    global _actions
    global storage_type
    return _actions[storage_type]


class ActionBase(object):

    def __init__(self, param, value=None,
                 time_off=0.0, cb_name=u"value_updated"):
        self.action_type = None
        self.cb_name = cb_name
        self.param = param
        self.value = value
        if self.value is None:
            self.value = param.value
        self.time = time.time()
        self.time += time_off

    @property
    def device_addr(self):
        raise NotImplementedError()

    @property
    def device_name(self):
        raise NotImplementedError()

    @property
    def device_alias(self):
        raise NotImplementedError()


class ActionSensor(ActionBase):

    def __init__(self, param, value=None,
                 time_off=0.0, cb_name=u"value_updated"):
        super(ActionSensor, self).__init__(param, value, time_off, cb_name)
        self.action_type = ActionType.sensor
        get_actions().append(self)

    @property
    def device_addr(self):
        return self.param.channel.address

    @property
    def device_name(self):
        return self.param.channel.name

    @property
    def device_alias(self):
        if hasattr(self.param.channel, u"alias"):
            return self.param.channel.alias
        else:
            return u""


class ActionActuator(ActionSensor):

    def __init__(self, param, value=None,
                 time_off=0.0, cb_name=u"value_updated"):
        super(ActionActuator, self).__init__(param, value, time_off, cb_name)
        self.action_type = ActionType.actuator
        get_actions().append(self)


class ActionValueObserver(ActionBase):
    _old_vals = dict()

    def __init__(self, variable_name, value=None,
                 time_off=0.0, cb_name=u"value_updated"):
        super(ActionValueObserver, self).__init__(None, value, time_off, cb_name)
        self.action_type = ActionType.value
        self.variable_name = variable_name
        self._add_to_actions_storage()

    def _add_to_actions_storage(self):
        global storage_type
        storage_type_old = storage_type
        storage_type = StorageType.value
        get_actions().append(self)
        storage_type = storage_type_old

    @staticmethod
    def get_old_vals():
        return ActionValueObserver._old_vals

    @property
    def device_name(self):
        return self.variable_name

    @property
    def device_alias(self):
        return u""


def get_action_plot_values_grouped_by_channel():
    all_times_vector = [act.time for act in get_actions()]
    if not all_times_vector:
        return
    vals = defaultdict(lambda: {u'time': [0.0, 0.0001], u'values': [1.1, 0.0]})
    min_time, max_time = min(all_times_vector), max(all_times_vector)
    start_correction_off = min_time - 1
    for act in get_actions():
        vals[act.device_name][u'time'].append(act.time - start_correction_off)
        vals[act.device_name][u'values'].append(float(act.value))
        if u"alias" not in vals[act.device_name] and act.device_alias:
            vals[act.device_name][u"alias"] = act.device_alias
    valsn = dict()
    for dev_name in vals:
        if len(vals[dev_name][u'time']) <= 3:
            continue
        valsn[dev_name] = copy.deepcopy(vals[dev_name])
        valsn[dev_name][u'time'].append(max_time - start_correction_off + 1)
        valsn[dev_name][u'values'].append(vals[dev_name][u'values'][-1])
    return valsn
