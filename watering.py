#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals

import os
import sys
import time
import datetime
import logging
import copy
import threading
from collections import defaultdict, OrderedDict, deque
from functools import wraps
import traceback
from operator import isCallable
from inspect import isclass
try:
    import multiprocessing
except Exception:
    multiprocessing = None
try:
    import watering_settings as settings
except ImportError:
    # watering_settings must have these constants    
    # USER = "<CCU2-user>"
    # PASSWORD = "<CCU2-PW>"
    # CCU_URL = "<CCU2-IP-address>"
    #
    # PUSHOVER_API_TOKEN ="<PUSHOVER_API_TOKEN>"
    # PUSHOVER_USER_TOKEN="<PUSHOVER_USER_TOKEN>"
    raise IOError("please provide watering_settings.py")

_ddatet = datetime.datetime
_tdelta = datetime.timedelta

# TODO:  # @NOSONAR @DontTrace
# > If restarted > restore old state


def runs_in_offline_sim_mode():
    return (sys.platform == "win32" and __name__ not in ["__main__", "__parents_main__"])


def runs_in_online_sim_mode():
    return (sys.platform == "win32" and __name__ in ["__main__", "__parents_main__"])


def runs_in_production():
    return (not runs_in_offline_sim_mode() and not runs_in_online_sim_mode())


if runs_in_offline_sim_mode():
    from offsim import pmaticpatched as pmatic  # @Reimport
    from offsim import consts as offsimconsts
    from offsim import devicecreator, simthread, simtime, flowerpots, simdatetime
    from offsim.pmaticpatched.exceptions import PMUserError  # @Reimport @UnusedImport
    from offsim.pmaticpatched import (entities, ccu, notify)  # @Reimport @UnusedImport
    time = simtime
    datetime = simdatetime
    _ddatet = simdatetime.datetime
    _tdelta = simdatetime.timedelta
    pmatic.logging(logging.INFO)
    logger = pmatic.logger
#     logger.setLevel(logging.INFO)
#     consoleh = logging.StreamHandler()
#     logger.addHandler(consoleh)
    logger.info("runs in runs_in_offline_sim_mode")
else:
    import pmatic  # @Reimport
    from pmatic import (entities, ccu, notify)  # @UnusedImport @Reimport
    from pmatic.exceptions import PMUserError  # @UnusedImport @Reimport
    pmatic.logging(logging.INFO)
    logger = pmatic.logger

if runs_in_online_sim_mode():
    logger.info("runs in runs_in_online_sim_mode")
    time.sleep(2.0)

elif runs_in_production():
    logger.info("runs in runs_in_production")
    time.sleep(10.0)

ccu_obj = None
script_start_time = _ddatet.now()


class WateringBaseError(Exception):
    pass


class Misc(object):

    @staticmethod
    def format_timespan(timespan):
        if isinstance(timespan, (int, float)):
            timespan = _tdelta(0, timespan)
        td = timespan
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        fmt_str = ""
        if days > 0:
            fmt_str = u"{days}d:{hours}h:{minutes}m"
        elif hours > 0:
            fmt_str = u"{hours}h:{minutes}m"
        else:
            if minutes > 0:
                fmt_str = u"{minutes}m:{seconds}s"
            else:
                fmt_str = u"{seconds} s"
        timespan_str = fmt_str.format(**locals())
        return timespan_str

    @staticmethod
    def format_time(timestamp):
        if runs_in_production():
            return "{:%d.%b %H:%M}".format(timestamp)
        else:
            return "{:%d.%b %H:%M:%S}".format(timestamp)

    @staticmethod
    def datetime_safe_replace(datetime0, **kwargs):
        try:
            dt_replaced = datetime0.replace(**kwargs)
        except ValueError as ex:
            if "day is out of range for month" not in ex.message:
                raise
            kwargs['month'] = datetime0.month + 1
            kwargs['day'] = 1
            dt_replaced = datetime0.replace(**kwargs)
        return dt_replaced


class TimerSimple(object):

    def __init__(self, timeout=0.0):
        assert(isinstance(timeout, (int, float, long,)))
        self.timeout = timeout
        self._starttime = -1.0

    def stop(self):
        self._starttime = -1.0

    def is_not_running(self):
        return not self.is_running()

    def is_running(self):
        return bool(self._starttime >= 0.0)

    def start(self):
        self._starttime = time.time()

    def is_timeout_reached(self):
        if self.is_not_running():
            raise WateringBaseError("Timer not running")
        return bool(self.get_elapsed_time() > self.timeout)

    def get_elapsed_time(self):
        if self.is_not_running():
            raise WateringBaseError("Timer not running")
        return time.time() - self._starttime


class Debug(object):
    ON = True

    @classmethod  # @IgnorePep8
    def SKIP_INIT_WAITING(cls):  # @NOSONAR @DontTrace
        ON = False
        return (ON and cls.ON)

    @classmethod  # @IgnorePep8
    def ADAPT_TIMES(cls):  # @NOSONAR @DontTrace
        ON = False
        return (ON and cls.ON)

    @classmethod  # @IgnorePep8
    def OMIT_PUSHOVER_SEND(cls):  # @NOSONAR @DontTrace
        ON = False
        return (ON and cls.ON)

    @classmethod  # @IgnorePep8
    def VERBOSE_CHN_INFO(cls):  # @NOSONAR @DontTrace
        ON = False
        return (ON and cls.ON)

    @classmethod  # @IgnorePep8
    def LIMIT_SCRIPT_TIMEOUT(cls):  # @NOSONAR @DontTrace
        ON = False
        return (ON and cls.ON)

    @classmethod  # @IgnorePep8
    def DEBUG_OUTOUT(cls):  # @NOSONAR @DontTrace
        ON = True
        return (ON and cls.ON)


class DebugExceptionSim(object):
    ON = False
    SIM_RELAIS_EX_IS_ON = True
    WAIT_TIME_BEFORE_FIRST_ERROR_TIME_IN_SEC = 30.0
    state_holder = dict()
    my_time = time.time()

    @classmethod
    def is_on(cls):
        return (cls.ON
                and not runs_in_production()
                and time.time() - cls.my_time > cls.WAIT_TIME_BEFORE_FIRST_ERROR_TIME_IN_SEC)

    @classmethod  # @IgnorePep8
    def get_sim_relais_ex(cls):
        return cls.is_on() and cls.SIM_RELAIS_EX_IS_ON

    @classmethod
    def sim_relais_oeffne_in(cls):
        if not cls.get_sim_relais_ex():
            return
        ACT_COUNT_TRESHOLD = 1
        if 'sim_relais_oeffne_in' not in cls.state_holder:
            cls.state_holder['sim_relais_oeffne_in'] = 0
        cls.state_holder['sim_relais_oeffne_in'] += 1
        print("sim_relais_oeffne_in {}".format(cls.state_holder['sim_relais_oeffne_in']))
        if cls.state_holder['sim_relais_oeffne_in'] >= ACT_COUNT_TRESHOLD:
            cls.state_holder['sim_relais_oeffne_in'] = 0
            print('pmatic.PMException')
            raise pmatic.PMException()


class PushoverPatched(notify.Pushover):

    @classmethod
    def send(cls, message, title=None, api_token=None, user_token=None,
             priority=None):
        """Send a notification via pushover.net.

        This class method can be used to send out custom notifiations to your tablet or
        mobile phone using pushover.net. To be able to send such notifications you need
        to register with pushover.net, register your appliation to obtaion an API token
        and a user or group token.

        If you have both, you can use this class method to send a notification containing
        only a *message*. But you can also provide an optional *title*.

        It returns ``True`` when the notification has been sent or raises a
        :class:`.pmatic.PMUserError` when either an invalid *message* or *title* is provided.
        In case of errors during sending the notification, a :class:`.pmatic.PMException`
        is raised.
        """
        import pmatic.utils as utils            
        try:
            from urllib.request import urlopen
        except ImportError:
            from urllib2 import urlopen        
        try:
            # Python 2
            from urllib import urlencode
        except ImportError:
            # Python 3+
            from urllib.parse import urlencode
        
        api_token, user_token = cls._load_tokens(api_token, user_token)

        if not message:
            raise PMUserError("A message has to be specified.")
        if not utils.is_text(message):
            raise PMUserError("The message needs to be a unicode string.")

        encoded_msg = message.encode("utf-8")
        if len(encoded_msg) > 1024:
            raise PMUserError("The message exceeds the maximum length of 1024 characters.")

        msg = [
            ("token", api_token.encode("utf-8")),
            ("user", user_token.encode("utf-8")),
            ("message", encoded_msg),
        ]

        if title != None:
            if not utils.is_text(title):
                raise PMUserError("The title needs to be a unicode string.")

            encoded_title = title.encode("utf-8")
            if len(encoded_title) > 250:
                raise PMUserError("The title exceeds the maximum length of 250 characters.")
            msg.append(("title", encoded_title))
        if priority is not None:
            if priority == "urgent":
                priority = 2
            else:
                raise ValueError("priority")
            msg.append(("priority", priority))
            if priority == 2:
                # expire and retry needed with priority "urgend"
                msg.append(("expire", 10 * 60))  # expiration time in seconds
                msg.append(("retry", 2 * 60))  # time to retry in seconds

        handle = urlopen("https://api.pushover.net/1/messages.json",
                         data=urlencode(msg).encode("utf-8"))
        return cls._check_response(handle)


class Log(object):
    _funcs_ids = defaultdict(int)

    @staticmethod
    def init():        
        PushoverPatched.set_default_tokens(api_token=settings.PUSHOVER_API_TOKEN,
                                           user_token=settings.PUSHOVER_USER_TOKEN)

    @classmethod
    def info_pushover(cls, msg, title=None, force=False):
        global logger
        if force or runs_in_production():
            logger.info(msg)
            cls._pushover_send_msg_ex_catched(msg, title)
        else:
            logger.info("[PUSHOVER] {}".format(msg))

    @classmethod
    def warning_pushover(cls, msg, title=None):
        global logger
        if runs_in_production():
            logger.warning(msg)
            cls._pushover_send_msg_ex_catched("WARNING: {}".format(msg), title)
        else:
            logger.warning("[PUSHOVER] {}".format(msg))

    @classmethod
    def error_pushover(cls, msg, title=None):
        global logger
        if runs_in_production():
            logger.error(msg)
            cls._pushover_send_msg_ex_catched("ERROR: {}".format(msg),
                                              title, priority="urgent")
        else:
            logger.error("[PUSHOVER] {}".format(msg))

    @staticmethod
    def logfunc_deco(the_function):
        func_name = Log._get_func_name_id(the_function.__name__)
        if hasattr(the_function, 'im_func'):
            the_function.im_func._unique_name = func_name
        else:
            the_function._unique_name = func_name

        @wraps(the_function)  # @IgnorePep8
        def _func_wrapper(*args, **kwargs):
            global logger
            try:
                Log._logfunc(func_name, u"started")
                return the_function(*args, **kwargs)
            finally:
                Log._logfunc(func_name, u"finished")

        return Log.logex_deco(_func_wrapper)

    @staticmethod
    def logex_deco(the_function):
        func_name = the_function.__name__

        @wraps(the_function)  # @IgnorePep8
        def _func_wrapper(*args, **kwargs):
            global logger
            try:
                return the_function(*args, **kwargs)
            except Exception:
                msg = u"Unhandled Exception in '{}'".format(func_name)
                logger.exception(msg)
                Log._pushover_send_ex()
                raise

        return _func_wrapper

    @staticmethod
    def _logfunc(func_name, whathappened, self=None):
        global logger
        if self is None:
            msg = u"Function '{}' {}".format(func_name, whathappened)
        else:
            msg = u"Method '{}' {}".format(func_name, whathappened)
        logger.info(msg)

    @classmethod
    def _pushover_send_ex(cls):
        title = u"Exception in HomeControl"
        msg = traceback.format_exc().decode(sys.getdefaultencoding())
        if runs_in_offline_sim_mode() or Debug.OMIT_PUSHOVER_SEND():
            print(u"Pushover:\n[{}]:\n{}".format(title, msg))
            return
        cls._pushover_send_msg_ex_catched(msg, title, priority="urgent")

    @staticmethod
    def _pushover_send_msg_ex_catched(msg, title, priority=None):
        if msg[0] == "\n":
            msg = msg[1:]
        try:
            PushoverPatched.send(msg, title, priority=priority)
        except Exception:
            pass

    @classmethod
    def _get_func_name_id(cls, func_name):
        cls._funcs_ids[func_name] += 1
        func_name_id = u"{}__{}".format(func_name, cls._funcs_ids[func_name] - 1)
        return func_name_id


