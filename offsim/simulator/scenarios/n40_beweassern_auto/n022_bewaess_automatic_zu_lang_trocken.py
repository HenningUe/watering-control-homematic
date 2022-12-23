# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts
from offsim import flowerpots, simtime as time, actionstorage
from offsim.simulator.scenarios import _watering_autom_common as _common

actionstorage.store_sensor_events = False


def run_scenario():
    import bewaesserung

    max_run_time = 50
    time_step = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


def adapt_csts():
    # acsts = consts.ActorConstants
    zcsts = consts.TimeConstants
    zcsts.autobewsrng_warte_zeit_bevor_start = 0.5  # sec
    zcsts.autobewsrng_max_bewaesserungs_zeit = 10
    zcsts.autobewsrng_max_delta_zeit_zwischen_balkonen = 230
    zcsts.autobewsrng_max_zeiten_ohne_bewaesserung = [14, 20, 27]


_common.FlowerPots.time_evaporate = 18.0
_common.FlowerPots.time_watering = 1.0


def flowerports_init():
    flowerpots.blumentopf_sued.evaporating_speed = \
        flowerpots.FlowerPot.evaporating_speed_default * 0.1


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts, flowerports_init)
