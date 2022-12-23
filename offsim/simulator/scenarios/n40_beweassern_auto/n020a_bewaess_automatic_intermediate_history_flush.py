# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import simthread, consts, flowerpots, simtime as time

import _bewaess_autom_common as _common

_common.FlowerPots.time_evaporate = 5.0
_common.FlowerPots.time_watering = 3.0
_common.FlowerPots.initial_level_sued = 4.0
_common.FlowerPots.initial_level_west = 8.0


def adapt_csts():
    acsts = consts.ActorConstants
    zcsts = consts.TimeConstants
    acsts.dauer_relais_schalten = 0.5
    acsts.dauer_uebertragung_an_geraet = 0.5
    zcsts.dauer_entwaesserung = 0.5
    zcsts.history_flushing_time_span = 10
    zcsts.autowatering_warte_zeit_bevor_start = 12


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
    watering.AutoWatering.aktiviere_autowatering()

    max_run_time = 50
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)
    simthread.wait_till_all_threads_are_finished()


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts)
