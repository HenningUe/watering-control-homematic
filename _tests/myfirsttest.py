'''
Created on 31.01.2017

@author: HenningUe
'''

import pmatic

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
ccu = pmatic.CCU(
    # TODO: Replace this with the URL to your CCU2.
    address=u"http://172.19.76.6",
    # TODO: Insert your credentials here.
    credentials=(u"Admin", u"YetAPW123"),
    connect_timeout=5
)

from pprint import pprint
# ccu.api.print_methods()
# pprint(ccu.api.interface_list_devices(interface=u'BidCos-RF'))
# pprint(ccu.api.interface_list_interfaces())
devices = ccu.api.device_list_all_detail()
item = [it for it in devices if it['name'].startswith('Fuellstand')]
pprint(item)
#
# TODO:
# #testen:
# HM_PB_2_WM55_2
#
# #create_device:
# u"""
# {u'address': u'MEQ0741367',
#   u'channels': [{u'address': u'MEQ0741367:1',
#                  u'category': u'CATEGORY_SENDER',
#                  u'channelType': u'KEY',
#                  u'deviceId': u'1238',
#                  u'id': u'1259',
#                  u'index': 1,
#                  u'isAesAvailable': True,
#                  u'isEventable': True,
#                  u'isLogable': True,
#                  u'isLogged': False,
#                  u'isReadable': False,
#                  u'isReady': True,
#                  u'isUsable': True,
#                  u'isVirtual': False,
#                  u'isVisible': True,
#                  u'isWritable': True,
#                  u'mode': u'MODE_AES',
#                  u'name': u'SchalterGarageRunter',
#                  u'partnerId': u'1265'},
#                 {u'address': u'MEQ0741367:2',
#                  u'category': u'CATEGORY_SENDER',
#                  u'channelType': u'KEY',
#                  u'deviceId': u'1238',
#                  u'id': u'1265',
#                  u'index': 2,
#                  u'isAesAvailable': True,
#                  u'isEventable': True,
#                  u'isLogable': True,
#                  u'isLogged': False,
#                  u'isReadable': False,
#                  u'isReady': True,
#                  u'isUsable': True,
#                  u'isVirtual': False,
#                  u'isVisible': True,
#                  u'isWritable': True,
#                  u'mode': u'MODE_AES',
#                  u'name': u'SchalterGarageHoch',
#                  u'partnerId': u'1259'}],
#   u'id': u'1238',
#   u'interface': u'BidCos-RF',
#   u'name': u'SchalterGarage',
#   u'operateGroupOnly': u'false',
#   u'type': u'HM-PB-2-WM55-2'}]
# """
