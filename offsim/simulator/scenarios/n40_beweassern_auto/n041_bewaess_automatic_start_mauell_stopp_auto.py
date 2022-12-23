# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts, flowerpots, simtime as time, actionstorage
from offsim.simulator.scenarios import _watering_autom_common as _common

actionstorage.store_sensor_events = False


def adapt_csts():
    zcsts = consts.TimeConstants
    zcsts.autobewsrng_max_bewaesserungs_zeit = 12
    zcsts.autobewsrng_max_delta_zeit_zwischen_balkonen = 40
    zcsts.autobewsrng_max_zeiten_ohne_bewaesserung = [25, 35, 45]


_common.FlowerPots.time_evaporate = 18.0
_common.FlowerPots.time_watering = 4.0
_common.FlowerPots.initial_level_sued = 0.0
_common.FlowerPots.initial_level_west = 1.0


def flowerports_init():
    flowerpots.blumentopf_sued.evaporating_speed = \
        ((flowerpots.FlowerPot.min_level - flowerpots.FlowerPot.max_level) / 45.0)


def run_scenario():
    import bewaesserung
    time_step = 5
    bewaesserung.ThreadContainer.do_set_timeout_for_threads_to_be_terminated(50)
    max_run_time1 = 20
    for xs in xrange(0, max_run_time1, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.time_org.sleep(time_step)
    _common._MyDevices.trigger_bewaesserung_gesamt()
    max_run_time2 = 40
    for xs in xrange(max_run_time1, max_run_time2, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.time_org.sleep(time_step)


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts, flowerports_init)
