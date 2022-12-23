# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import simthread, consts, flowerpots, simtime as time, actionstorage

import _bewaess_autom_common as _common

actionstorage.store_sensor_events = False

CST_WATER_TIME = 10

_common.FlowerPots.time_evaporate = 4.0
_common.FlowerPots.time_watering = CST_WATER_TIME
_common.FlowerPots.initial_level_sued = 1.0
_common.FlowerPots.initial_level_west = 0.0


def adapt_csts():
    acsts = consts.ActorConstants
    zcsts = consts.TimeConstants
    acsts.dauer_relais_schalten = 0.5
    acsts.dauer_uebertragung_an_geraet = 0.5
    zcsts.dauer_entwaesserung = 2
    zcsts.autobewsrng_max_bewaesserungs_zeit = CST_WATER_TIME + 4
    zcsts.autobewsrng_max_delta_zeit_zwischen_balkonen = 120
    zcsts.autobewsrng_max_delta_zeit_zwischen_balkonen = 140


def run_scenario():
    # time.set_time_modus_to_simulation()
    # simthread.thread_mode_is_active = False

    # Problem: waehrend einer waessert, ist der thread blockiert. D.h. keiner Ueberpruefung
    # des anderen kann stattfinden.
    import bewaesserung
    bewaesserung.DebugExceptionSim.ON = True
    bewaesserung.DebugExceptionSim.SIM_RELAIS_EX = True
    time_step = 5

    max_run_time = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        for xs_ in xrange(0, time_step * 10, 1):
            time.sleep(0.1)
            if bewaesserung.ExceptionsInThreadsContainer.any_threads_occured():
                return

    flowerpots.FlowerPots.set_is_active_state_all(True)
    bewaesserung.AutoBewaesserung.aktiviere_autobewaesserung()

    max_run_time = 40
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        for xs_ in xrange(0, time_step * 10, 1):
            time.sleep(0.1)
            if bewaesserung.ExceptionsInThreadsContainer.any_threads_occured():
                return


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts)
