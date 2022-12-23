
# encoding: utf-8


import time
import inspect
import pmatic
from pmatic import entities, ccu
pmatic.logging(pmatic.INFO)


#HENNING BEGINN
class _MonkeyPatcher(object):
    @classmethod
    def do_patch(cls):
        entities.HM_PB_2_WM55_2 = cls.HM_PB_2_WM55_2
        entities.HM_PB_6_WM55 = cls.HM_PB_6_WM55
        entities.Devices.get_first = cls.get_first
        entities.Devices.get_by_name = cls.get_by_name
        ccu.CCU._get_events = cls._get_events
        ccu.CCU.events = property(ccu.CCU._get_events)  # @UndefinedVariable
        cls.re_init_entities_globals()
        
    @staticmethod
    def re_init_entities_globals():
        device_classes_by_type_name = {}
        for key in dir(entities):
            val = getattr(entities, key)
            if isinstance(val, type):
                if issubclass(val, entities.Device) and key != u"Device":
                    device_classes_by_type_name[val.type_name] = val
        entities.device_classes_by_type_name = device_classes_by_type_name
        channel_classes_by_type_name = {}
        for key in dir(entities):
            val = getattr(entities, key)
            if isinstance(val, type):
                if issubclass(val, entities.Channel) and val != entities.Channel:
                    channel_classes_by_type_name[val.type_name] = val
        entities.channel_classes_by_type_name = channel_classes_by_type_name
    
    class HM_PB_2_WM55_2(entities.Device):
        type_name = u"HM-PB-2-WM55-2"
    
        @property
        def switch_top(self):
            u"""Provides to the :class:`.ChannelKey` object of the first switch."""
            return self.channels[1]
    
        @property
        def switch_bottom(self):
            u"""Provides to the :class:`.ChannelKey` object of the second switch."""
            return self.channels[2]
    
    # Funk-Taster 6-fach  
    class HM_PB_6_WM55(entities.Device):
        type_name = u"HM-PB-6-WM55"
    
        @property
        def switch_top_left(self):
            u"""Provides to the :class:`.ChannelKey` object of the first switch."""
            return self.channels[1]
    
        @property
        def switch_top_right(self):
            u"""Provides to the :class:`.ChannelKey` object of the second switch."""
            return self.channels[2]
    
        @property
        def switch_middle_left(self):
            u"""Provides to the :class:`.ChannelKey` object of the first switch."""
            return self.channels[3]
    
        @property
        def switch_middle_right(self):
            u"""Provides to the :class:`.ChannelKey` object of the first switch."""
            return self.channels[4]
    
        @property
        def switch_bottom_left(self):
            u"""Provides to the :class:`.ChannelKey` object of the first switch."""
            return self.channels[5]
    
        @property
        def switch_bottom_right(self):
            u"""Provides to the :class:`.ChannelKey` object of the first switch."""
            return self.channels[6]
        
    @staticmethod
    def get_by_name(self, device_name):
        devs = self.query(device_name=device_name)
        first_adr = devs.addresses()[0] if len(devs) > 0 else u""
        return self._devices.get(first_adr, None)
    
    @staticmethod
    def get_first(self):
        first_adr = self.addresses()[0] if len(self._devices) > 0 else u""
        return self._devices.get(first_adr, None)
    
    @staticmethod
    def _get_events(self):
        u"""Using this property you can use the XML-RPC event listener of pmatic.
        Provides access to the XML-RPC :class:`pmatic.events.EventListener` instance."""
        if not self._events:
            self._events = pmatic.events.EventListener(self, listen_address=(u"", 1339))
        return self._events
    
_MonkeyPatcher.do_patch()
#HENNING ENDE

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
ccu = pmatic.CCU(
    # TODO: Replace this with the URL to your CCU2.
    address=u"http://172.19.76.6",
    # TODO: Insert your credentials here.
    credentials=(u"Admin", u"YetAPW123"),
    connect_timeout=12
)
#ccu = pmatic.CCU()