class LogDebug(object):

    class TimeIt(object):

        def __init__(self, max_duration=0.0, msg_add=u""):
            self.max_duration = max_duration
            self._msg_add = msg_add
            self._start_time = time.time()

        def __enter__(self):  # @IgnorePep8
            self.start()
            return self

        def __exit__(self, type_, value, traceback):  # @IgnorePep8
            self.stop()

        def increase_max_duration(self, increase_time):
            self.max_duration += increase_time

        def start(self, max_duration=None):  # @IgnorePep8
            if max_duration is not None:
                self.max_duration = max_duration
            self._start_time = time.time()

        def stop(self):  # @IgnorePep8
            cur_duration = time.time() - self._start_time
            max_duration = self.max_duration
            if cur_duration > max_duration:
                msg_add = u""
                if self._msg_add:
                    msg_add = u"{}:".format(self._msg_add)
                msg = (u"{msg_add}Expected duration {max_duration} sec exceeded. "
                       u"Duration {cur_duration} sec."
                       .format(**locals()))
                LogDebug.error(msg)

    @classmethod
    def info(cls, msg):
        global logger
        if Debug.DEBUG_OUTOUT():
            logger.info(cls._add_func_id_to_msg(msg))

    @classmethod
    def debug(cls, msg):
        global logger
        if Debug.DEBUG_OUTOUT():
            logger.debug(cls._add_func_id_to_msg(msg))

    @classmethod
    def error(cls, msg):
        global logger
        if Debug.DEBUG_OUTOUT():
            logger.error(cls._add_func_id_to_msg(msg))

    @classmethod
    def create_timeit(cls, max_duration, add_msg=u""):
        return cls.TimeIt(max_duration, add_msg)

    @classmethod
    def timeit_deco(cls, max_duration, add_msg=u""):

        def timeit_f(func_outer):

            @wraps(func_outer)
            def func_inner(*args, **kwargs):
                with cls.create_timeit(max_duration, add_msg):
                    return func_outer(*args, **kwargs)

            return func_inner

        return timeit_f

    @classmethod
    def _add_func_id_to_msg(cls, msg):
        fn = cls._func_id()
        return u"    [{fn}]:{msg}".format(**locals())

    @staticmethod
    def _func_id():
        return ThreadContainer.get_thread_func_name()


class ExceptionsInThreadsContainer(object):
    thread_exceptions = deque()

    @classmethod
    def clear_threads_list(cls):
        cls.thread_exceptions = deque()

    @classmethod
    def any_threads_occured(cls):
        return len(cls.thread_exceptions) > 0

    @classmethod
    def raise_last_thread_exception_in_main_thread(cls):
        if cls.any_threads_occured():
            ex = cls.thread_exceptions[-1]
            cls.thread_exceptions = deque()
            raise ex

    @classmethod
    def reboot_on_any_exception(cls):
        if cls.any_threads_occured():
            os.system("reboot -f")

    @classmethod
    def catch_threaded_exception_deco(cls, func_outer):

        @wraps(func_outer)
        def func_inner(*args, **kwargs):
            try:
                return func_outer(*args, **kwargs)
            except Exception as ex:
                cls.thread_exceptions.append(ex)
                raise

        return func_inner


class IterantExecSampler(object):
    REFEED_KWARG_KEY = "refeed_kwarg_key"

    def __init__(self, sampler_func, max_try_count=1,
                 intermediate_wait_time=5.0, exec_types_to_catch=None,
                 exec_type_to_raise=None,
                 reboot_on_err=False):
        self.sampler_func = sampler_func
        self.max_try_count = max_try_count
        self.intermediate_wait_time = intermediate_wait_time
        self._exec_types_to_catch = exec_types_to_catch
        self._exec_type_to_raise = exec_type_to_raise
        self.reboot_on_err = reboot_on_err
        self._try_counter = 0

    def run(self, *args, **kwargs):  # @IgnorePep8 @NOSONAR
        refeed_kwargs = dict()
        while True:
            self._try_counter += 1
            try:
                kwargs.update(refeed_kwargs)
                return self._get_embedded_run_func(*args, **kwargs)
            except Exception as ex:
                if runs_in_online_sim_mode():
                    raise
                if self._exec_types_to_catch is not None \
                   and type(ex) not in self._exec_types_to_catch:
                    raise
                if hasattr(ex, self.REFEED_KWARG_KEY):
                    refeed_kwargs = getattr(ex, self.REFEED_KWARG_KEY)
                    assert(isinstance(refeed_kwargs, dict))
                f_name = self.sampler_func.func_name
                if self.max_try_count > 0 and self._try_counter >= self.max_try_count:
                    msg = ("  Function '{}' failed after {} trails."
                           .format(f_name, self._try_counter))
                    Log.error_pushover(msg, "Function '{}' failure".format(f_name))
                    if self.reboot_on_err:
                        Log.error_pushover(msg, "Restarting CCU ..")
                        os.system("/sbin/reboot")
                    if self._exec_type_to_raise is None:
                        raise
                    else:
                        raise self._exec_type_to_raise()
                else:
                    msg = ("  Function '{}' failed after {} trails. Next try ..".
                           format(f_name, self._try_counter))
                    Log.error_pushover(msg, "Function '{}' failure".format(f_name))
                intm_wait_time = self.intermediate_wait_time
                if isCallable(self.intermediate_wait_time):
                    intm_wait_time = self.intermediate_wait_time(self._try_counter)
                time.sleep(intm_wait_time)


class IterantExecSamplerForFunction(IterantExecSampler):

    def _get_embedded_run_func(self, *args, **kwargs):
        return self.sampler_func(*args, **kwargs)


class IterantExecSamplerForProcess(IterantExecSampler):

    def __init__(self, sampler_func, max_try_count=1,
                 intermediate_wait_time=5.0, exec_types_to_catch=None,
                 exec_type_to_raise=None,
                 reboot_on_err=False):
        kwargs = copy.copy(locals())
        kwargs.pop('self')
        super(IterantExecSamplerForProcess, self).__init__(**kwargs)

    def in_process_func(self, multiprc_queue):
        if not multiprc_queue.empty():
            in_vals = multiprc_queue.get()
            args = in_vals['args']
            kwargs = in_vals['kwargs']
        else:
            args = list()
            kwargs = dict()
        try:
            rtn_val = self.sampler_func(*args, **kwargs)
            rtn_val = dict(return_value=rtn_val)
        except Exception as ex:
            rtn_val = dict(last_exception=ex)
        multiprc_queue.put(rtn_val)

    def _get_embedded_run_func(self, *args, **kwargs):
        multipr_queue = multiprocessing.Queue()
        in_vals = dict(args=args, kwargs=kwargs)
        multipr_queue.put(in_vals)
        func_wrapper = self.in_process_func
        process = multiprocessing.Process(target=func_wrapper, args=(multipr_queue,))
        process.start()
        process.join()
        if not multipr_queue.empty():
            rtn_vals = multipr_queue.get()
            if rtn_vals.get('last_exception') is not None:
                raise rtn_vals['last_exception']
            else:
                return rtn_vals.get('return_value')


class ThreadContainer(object):
    thread_mode_is_active = True
    _all_sim_threads_to_be_waited_for = list()
    _all_sim_threads_to_be_terminated = list()
    _sideline_threads_must_be_terminated_flag = False
    _timer_for_threads_to_be_terminated = None

    @classmethod
    def clear_threads_lists(cls):
        cls._all_sim_threads_to_be_waited_for = list()
        cls._all_sim_threads_to_be_terminated = list()
        cls._timer_for_threads_to_be_terminated = None

    @classmethod
    def get_sideline_threads_must_be_terminated(cls):
        if runs_in_offline_sim_mode():
            if cls._sideline_threads_must_be_terminated_flag \
               or cls.all_threads_are_finished() \
               or (cls._timer_for_threads_to_be_terminated is not None
                   and cls._timer_for_threads_to_be_terminated.is_timeout_reached()):
                return True
        elif runs_in_production():
            return cls._sideline_threads_must_be_terminated_flag
        else:
            return False

    @classmethod
    def do_set_timeout_for_threads_to_be_terminated(cls, timeout):
        # for simmode
        cls._timer_for_threads_to_be_terminated = TimerSimple(timeout)
        cls._timer_for_threads_to_be_terminated.start()

    @classmethod
    def do_terminate_threads_to_be_terminated(cls):
        # for production mode
        cls._sideline_threads_must_be_terminated_flag = True
        time.sleep(0.1)

    @classmethod
    def _get_all_sim_threads_to_be_waited_for(cls):
        # IMPORTANT: DO NOT CHANGE. HAS TO BE LIKE THIS.
        # OTHERWISE '_all_sim_threads_to_be_waited_for'
        # IS RESET
        if runs_in_offline_sim_mode():
            return simthread._all_sim_threads_to_be_waited_for
        else:
            return cls._all_sim_threads_to_be_waited_for

    @classmethod
    def any_thread_is_alive(cls):
        for st in cls._get_all_sim_threads_to_be_waited_for():
            if st[u'thread'].ident != threading.current_thread().ident \
               and st[u'thread'].is_alive():
                return True
        return False

    @classmethod
    def get_thread_func_name(cls, thread_to_get_name=None):
        if thread_to_get_name is None:
            thread_to_get_name = threading.current_thread()
        for st in cls._get_all_sim_threads_to_be_waited_for():
            if st['thread'] == thread_to_get_name:
                return st['func_name']

    @classmethod
    def all_threads_are_finished(cls):
        return not cls.any_thread_is_alive()

    @classmethod
    def wait_till_all_threads_are_finished(cls, reraise_thread_exception=False):
        # for simmode
        while True:
            if cls.all_threads_are_finished():
                return
            if reraise_thread_exception:
                ExceptionsInThreadsContainer.raise_last_thread_exception_in_main_thread()
            time.sleep(0.1)

    @classmethod
    def run_threaded_wait_till_finished_deco(cls, func_outer):

        def _remove_thread_if_finished(*args, **kwargs):
            try:
                rtn = func_outer(*args, **kwargs)
            finally:
                thread_list_item = [x for x in cls._get_all_sim_threads_to_be_waited_for()
                                    if x[u'func_name'] == cls.get_func_name(func_outer)]
                if thread_list_item:
                    cls._get_all_sim_threads_to_be_waited_for().remove(thread_list_item[0])
            return rtn

        @wraps(func_outer)
        def async_func(*args, **kwargs):
            if cls.thread_mode_is_active:
                thread_hl = threading.Thread(target=_remove_thread_if_finished,
                                             args=args, kwargs=kwargs)
                thread_hl.start()
                cls._get_all_sim_threads_to_be_waited_for().append(
                    {u'thread': thread_hl, u'func_name': cls.get_func_name(func_outer)})
                return thread_hl
            else:
                return func_outer(*args, **kwargs)

        return async_func

    @classmethod
    def run_threaded_to_be_terminated_deco(cls, func_outer):

        @wraps(func_outer)
        def async_func(*args, **kwargs):
            if cls.thread_mode_is_active:
                thread_hl = threading.Thread(target=func_outer, args=args, kwargs=kwargs)
                thread_hl.start()
                cls._all_sim_threads_to_be_terminated.append(
                    {u'thread': thread_hl, u'func_name': cls.get_func_name(func_outer)})
                return thread_hl
            else:
                return func_outer(*args, **kwargs)

        return async_func

    @staticmethod
    def get_func_name(func):
        if hasattr(func, '_unique_name'):
            func_name = func._unique_name
        elif hasattr(func, 'im_func'):
            func_name = func.im_func.func_name
        else:
            func_name = func.func_name
        return func_name


