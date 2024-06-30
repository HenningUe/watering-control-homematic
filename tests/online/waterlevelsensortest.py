# encoding: utf-8

from __future__ import unicode_literals

import time
import threading
from operator import isCallable

import pmatic  # @Reimport
from pmatic import (entities, ccu, notify)  # @UnusedImport @Reimport

time.sleep(2.0)

ccu_obj = None


class _MonkeyPatcher(object):

    @classmethod
    def do_patch(cls):
        entities.HM_PB_2_WM55_2 = cls.HM_PB_2_WM55_2
        entities.HM_PB_6_WM55 = cls.HM_PB_6_WM55
        entities.HM_LC_Sw4_DR = cls.HM_LC_Sw4_DR
        entities.HM_SCI_3_FM = cls.HM_SCI_3_FM
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

    # Funk-Taster 2-fach
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
        def relais1(self):
            return self.channels[1]

        @property
        def relais2(self):
            return self.channels[2]

        @property
        def relais3(self):
            return self.channels[3]

        @property
        def relais4(self):
            return self.channels[4]

    # Funk-Tür-/ Fensterkontakt  (als Fuellstandssensor verwendet)
    class HM_SCI_3_FM(entities.Device):
        type_name = "HM-SCI-3-FM"

        # Make methods of ChannelShutterContact() available
        def __getattr__(self, attr):
            return getattr(self.channels[1], attr)

        @property
        def shutter_contact_empty_channel(self):
            return self.channels[1]

        @property
        def shutter_contact_empty_is_open(self):
            return self.shutter_contact_empty_channel.is_open

#         @shutter_contact_empty_is_open.setter
#         def shutter_contact_empty_is_open(self, value):
#             self.channels[1].values["STATE"].value = value

        @property
        def shutter_contact_full_channel(self):
            return self.channels[2]

        @property
        def shutter_contact_full_is_open(self):
            return self.shutter_contact_full_channel.is_open

        @property
        def shutter_contact_active_channel(self):
            return self.channels[3]

        @property
        def shutter_contact_activated_is_open(self):
            return self.shutter_contact_active_channel.is_open

    @staticmethod
    def get_by_name(self, device_name):
        devs = self.query(device_name=device_name)
        first_adr = devs.addresses()[0] if len(devs) > 0 else u""
        return self._devices.get(first_adr, None)

    @staticmethod
    def get_by_name_offsim(self, device_name):
        for k in self._devices:
            v = self._devices[k]
            if v.name == device_name:
                return v

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


class IterantExecSampler(object):

    def __init__(self, sampler_func, max_try_count=1,
                 intermediate_wait_time=5.0, exec_types_to_catch=None,
                 exec_type_to_raise=None):
        self.sampler_func = sampler_func
        self.max_try_count = max_try_count
        self.intermediate_wait_time = intermediate_wait_time
        self._exec_types_to_catch = exec_types_to_catch
        self._exec_type_to_raise = exec_type_to_raise
        self._try_counter = 0

    def run(self, *args, **kwargs):  # @IgnorePep8
        f_name = self.sampler_func.func_name
        while True:
            self._try_counter += 1
            try:
                return self.sampler_func(*args, **kwargs)
            except Exception as ex:
                if self._exec_types_to_catch is not None \
                   and type(ex) not in self._exec_types_to_catch:
                    raise
                if self._try_counter >= self.max_try_count:
                    msg = ("  Function '{}' failed after {} trails."
                           .format(f_name, self._try_counter))
                    print(msg, "Function '{}' failure".format(f_name))
                    if self._exec_type_to_raise is None:
                        raise
                    else:
                        raise self._exec_type_to_raise()
                else:
                    msg = ("  Function '{}' failed after {} trails. Next try ..".
                           format(f_name, self._try_counter))
                    print(msg, "Function '{}' failure".format(f_name))
                intm_wait_time = self.intermediate_wait_time
                if isCallable(self.intermediate_wait_time):
                    intm_wait_time = self.intermediate_wait_time(self._try_counter)
                time.sleep(intm_wait_time)


