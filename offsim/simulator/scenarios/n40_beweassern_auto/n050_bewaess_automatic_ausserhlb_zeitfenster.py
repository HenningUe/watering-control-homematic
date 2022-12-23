# encoding: utf-8

from __future__ import unicode_literals, division

import datetime

from offsim import consts, simtime as time
from offsim.simulator.scenarios import _watering_autom_common as _common

_common.FlowerPots.time_evaporate = 9.0
_common.FlowerPots.time_watering = 3.0
_common.FlowerPots.initial_level_sued = 4.0
_common.FlowerPots.initial_level_west = 8.0


def adapt_csts():
    zcsts = consts.TimeConstants
    zcsts.autowatering_max_waterings_zeit = 15
    zcsts.autowatering_max_delta_zeit_zwischen_balkonen = 20
    zcsts.autowatering_max_zeiten_ohne_watering = [30, 40, 75]

    from watering import AutoWateringBalconies
    AutoWateringBalconies.permitted_watering_time_slots = [
        dict(start=datetime.time(hour=22, minute=30, second=20),
             end=datetime.time(hour=22, minute=30, second=40))]
    time.set_time_0_day_related(datetime.time(hour=21, minute=30))


def run_scenario():
    max_run_time = 60
    time_step = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts)