class TimeConstants(object):
    # general
    dauer_entwaesserung = 20.0  # sec
    dauer_entwaesserung_lang = 5 * 60  # sec
    dauer_hauptventil_alleine = 20 * 60.0  # sec
    dauer_hauptventil_alleine_max = 60 * 60  # sec

    # balconies
    waterlvlsensor_empty_time_change_treshold = 2 * 60 * 60
    waterlvlsensor_full_time_change_treshold = 2 * 60 * 60
    autowatering_warte_zeit_bevor_start = 1 * 60 * 60
    autowatering_max_watering_time = 8 * 60
    autowatering_max_delta_zeit_zwischen_balkonen = 24 * 60 * 60
    autowatering_max_zeit_ohne_watering = 2 * 24 * 60 * 60
    history_flushing_time_span = 7 * 24 * 60 * 60

    # flower beds
    autowatering_beds_times = [datetime.time(hour=8, minute=0,), ]
    autwatering_bed_lower_watering_time = 10 * 60
    autwatering_bed_upper_watering_time = 20 * 60

    @classmethod
    def adapt_times(cls):
        if runs_in_offline_sim_mode():
            offsim_time_csts = offsimconsts.TimeConstants

            cls.dauer_entwaesserung = offsim_time_csts.dauer_entwaesserung
            cls.dauer_entwaesserung_lang = offsim_time_csts.dauer_entwaesserung_lang
            cls.dauer_hauptventil_alleine = offsim_time_csts.dauer_hauptventil_alleine
            cls.dauer_hauptventil_alleine_max = offsim_time_csts.dauer_hauptventil_alleine_max
            cls.autowatering_warte_zeit_bevor_start = \
                offsim_time_csts.autowatering_warte_zeit_bevor_start
            cls.autowatering_max_watering_time = \
                offsim_time_csts.autowatering_max_watering_time
            cls.autowatering_max_delta_zeit_zwischen_balkonen = \
                offsim_time_csts.autowatering_max_delta_zeit_zwischen_balkonen
            cls.autowatering_max_zeit_ohne_watering = \
                offsim_time_csts.autowatering_max_zeit_ohne_watering
            cls.waterlvlsensor_full_time_change_treshold = 2
            cls.history_flushing_time_span = offsim_time_csts.history_flushing_time_span
            cls.autowatering_beds_times = offsim_time_csts.autowatering_beds_times
            cls.autwatering_bed_lower_watering_time = \
                offsim_time_csts.autwatering_bed_lower_watering_time
            cls.autwatering_bed_upper_watering_time = \
                offsim_time_csts.autwatering_bed_upper_watering_time
        elif runs_in_online_sim_mode() or Debug.ADAPT_TIMES():
            cls.dauer_entwaesserung = 2.0  # sec
            cls.dauer_entwaesserung_lang = 2  # sec
            cls.dauer_hauptventil_alleine = 20.0  # sec
            cls.dauer_hauptventil_alleine_max = 60.0
            cls.autowatering_warte_zeit_bevor_start = 3.0
            cls.autowatering_max_watering_time = 70.0
            cls.autowatering_max_delta_zeit_zwischen_balkonen = 120.0
            cls.autowatering_max_zeit_ohne_watering = 160
            cls.waterlvlsensor_full_time_change_treshold = 2
            cls.history_flushing_time_span = 60


TimeConstants.adapt_times()


class LowBattReporter(object):
    low_batt_items = dict()
    _msg_repetition_period = _tdelta(days=7)

    @classmethod
    def is_low_batt_item(cls, param):
        return (param.id.upper() == "LOWBAT")

    @classmethod
    def add_low_batt_item(cls, param):
        if not cls.is_low_batt_item(param):
            return
        now = _ddatet.now()
        now_min_2 = now - (cls._msg_repetition_period + _tdelta(hours=1))
        device = param.channel.device.name
        if (now - cls.low_batt_items.get(device, now_min_2)) < cls._msg_repetition_period:
            return
        msg = ("Device {} reported low battery".format(device))
        Log.warning_pushover(msg, "Low Battery")
        cls.low_batt_items[device] = now


class LowBattReporterViaEventTracing(LowBattReporter):
    _min_check_period_sec = 30
    device_notifications = defaultdict(dict)
    _max_time_wo_notification = _tdelta(days=7)
    _last_check = time.time()

    @classmethod
    def add_device_notification(cls, param):
        now = _ddatet.now()
        device_name = param.channel.device.name
        cls.device_notifications[device_name]['last_device_notification'] = now

    @classmethod
    def check_low_bat(cls):
        if time.time() - cls._last_check < cls._min_check_period_sec:
            return
        cls._last_check = time.time()
        now = _ddatet.now()
        for device_name in cls.device_notifications:
            device_dict = cls.device_notifications[device_name]
            delta_time_since_last_msg_issue = \
                (now - device_dict.get('last_msg_issue_time', now))
            msg_to_be_sent_as_repetition_period_is_hit = (
                'last_msg_issue_time' not in device_dict
                or delta_time_since_last_msg_issue > cls._msg_repetition_period)
            delta_time_since_last_notification = \
                (now - device_dict.get('last_device_notification', now))
            too_long_no_notification = (
                delta_time_since_last_notification > cls._max_time_wo_notification)         
            if msg_to_be_sent_as_repetition_period_is_hit or too_long_no_notification:
                msg = "Device {} reported low battery.".format(device_name)
                if too_long_no_notification:
                    msg = ("{} Device did not sent notification for {}"
                           .format(Misc.format_timespan(delta_time_since_last_notification)))
                Log.warning_pushover(msg, "Low Battery")
                device_dict['last_msg_issue_time'] = now


class _RemoteRelaisSwitch4FoldBase(entities.Device):

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


class _MonkeyPatcher(object):

    @classmethod
    def do_patch(cls):
        entities.HM_PB_2_WM55_2 = cls.HM_PB_2_WM55_2
        entities.HM_PB_6_WM55 = cls.HM_PB_6_WM55
        entities.HM_LC_Sw4_DR = cls.HM_LC_Sw4_DR
        entities.HM_LC_Sw4_DR_2 = cls.HM_LC_Sw4_DR_2
        entities.HM_SCI_3_FM = cls.HM_SCI_3_FM
        if runs_in_offline_sim_mode():
            entities.Devices.get_by_name = cls.get_by_name_offsim
        else:
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
    class HM_PB_2_WM55_2(entities.Device):  # @NOSONAR @DontTrace
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
    class HM_PB_6_WM55(entities.Device):  # @NOSONAR @DontTrace
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
    class HM_LC_Sw4_DR(_RemoteRelaisSwitch4FoldBase):  # @NOSONAR @DontTrace
        type_name = u"HM-LC-Sw4-DR"

    # Funk-Schaltaktor 4-fach, New Generation
    class HM_LC_Sw4_DR_2(_RemoteRelaisSwitch4FoldBase):  # @NOSONAR @DontTrace
        type_name = u"HM-LC-Sw4-DR-2"

    # Funk-Tuer-/ Fensterkontakt  (als Fuellstandssensor verwendet)
    class HM_SCI_3_FM(entities.Device):  # @NOSONAR @DontTrace
        type_name = "HM-SCI-3-FM"

        # Make methods of ChannelShutterContact() available
        def __getattr__(self, attr):
            return getattr(self.channels[1], attr)

        def set_linked_flower_pot(self, linked_flower_pot):
            if runs_in_offline_sim_mode():
                self._linked_flower_pot = linked_flower_pot

        @property
        def shutter_contact_empty_channel(self):
            return self.channels[1]

        @property
        def shutter_contact_empty_is_open(self):
            if runs_in_offline_sim_mode() and hasattr(self, '_linked_flower_pot'):
                if self._linked_flower_pot.is_empty():
                    return flowerpots.MappingSensorLevelToContactStates.is_empty
                else:
                    return not flowerpots.MappingSensorLevelToContactStates.is_empty
            else:
                return self.shutter_contact_empty_channel.is_open

        @property
        def shutter_contact_full_channel(self):
            return self.channels[2]

        @property
        def shutter_contact_full_is_open(self):
            if runs_in_offline_sim_mode() and hasattr(self, '_linked_flower_pot'):
                if self._linked_flower_pot.is_full():
                    return flowerpots.MappingSensorLevelToContactStates.is_full
                else:
                    return not flowerpots.MappingSensorLevelToContactStates.is_full
            else:
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


class TimeLineAnalyser(object):

    @staticmethod
    def is_at_dewatering(timeline=None):
        if timeline is None:
            timeline = TimeLineWorker.get_timeline()
        return any([tl_item for tl_item in timeline
                    if (tl_item.event_bound == EventDeWatering)])

    @staticmethod
    def is_any_non_dewatering_item(timeline=None):
        if timeline is None:
            timeline = TimeLineWorker.get_timeline()
        return any([tl_item for tl_item in timeline
                    if tl_item.event_bound != EventDeWatering])

    @classmethod
    def is_at_balcony_watering(cls, timeline=None, valve=None):
        if valve is None:
            valve = EventValveNames.watering_balcony
        return cls.is_at_watering(timeline, valve)

    @staticmethod
    def is_at_watering(timeline=None, valve=None):
        if timeline is None:
            timeline = TimeLineWorker.get_timeline()
        if valve is None:
            valve = EventValveNames.watering
        tl_items = [tl_item for tl_item in timeline
                    if tl_item.valve.startswith(valve)]
        is_at_balcony_watering = (len(tl_items) > 0)
        return is_at_balcony_watering

# special
# double press lengthen watering
# manual warter start interrupted by water full
# double press manuel water = interrupt


