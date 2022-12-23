# encoding: utf-8

from __future__ import unicode_literals, division

import time
import threading

from . import simdatetime as datetime


class ContactStates(object):
    is_open = True
    is_closed = False


class MappingSensorLevelToContactStates(object):
    is_empty = ContactStates.is_open
    is_full = ContactStates.is_closed
    is_active = ContactStates.is_closed


class FlowerPot(object):
    min_level = 0.0
    max_level = 10.0
    evaporating_speed_default = -0.01 / 1
    watering_speed_default = 0.2 / 1

    class _EventTypes(object):
        got_empty = 0
        left_empty = 1
        got_full = 2
        left_full = 3
        got_active = 4
        left_active = 5

    class _ChangeStates(object):
        evaporating = 0
        watering = 1

    def __init__(self, name, evaporating_speed=None, watering_speed=None, initial_level=0.0):
        self.name = name
        self._evaporating_speed = evaporating_speed
        self._watering_speed = watering_speed
        self.initial_level = initial_level
        self._change_states = [self._create_state_dict(self._ChangeStates.evaporating)]
        self._last_event_type = None
        self._event_callback = None
        self._is_active = False

    @property
    def evaporating_speed(self):
        return (self.evaporating_speed_default if self._evaporating_speed is None
                else self._evaporating_speed)

    @evaporating_speed.setter
    def evaporating_speed(self, value):
        self._evaporating_speed = value

    @property
    def time_evaporating(self):
        return ((self.min_level - self.max_level) / self.evaporating_speed)

    @time_evaporating.setter
    def time_evaporating(self, value):
        self.evaporating_speed = ((self.min_level - self.max_level) / value)

    @property
    def watering_speed(self):
        return (self.watering_speed_default if self._watering_speed is None
                else self._watering_speed)

    @watering_speed.setter
    def watering_speed(self, value):
        self._watering_speed = value

    def get_water_level(self):
        water_lvl = self.initial_level
        for i_state, state in enumerate(self._change_states):
            if i_state < len(self._change_states) - 1:
                next_state = self._change_states[i_state + 1]
            else:
                next_state = self._create_state_dict()
            delta_time = (next_state['time'] - state['time']).total_seconds()
            if state['state'] == self._ChangeStates.watering:
                speed = self.watering_speed
            else:
                speed = self.evaporating_speed
            water_lvl += speed * delta_time
            if water_lvl < self.min_level:
                water_lvl = self.min_level
            elif water_lvl > self.max_level:
                water_lvl = self.max_level
        return water_lvl

    def is_full(self):
        is_full = self.get_water_level() >= self.max_level
        return is_full

    def is_empty(self):
        is_empty = self.get_water_level() <= self._get_min_level_unsteady()
        return is_empty

    def is_active(self):
        return self._is_active

    def set_is_active(self, is_active, force_setting=False):
        if force_setting or not is_active == self._is_active:
            self._is_active = is_active
            if self._is_active:
                self._event_callback(self.name, "got_active")
            else:
                self._event_callback(self.name, "left_active")

    def _get_min_level_unsteady(self, store=dict()):
        if 'lastid' not in store:
            store['lastid'] = 0
        undulations_perc = [0, 5, 7, 2, -4, -2, -5, 0, 8, 5, -5, 7, 3, 0, -3, 5, 7]
        deviation = (self.max_level - self.min_level) * (undulations_perc[store['lastid']] / 100)
        store['lastid'] += 1
        if store['lastid'] == len(undulations_perc):
            store['lastid'] = 0
        return self.min_level + deviation

    def start_watering(self):
        if self._change_states[-1]['state'] == self._ChangeStates.watering:
            return
        self._change_states.append(self._create_state_dict(self._ChangeStates.watering))

    def stop_watering(self):
        if self._change_states[-1]['state'] == self._ChangeStates.evaporating:
            return
        self._change_states.append(self._create_state_dict(self._ChangeStates.evaporating))

    def register_state_change_callback(self, callback):
        self._event_callback = callback

    def run_state_check(self):
        if self._event_callback is None:
            return
        if self.is_empty() and (not self._last_event_type == self._EventTypes.got_empty
                                or self._last_event_type is None):
            self._last_event_type = self._EventTypes.got_empty
            self._event_callback(self.name, "got_empty")
        elif self.is_full() and (not self._last_event_type == self._EventTypes.got_full
                                 or self._last_event_type is None):
            self._last_event_type = self._EventTypes.got_full
            self._event_callback(self.name, "got_full")
        elif self._last_event_type == self._EventTypes.got_empty and not self.is_empty():
            self._last_event_type = self._EventTypes.left_empty
            self._event_callback(self.name, "left_empty")
        elif self._last_event_type == self._EventTypes.got_full and not self.is_full():
            self._last_event_type = self._EventTypes.left_full
            self._event_callback(self.name, "left_full")

    def _create_state_dict(self, state=None):
        state_dict = dict(time=datetime.datetime.now())
        if state == self._ChangeStates.evaporating:
            state_dict['state'] = self._ChangeStates.evaporating
        elif state == self._ChangeStates.watering:
            state_dict['state'] = self._ChangeStates.watering
        return state_dict


class FlowerPots(object):
    _flowerpots = list()

    @classmethod
    def set_is_active_state_all(cls, is_active, force_setting=False):
        for flwpot in cls._flowerpots:
            flwpot.set_is_active(is_active, force_setting)

    @classmethod
    def create_flower_pot(cls, name):
        flowerpot = FlowerPot(name)
        cls._flowerpots.append(flowerpot)
        return flowerpot

    @classmethod
    def continousily_oberserve_water_levels(cls):
        func_wrap = cls._observe_water_levels_threaded
        thread_hl = threading.Thread(target=func_wrap)
        thread_hl.start()

    @classmethod
    def _observe_water_levels_threaded(cls):
        # time.sleep(0.1)
        import bewaesserung as bw
        while True:
            for flwpot in cls._flowerpots:
                flwpot.run_state_check()
            time.sleep(0.1)
            if bw.ThreadContainer.get_sideline_threads_must_be_terminated() \
               or bw.ExceptionsInThreadsContainer.any_threads_occured():
                break


blumentopf_sued = FlowerPots.create_flower_pot("Sued")
blumentopf_west = FlowerPots.create_flower_pot("West")


def start_continous_water_level_observation():
    FlowerPots.continousily_oberserve_water_levels()
