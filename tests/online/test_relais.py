
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
        entities.Devices.get_first = cls.get_first
        entities.Devices.get_by_name = cls.get_by_name
        entities.HM_PB_2_WM55_2 = cls.HM_PB_2_WM55_2
        entities.HM_LC_Sw4_DR = cls.HM_LC_Sw4_DR
        ccu.CCU._get_events = cls._get_events
        ccu.CCU.events = property(ccu.CCU._get_events)  # @UndefinedVariable
    
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
    
    # Funk-Schaltaktor 4-fach
    class HM_LC_Sw4_DR(entities.Device):
        type_name = u"HM-LC-Sw4-DR"
    
        # Make methods of ChannelSwitch() available
        def __getattr__(self, attr):
            return getattr(self.channels[1], attr)
    
        @property
        def summary_state(self):
            return super(_MonkeyPatcher.HM_LC_Sw4_DR, self)._get_summary_state()
    
        @property
        def switch1(self):
            return self.channels[1]
    
        @property
        def switch2(self):
            return self.channels[2]
    
        @property
        def switch3(self):
            return self.channels[3]
    
        @property
        def switch4(self):
            return self.channels[4]
        
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
bewasserung_relais = ccu.devices.get_by_name(u"WateringRelais1")
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

bewasserung_relais.switch1.switch_on()
bewasserung_relais.switch1.switch_off()
# Register event handler for all grouped devices. It is possible to register to device
# specific events like on_closed and on_opend or generic events like on_value_changed:
#devices.on_opend(print_summary_state)
#devices.on_closed(print_summary_state)