class TimeLineWorker(object):
    events = list()
    _timeline = list()
    _timeline_copy_for_static_analysis = list()
    _lock_event = threading.RLock()
    _lock_timeline = threading.RLock()
    _is_at_dewatering = False
    _valve_mapping = dict(main_valve="watering_relais_rail_1.relais1",
                          dewater_valve="watering_relais_rail_1.relais2",
                          watering_balcony_south="watering_relais_rail_1.relais3",
                          watering_balcony_west="watering_relais_rail_1.relais4",
                          watering_bed_lower="watering_relais_rail_2.relais1",
                          watering_bed_upper="watering_relais_rail_2.relais2",)

    @classmethod
    def run_continuously(cls):
        func_wrap = cls._run_continuously
        func_wrap = ExceptionsInThreadsContainer.catch_threaded_exception_deco(func_wrap)
        func_wrap = Log.logex_deco(func_wrap)
        thread_hl = threading.Thread(target=func_wrap)
        thread_hl.start()

    @classmethod
    def _run_continuously(cls):
        while True:
            cls._check_events()
            cls._execute_timeline_items()
            cls._check_timeline_dewatering()
            time.sleep(0.01)
            if cls.break_required():
                return

    @classmethod
    def break_required(cls):
        return (ThreadContainer.get_sideline_threads_must_be_terminated()
                or ExceptionsInThreadsContainer.any_threads_occured())

    @classmethod
    def get_timeline(cls):
        with cls._lock_timeline:
            return cls._timeline_copy_for_static_analysis

    @classmethod
    def add_event_item(cls, new_events,):
        with cls._lock_event:
            if isclass(new_events):
                new_events = new_events()
            if isinstance(new_events, EventItemBase):
                new_events = [new_events]
            # check if there are events, which not allowed to appear multiple times
            events_uc = [unicode(ev) for ev in cls.events]
            new_events = [ev for ev in new_events
                          if ev.multiple_items_allowed or
                          (not ev.multiple_items_allowed and unicode(ev) not in events_uc)]
            if not any(new_events):
                return
            cls.events.extend(new_events)
            # Preliminary added to _timeline_copy_for_static_analysis for TimelineAnalyser
            cls._check_events(persistent=False)

    @classmethod
    def _check_events(cls, persistent=True, _static=dict()):  # @NOSONAR @DontTrace
        with cls._lock_event:
            if not cls.events:
                return
            timeline_changed = cls._get_safe_timelinecopy()
            len_tl_items_before = len(timeline_changed)
            for event in cls.events:
                timeline_changed = event.modify_timeline_items(timeline_changed)
                timeline_changed.sort(key=lambda tl: tl.time_stamp)
            tl_items_added = (len(timeline_changed) > len_tl_items_before)
            tl_items_initially_added = (tl_items_added and len_tl_items_before == 0)
            if tl_items_initially_added \
               or (tl_items_added and TimeLineAnalyser.is_at_dewatering(timeline_changed)):
                timeline_changed = cls._add_main_valve_timeline(timeline_changed)

            if persistent:
                event_msg = ", ".join([unicode(e) for e in cls.events])
                if _static.get('last_event_msg', None) != event_msg:
                    _static['last_event_msg'] = event_msg
                    logger.info("\n++ TIMELINE-EVENTS: {}".format(event_msg))
                cls._analyse_timeline_changes_due_to_events(cls._timeline, timeline_changed)
                cls._timeline = timeline_changed
                cls._timeline_copy_for_static_analysis = cls._get_safe_timelinecopy()
                cls.events = list()
            else:
                cls._timeline_copy_for_static_analysis = timeline_changed

    @classmethod
    def _execute_timeline_items(cls):
        global logger
        if not any(cls._timeline):
            return
        c_tl_item = cls._timeline[0]
        if _ddatet.now() > c_tl_item.time_stamp:
            cls._timeline = cls._timeline[1:]
            cls._timeline_copy_for_static_analysis = cls._get_safe_timelinecopy()
            valve_relais_name_full = cls._valve_mapping.get(c_tl_item.valve, None)
            if valve_relais_name_full is not None:
                relais_ledge_name, valve_relais_name = valve_relais_name_full.split(".")
                relais_ledge = getattr(WateringControlRelais, relais_ledge_name)
                valve_relais = getattr(relais_ledge, valve_relais_name)
                if c_tl_item.valve_state == "open":
                    valve_relais.oeffne()
                elif c_tl_item.valve_state == "close":
                    valve_relais.schliesse()
            logger.info("\n++ RELAIS: {} ({}) is {}d"
                        .format(c_tl_item.valve, valve_relais_name_full, c_tl_item.valve_state))

    @classmethod
    def _check_timeline_dewatering(cls, _static=dict()):  # @NOSONAR @DontTrace
        global logger
        if _static.get('is_any_non_dewatering_item_at_last_step', False) \
           and not TimeLineAnalyser.is_any_non_dewatering_item(cls._timeline):
            cls._timeline = cls._add_dewatering_timeline(cls._timeline)
            cls._timeline_copy_for_static_analysis = cls._get_safe_timelinecopy()
            logger.info("** Dewatering added")
            cls._print_timeline_formatted()
        _static['is_any_non_dewatering_item_at_last_step'] = \
            TimeLineAnalyser.is_any_non_dewatering_item(cls._timeline)

    @classmethod
    def _get_safe_timelinecopy(cls):
        with cls._lock_timeline:
            timeline_copy = copy.deepcopy(cls._timeline)
        return timeline_copy

    @classmethod
    def _analyse_timeline_changes_due_to_events(cls, timeline_before, timeline_changed):
        global logger
        last_time_stamp = None
        if timeline_before:
            last_time_stamp = timeline_before[-1].time_stamp
        len_tl_items_before = len(timeline_before)
        tl_items_added = (len(timeline_changed) > len_tl_items_before)
        tl_items_removed = (len(timeline_changed) < len_tl_items_before)
        tl_items_modified = (timeline_changed
                             and last_time_stamp != timeline_changed[-1].time_stamp)
        if tl_items_added:
            logger.info("\n++ TIMELINE-MODIFICATION: item(s) added\n{}"
                        .format(cls._get_timeline_formatted(timeline_changed)))
        elif tl_items_removed:
            logger.info("\n++ TIMELINE-MODIFICATION: item(s) removed\n{}"
                        .format(cls._get_timeline_formatted(timeline_changed)))
        elif tl_items_modified:
            logger.info("\n++ TIMELINE-MODIFICATION: item(s) modified\n{}"
                        .format(cls._get_timeline_formatted(timeline_changed)))

    @classmethod
    def _add_main_valve_timeline(cls, timeline):
        now = _ddatet.now() - _tdelta(seconds=1)
        timeline = cls._clear_main_valve_timeline_items(timeline)
        timeline.extend([TimeLineItemDewaterValve("close", now - _tdelta(milliseconds=100)),
                         TimeLineItemMainValve("open", now)])
        timeline.sort(key=lambda tl: tl.time_stamp)
        return timeline

    @classmethod
    def _add_dewatering_timeline(cls, timeline):
        timeline = EventDeWatering.modify_timeline_items(timeline)
        timeline.sort(key=lambda tl: tl.time_stamp)
        return timeline

    @classmethod
    def _clear_main_valve_timeline_items(cls, timeline):
        timeline = [tl_item for tl_item in timeline
                    if not isinstance(tl_item, TimeLineItemMainValve)]
        return timeline

    @classmethod
    def _print_timeline_formatted(cls):
        global logger
        logger.info(cls._get_timeline_formatted(cls._timeline))

    @staticmethod
    def _get_timeline_formatted(timeline):
        if any(timeline):
            time_0 = (_ddatet.now() if _ddatet.now() < timeline[0].time_stamp
                      else timeline[0].time_stamp)
            msg = (" Time now: {}\n".format(Misc.format_time(time_0)))
            msgx = "\n".join(["  > {}".format(tlitem.get_formatted(time_0))
                              for tlitem in timeline])
            return msg + msgx
        else:
            return "<No items>"


class TimeLineItem(object):

    def __init__(self, valve, valve_state, time_stamp, event_bound=None):
        self.valve = valve
        self.valve_state = valve_state
        self.time_stamp = time_stamp
        self.event_bound = event_bound

    def __repr__(self, *args, **kwargs):
        return ("{} {} at {}"
                .format(self.valve, self.valve_state, unicode(self.time_stamp)))

    def get_formatted(self, time_0=None):
        time_stamp = self.time_stamp
        if time_0 is not None:
            time_span = time_stamp - time_0
            return ("{}: {} to be {}d"
                    .format(Misc.format_timespan(time_span), self.valve, self.valve_state))
        else:
            return ("{}: {} to be {}d"
                    .format(Misc.format_time(time_stamp), self.valve, self.valve_state))


class TimeLineItemMainValve(TimeLineItem):

    def __init__(self, valve_state, time_stamp, event_bound=None):
        valve = "main_valve"
        super(TimeLineItemMainValve, self).__init__(valve, valve_state, time_stamp, event_bound)


class TimeLineItemDewaterValve(TimeLineItemMainValve):

    def __init__(self, valve_state, time_stamp, event_bound=None):
        valve = "dewater_valve"
        super(TimeLineItemMainValve, self).__init__(valve, valve_state, time_stamp, event_bound)


class classproperty(object):

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class EventValveNames(object):
    _sep = "_"
    watering = "watering"

    @classproperty
    def watering_balcony(cls):  # @NoSelf
        return cls._sep.join([cls.watering, "balcony"])

    @classmethod
    def get_watering_balcony_valve(cls, name=None):
        if name is None:
            return cls.watering_balcony
        else:
            name = name.lower()
            if name == "sued":
                name = "south"
            if name not in ("south", "west", None):
                raise WateringBaseError("Wrong parameter name (={})"
                                        .format(name))
            return cls._sep.join([cls.watering_balcony, name])

    @classmethod
    def is_watering_balcony_valve_name(cls, name):
        return name.startswith(cls.watering_balcony)

    @classmethod
    def is_watering_valve_name(cls, name):
        return name.startswith(cls.watering)

    @classproperty
    def watering_bed(cls):  # @NoSelf
        return cls._sep.join([cls.watering, "bed"])

    @classmethod
    def get_watering_bed_valve(cls, name=None):
        if name is None:
            return cls.watering_bed
        else:
            return cls._sep.join([cls.watering_bed, name])


class EventItemBase(object):
    multiple_items_allowed = False

    @classmethod
    def modify_timeline_items(cls, _timeline):
        raise NotImplementedError()

    @staticmethod
    def get_eventclass_by_name(event_name):
        assert(isinstance(event_name, unicode))
        return eval(event_name)

    def __repr__(self):
        return self.__class__.__name__


class EventDeWatering(EventItemBase):

    @classmethod
    def modify_timeline_items(cls, _timeline):
        now = _ddatet.now()
        dur = TimeConstants.dauer_entwaesserung
        _timeline.extend([TimeLineItemMainValve("close", now, cls),
                         TimeLineItemDewaterValve("open", now + _tdelta(milliseconds=100), cls),
                         TimeLineItemDewaterValve("close", now + _tdelta(seconds=dur), cls), ])
        return _timeline


class EventWaterTapOpen(EventItemBase):
    my_valve = "virtual_water_tap"
    multiple_items_allowed = True

    @classmethod
    def modify_timeline_items(cls, _timeline):
        water_tap_close_events = [tl_item for tl_item
                                  in _timeline if (tl_item.valve == cls.my_valve
                                                   and tl_item.valve_state == "close")]
        now = _ddatet.now()
        duration = TimeConstants.dauer_hauptventil_alleine
        max_time = TimeConstants.dauer_hauptventil_alleine_max
        if not any(water_tap_close_events):
            close_time = now + _tdelta(seconds=duration)
            _timeline.extend([TimeLineItem(cls.my_valve, "open", now, cls),
                              TimeLineItem(cls.my_valve, "close", close_time, cls)])
        else:
            last_close_event = water_tap_close_events[-1]
            close_time = last_close_event.time_stamp + _tdelta(seconds=duration)
            if close_time > now + _tdelta(seconds=max_time):
                close_time = now + _tdelta(seconds=max_time)
            _timeline.remove(last_close_event)
            _timeline.append(TimeLineItem(cls.my_valve, "close", close_time, cls))
        return _timeline


class EventWaterTapClose(EventWaterTapOpen):

    @classmethod
    def modify_timeline_items(cls, _timeline):
        tl_witho_water_tap = [tl_item for tl_item
                              in _timeline if tl_item.valve != cls.my_valve]
        return tl_witho_water_tap


