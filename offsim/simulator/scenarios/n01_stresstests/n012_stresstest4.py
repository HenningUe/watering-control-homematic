# encoding: utf-8

from __future__ import unicode_literals, division

from offsim import consts
from offsim.simulator import _plotter
from offsim import simthread, simtime as time
from offsim.simulator import _sensortrigger


def simulate(ccu):
    _MyDevices.init(ccu)
    _run_scenario()
    _plotter.plot_variables()


def _run_scenario():
    # bug: time_sleep = 0.5
    time_sleep = 0.8
    for _ in xrange(10):
        _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_long(_MyDevices.schalter_garage.switch_bottom)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_long(_MyDevices.schalter_garage.switch_bottom)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_long(_MyDevices.schalter_garage.switch_bottom)
        time.sleep(time_sleep)
        _sensortrigger.trigger_event_but_long(_MyDevices.schalter_garage.switch_bottom)
        time_sleep /= 2
        print(time_sleep)
    simthread.wait_till_all_threads_are_finished()


class _MyDevices(object):
    schalter_garage = None
    watering_relais_rail_1 = None
    # schalter_schuppen = None
    # schalter_wozi_1 = None
    # schalter_wozi_2 = None

    @classmethod
    def init(cls, ccu):
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"WateringRelais1")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            # oben-links = Hauptventil
            # oben-rects = Watering gesamt
            # mitte-links = Watering sued
            # mitte-rechts = Watering west


def run():
    import watering
    watering.AutoWatering.is_autowatering_enabled = False
    watering.run(simulate)


if __name__ == u"__main__":
    run()
