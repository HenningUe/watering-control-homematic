
# encoding: utf-8


from ... import consts, actionstorage, simtime as time, simthread

from .. import _sensortrigger, _plotbyhand, _plotter
    

def simulate(ccu):
    _MyDevices.init(ccu)
    _run_scenario()
    _create_byhand_plot()
    _plotter.plot_variables(__file__)
    

def _run_scenario():
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_schuppen.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten*2.5)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.ActorConstants.dauer_relais_schalten*0.2)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine*0.5)
    _sensortrigger.trigger_event_but_short(_MyDevices.schalter_schuppen.switch_top)
    simthread.wait_till_all_threads_are_finished()
    

def _create_byhand_plot():
    time.set_time_modus_to_simulation()
    actionstorage.set_storage_type_to_byhand()
    ### Sensoren ..
    #Schalter Garage
    _plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)
    
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
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"BewaesserungRelais1")
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.schalter_schuppen = ccu.devices.get_by_name(u"SchalterSchuppen")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            #oben-links = Hauptventil
            #oben-rects = Bewaesserung gesamt
            #mitte-links = Bewaesserung sued
            #mitte-rechts = Bewaesserung west