# Get all HM-Sec-SC (shutter contact) devices
print(u"Get devices")
#schalter_garage = ccu.devices.query(device_name=u"SchalterGarage").get_first()
schalter_garage = ccu.devices.get_by_name(u"SchalterGarage")
schalter_wozi_1 = ccu.devices.get_by_name(u"SchalterGarage")
#all_devs = ccu.devices.query(device_name_regex=u".*")
#schalter_garage = all_devs.get_device_or_channel_by_address(u'MEQ0741367')


def _print_param(param):
    print(u"id: {}".format(param.id)) #PRESS_SHORT, PRESS_LONG, PRESS_LONG_RELEASE
    if hasattr(param, u"control"):
        print(u"control: {}".format(param.control)) #BUTTON.SHORT, BUTTON.LONG
    print(u"ch.name: {}".format(param.channel.name)) #SchalterGarageHoch/Runter

def _print_details(obj):
    for attrn in dir(obj):
        if attrn.startswith(u"_"):
            continue
        try:
            attr = getattr(obj, attrn)
            if inspect.ismethod(attr):
                continue
            print(u"{}: {}".format(attrn, attr))
        except:
            print(u"{}: Not readable".format(attrn))

def _print_dict_details(dict_):
    for key in dict_:
        try:
            val = dict_[key]
            print(u"For key {}".format(key))
            _print_details(val)
        except:
            print(u"{}: Key not readable".format(key))

# ===== Update
# id: PRESS_SHORT
# control: BUTTON.SHORT
# ch.name: SchalterGarage_DruckOben
#   
# ===== Update
# id: PRESS_SHORT
# control: BUTTON.SHORT
# ch.name: SchalterGarage_DruckUnten
#   
# ===== Update
# id: PRESS_LONG
# control: BUTTON.LONG
# ch.name: SchalterGarage_DruckUnten
#   
# ===== Update
# id: PRESS_LONG_RELEASE
# ch.name: SchalterGarage_DruckUnten


# This function is executed on each state change
def print_summary_state_update(param):
    # Format the time of last change for printing
    #last_changed = time.strftime(u"%Y-%m-%d %H:%M:%S", time.localtime(param.last_changed))
    if u"INSTALL_TEST" in param.id.upper():
        return
    print(u"===== Update")
    #msg = u"Event update: {}, {}".format(param.channel.device.name, param.channel.summary_state)
    #print(msg)
    _print_param(param)
    #msg = u"%s %s %s" % (last_changed, param.channel.device.name, param.channel.summary_state)4
    #print(u">>param:")
    #_print_details(param)
    #print(u">>param.channel:")
    #_print_details(param.channel)
    #print(u">>param.channel.values:")
    #_print_dict_details(param.channel.values)
    #print(u">>param.channel.device:")
    #_print_details(param.channel.device)
    print(u"  ")
    #pmatic.logger.info(msg)

# This function is executed on each state change
def print_summary_state_change(param):
    # Format the time of last change for printing
    #last_changed = time.strftime(u"%Y-%m-%d %H:%M:%S", time.localtime(param.last_changed))
    print(u"===== Change")
    _print_param(param)
#     msg = u"Event changed: {}, {}".format(param.channel.device.name, param.channel.summary_state)
#     print(msg)
#     #msg = u"%s %s %s" % (last_changed, param.channel.device.name, param.channel.summary_state)
#     print(u"param:")
#     _print_details(param)
#     print(u"param.channel:")
#     _print_details(param.channel)
#     print(u"param.channel.device:")
#     _print_details(param.channel.device)
    #print(u"  ")
    #pmatic.logger.info(msg)
    pass
    
# Register event handler for all grouped devices. It is possible to register to device
# specific events like on_closed and on_opend or generic events like on_value_changed:
#devices.on_opend(print_summary_state)
#devices.on_closed(print_summary_state)
print(u"Register callback")
schalter_garage.on_value_updated(print_summary_state_update)
schalter_garage.on_value_changed(print_summary_state_change)
#devices.on_value_updated(print_summary_state)


print(u"Init events")
ccu.events.init()

# Now wait for changes till termination of the program
print(u"Wait events")
print(u"   ")
ccu.events.wait(timeout=30)
print(u"   ")
print(u"Close events")
ccu.events.close()
print(u"Finished")
