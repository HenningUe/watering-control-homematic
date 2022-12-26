
# encoding: utf-8

from __future__ import unicode_literals

import sys
import os
import inspect
import threading
import time
from functools import wraps
from collections import deque
import traceback

import msgs


class ThreadContainer(object):
    thread_mode_is_active = True
    _all_sim_threads = list()

    @classmethod
    def _get_all_sim_threads(cls):
        # IMPORTANT: DO NOT CHANGE. HAS TO BE LIKE THIS. OTHERWISE '_all_sim_threads'
        # IS RESET
        return cls._all_sim_threads

    @classmethod
    def any_thread_is_alive(cls):
        for st in cls._get_all_sim_threads():
            if st[u'thread'].is_alive():
                return True
        return False

    @classmethod
    def get_thread_func_name(cls, thread_to_get_name=None):
        if thread_to_get_name is None:
            thread_to_get_name = threading.current_thread()
        for st in cls._get_all_sim_threads():
            if st['thread'] == thread_to_get_name:
                return st['func_name']

    @classmethod
    def all_threads_are_finished(cls):
        return not cls.any_thread_is_alive()

    @classmethod
    def wait_till_all_threads_are_finished(cls):
        while True:
            if cls.all_threads_are_finished():
                return
            time.sleep(0.1)

    @classmethod
    def run_threaded_deco(cls, func_outer):

        @wraps(func_outer)
        def async_func(*args, **kwargs):
            if cls.thread_mode_is_active:
                thread_hl = threading.Thread(target=func_outer, args=args, kwargs=kwargs)
                thread_hl.start()
                # ThreadContainer._all_sim_threads[thread_hl] = func_outer._unique_name
                cls._get_all_sim_threads().append({u'thread': thread_hl,
                                                   u'func_name': func_outer._unique_name})
                return thread_hl
            else:
                return func_outer(*args, **kwargs)

        return async_func


class TraceableRLock(threading._RLock):

    def __init__(self, *args, **kwargs):
        super(TraceableRLock, self).__init__(*args, **kwargs)
        self.locking_threads = deque()
        self._info_lock = threading.RLock()

    @property
    def curr_blocking_thread(self):
        if self.locking_threads:
            return self.locking_threads[0]
        else:
            return None

    def __enter__(self, blocking=1):
        return self.aquire(blocking)

    def aquire(self, blocking=1):
        with self._info_lock:
            if not threading.current_thread() == self.curr_blocking_thread:
                self.locking_threads.append(threading.current_thread())
                if len(self.locking_threads) > 1:
                    self.get_locking_thread_info()
        return super(TraceableRLock, self).acquire(blocking)

    def release(self):
        with self._info_lock:
            if self.locking_threads:
                self.locking_threads.popleft()
        super(TraceableRLock, self).release()

    def get_locking_thread_info(self):
        func_name = ThreadContainer.get_thread_func_name(self.curr_blocking_thread)
        msg = ("Lock is currently blocked by '{}'\n{}"
               .format(func_name, self._get_formatted_thread_stack_info()))
        LogDebug.info(msg)

    def _get_formatted_thread_stack_info(self):
        thread_frame = sys._current_frames()[self.curr_blocking_thread.ident]
        if not thread_frame:
            msg = "Thread frame not found"
            return msg
        msgs = ["Thread got stuck at "]
        frames = inspect.getouterframes(thread_frame)
        for outer_frame in frames:
            info = inspect.getframeinfo(outer_frame[0])
            if os.path.split(info.filename)[1].lower() == "threading.py":
                break
            msgs.append(u"   > file '{filename}' > func '{function}' > line {lineno}"
                        .format(**info.__dict__))
        if len(msgs) == 1:
            trc_backs = traceback.extract_stack(thread_frame)
            trc_backs.reverse()
            for stack_item in trc_backs:
                msgs.append(u"   > file '{0}' > func '{2}' > line {1}"
                            .format(*stack_item))

        if len(msgs) == 1:
            msgs.append("<NO FRAME INFO>")
        msg = "\n".join(msgs)
        return msg


class LogDebug(object):

    @staticmethod
    def info(msg):
        print(msg)
