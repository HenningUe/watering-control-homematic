# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import timedelta as _tdelta
import time

import bewaesserung

LowBattReporter = bewaesserung.LowBattReporterViaEventTracing
LowBattReporter._min_check_period_sec = 5
LowBattReporter._max_time_wo_notification = _tdelta(seconds=9)


class Device(object):

    def __init__(self, name):
        self.name = name


class Channel(object):

    def __init__(self, name):
        self.device = Device(name)


class Param(object):

    def __init__(self, name, id_):
        self.id = id_
        self.channel = Channel(name)

    @classmethod
    def add_device_notification(cls, name, id_):
        print("'{}' '{}'".format(name, id_))
        LowBattReporter.add_device_notification(cls(name, id_))
        LowBattReporter.check_low_bat()


def run_test():
    print("Start")
    for i in xrange(1, 4):
        Param.add_device_notification("SensorSued", "lowbat")
        time.sleep(4 * i)
        Param.add_device_notification("SensorWest", "lowbat")
        time.sleep(1 * i)
        Param.add_device_notification("SensorSued", "SensorEventFull")
        Param.add_device_notification("SensorWest", "SensorEventFull")
        time.sleep(5 * i)
        Param.add_device_notification("SensorSued", "SensorEventFull")

    print("Finished")


if __name__ == "__main__":
    run_test()
