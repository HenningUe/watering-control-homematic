
# encoding: utf-8

from __future__ import unicode_literals

from collections import defaultdict
import threading
import datetime
import time as time_org


class TimeModus(object):
    real = u"real"
    simulation = u"simulation"


class TimePropContainer(object):

    def __init__(self):
        self.time_0 = _get_time0()
        self.time_offset = 0
        self.sleep_offset = 86400  # 1 day
        self.modus = TimeModus.real


_time_defs = defaultdict(TimePropContainer)


def _translate_thread_id(thread_id):
    global _time_defs
    if thread_id is None:
        if threading.current_thread().ident in _time_defs:
            thread_id = threading.current_thread().ident
        else:
            thread_id = 'allthreads'
    elif isinstance(thread_id, (str, unicode)) and thread_id.lower() == 'thisthread':
        thread_id = threading.current_thread().ident
    return thread_id


def set_time_modus_to_real(thread_id='allthreads'):
    global _time_defs
    thread_id = _translate_thread_id(thread_id)
    reset_time_0(thread_id)
    _time_defs[thread_id].modus = TimeModus.real


def set_time_modus_to_simulation(thread_id='allthreads'):
    global _time_defs
    thread_id = _translate_thread_id(thread_id)
    reset_time_0(thread_id)
    _time_defs[thread_id].modus = TimeModus.simulation


def reset_time_0(thread_id='allthreads'):
    global _time_defs
    thread_id = _translate_thread_id(thread_id)
    _time_defs[thread_id].sleep_offset = 0
    _time_defs[thread_id].time_0 = _get_time0()


def set_time_offset(time_offset, thread_id=None):
    global _time_defs
    thread_id = _translate_thread_id(thread_id)
    _time_defs[thread_id].time_offset = time_offset


def set_time_0_day_related(day_related_time_0=datetime.time(hour=0, minute=0), thread_id=None):
    global _time_defs
    if day_related_time_0 is None:
        return
    thread_id = _translate_thread_id(thread_id)
    time_0 = _time_defs[thread_id].time_0
    ctime = time_org.time()
    atime = ctime - time_0
    atime_dt = datetime.datetime.fromtimestamp(atime)
    atime_dt = atime_dt.replace(hour=day_related_time_0.hour,
                                minute=day_related_time_0.minute,
                                second=day_related_time_0.second)
    atime = (atime_dt - datetime.datetime(1971, 1, 1)).total_seconds()
    time_0 = ctime - atime
    _time_defs[thread_id].time_0 = time_0


def sleep(seconds, thread_id=None):
    global _time_defs
    thread_id = _translate_thread_id(thread_id)
    if _time_defs[thread_id].modus == TimeModus.real:
        time_org.sleep(seconds)
    elif _time_defs[thread_id].modus == TimeModus.simulation:
        _time_defs[thread_id].sleep_offset += seconds


def time(thread_id=None):
    global _time_defs
    thread_id = _translate_thread_id(thread_id)
    ctime = time_org.time()
    if _time_defs[thread_id].modus == TimeModus.simulation:
        ctime += _time_defs[thread_id].sleep_offset
    return ctime - _time_defs[thread_id].time_0 + _time_defs[thread_id].time_offset


def _get_time0():
    return time_org.time() - 60 * 60 * 24 * 30
