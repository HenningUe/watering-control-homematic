# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts, flowerpots, simtime as time, actionstorage, simdatetime as dt
from tests.offline.common import watering_autom_common as _common

actionstorage.store_sensor_events = False

CST_WATER_TIME = 4

_common.FlowerPots.time_evaporate = 4.0
_common.FlowerPots.time_watering = CST_WATER_TIME
_common.FlowerPots.initial_level_sued = 1.0
_common.FlowerPots.initial_level_west = 0.5


def adapt_csts():
    acsts = consts.ActorConstants
    tcsts = consts.TimeConstants
    acsts.dauer_relais_schalten = 0.5
    acsts.dauer_uebertragung_an_geraet = 0.5
    tcsts.dauer_entwaesserung = 1
    tcsts.autowatering_max_watering_time = CST_WATER_TIME + 1
    tcsts.autowatering_max_delta_zeit_zwischen_balkonen = 120
    tcsts.autowatering_max_delta_zeit_zwischen_balkonen = 140

    watering_time_1 = dt.datetime.now() + dt.timedelta(seconds=2)
    watering_time_2 = dt.datetime.now() + dt.timedelta(seconds=6)
    tcsts.autowatering_beds_times = [watering_time_1.time(),
                                     watering_time_2.time(), ]
    tcsts.autwatering_bed_lower_watering_time = 2
    tcsts.autwatering_bed_upper_watering_time = 3

    import watering
    watering.DebugExceptionSim.ON = False


def run_scenario():
    # time.set_time_modus_to_simulation()
    # simthread.thread_mode_is_active = False

    # Problem: waehrend einer waessert, ist der thread blockiert. D.h. keiner Ueberpruefung
    # des anderen kann stattfinden.
    import watering
    time_step = 5

    max_run_time = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)

    flowerpots.FlowerPots.set_is_active_state_all(True)
    watering.AutoWateringBalconies.activate_autowatering()

    max_run_time = 40
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts)
