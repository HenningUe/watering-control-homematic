# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts
from offsim import flowerpots, simtime as time, actionstorage
from tests.offline.common import watering_autom_common as _common

actionstorage.store_sensor_events = False


def run_scenario():
    import watering

    max_run_time = 50
    time_step = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


def adapt_csts():
    # acsts = consts.ActorConstants
    zcsts = consts.TimeConstants
    zcsts.autowatering_warte_zeit_bevor_start = 0.5  # sec
    zcsts.autowatering_max_watering_time = 10
    zcsts.autowatering_max_delta_zeit_zwischen_balkonen = 230
    zcsts.autowatering_max_zeiten_ohne_watering = [14, 20, 27]


_common.FlowerPots.time_evaporate = 18.0
_common.FlowerPots.time_watering = 1.0


def flowerports_init():
    flowerpots.blumentopf_sued.evaporating_speed = \
        flowerpots.FlowerPot.evaporating_speed_default * 0.1


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts, flowerports_init)
