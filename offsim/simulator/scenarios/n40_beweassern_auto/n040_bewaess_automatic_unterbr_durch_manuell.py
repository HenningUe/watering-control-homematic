# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts, simtime as time, actionstorage
from offsim.simulator.scenarios import _watering_autom_common as _common

actionstorage.store_sensor_events = False

_common.FlowerPots.time_evaporate = 16.0
_common.FlowerPots.time_watering = 10.0
_common.FlowerPots.initial_level_sued = 0.0
_common.FlowerPots.initial_level_west = 1.0


def adapt_csts():
    zcsts = consts.TimeConstants
    zcsts.autowatering_max_waterings_zeit = 12
    zcsts.autowatering_max_delta_zeit_zwischen_balkonen = 40
    zcsts.autowatering_max_zeiten_ohne_watering = [25, 35, 45]


def run_scenario():
    # time.set_time_modus_to_simulation()
    # simthread.thread_mode_is_active = False

    # Problem: waehrend einer waessert, ist der thread blockiert. D.h. keiner Ueberpruefung
    # des anderen kann stattfinden.
    import watering
    time_step = 5

    print("Initial wait")
    time.sleep(7)
    _common._MyDevices.trigger_watering_gesamt()
    max_run_time = 40
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.time_org.sleep(time_step)


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts)