class WaterLevelSensors(object):
    _sensors = dict()

    @classmethod
    def init_devices(cls):
        for sensor_name in (u"FuellstandSensorSued", u"FuellstandSensorWest"):
            real_sensor = ccu_obj.devices.get_by_name(sensor_name)
            cls._sensors[sensor_name] = real_sensor
            real_sensor.on_value_updated(cls.callback_router)

    @classmethod
    def callback_router(cls, param):

        def get_lock(lstore=dict()):
            if u'lock' not in lstore:
                lstore[u'lock'] = threading.RLock()
            return lstore[u'lock']

        with get_lock():
            cls.callback_router_locked(param)

    @classmethod
    def callback_router_locked(cls, param):
        device_name = param.channel.device.name  # 'FuellstandSensorSued'
        print(u"     param.device.name: {}".format(device_name))
        ch_name = param.channel.name  # 'FuellstandSensorSuedLeer'
        print(u"EVENT: channel.name: {}".format(ch_name))
        if ch_name == "Maintenance":
            return
        print(u"     param.control: {}".format(getattr(param, 'control', "unknown")))
        print(u"     param.id: {}".format(getattr(param, 'id', "unknown")))
        print(u"     param.flags: {}".format(getattr(param, 'flags', "unknown")))
        print(u"     param.operations: {}".format(getattr(param, 'operations', "unknown")))
        print(u"     param.internal_name: {}".format(getattr(param, 'internal_name', "unknown")))
        print(u"     unicode(param): {}".format(unicode(param)))


def create_ccu_obj():
    global ccu_obj
    # Open up a remote connection via HTTP to the CCU and login as admin. When the connection
    # can not be established within 5 seconds it raises an exception.
    kwargs = {
        # TODO: Replace this with the URL to your CCU2.
        u'address': u"http://172.19.76.11",
        # TODO: Insert your credentials here.
        u'credentials': (u"Admin", u"YetAPW123"),
        u'connect_timeout': 12}
    ccu_obj = pmatic.CCU(**kwargs)
    return ccu_obj


class MainLoop(object):

    @classmethod
    def main_event_loop(cls, sim_func):
        global logger
        print(u"Starting main")
        cls.main_event_loop_ex(sim_func)
        # func_sampler = IterantExecSampler(cls.main_event_loop_ex, max_try_count=5,
        #                                   intermediate_wait_time=60.0,
        #                                   exec_types_to_catch=(pmatic.PMConnectionError,
        #                                                        pmatic.PMException))
        # func_sampler.run(sim_func)

    @classmethod
    def main_event_loop_ex(cls, sim_func=None):
        global logger
        # INIT_WAIT_SEC = 10
        # print(u"Initially waiting {} sec".format(INIT_WAIT_SEC))
        # time.sleep(INIT_WAIT_SEC)
        create_ccu_obj()
        print(u"Init devices")
        WaterLevelSensors.init_devices()
        cls._init_events()
        cls._main_event_loop_normalmode()
        print(u"Finished main")

    @staticmethod
    def _init_events():
        global ccu_obj
        print(u"Init events")
        # func_sampler = IterantExecSampler(ccu_obj.events.init, max_try_count=5,
        #                                   intermediate_wait_time=lambda tc: tc * 5.0,)
        # func_sampler.run()
        ccu_obj.events.init()
        print("  Events successfully initialized")

    @staticmethod
    def _main_event_loop_offsimmode(sim_func):
        global ccu_obj
        sim_func(ccu_obj)

    @classmethod
    def _main_event_loop_normalmode(cls):
        global ccu_obj
        rcp_server = ccu_obj.events._server
        try:
            print(u"=========================================")
            print(u"READY: Waiting for events ..")
            print("Successfully initialized. Waiting for events ..",
                  "Successfully initialized")
            cls._wait_events(rcp_server)
        finally:
            rcp_server.stop()
            rcp_server.join()
            print(u"Close events")
            ccu_obj.events.close()

    @classmethod
    def _wait_events(cls, rcp_server, timeout=None):
        while rcp_server.is_alive():
            time.sleep(0.1)
            if timeout is not None:
                timeout -= 0.1
                if timeout <= 0:
                    break
        return rcp_server.is_alive()


def run(sim_func=None):
    MainLoop.main_event_loop(sim_func)


if __name__ == u"__main__":

    run()
