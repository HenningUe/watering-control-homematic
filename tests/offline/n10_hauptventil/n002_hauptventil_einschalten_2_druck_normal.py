
# encoding: utf-8

from offsim import consts, actionstorage, simtime as time, simthread, flowerpots
from offsim.simulator import sensortrigger, plotbyhand, plotter

flowerpots.is_idle = True


def get_simulate_func(run_scenario_func):

    def simulate_inner(ccu):
        _MyDevices.init(ccu)
        time.sleep(0.5)
        run_scenario_func()
        # _create_byhand_plot()
        plotter.plot_variables(__file__)

    return simulate_inner


def _run_scenario():
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(3)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time_step = 5
    max_run_time = 30
    for xs in xrange(0, max_run_time, time_step):
        print(u".. script is living for {xs} sec ..".format(**locals()))
        time.sleep(time_step)
    simthread.wait_till_all_threads_are_finished()


def _create_byhand_plot():
    time.set_time_modus_to_simulation()
    actionstorage.set_storage_type_to_byhand()
    # ## Sensoren ..
    # Schalter Garage
    plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)
    time.sleep(3)
    plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)

    # ## Aktuatoren ..
    time.reset_time_0()
    # Haupt-Ventil auf
    plotbyhand.add_actuator_switch_on(_MyDevices.watering_relais_rail_1.relais1)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine * 1.5)
    plotbyhand.add_actuator_switch_off(_MyDevices.watering_relais_rail_1.relais1)
    # Entwaesserung
    plotbyhand.add_actuator_switch_on(_MyDevices.watering_relais_rail_1.relais2)
    time.sleep(consts.TimeConstants.dauer_entwaesserung)
    plotbyhand.add_actuator_switch_off(_MyDevices.watering_relais_rail_1.relais2)


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


if __name__ == u"__main__":
    import watering
    watering.AutoWateringBalconies._is_disabled_for_debugging = True
    simulate_func = get_simulate_func(_run_scenario)
    watering.run(simulate_func)
