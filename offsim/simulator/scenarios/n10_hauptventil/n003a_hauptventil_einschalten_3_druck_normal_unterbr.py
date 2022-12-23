# encoding: utf-8

from offsim import consts, actionstorage, simtime as time, simthread, simtime
from offsim.simulator import _sensortrigger, _plotter


def get_simulate_func(run_scenario_func):

    def simulate_inner(ccu):
        _MyDevices.init(ccu)
        time.sleep(0.5)
        run_scenario_func()
        _plotter.plot_variables(__file__)

    return simulate_inner


def _run_scenario():
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(3)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(2)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(2)
    _sensortrigger.trigger_event_but_long(_MyDevices.schalter_schuppen.switch_bottom)
    time.sleep(6)
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
        cls.schalter_schuppen = ccu.devices.get_by_name(u"SchalterSchuppen")
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"BewaesserungRelais1")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            # oben-links = Hauptventil
            # oben-rects = Bewaesserung gesamt
            # mitte-links = Bewaesserung sued
            # mitte-rechts = Bewaesserung west


if __name__ == u"__main__":
    import bewaesserung
    simulate_func = get_simulate_func(_run_scenario)
    bewaesserung.run(simulate_func)
