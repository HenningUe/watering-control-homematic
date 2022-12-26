# encoding: utf-8

from offsim import consts, actionstorage, simtime as time, simthread, simtime
from offsim.simulator import sensortrigger, plotter


def get_simulate_func(run_scenario_func):

    def simulate_inner(ccu):
        _MyDevices.init(ccu)
        time.sleep(0.5)
        run_scenario_func()
        plotter.plot_variables(__file__)

    return simulate_inner


def _run_scenario():
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten * 2.2)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten * 0.2)
    sensortrigger.trigger_event_but_long(_MyDevices.schalter_garage.switch_bottom)
    time.sleep(consts.TimeConstants.dauer_entwaesserung * 0.5)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(15)
    simthread.wait_till_all_threads_are_finished()


def adapt_csts():
    acsts = consts.ActorConstants
    zcsts = consts.TimeConstants
    zcsts.dauer_entwaesserung = 10


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
            # oben-rechts = Watering gesamt
            # mitte-links = Watering sued
            # mitte-rechts = Watering west


if __name__ == u"__main__":
    adapt_csts()
    import watering
    simulate_func = get_simulate_func(_run_scenario)
    watering.run(simulate_func)
