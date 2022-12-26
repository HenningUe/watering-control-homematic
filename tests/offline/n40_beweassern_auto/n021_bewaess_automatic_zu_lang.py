# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts
from offsim import flowerpots, simtime as time, actionstorage
from tests.offline.common import watering_autom_common as _common

actionstorage.store_sensor_events = False


def run_scenario():
    import watering
    # time.set_time_modus_to_simulation()
    # simthread.thread_mode_is_active = False

    # Problem: waehrend einer waessert, ist der thread blockiert. D.h. keiner Ueberpruefung
    # des anderen kann stattfinden.

    max_run_time = 50
    time_step = 5
    for xs in xrange(0, max_run_time, time_step):
        print(u".. flowpots are living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)


def adapt_csts():
    acsts = consts.ActorConstants
    zcsts = consts.TimeConstants
    acsts.dauer_uebertragung_an_geraet = 0.5
    zcsts.dauer_entwaesserung = 3
    zcsts.autowatering_warte_zeit_bevor_start = 0.5  # sec
    zcsts.autowatering_max_watering_time = 3
    zcsts.autowatering_max_delta_zeit_zwischen_balkonen = 20
    zcsts.autowatering_max_zeiten_ohne_watering = [30, 40, 75]


_common.FlowerPots.time_evaporate = 18.0
_common.FlowerPots.time_watering = 1.0


def flowerports_init():
    flowerpots.blumentopf_sued.watering_speed = \
        flowerpots.FlowerPot.watering_speed_default * 0.25


if __name__ == u"__main__":
    _common.run(run_scenario, adapt_csts, flowerports_init)
