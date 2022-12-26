
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import pmatic
import time

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.

API = pmatic.api.init(
    address=u"http://172.19.76.6",
    credentials=(u"Admin", u"YetAPW123"),
    connect_timeout=20,
)

devices = API.device_list_all_detail()
# Loop all devices, only care about shutter contacts

tmp_device = [device for device in devices if device["type"] == "HM-WDS30-OT2-SM-2"][0]
ch1 = tmp_device["channels"][0]
ch2 = tmp_device["channels"][1]
# val1 = API.channel_get_value(id=ch1["id"])
# val2 = API.channel_get_value(id=ch2["id"])


class ValChangeObserver(object):

    def __init__(self, val1, val2):
        self.val1 = val1
        self.val2 = val2
        self.last_change_time = time.time()

    def get_val_has_changed(self, val1_new, val2_new):
        return (not val1_new == self.val1 or not val2_new == self.val2)

    def get_time_since_last_change(self):
        return time.time() - self.last_change_time

    def set_new_values(self, val1_new, val2_new):
        self.val1 = val1_new
        self.val2 = val2_new
        self.last_change_time = time.time()


val_change_observer = ValChangeObserver(API.channel_get_value(id=ch1["id"]),
                                        API.channel_get_value(id=ch2["id"]))

time_start = time.time()

print("started")
while True:
    val1_new = API.channel_get_value(id=ch1["id"])
    val2_new = API.channel_get_value(id=ch2["id"])
    if val_change_observer.get_val_has_changed(val1_new, val2_new):
        print("New values taken: {} and {}".format(val1_new, val2_new))
        print("Timespan since last change: {}"
              .format(val_change_observer.get_time_since_last_change()))
        val_change_observer.set_new_values(val1_new, val2_new)
    if time.time() - time_start > 10 * 60:
        break

#todo beruecksichtigen
  File "D:\Work\__temp\pr\HomeControl\src\_tests\thermo_check_update_rate.py", line 70, in <module>
    val2_new = API.channel_get_value(id=ch2["id"])
  File "D:\Work\__temp\pr\HomeControl\src\pmatic\api.py", line 190, in lowlevel_call
    return self._call(method_name_int, **kwargs)
  File "D:\Work\__temp\pr\HomeControl\src\pmatic\api.py", line 470, in _call
    return self._do_call(method_name_int, **kwargs)
  File "D:\Work\__temp\pr\HomeControl\src\pmatic\api.py", line 520, in _do_call
    return self._parse_api_response(method_name_int, kwargs, response_txt)
  File "D:\Work\__temp\pr\HomeControl\src\pmatic\api.py", line 148, in _parse_api_response
    (method_name_int, e, body))
pmatic.exceptions.PMException: Failed to parse response to channel_get_value (No JSON object could be decoded):
CONTENT-TYPE: application/json; charset=utf-8


print("finished")

API.close()
