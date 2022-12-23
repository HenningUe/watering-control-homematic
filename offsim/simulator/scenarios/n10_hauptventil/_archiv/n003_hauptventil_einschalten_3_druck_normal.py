
# encoding: utf-8


from ... import consts, actionstorage, simtime as time, simthread

from .. import _sensortrigger, _plotbyhand, _plotter
    

def simulate(ccu):
    _MyDevices.init(ccu)
    _run_scenario()
    _create_byhand_plot()
    _plotter.plot_variables(__file__)
    

def _run_scenario():
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(3)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(2)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    simthread.wait_till_all_threads_are_finished()
    

def _create_byhand_plot():
    time.set_time_modus_to_simulation()
    actionstorage.set_storage_type_to_byhand()
    ### Sensoren ..
    #Schalter Garage
    _plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)
    time.sleep(3)
    _plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)
    time.sleep(2)
    _plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)
    
    ### Aktuatoren ..
    time.reset_time_0()
    #Haupt-Ventil auf
    _plotbyhand.add_actuator_switch_on(_MyDevices.watering_relais_rail_1.relais1)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine*2 +3.5) #3.5 = 3 + 2 - dauer_relais_schalten
    _plotbyhand.add_actuator_switch_off(_MyDevices.watering_relais_rail_1.relais1)
    #Entwaesserung
    _plotbyhand.add_actuator_switch_on(_MyDevices.watering_relais_rail_1.relais2)
    time.sleep(consts.TimeConstants.dauer_entwaesserung)
    _plotbyhand.add_actuator_switch_off(_MyDevices.watering_relais_rail_1.relais2)


class _MyDevices(object):
    schalter_garage = None
    watering_relais_rail_1 = None
    #schalter_schuppen = None
    #schalter_wozi_1 = None
    #schalter_wozi_2 = None
    
    @classmethod
    def init(cls, ccu):
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"BewaesserungRelais1")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            #oben-links = Hauptventil
            #oben-rects = Bewaesserung gesamt
            #mitte-links = Bewaesserung sued
            #mitte-rechts = Bewaesserung west