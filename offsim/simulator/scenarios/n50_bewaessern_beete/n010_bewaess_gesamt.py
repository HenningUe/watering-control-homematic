# encoding: utf-8

from __future__ import unicode_literals, division

import time
import datetime as dt

from offsim import consts, simdatetime
from offsim.simulator.scenarios import _watering_autom_common as _common

simdatetime.datetime = dt.datetime


def adapt_csts():
    watering_time_1 = dt.datetime.now() + dt.timedelta(seconds=2)
    watering_time_2 = dt.datetime.now() + dt.timedelta(seconds=6)
    consts.TimeConstants.autowatering_beds_times = [watering_time_1.time(),
                                                    watering_time_2.time(), ]
    consts.TimeConstants.autwatering_bed_lower_watering_time = 2
    consts.TimeConstants.autwatering_bed_upper_watering_time = 3
    import watering
    watering.AutoWateringBalconies._is_disabled_for_debugging = True


def run_scenario():
    # time.set_time_modus_to_simulation()
    # simthread.thread_mode_is_active = False

    # Problem: waehrend einer waessert, ist der thread blockiert. D.h. keiner Ueberpruefung
    # des anderen kann stattfinden.
    import watering
    time_step = 5
    max_run_time = 40
    for xs in xrange(0, max_run_time, time_step):
        print(u".. running for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts)