class EventWateringHelper():

    @classmethod
    def add_open_close_events_to_timeline(cls, _timeline, valve, duration, offset=None):
        other_watering_close_items = \
            cls.get_watering_close_items(_timeline, valve_to_excl=valve)
        time_offset = _tdelta(seconds=0)
        if len(other_watering_close_items):
            now = _ddatet.now()
            time_offset = other_watering_close_items[-1].time_stamp - now + _tdelta(seconds=2)
        if offset is not None:
            time_offset += offset
        _timeline.extend(
            cls._create_watering_timeline_items(valve, duration, time_offset))
        return _timeline

    @classmethod
    def get_watering_close_items(cls, _timeline, valve_to_excl=None):
        other_watering_close_items = [tl_item for tl_item in _timeline
                                      if (EventValveNames.is_watering_valve_name(tl_item.valve)
                                          and tl_item.valve_state == "close")]
        if valve_to_excl is not None:
            other_watering_close_items = [tl_item for tl_item in other_watering_close_items
                                          if not tl_item.valve.startswith(valve_to_excl)]
        return other_watering_close_items

    @classmethod
    def _create_watering_timeline_items(cls, valve, duration, offset=None):
        now = _ddatet.now()
        if offset is not None and offset > _tdelta(seconds=0):
            now += offset
        close_time = now + _tdelta(seconds=duration)
        return [TimeLineItem(valve, "open", now, cls),
                TimeLineItem(valve, "close", close_time, cls), ]


class EventBalconyWateringAll(EventItemBase):

    @classmethod
    def modify_timeline_items(cls, _timeline):
        _timeline = EventBalconyWateringSued.modify_timeline_items(_timeline)
        last_event_time = _timeline[-1].time_stamp
        offset = (last_event_time - _ddatet.now()) + _tdelta(seconds=3)
        _timeline = EventBalconyWateringWest.modify_timeline_items(_timeline, offset=offset)
        return _timeline

    @classmethod
    def _get_modified_watering_timeline_items(cls, _timeline, valve, duration, offset=None):
        if TimeLineAnalyser.is_at_balcony_watering(_timeline, valve):
            return _timeline
        return EventWateringHelper.add_open_close_events_to_timeline(_timeline, valve, duration,
                                                                     offset)


class EventBalconyWateringStop(EventItemBase):

    def __init__(self, balcony_to_stop=None):
        self.balcony_to_stop = EventValveNames.get_watering_balcony_valve(balcony_to_stop)

    def modify_timeline_items(self, _timeline):
        now = _ddatet.now()
        tl_items_filters = [tl_item for tl_item in _timeline
                            if (not tl_item.valve.startswith(self.balcony_to_stop))]
        balc_close_items = [tl_item for tl_item in _timeline
                            if (tl_item.valve.startswith(self.balcony_to_stop)
                                and tl_item.valve_state == "close")]
        if any(balc_close_items):
            time_shift = balc_close_items[-1].time_stamp - now + _tdelta(milliseconds=200)
            for tl_item in balc_close_items:
                tl_item.time_stamp = now
            for tl_item in tl_items_filters:
                tl_item.time_stamp -= time_shift
            tl_items_filters.extend(balc_close_items)
        return tl_items_filters

    def __repr__(self):
        return self.__class__.__name__ + self.balcony_to_stop


class EventBalconyWateringSued(EventBalconyWateringAll):
    my_valve = EventValveNames.get_watering_balcony_valve("south")

    @classmethod
    def modify_timeline_items(cls, _timeline, offset=None):
        duration = TimeConstants.autowatering_max_watering_time
        return cls._get_modified_watering_timeline_items(_timeline, cls.my_valve, duration, offset)


class EventBalconyWateringWest(EventBalconyWateringAll):
    my_valve = EventValveNames.get_watering_balcony_valve("west")

    @classmethod
    def modify_timeline_items(cls, _timeline, offset=None):
        duration = TimeConstants.autowatering_max_watering_time
        return cls._get_modified_watering_timeline_items(_timeline, cls.my_valve, duration, offset)


class EventBedLowerWatering(EventItemBase):
    my_valve = EventValveNames.get_watering_bed_valve("lower")

    @classmethod
    def modify_timeline_items(cls, _timeline):
        duration = TimeConstants.autwatering_bed_lower_watering_time
        return EventWateringHelper.add_open_close_events_to_timeline(_timeline, cls.my_valve,
                                                                     duration)


class EventBedUpperWatering(EventBedLowerWatering):
    my_valve = EventValveNames.get_watering_bed_valve("upper")

    @classmethod
    def modify_timeline_items(cls, _timeline):
        duration = TimeConstants.autwatering_bed_upper_watering_time
        return EventWateringHelper.add_open_close_events_to_timeline(_timeline, cls.my_valve,
                                                                     duration)


class Switches(object):

    schalter_garage = None
    schalter_schuppen = None
    schalter_wozi_1 = None

    @classmethod
    def init_devices(cls):
        global ccu_obj
        cls.schalter_garage = ccu_obj.devices.get_by_name(u"SchalterGarage")
        cls.schalter_garage.on_value_updated(Switches.callback_router)
        cls.schalter_schuppen = ccu_obj.devices.get_by_name(u"SchalterSchuppen")
        cls.schalter_schuppen.on_value_updated(Switches.callback_router)
        cls.schalter_wozi_1 = ccu_obj.devices.get_by_name(u"SchalterWoZi1")
        cls.schalter_wozi_1.on_value_updated(Switches.callback_router)

    @classmethod
    @Log.logex_deco
    def callback_router(cls, param, _static=dict()):  # @NOSONAR @DontTrace
        global logger

        if not hasattr(param, u"control"):
            return
        if not param.control.upper().startswith(u"BUTTON."):
            return
        if not param.id.upper().startswith(u"PRESS_"):
            return
        is_press_long = param.id.upper().endswith(u"_LONG")
        is_press_short = not is_press_long
        ch_name = param.channel.name
        if LowBattReporter.is_low_batt_item(param):
            LowBattReporter.add_low_batt_item(param)
            return

        MIN_DELTA_BETWEEN_EVENTS = 1.5  # s
        last_evt_time = _static.get('last_event_time', -MIN_DELTA_BETWEEN_EVENTS)
        if time.time() - last_evt_time < MIN_DELTA_BETWEEN_EVENTS:
            logger.info("Event ignored channel.name: {}. "
                        "Min delta time {} s not met.".format(ch_name, MIN_DELTA_BETWEEN_EVENTS))
            return
        _static['last_event_time'] = time.time()

        logger.info(u"EVENT: channel.name: {}, Long: {}".format(ch_name, is_press_long))
        if Debug.VERBOSE_CHN_INFO():
            logger.info(u"     param.id: {}".format(param.id))
            logger.info(u"     param.flags: {}".format(param.flags))
            logger.info(u"     param.operations: {}".format(param.operations))
            logger.info(u"     param.internal_name: {}".format(param.internal_name))
            logger.info(u"     unicode(param): {}".format(unicode(param)))

        if is_press_short \
           and ch_name in [u"SchalterGarage_DruckOben", u"SchalterSchuppen_DruckOben",
                           u"SchalterGarage_DruckUnten", u"SchalterSchuppen_DruckUnten",
                           u"SchalterWoZi1_DruckObenLi"]:
            TimeLineWorker.add_event_item(EventWaterTapOpen)
            return
        if (is_press_long
            and ch_name in [u"SchalterSchuppen_DruckUnten",
                            u"SchalterWoZi1_DruckObenLi"]):
            TimeLineWorker.add_event_item(EventWaterTapClose)
            return
        if is_press_long:
            if ch_name in [u"SchalterGarage_DruckOben"]:
                TimeLineWorker.add_event_item(EventBedUpperWatering)
                return
            elif ch_name in [u"SchalterGarage_DruckUnten"]:
                TimeLineWorker.add_event_item(EventBedLowerWatering)
                return
        if ch_name in [u"SchalterWoZi1_DruckObenRe"]:
            if TimeLineAnalyser.is_at_balcony_watering():
                TimeLineWorker.add_event_item(EventBalconyWateringStop)
                return
            else:
                TimeLineWorker.add_event_item(EventBalconyWateringAll)
                return
        if ch_name in [u"SchalterWoZi1_DruckMitteLi"]:
            if TimeLineAnalyser.is_at_balcony_watering():
                TimeLineWorker.add_event_item(EventBalconyWateringStop)
                return
            else:
                TimeLineWorker.add_event_item(EventBalconyWateringSued)
                return
        if ch_name in [u"SchalterWoZi1_DruckMitteRe"]:
            if TimeLineAnalyser.is_at_balcony_watering():
                TimeLineWorker.add_event_item(EventBalconyWateringStop)
                return
            else:
                TimeLineWorker.add_event_item(EventBalconyWateringWest)
                return
        if is_press_long and ch_name in [u"SchalterWoZi1_DruckUntenLi"]:
            logger.info(u"AutoWateringBalconies.activate_autowatering()")
            AutoWateringBalconies.activate_autowatering()
            return
        if is_press_long and ch_name in [u"SchalterWoZi1_DruckUntenRe"]:
            AutoWateringBalconies.deactivate_autowatering()
            return

        logger.info("Switch action has no effect. ")
        logger.info(u"     param.id: {}".format(param.id))
        logger.info(u"     param.control: {}".format(param.control))


