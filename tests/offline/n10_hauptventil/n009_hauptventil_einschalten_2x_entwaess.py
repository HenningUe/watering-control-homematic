
# encoding: utf-8


from ... import consts, actionstorage, simtime as time, simthread

from .. import sensortrigger, plotbyhand, plotter
    

def simulate(ccu):
    _MyDevices.init(ccu)
    _run_scenario()
    _create_byhand_plot()
    plotter.plot_variables()
    

def _run_scenario():
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_top)
    time.sleep(consts.TimeConstants.dauer_hauptventil_alleine*0.5)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_bottom)
    time.sleep(4)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_bottom)
    time.sleep(1)
    sensortrigger.trigger_event_but_short(_MyDevices.schalter_garage.switch_bottom)
    simthread.wait_till_all_threads_are_finished()
    

def _create_byhand_plot():
    time.set_time_modus_to_simulation()
    actionstorage.set_storage_type_to_byhand()
    
    ### Sensoren ..
    plotbyhand.add_sensor_event(_MyDevices.schalter_garage.switch_top)


class _MyDevices(object):
    schalter_garage = None
    watering_relais_rail_1 = None
    #schalter_schuppen = None
    #schalter_wozi_1 = None
    #schalter_wozi_2 = None
    
    @classmethod
    def init(cls, ccu):
        cls.schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
        cls.watering_relais_rail_1 = ccu.devices.get_by_name(u"WateringRelais1")
        cls.schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterWoZi1")
            #oben-links = Hauptventil
            #oben-rects = Watering gesamt
            #mitte-links = Watering sued
            #mitte-rechts = Watering west