# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts
from offsim import flowerpots, simtime as time, actionstorage
from offsim.simulator.scenarios import _watering_autom_common as _common

actionstorage.store_sensor_events = False


def run_scenario():
    # time.set_time_modus_to_simulation()
    # simthread.thread_mode_is_active = False

    # Problem: waehrend einer waessert, ist der thread blockiert. D.h. keiner Ueberpruefung
    # des anderen kann stattfinden.
    max_run_time = 90
    time_step = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


def adapt_csts():
    zcsts = consts.TimeConstants
    zcsts.autowatering_warte_zeit_bevor_start = 0.5  # sec
    zcsts.autowatering_max_waterings_zeit = 3
    zcsts.autowatering_max_delta_zeit_zwischen_balkonen = 20
    zcsts.autowatering_max_zeiten_ohne_watering = [25, 35, 45]


_common.FlowerPots.time_evaporate = 18.0
_common.FlowerPots.time_watering = 1.0
_common.FlowerPots.initial_level_sued = 9.5
_common.FlowerPots.initial_level_west = 0.0


def flowerports_init():
    flowerpots.blumentopf_sued.evaporating_speed = \
        ((flowerpots.FlowerPot.min_level - flowerpots.FlowerPot.max_level) / 45.0)


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts, flowerports_init)