class WaterLevelSensors(object):
    _sensors = dict()
    _open_state_inversions = dict(full=True, empty=False)

    @classmethod
    def init_devices(cls):
        for sensor_name in (u"FuellstandSensorSued", u"FuellstandSensorWest"):
            cls._sensors[sensor_name] = WaterLevelSensors.WaterLevelSensor(sensor_name)
            cls._sensors[sensor_name].real_sensor.on_value_updated(cls.callback_router)

    @classmethod
    def get_sensor(cls, sensor_name):
        return cls._sensors[sensor_name]

    @classmethod
    def refresh_sensor_values(cls):
        for sensor in cls._sensors.itervalues():
            sensor.refresh_sensor_values()

    @classmethod
    @Log.logex_deco
    def callback_router(cls, param):
        global logger
        sensor_name = param.channel.device.name  # 'FuellstandSensorSued'
        ch_name = param.channel.name  # 'FuellstandSensorSuedLeer'
        if param.channel.type.upper() == "MAINTENANCE":
            return
        if LowBattReporterViaEventTracing.is_low_batt_item(param):
            LowBattReporterViaEventTracing.add_device_notification(param)
        if runs_in_online_sim_mode():
            device_name = param.channel.device.name 
            logger.info(u"   param.device.name: {}".format(device_name))
            ch_name = param.channel.name 
            logger.info(u"EVENT: channel.name: {}".format(ch_name))
            if ch_name == "Maintenance":
                return
            logger.info(u"   param.control: {}".format(getattr(param, 'control', "unknown")))
            logger.info(u"   param.id: {}".format(getattr(param, 'id', "unknown")))
            logger.info(u"   param.flags: {}".format(getattr(param, 'flags', "unknown")))
            logger.info(u"   param.operations: {}".format(getattr(param, 'operations', "unknown")))
            logger.info(u"   param.internal_name: {}".format(getattr(param, 'internal_name', "unknown")))
            channel = getattr(param, 'channel', "unknown")
            logger.info(u"   param.channel: {}".format(channel))
            is_open = getattr(channel, 'is_open', "unknown")
            logger.info(u"   param.channel.is_open: {}".format(is_open))
            logger.info
        if param.id == "STATE":
            cls._sensors[sensor_name].add_state_change_event(ch_name, param.channel.is_open)

    class _TimeHysteresisValue(object):

        def __init__(self, time_hysterisis_locked_values=[], timespan=0.0):  # @NOSONAR @DontTrace
            assert isinstance(time_hysterisis_locked_values, list)
            assert isinstance(timespan, (float, int, type(None)))
            self.timespan = timespan
            self.value_has_changed = False
            self._time_hysterisis_locked_values = time_hysterisis_locked_values
            self._last_value_set_time = None
            self._value = None
            self._value_change_candidate = dict(val=None, time=None)

        @property
        def value(self):
            if self._value_change_candidate['val'] is not None \
               and self._value_change_candidate['val'] != self._value \
               and (time.time() - self._value_change_candidate['time'] >= self.timespan):
                self._value = self._value_change_candidate['val']
                self._value_change_candidate['val'] = None
            return self._value

        @value.setter
        def value(self, value):
            assert isinstance(value, (bool, type(None)))
            if value is not None and value != self._value \
               and (self.value_can_be_set or value in self._time_hysterisis_locked_values):
                self._last_value_set_time = time.time()
                self.value_has_changed = True
                self._value = value
                self._value_change_candidate['val'] = None
            else:
                if value != self._value:
                    self._value_change_candidate['time'] = time.time()
                    self._value_change_candidate['val'] = value
                else:
                    self._value_change_candidate['val'] = None
                self.value_has_changed = False

        def set_value_unfiltered(self, value):
            self._last_value_set_time = time.time()
            self.value_has_changed = True
            self._value = value
            self._value_change_candidate = dict(val=None, time=None)

        @property
        def value_can_be_set(self):
            if self.timespan is None or self._last_value_set_time is None:
                return True
            else:
                return (time.time() - self._last_value_set_time >= self.timespan)

        @value_can_be_set.setter
        def value_can_be_set(self, value=True):
            assert value is True
            if value is True:
                self._last_value_set_time = time.time() - self.timespan

    class WaterLevelSensor(object):

        def __init__(self, sensor_name):
            global ccu_obj
            self.sensor_name = sensor_name
            self.real_sensor = ccu_obj.devices.get_by_name(sensor_name)
            self._open_state_inversions = WaterLevelSensors._open_state_inversions
            self._is_empty_value = WaterLevelSensors._TimeHysteresisValue(
                time_hysterisis_locked_values=[True],
                timespan=TimeConstants.waterlvlsensor_empty_time_change_treshold)
            self._is_full_value = WaterLevelSensors._TimeHysteresisValue(
                time_hysterisis_locked_values=[True],
                timespan=TimeConstants.waterlvlsensor_full_time_change_treshold)
            self._is_active_value = WaterLevelSensors._TimeHysteresisValue()
            self._state_update_lock = threading.RLock()
            if not runs_in_offline_sim_mode():
                self.refresh_sensor_values()

        def is_empty(self):
            with self._state_update_lock:
                return self._is_empty_value.value

        def is_full(self):
            with self._state_update_lock:
                return self._is_full_value.value

        def is_active(self):
            # with self._state_update_lock:
            return True

        def get_states_string_formatted(self):
            with self._state_update_lock:
                msg = ("'{}' is {}active, {}empty and {}full"
                       .format(self.sensor_name,
                               "" if self.is_active() else "not ",
                               "" if self.is_empty() else "not ",
                               "" if self.is_full() else "not ",))
                return msg

        def add_state_change_event(self, ch_name, is_open):
            with self._state_update_lock:
                states = self._translate_incoming_event_to_state(ch_name, is_open)
                self._is_empty_value.value = states['empty']
                self._is_full_value.value = states['full']
                self._is_active_value.value = states['active']
                if self._is_empty_value.value_has_changed and self.is_empty():
                    self._is_full_value.value_can_be_set = True
                    self._is_full_value.value = False
                if self._is_full_value.value_has_changed and self.is_full():
                    self._is_empty_value.value_can_be_set = True
                    self._is_empty_value.value = False
                self._log_states()
                self._add_history_event()

        def refresh_sensor_values(self):
            # send poll request
            with self._state_update_lock:
                self.add_state_change_event('{}Leer'.format(self.sensor_name),
                                            self.real_sensor.shutter_contact_empty_is_open)
                self.add_state_change_event('{}Voll'.format(self.sensor_name),
                                            self.real_sensor.shutter_contact_full_is_open)
                #             self.add_state_change_event('{}Aktiv'.format(self.sensor_name),
                #                                         self.real_sensor.shutter_contact_activated_is_open)

        def _log_states(self):
            global logger
            if self._is_empty_value.value_has_changed and self.is_empty():
                msg = ("\n++ SENSOR-EVENT: {} is {}"
                       .format(self.sensor_name, "empty" if self.is_empty() else "not empty"))
                Log.info_pushover(msg)
            if self._is_full_value.value_has_changed and self.is_full():
                msg = ("\n++ SENSOR-EVENT: {} is {}"
                       .format(self.sensor_name, "full" if self.is_full() else "not full"))
                Log.info_pushover(msg)

        def _add_history_event(self):
            if self._is_empty_value.value_has_changed and self.is_empty():
                AutoWateringHistory.add_event(self.sensor_name,
                                              AutoWateringHistory.Events.sensor_got_empty)
            if self._is_full_value.value_has_changed and self.is_full():
                AutoWateringHistory.add_event(self.sensor_name,
                                              AutoWateringHistory.Events.sensor_got_full)

        def _translate_incoming_event_to_state(self, ch_name, is_open):
            states = dict(empty=None, full=None, active=None)
            if ch_name.lower().endswith('leer'):
                states['empty'] = bool(is_open ^ self._open_state_inversions['empty'])
            elif ch_name.lower().endswith('voll'):
                states['full'] = bool(is_open ^ self._open_state_inversions['full'])
            elif ch_name.lower().endswith('aktiv'):
                states['active'] = bool(not is_open)
            return states


class RelaisInitError(WateringBaseError):
    pass


class WateringControlRelais(object):
    watering_relais_rail_1 = None
    watering_relais_rail_2 = None

    @classmethod
    def init_relais(cls):  # @NOSONAR @DontTrace
        global ccu_obj

        def func_to_run(relais_name):
            relais1 = ccu_obj.devices.get_by_name(relais_name)
            return relais1

        func_sampler = IterantExecSamplerForFunction(func_to_run, max_try_count=1,
                                                     intermediate_wait_time=10.0,
                                                     exec_types_to_catch=(KeyError,),
                                                     exec_type_to_raise=RelaisInitError)
        cls.watering_relais_rail_1 = func_sampler.run(u"BewaesserungRelais1")
        if cls.watering_relais_rail_1 is None:
            raise ValueError(u"No relais named 'BewaesserungRelais1'")

        cls.watering_relais_rail_1.relais1.switch_on_time = None
        cls.watering_relais_rail_1.relais2.switch_on_time = None
        cls.watering_relais_rail_1.relais3.switch_on_time = None
        cls.watering_relais_rail_1.relais4.switch_on_time = None

        cls.watering_relais_rail_2 = func_sampler.run(u"BewaesserungRelais2")
        if cls.watering_relais_rail_2 is None:
            raise ValueError(u"No relais named 'BewaesserungRelais2'")

        cls.watering_relais_rail_2.relais1.switch_on_time = None
        cls.watering_relais_rail_2.relais2.switch_on_time = None
        cls.watering_relais_rail_2.relais3.switch_on_time = None
        cls.watering_relais_rail_2.relais4.switch_on_time = None

        def open_f(relais, linked_flowerpot_name=None):  # @IgnorePep8

            @LogDebug.timeit_deco(2.0, u"oeffne({})".format(relais.name))
            def open_in(*args, **kwargs):
                MAX_TRIES = 3
                DebugExceptionSim.sim_relais_oeffne_in()
                for i_try in xrange(MAX_TRIES):
                    try:
                        if not runs_in_online_sim_mode():
                            relais.switch_on()
                        relais.switch_on_time = _ddatet.now()
                        if runs_in_offline_sim_mode() and linked_flowerpot_name is not None:
                            flowerpot = getattr(flowerpots, linked_flowerpot_name)
                            flowerpot.start_watering()
                        break
                    except pmatic.PMException:
                        if i_try == MAX_TRIES - 1:
                            raise
                        time.sleep(0.4)

            return open_in

        def close_f(relais, linked_flowerpot_name=None):  # @IgnorePep8

            @LogDebug.timeit_deco(2.0, u"schliesse({})".format(relais.name))
            def close_in(*args, **kwargs):
                MAX_TRIES = 3
                for i_try in xrange(MAX_TRIES):
                    try:
                        if not runs_in_online_sim_mode():
                            relais.switch_off()
                        if runs_in_offline_sim_mode() and linked_flowerpot_name is not None:
                            flowerpot = getattr(flowerpots, linked_flowerpot_name)
                            flowerpot.stop_watering()
                        break
                    except pmatic.PMException:
                        if i_try == MAX_TRIES - 1:
                            raise
                        time.sleep(0.4)

            return close_in

        relais_rail_1 = cls.watering_relais_rail_1
        relais_rail_1.relais1.oeffne = open_f(relais_rail_1.relais1)
        relais_rail_1.relais1.schliesse = close_f(relais_rail_1.relais1)
        relais_rail_1.relais2.oeffne = open_f(relais_rail_1.relais2)
        relais_rail_1.relais2.schliesse = close_f(relais_rail_1.relais2)
        relais_rail_1.relais3.oeffne = open_f(relais_rail_1.relais3, "blumentopf_sued")
        relais_rail_1.relais3.schliesse = close_f(relais_rail_1.relais3, "blumentopf_sued")
        relais_rail_1.relais4.oeffne = open_f(relais_rail_1.relais4, "blumentopf_west")
        relais_rail_1.relais4.schliesse = close_f(relais_rail_1.relais4, "blumentopf_west")
        relais_rail_2 = cls.watering_relais_rail_2
        relais_rail_2.relais1.oeffne = open_f(relais_rail_2.relais1)
        relais_rail_2.relais1.schliesse = close_f(relais_rail_2.relais1)
        relais_rail_2.relais2.oeffne = open_f(relais_rail_2.relais2)
        relais_rail_2.relais2.schliesse = close_f(relais_rail_2.relais2)
        # alle schliessen
        relais_rail_1.relais1.schliesse()
        relais_rail_1.relais2.schliesse()
        relais_rail_1.relais3.schliesse()
        relais_rail_1.relais4.schliesse()
        relais_rail_2.relais1.schliesse()
        relais_rail_2.relais2.schliesse()


