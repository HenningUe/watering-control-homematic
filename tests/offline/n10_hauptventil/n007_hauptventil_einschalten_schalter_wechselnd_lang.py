
# encoding: utf-8


from ... import consts, actionstorage, simtime as time, simthread

from .. import sensortrigger, plotbyhand, plotter
    

def simulate(ccu):
    _MyDevices.init(ccu)
    _run_scenario()
    _create_byhand_plot()
    plotter.plot_variables(__file__)
    

def _run_scenario():
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_wozi_1.switch_top_left)
    time.sleep(consts.ActorConstants.dauer_relais_schalten*2.5)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten*0.2)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine*0.5)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_schuppen.switch_top)
    time.sleep(40.0)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten*0.2)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(40.0)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_schuppen.switch_top)
    time.sleep(60.0)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine*0.5)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_schuppen.switch_top)
    time.sleep(40.0)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten*0.2)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(40.0)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_schuppen.switch_top)
    time.sleep(60.0)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    simthread.wait_till_all_threads_are_finished()
    

def _create_byhand_plot():
    time.set_time_modus_to_simulation()
    actionstorage.set_storage_type_to_byhand()
    ### Sensoren ..
    #Schalter Garage
    plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)
    
    ### Aktuatoren ..
    time.reset_time_0()



class _MyDevices(object):
    schalter_garage = None
    watering_relais_rail_1 = None
    #schalter_schuppen = None
    #schalter_wozi_1 = None
    #schalter_wozi_2 = None
    
    @classmethod
    def init(cls, ccu):
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"WateringRelais1")
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.schalter_schuppen = ccu.devices.get_by_name(u"SchalterSchuppen")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            #oben-links = Hauptventil
            #oben-rects = Watering gesamt
            #mitte-links = Watering sued
            #mitte-rechts = Watering west