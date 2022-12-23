# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime as datetime_org

from .. import simtime


class datetime(datetime_org.datetime):

    @staticmethod
    def now():
        timestamp = simtime.time()
        try:
            return datetime_org.datetime.fromtimestamp(timestamp)
        except:
            x = 1