class AutoWateringHistory(object):

    last_events = dict()
    events = []
    special_events = []
    last_flush_time = _ddatet.now()

    class Events(object):
        sensor_got_empty = "1_sensor_got_empty"
        start_watering = "2_start_watering"
        sensor_got_full = "3_sensor_got_full"
        finished_watering = "4_finished_watering"

        @classmethod
        def is_in_events(cls, event_to_check):
            return (event_to_check[2:] in dir(cls))

    class SpecialEvents(object):
        delta_time_excess = "delta_time_excess"
        too_long_watering = "too_long_watering"
        too_long_not_watered = "too_long_not_watered"

    @classmethod
    def add_event(cls, balcony, event):
        if cls.Events.is_in_events(event):
            balcony = balcony.replace("FuellstandSensor", "")
            # avoid storing same event several times.
            if cls.last_events.get(balcony, None) == event:
                return
            cls.last_events[balcony] = event
            balc_events = [e for e in cls.events if e.get('0_balcony', None) == balcony]
            if len(balc_events) == 0 \
               or any([e for e in balc_events[-1] if e > event]):
                balc_event = OrderedDict({'0_balcony': balcony})
                cls.events.append(balc_event)
            else:
                balc_event = balc_events[-1]
            balc_event[event] = _ddatet.now()
            if True:  # @NOSONAR @DontTrace
                event_msgs = list()
                for key in balc_event:
                    event_msgs.append("  {}: {}".format(key, balc_event[key]))
                msg = "\n++ AUTOWATERING-EVENT:\n{}".format("\n".join(event_msgs))
                logger.info(msg)
        else:
            cls.special_events.append(
                dict(time=_ddatet.now(),
                     event=event))

    @classmethod
    def is_flushing_required(cls):
        flushing_time_span = TimeConstants.history_flushing_time_span
        flushing_time_span = _tdelta(seconds=flushing_time_span)
        if runs_in_production():
            flushing_watering_events = 12
            min_wait_time_span = _tdelta(days=1)
        elif runs_in_online_sim_mode():
            flushing_watering_events = 6
            min_wait_time_span = _tdelta(seconds=40)
        elif runs_in_offline_sim_mode():
            flushing_watering_events = 6
            min_wait_time_span = _tdelta(seconds=20)
        time_span = _ddatet.now() - cls.last_flush_time
        return (time_span > min_wait_time_span
                and (time_span > flushing_time_span or len(cls.events) > flushing_watering_events))

    @classmethod
    def flush_formatted_event_list(cls):
        time_now = _ddatet.now()
        last_flush_time = cls.last_flush_time
        cls.last_flush_time = time_now
        statistics_time_span = Misc.format_timespan(time_now - last_flush_time)
        cls.events = [e for e in cls.events if any(e)]
        num_delta_time_excesses = len([e for e in cls.special_events
                                       if e['event'] == cls.SpecialEvents.delta_time_excess])
        num_too_long_waterings = len([e for e in cls.special_events
                                      if e['event'] == cls.SpecialEvents.too_long_watering])
        num_too_long_not_watered = len([e for e in cls.special_events
                                        if e['event'] == cls.SpecialEvents.too_long_not_watered])

        rowt = "{balcony:1}|{starttime:17}|{watertime:7}"  # | {evaportime:12} "
        rows = [rowt.format(balcony="B", starttime="Start time",
                            watertime="Wat. ",)]  # , evaportime="Evap.")]
        events_not_yet_flushed = list()
        num_waterings = 0
        for i_ev, ev in enumerate(cls.events):
            num = unicode(num_waterings + 1)
            balcony = ev['0_balcony']
            watertime = "??"
            starttime = ev.get(cls.Events.start_watering, "??")
            if 'datetime' in unicode(type(starttime)):
                starttime = Misc.format_time(starttime)
            if cls.Events.finished_watering in ev and cls.Events.start_watering in ev:
                watering_timespan = ev[cls.Events.finished_watering] - ev[cls.Events.start_watering]
                watertime = Misc.format_timespan(watering_timespan)

            if starttime == "??" or watertime == "??":
                events_not_yet_flushed.append(ev)
                continue
            balcony = balcony[0]
            rows.append(rowt.format(**locals()))
            num_waterings += 1
        if len(rows) == 1:
            rows.append(rowt.format(balcony="-", starttime="--",
                                    watertime="--"))
        num_delta_time_excesses_str = ""
        if num_delta_time_excesses > 0:
            num_delta_time_excesses_str = ("  > Num. delta time excesses:\n"
                                           "     {}\n"
                                           .format(num_delta_time_excesses))
        num_too_long_waterings_str = ""
        if num_too_long_waterings > 0:
            num_too_long_waterings_str = ("  > Num. too long waterings:\n"
                                          "     {}\n"
                                          .format(num_too_long_waterings))
        num_too_long_not_watered_str = ""
        if num_too_long_not_watered > 0:
            num_too_long_not_watered_str = ("  > Num. too long not watered:\n"
                                            "     {}\n"
                                            .format(num_too_long_not_watered))
        tablestr = "\n".join(["{}".format(r) for r in rows])
        sep_row = "#"*25
        bot_row = "_"*25
        msg = ("\n{}\n"
               "WATERING STATISTICS\n"
               "    [from {}\n"
               "       to {}]\n"
               "    [ .. = duration {}]\n"
               "  > Number of waterings:\n"
               "     {}\n"
               "{}{}{}"
               "{}\n"
               "{}\n"
               "{}\n"
               .format(sep_row, Misc.format_time(last_flush_time),
                       Misc.format_time(time_now), statistics_time_span,
                       num_waterings, num_delta_time_excesses_str, num_too_long_waterings_str,
                       num_too_long_not_watered_str, bot_row, tablestr, sep_row))
        Log.info_pushover(msg, "Watering statistics")
        cls.events = events_not_yet_flushed
        cls.special_events = []


class AutoWateringBeds(object):

    @classmethod
    def continuousily_run_trigger_func(cls):
        func_wrap = cls._continuousily_run_trigger_func
        func_wrap = ExceptionsInThreadsContainer.catch_threaded_exception_deco(func_wrap)
        func_wrap = Log.logex_deco(func_wrap)
        thread_hl = threading.Thread(target=func_wrap)
        thread_hl.start()

    @classmethod
    def _continuousily_run_trigger_func(cls):
        time.sleep(0.5)  # wait for other threads to initialize
        global logger
        dt_repl_func_org = Misc.datetime_safe_replace
        dt_repl_func = lambda time_pt, day_offs: dt_repl_func_org(_ddatet.now(),  # @IgnorePep8
                                                                  day=_ddatet.now().day + day_offs,
                                                                  hour=time_pt.hour,
                                                                  minute=time_pt.minute,
                                                                  second=time_pt.second,)
        start_times = [dt_repl_func(time_pt, 1)
                       for time_pt in TimeConstants.autowatering_beds_times]
        while True:
            if cls.break_required():
                break
            if not cls.inside_season():
                time.sleep(24 * 3600)
                continue
            for i_time, start_time in enumerate(start_times):
                if _ddatet.now() > start_time:
                    start_times[i_time] = dt_repl_func(start_time, 1)
                    TimeLineWorker.add_event_item(EventBedLowerWatering)
                    TimeLineWorker.add_event_item(EventBedUpperWatering)
            time.sleep(5.0)

    @classmethod
    def inside_season(cls):
        now = _ddatet.now()
        return 5 <= now.month <= 10 

    @classmethod
    def break_required(cls):
        return (ThreadContainer.get_sideline_threads_must_be_terminated()
                or ExceptionsInThreadsContainer.any_threads_occured())


class AutoWateringBalconies(object):
    _is_disabled_for_debugging = False
    _is_autowatering_enabled = False
    listening_start_time = _ddatet.now()
    permitted_watering_time_slots = [dict(start=datetime.time(hour=0, minute=01),
                                          end=datetime.time(hour=23, minute=59))]

    @classmethod
    def get_is_autowatering_enabled(cls):
        if runs_in_production():
            return (cls._is_autowatering_enabled is True)
        else:
            return True

    @classmethod
    def activate_autowatering(cls):
        if cls._is_autowatering_enabled:
            Log.info_pushover("Autowatering already enabled",
                              "Autowatering already enabled.")
            return
        Log.info_pushover("Autowatering enabled",
                          "Autowatering enabled. Start initial autowatering")
        cls._is_autowatering_enabled = True
        TimeLineWorker.add_event_item(EventBalconyWateringAll)

    @classmethod
    def activate_autowatering_after_x_seconds_threaded(cls, wait_time):

        def _activate_autowatering():
            time.sleep(wait_time)
            if not cls._get_is_autowatering_explicitly_disabled():
                cls.activate_autowatering()

        func_wrap = _activate_autowatering
        func_wrap = ExceptionsInThreadsContainer.catch_threaded_exception_deco(func_wrap)
        func_wrap = Log.logex_deco(func_wrap)
        thread_hl = threading.Thread(target=func_wrap)
        thread_hl.start()

    @classmethod
    def deactivate_autowatering(cls):
        if cls._is_autowatering_enabled is not True:
            Log.info_pushover("Autowatering already disabled",
                              "Autowatering already disabled.")
            return
        Log.info_pushover("Autowatering disabled",
                          "Autowatering disabled")
        cls._is_autowatering_enabled = False

    @classmethod
    def _get_is_autowatering_explicitly_disabled(cls):
        return (cls._is_autowatering_enabled is False)

    @classmethod
    def continuousily_oberserve_water_levels(cls):
        if cls._is_disabled_for_debugging:
            return
        func_wrap = cls._continuousily_oberserve_water_levels
        func_wrap = ExceptionsInThreadsContainer.catch_threaded_exception_deco(func_wrap)
        func_wrap = Log.logex_deco(func_wrap)
        thread_hl = threading.Thread(target=func_wrap)
        thread_hl.start()

    @classmethod
    def _continuousily_oberserve_water_levels(cls):  # @NOSONAR @DontTrace
        time.sleep(0.5)  # wait for other threads to initialize
        global logger
        cls.listening_start_time = _ddatet.now()
        auto_watering_handlers = [cls("Sued"),
                                  cls("West"), ]
        WaterLevelSensors.refresh_sensor_values()
        while True:
            if cls.break_required():
                break
            for handler in auto_watering_handlers:
                if cls.get_is_autowatering_enabled():
                    if handler.is_ready_for_watering:
                        if handler.is_inside_watering_time_slot():
                            handler.do_watering()
                        continue
                    if handler.is_watering_required() \
                       or handler.check_if_max_time_without_watering_is_exceeded() \
                       or handler.check_if_watering_is_required_due_to_max_delta_time_compared_to_others(auto_watering_handlers):  # @IgnorePep8
                        handler.set_is_ready_for_watering()
                        continue
                handler.trigger_stop_watering_if_sensor_reports_full()

            if cls.break_required():
                break
            time.sleep(0.15)
            if AutoWateringHistory.is_flushing_required():
                AutoWateringHistory.flush_formatted_event_list()

    @classmethod
    def break_required(cls):
        return (ThreadContainer.get_sideline_threads_must_be_terminated()
                or ExceptionsInThreadsContainer.any_threads_occured())

    def __init__(self, name):
        self.name = name
        self._event = eval("EventBalconyWatering{}".format(name))
        water_lvl_sns_name = "FuellstandSensor{}".format(name)
        self._water_level_sensor = WaterLevelSensors.get_sensor(water_lvl_sns_name)
        self._timer_lag_time_before_starting_watering = \
            TimerSimple(timeout=TimeConstants.autowatering_warte_zeit_bevor_start)
        self._timer_max_watering_time = \
            TimerSimple(timeout=TimeConstants.autowatering_max_watering_time)
        self._max_watering_time_excess_occured = False
        self._is_ready_for_watering = False
        self._temp_data = dict()
        self._report_sensor_state_at_ini()
        self._last_watering_time = None

    @property
    def is_ready_for_watering(self):
        if not self._water_level_sensor.is_active():
            self._is_ready_for_watering = False
        return self._is_ready_for_watering

    def set_is_ready_for_watering(self):
        self._is_ready_for_watering = True

    def check_if_watering_is_required_due_to_max_delta_time_compared_to_others(self, others):
        if self.is_ready_for_watering:
            # is already armed..
            return False
        delta_rslt = self.get_max_delta_watering_time_compared_to_others(others)
        max_delta = delta_rslt['max_delta']
        max_allw_delta = TimeConstants.autowatering_max_delta_zeit_zwischen_balkonen
        if max_delta > max_allw_delta:
            delta_str = Misc.format_timespan(max_allw_delta)
            last_water_time = Misc.format_time(self.get_last_watering_time())
            last_water_time_other = Misc.format_time(delta_rslt['other'].get_last_watering_time())
            msg = ("Delta time between both balconies exceeded {}. \n"
                   "Last time '{}' reported low water level was at {}. \n"
                   "Last time '{}' reported low water level was at {}. \n"
                   "Watering is started."
                   .format(delta_str, self.name, last_water_time,
                           delta_rslt['other'].name, last_water_time_other))
            Log.warning_pushover(msg)
            AutoWateringHistory.\
                add_event(self.name, AutoWateringHistory.SpecialEvents.delta_time_excess)
            return True
        else:
            return False

    def get_max_delta_watering_time_compared_to_others(self, others):
        rtn_dict = dict(max_delta=0.0, other=None)
        for handler in others:
            if handler == self:
                continue
            c_delta = (handler.get_last_watering_time() -
                       self.get_last_watering_time()).total_seconds()
            if c_delta > rtn_dict['max_delta']:
                rtn_dict = dict(max_delta=c_delta, other=handler)
        return rtn_dict

    def check_if_max_time_without_watering_is_exceeded(self):
        if not self._water_level_sensor.is_active():
            return False
        if self.is_ready_for_watering:
            # is already armed..
            return False
        max_zeit_ohne_bewss = TimeConstants.autowatering_max_zeit_ohne_watering
        c_delta = (_ddatet.now() - self.get_last_watering_time()).total_seconds()
        if (c_delta < max_zeit_ohne_bewss):
            self._max_watering_time_excess_occured = False
        if (c_delta >= max_zeit_ohne_bewss and not self._max_watering_time_excess_occured):
            self._max_watering_time_excess_occured = True
            delta_str = \
                Misc.format_timespan(max_zeit_ohne_bewss)
            msg = ("'{}' did not report low water level for more than {}. "
                   "Autowatering is started."
                   .format(self.name, delta_str))
            Log.warning_pushover(msg)
            event_to_add = AutoWateringHistory.SpecialEvents.too_long_not_watered
            AutoWateringHistory.add_event(self.name, event_to_add)
            return True
        else:
            return False

    def get_last_watering_time(self):
        if self._timer_lag_time_before_starting_watering.is_running() \
           or self._timer_max_watering_time.is_running():
            return _ddatet.now()
        elif self._last_watering_time is None:
            return self.listening_start_time
        else:
            return self._last_watering_time

    def is_watering_required(self):
        global logger
        if not self.get_is_autowatering_enabled() \
           or not self._water_level_sensor.is_active():
            self._timer_lag_time_before_starting_watering.stop()
            return False
        if self._timer_lag_time_before_starting_watering.is_not_running():
            if self._water_level_sensor.is_empty():
                logger.info("{} ststart dead timeimer".format(self.name))
                self._timer_lag_time_before_starting_watering.start()
            return False
        elif not self._timer_lag_time_before_starting_watering.is_timeout_reached():
            return False
        else:
            self._timer_lag_time_before_starting_watering.stop()
            return True  # self._water_level_sensor.is_empty()

    @Log.logfunc_deco
    def do_watering(self):
        global logger
        logger.info("{} start autowatering".format(self.name))
        self._last_watering_time = _ddatet.now()
        AutoWateringHistory.\
            add_event(self.name, AutoWateringHistory.Events.start_watering)
        self._do_watering()
        AutoWateringHistory.\
            add_event(self.name, AutoWateringHistory.Events.finished_watering)
        self._is_ready_for_watering = False

    def _do_watering(self):
        if self._water_level_sensor.is_full():
            logger.info("  {} autowatering skipped as sensor reported full".format(self.name))
            return
        while True:
            if not TimeLineAnalyser.is_at_watering():
                break
            time.sleep(0.5)
        TimeLineWorker.add_event_item(self._event)
        self._timer_max_watering_time.start()
        while True:
            is_full = self._water_level_sensor.is_full()
            is_timeout_reached = self._timer_max_watering_time.is_timeout_reached()
            if is_full or is_timeout_reached:
                TimeLineWorker.add_event_item(EventBalconyWateringStop(self.name))
                break
            elif not TimeLineAnalyser.is_at_balcony_watering():
                break
            time.sleep(0.5)
        if self._timer_max_watering_time.is_timeout_reached():
            msg = ("{} watering took more than {} seconds. Water level sensor "
                   "did not report full. Watering is interrupted."
                   .format(self.name, self._timer_max_watering_time.timeout))
            Log.warning_pushover(msg)
            AutoWateringHistory.\
                add_event(self.name, AutoWateringHistory.SpecialEvents.too_long_watering)
        self._timer_max_watering_time.stop()

    def trigger_stop_watering_if_sensor_reports_full(self, _static=dict()):  # @NOSONAR @DontTrace
        if self not in _static:
            _static[self] = dict()
        if self._water_level_sensor.is_full()\
           and not _static[self].get('last_state_was_full', False):
            _static[self]['last_state_was_full'] = True
            TimeLineWorker.add_event_item(EventBalconyWateringStop(self.name))
        elif not self._water_level_sensor.is_full():
            _static[self]['last_state_was_full'] = False

    def is_inside_watering_time_slot(self):
        now = _ddatet.now()
        next_start_time_slot = Misc.datetime_safe_replace(now, day=now.day + 1)
        for time_slot in self.permitted_watering_time_slots:
            time_slot_start = Misc.datetime_safe_replace(now,
                                                         hour=time_slot['start'].hour,
                                                         minute=time_slot['start'].minute,
                                                         second=time_slot['start'].second,
                                                         microsecond=0)
            time_slot_end = Misc.datetime_safe_replace(now,
                                                       hour=time_slot['end'].hour,
                                                       minute=time_slot['end'].minute,
                                                       second=time_slot['end'].second,
                                                       microsecond=0)
            if time_slot_end < time_slot_start:
                time_slot_end = Misc.datetime_safe_replace(time_slot_end, day=now.day + 1)
            now_plus_1_day = Misc.datetime_safe_replace(now, day=now.day + 1)
            if time_slot_start <= now <= time_slot_end \
               or time_slot_start <= now_plus_1_day <= time_slot_end:
                self._temp_data['time_slot_message_issued'] = False
                return True
            if time_slot_start < next_start_time_slot:
                next_start_time_slot = time_slot_start
        if not self._temp_data.get('time_slot_message_issued', False):
            self._temp_data['time_slot_message_issued'] = True
            secs_till_next_time_slot = (next_start_time_slot - now).seconds
            delta_str = Misc.format_timespan(secs_till_next_time_slot)
            msg = ("Time till next slot: {}.".format(delta_str))
            msg = ("Watering required for {}, but now is currently outside allowed time "
                   "slots. {}".format(self.name, msg))
            Log.warning_pushover(msg)
        return False

    def _report_sensor_state_at_ini(self):
        msg = ("At starting autowatering {}"
               .format(self._water_level_sensor.get_states_string_formatted()))
        Log.info_pushover(msg)


