# encoding: utf-8

from offsim import simthread, consts, flowerpots, simtime as time, actionstorage
from offsim.simulator import sensortrigger, plotbyhand, plotter
from tests.offline.common import watering_autom_common as _common


def simulate(ccu):
    _MyDevices.init(ccu)
    _run_scenario()
    _create_byhand_plot()
    plotter.plot_variables(__file__)


def _run_scenario():
    time.set_time_modus_to_simulation()
    simthread.thread_mode_is_active = False
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_wozi_1.switch_middle_right)
    simthread.wait_till_all_threads_are_finished()


def _create_byhand_plot():
    time.set_time_modus_to_simulation()
    actionstorage.set_storage_type_to_byhand()
    # ## Sensoren ..
    # Schalter Garage
    plotbyhand.add_sensor_event(_MyDevices.schalter_wozi_1.switch_middle_right)

    # ## Aktuatoren ..
    time.reset_time_0()


class _MyDevices(object):
    schalter_garage = None
    watering_relais_rail_1 = None
    # schalter_schuppen = None
    # schalter_wozi_1 = None
    # schalter_wozi_2 = None

    @classmethod
    def init(cls, ccu):
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"WateringRelais1")
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.schalter_schuppen = ccu.devices.get_by_name(u"SchalterSchuppen")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            # oben-links = Hauptventil
            # oben-rects = Watering gesamt
            # mitte-links = Watering sued
            # mitte-rechts = Watering west
