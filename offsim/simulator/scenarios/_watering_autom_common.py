# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from offsim import consts, flowerpots
from offsim.simulator import _sensortrigger


def get_simulate_func(run_scenario_func, do_plot):

    def simulate_inner(ccu):
        _MyDevices.init(ccu)
        flowerpots.FlowerPots.set_is_active_state_all(False, force_setting=True)
        flowerpots.start_continous_water_level_observation()
        import watering
        # watering.WaterLevelSensors.refresh_sensor_values()
        run_scenario_func()
        watering.ThreadContainer.do_terminate_threads_to_be_terminated()
        if do_plot:
            from offsim.simulator import _plotter
            _plotter.plot_variables(__file__)

    return simulate_inner


def run(run_scenario_func, adapt_csts_func=None, flowerpots_init_func=None, do_plot=True):
    adapt_csts()
    if adapt_csts_func is not None:
        adapt_csts_func()
    FlowerPots.init()
    if flowerpots_init_func is not None:
        flowerpots_init_func()
    import watering
    simulate_func = get_simulate_func(run_scenario_func, do_plot)
    watering.run(simulate_func)


def adapt_csts():
    acsts = consts.ActorConstants
    tcsts = consts.TimeConstants
    acsts.dauer_relais_schalten = 0.5
    acsts.dauer_uebertragung_an_geraet = 0.5
    tcsts.dauer_entwaesserung = 0.5


class _MyDevices(object):
    schalter_garage = None
    watering_relais_rail_1 = None
    # schalter_schuppen = None
    # schalter_wozi_1 = None
    # schalter_wozi_2 = None

    @classmethod
    def init(cls, ccu):
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"WateringRelais1")
        cls.watering_relais_rail_2 = ccu.devices.get_by_name(u"WateringRelais2")
        cls.fuellstand_sensor_sued = ccu.devices.get_by_name(u"FuellstandSensorSued")
        cls.fuellstand_sensor_sued.set_linked_flower_pot(flowerpots.blumentopf_sued)
        cls.fuellstand_sensor_west = ccu.devices.get_by_name(u"FuellstandSensorWest")
        cls.fuellstand_sensor_west.set_linked_flower_pot(flowerpots.blumentopf_west)
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.schalter_schuppen = ccu.devices.get_by_name(u"SchalterSchuppen")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
        # oben-links = Hauptventil
        # oben-rects = Watering gesamt
        # mitte-links = Watering sued
        # mitte-rechts = Watering west

    # schalter_wozi_2 = None
    @classmethod
    def trigger_watering_gesamt(cls):
        _sensortrigger.trigger_event_but_short(cls.schalter_wozi_1.switch_top_right)

    @classmethod
    def trigger_watering_sued(cls):
        _sensortrigger.trigger_event_but_short(cls.schalter_wozi_1.switch_middle_left)

    @classmethod
    def trigger_watering_west(cls):
        _sensortrigger.trigger_event_but_short(cls.schalter_wozi_1.switch_middle_right)


class FlowerPots(object):
    time_evaporate = 9.0
    time_watering = 3.0
    initial_level_sued = 4.0
    initial_level_west = 8.0

    @classmethod
    def init(cls):
        flowerpots.FlowerPot.evaporating_speed_default = \
            ((flowerpots.FlowerPot.min_level - flowerpots.FlowerPot.max_level) / cls.time_evaporate)
        flowerpots.FlowerPot.watering_speed_default = \
            ((flowerpots.FlowerPot.max_level - flowerpots.FlowerPot.min_level) / cls.time_watering)
        flowerpots.blumentopf_sued.initial_level = cls.initial_level_sued
        flowerpots.blumentopf_west.initial_level = cls.initial_level_west
        flowerpots.blumentopf_sued.register_state_change_callback(
            cls.wasserstand_sensor_event_handler)
        flowerpots.blumentopf_west.register_state_change_callback(
            cls.wasserstand_sensor_event_handler)

    @staticmethod
    def wasserstand_sensor_event_handler(flowerpot_name, event_type):
        if flowerpot_name.lower() == "sued":
            device = _MyDevices.fuellstand_sensor_sued
        elif flowerpot_name.lower() == "west":
            device = _MyDevices.fuellstand_sensor_west
        mapx = flowerpots.MappingSensorLevelToContactStates
        is_open_state, channel = None, None
        if event_type == "got_empty":
            channel, is_open_state = device.shutter_contact_empty_channel, mapx.is_empty
        elif event_type == "left_empty":
            channel, is_open_state = device.shutter_contact_empty_channel, not mapx.is_empty
        elif event_type == "got_full":
            channel, is_open_state = device.shutter_contact_full_channel, mapx.is_full
        elif event_type == "left_full":
            channel, is_open_state = device.shutter_contact_full_channel, not mapx.is_full
        elif event_type == "got_active":
            channel, is_open_state = device.shutter_contact_active_channel, mapx.is_active
        elif event_type == "left_active":
            channel, is_open_state = device.shutter_contact_active_channel, not mapx.is_active
        if is_open_state is not None:
            _sensortrigger.trigger_event_shutter_contact(channel, is_open_state)