def create_ccu_obj():
    global ccu_obj
    USER = settings.USER
    PASSWORD = settings.PASSWORD
    CCU_URL = settings.CCU_URL
    # Open up a remote connection via HTTP to the CCU and login as admin. When the connection
    # can not be established within 5 seconds it raises an exception.
    kwargs = {
        # TODO: Replace this with the URL to your CCU2.  # @NOSONAR @DontTrace
        u'address': CCU_URL,
        # TODO: Insert your credentials here.  # @NOSONAR @DontTrace
        u'credentials': (USER, PASSWORD),
        u'connect_timeout': 12}
    ccu_obj = pmatic.CCU(**kwargs)
    return ccu_obj


class MainLoop(object):

    @classmethod
    def main_event_loop(cls, offline_sim_func):
        global logger
        Log.info_pushover(u"Starting main")
        intermediate_wait_time = 5.0
        if runs_in_production():
            intermediate_wait_time = 60.0
        if runs_in_offline_sim_mode():
            class_to_use = IterantExecSamplerForFunction
            run_args = dict(offline_sim_func=offline_sim_func)
        else:
            if 'multiprocessing' in globals() and multiprocessing is not None:
                class_to_use = IterantExecSamplerForProcess
            else:
                class_to_use = IterantExecSamplerForFunction
            run_args = dict()
        func_sampler = class_to_use(cls.main_event_loop_ex, max_try_count=5,
                                    intermediate_wait_time=intermediate_wait_time,
                                    exec_types_to_catch=(pmatic.PMConnectionError,
                                                         pmatic.PMException, RelaisInitError,),
                                    reboot_on_err=True)
        func_sampler.run(**run_args)

    @classmethod
    def main_event_loop_ex(cls, *args, **kwargs):
        try:
            return cls._main_event_loop(*args, **kwargs)
        except Exception as ex:
            refeed_args = \
                dict(is_enabled_autowatering=AutoWateringBalconies.get_is_autowatering_enabled())
            setattr(ex, IterantExecSampler.REFEED_KWARG_KEY, refeed_args)
            raise

    @classmethod
    @Log.logex_deco
    def _main_event_loop(cls, *args, **kwargs):
        global logger
        ExceptionsInThreadsContainer.clear_threads_list()
        ThreadContainer.clear_threads_lists()
        if runs_in_production() and not Debug.SKIP_INIT_WAITING():
            init_wait_time = settings.INIT_WAIT_SEC
            logger.info(u"Initially waiting {} sec".format(init_wait_time))
            time.sleep(init_wait_time)
        ccu_obj = create_ccu_obj()
        logger.info(u"Init devices")
        if runs_in_offline_sim_mode():
            devicecreator.create_devices(ccu_obj)
        WateringControlRelais.init_relais()
        Switches.init_devices()
        WaterLevelSensors.init_devices()
        cls._init_events()
        TimeLineWorker.run_continuously()
        AutoWateringBalconies.continuousily_oberserve_water_levels()
        AutoWateringBeds.continuousily_run_trigger_func()
        if 'is_enabled_autowatering' in kwargs and \
           kwargs.pop('is_enabled_autowatering') is False:
            AutoWateringBalconies.deactivate_autowatering()
        if runs_in_offline_sim_mode():
            cls._main_event_loop_offsimmode(*args, **kwargs)
        else:
            cls._main_event_loop_normalmode()
        Log.info_pushover(u"Finished main")

    @staticmethod
    def _init_events():
        global logger, ccu_obj
        if runs_in_offline_sim_mode():
            return
        logger.info(u"Init events")
        func_sampler = IterantExecSamplerForFunction(ccu_obj.events.init, max_try_count=1,
                                                     intermediate_wait_time=lambda tc: tc * 5.0,)
        func_sampler.run()
        logger.info("  Events successfully initialized")

    @staticmethod
    def _main_event_loop_offsimmode(offline_sim_func):
        global ccu_obj

        # sim_func(ccu_obj)
        targetfunc = ThreadContainer.run_threaded_wait_till_finished_deco(offline_sim_func)
        targetfunc = ExceptionsInThreadsContainer.catch_threaded_exception_deco(targetfunc)
        thread_sim = threading.Thread(target=targetfunc, args=[ccu_obj])
        thread_sim.start()
        time.sleep(0.2)  # wait to assure that thread is added to observable list
        simthread.wait_till_all_threads_are_finished(reraise_thread_exception=True)

    @classmethod
    def _main_event_loop_normalmode(cls):
        global logger
        global ccu_obj
        rcp_server = ccu_obj.events._server
        try:
            logger.info(u"=========================================")
            logger.info(u"READY: Waiting for events ..")
            Log.info_pushover(u"Successfully initialized. Waiting for events ..",
                              "Successfully initialized")
            kwargs = dict()
            if Debug.LIMIT_SCRIPT_TIMEOUT():
                kwargs[u'timeout'] = 2 * 60 * 60
            cls._wait_events(rcp_server)
        finally:
            rcp_server.stop()
            rcp_server.join()
            logger.info(u"Close events")
            ccu_obj.events.close()

    @classmethod
    def _wait_events(cls, rcp_server, timeout=None):
        SLEEP_TIME = 0.1
        timer = 0
        while rcp_server.is_alive():
            time.sleep(SLEEP_TIME)
            LowBattReporterViaEventTracing.check_low_bat()
            if ExceptionsInThreadsContainer.any_threads_occured():
                ThreadContainer.do_terminate_threads_to_be_terminated()
                ExceptionsInThreadsContainer.raise_last_thread_exception_in_main_thread()
            if timeout is not None:
                timeout -= 0.1
                if timeout <= 0:
                    break
            if not runs_in_production():
                timer += SLEEP_TIME
                if timer > 10:
                    timer = 0
                    print("Running")


def run(offline_sim_func=None):
    Log.init()
    MainLoop.main_event_loop(offline_sim_func)


if __name__ == u"__main__":
    run()
