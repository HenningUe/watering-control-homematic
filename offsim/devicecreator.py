
# encoding: utf-8

from .pmaticpatched import entities, params


def create_devices(ccu):

    def get_address(address=[-1]):
        address[0] += 1
        return unicode(address[0])

    def get_index(reset=False, index=[-1]):  # @IgnorePep8
        if reset:
            index[0] = -1
        index[0] += 1
        return index[0]

    # switches:
    # schalter_garage
    spec = dict()
    spec[u"type"] = u"HM-PB-2-WM55-2"
    spec[u"name"] = u"SchalterGarage"
    spec[u"address"] = get_address()
    schalter_garage = entities.Device.from_dict(ccu, spec)
    channels_spec_dict = [
        {u"type": u"MAINTENANCE",
         u"address": get_address(),
         u"index": get_index(reset=True)},
        {u"type": u"KEY",
         u"name": u"SchalterGarage_DruckOben",
         u"alias": u"SchalterAktivHauptVentil1",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterGarage_DruckUnten",
         u"alias": u"SchalterDeaktivHauptVentil1",
         u"address": get_address(),
         u"index": get_index()}]
    channels = entities.Channel.from_channel_dicts(schalter_garage, channels_spec_dict)
    schalter_garage.channels = channels
    ccu.devices.add(schalter_garage)
    for ch in channels:
        ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
                                                    u"default": 0})
        ccu.devices.add(ch)

    # schalter_schuppen
    spec = dict()
    spec[u"type"] = u"HM-PB-2-WM55-2"
    spec[u"name"] = u"SchalterSchuppen"
    spec[u"address"] = get_address()
    schalter_schuppen = entities.Device.from_dict(ccu, spec)
    channels_spec_dict = [
        {u"type": u"MAINTENANCE",
         u"address": get_address(),
         u"index": get_index(reset=True)},
        {u"type": u"KEY",
         u"name": u"SchalterSchuppen_DruckOben",
         u"alias": u"SchalterAktivHauptVentil2",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterSchuppen_DruckUnten",
         u"alias": u"SchalterDeaktivHauptVentil2",
         u"address": get_address(),
         u"index": get_index()}]
    channels = entities.Channel.from_channel_dicts(schalter_schuppen, channels_spec_dict)
    schalter_schuppen.channels = channels
    ccu.devices.add(schalter_schuppen)
    for ch in channels:
        ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
                                                    u"default": 0})
        ccu.devices.add(ch)

    # schalter_wozi_1
    spec = dict()
    spec[u"type"] = u"HM-PB-6-WM55"
    spec[u"name"] = u"SchalterWoZi1"
    spec[u"address"] = get_address()
    schalter_wozi_1 = entities.Device.from_dict(ccu, spec)
    channels_spec_dict = [
        {u"type": u"MAINTENANCE",
         u"address": get_address(),
         u"index": get_index(reset=True)},
        {u"type": u"KEY",
         u"name": u"SchalterWoZi1_DruckObenLi",
         u"alias": u"SchalterAktivHauptVentil3",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterWoZi1_DruckObenRe",
         u"alias": u"SchalterBewaessGesamt",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterWoZi1_DruckMitteLi",
         u"alias": u"SchalterBewaessSued",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterWoZi1_DruckMitteRe",
         u"alias": u"SchalterBewaessWest",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterWoZi1_DruckUntenLi",
         u"alias": u"Nix",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"KEY",
         u"name": u"SchalterWoZi1_DruckUntenRe",
         u"alias": u"Nix",
         u"address": get_address(),
         u"index": get_index()}]
    channels = entities.Channel.from_channel_dicts(schalter_wozi_1, channels_spec_dict)
    schalter_wozi_1.channels = channels
    ccu.devices.add(schalter_wozi_1)
    for ch in channels:
        ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
                                                    u"default": 0})
        ccu.devices.add(ch)

    # relais:
    spec = dict()
    spec[u"type"] = u"HM-LC-Sw4-DR"
    spec[u"name"] = u"WateringRelais1"
    spec[u"address"] = get_address()
    watering_relais_1 = entities.Device.from_dict(ccu, spec)
    channels_spec_dict = [
        {u"type": u"MAINTENANCE",
         u"address": get_address(),
         u"index": get_index(reset=True)},
        {u"type": u"SWITCH",
         u"name": u"WateringRelais1_Kanal1",
         u"alias": u"VentHaupt",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SWITCH",
         u"name": u"WateringRelais1_Kanal2",
         u"alias": u"VentEntwaess",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SWITCH",
         u"name": u"WateringRelais1_Kanal3",
         u"alias": u"VentBewSued",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SWITCH",
         u"name": u"WateringRelais1_Kanal4",
         u"alias": u"VentBewWest",
         u"address": get_address(),
         u"index": get_index()}]
    channels = entities.Channel.from_channel_dicts(watering_relais_1, channels_spec_dict)
    watering_relais_1.channels = channels
    ccu.devices.add(watering_relais_1)
    for ch in channels:
        ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
                                                    u"default": 0})
        ccu.devices.add(ch)

#     # Wasserfuellstandssensor (Temperaturdifferenz-Sensor)
#     spec = dict()
#     spec[u"type"] = u"HM-WDS30-OT2-SM-2"
#     spec[u"name"] = u"WasserstandsSensorSued"
#     spec[u"address"] = get_address()
#     fuellstand_sensor_sued = entities.Device.from_dict(ccu, spec)
#     channels_spec_dict = [
#         {u"type": u"MAINTENANCE",
#          u"address": get_address(),
#          u"index": get_index(reset=True)},
#         {u"type": u"TEMPERATURE",
#          u"name": u"Temperatur1",
#          u"alias": u"WiderstandVoll",
#          u"address": get_address(),
#          u"index": get_index()},
#         {u"type": u"TEMPERATURE",
#          u"name": u"Temperatur2",
#          u"alias": u"WiderstandLeer",
#          u"address": get_address(),
#          u"index": get_index()}]
#     channels = entities.Channel.from_channel_dicts(fuellstand_sensor_sued, channels_spec_dict)
#     fuellstand_sensor_sued.channels = channels
#     ccu.devices.add(fuellstand_sensor_sued)
#     for ch in channels:
#         ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
#                                                     u"default": 0})
#         if isinstance(ch, getattr(entities, u'ChannelTemperature')):
#             ch.values[u"TEMPERATURE"] = params.Parameter(ch, {u"operations": 7,
#                                                               u"default": 0})
#         ccu.devices.add(ch)
#
#     # Wasserfuellstandssensor (Temperaturdifferenz-Sensor)
#     spec = dict()
#     spec[u"type"] = u"HM-WDS30-OT2-SM-2"
#     spec[u"name"] = u"WasserstandsSensorWest"
#     spec[u"address"] = get_address()
#     fuellstand_sensor_west = entities.Device.from_dict(ccu, spec)
#     channels_spec_dict = [
#         {u"type": u"MAINTENANCE",
#          u"address": get_address(),
#          u"index": get_index(reset=True)},
#         {u"type": u"TEMPERATURE",
#          u"name": u"Temperatur1",
#          u"alias": u"WiderstandVoll",
#          u"address": get_address(),
#          u"index": get_index()},
#         {u"type": u"TEMPERATURE",
#          u"name": u"Temperatur2",
#          u"alias": u"WiderstandLeer",
#          u"address": get_address(),
#          u"index": get_index()}]
#     channels = entities.Channel.from_channel_dicts(fuellstand_sensor_west, channels_spec_dict)
#     fuellstand_sensor_west.channels = channels
#     ccu.devices.add(fuellstand_sensor_west)
#     for ch in channels:
#         ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
#                                                     u"default": 0})
#         if isinstance(ch, getattr(entities, u'ChannelTemperature')):
#             ch.values[u"TEMPERATURE"] = params.Parameter(ch, {u"operations": 7,
#                                                               u"default": 0})
#         ccu.devices.add(ch)

    # FuellstandSensorSued ShutterContact
    spec = dict()
    spec[u"type"] = u"HM-SCI-3-FM"
    spec[u"name"] = u"FuellstandSensorSued"
    spec[u"address"] = get_address()
    fuellstand_sensor_sued = entities.Device.from_dict(ccu, spec)
    channels_spec_dict = [
        {u"type": u"MAINTENANCE",
         u"address": get_address(),
         u"index": get_index(reset=True)},
        {u"type": u"SHUTTER_CONTACT",
         u"name": u"FuellstandSensorSuedLeer",
         u"alias": u"FuellstandSensorSuedLeer",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SHUTTER_CONTACT",
         u"name": u"FuellstandSensorSuedVoll",
         u"alias": u"FuellstandSensorSuedVoll",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SHUTTER_CONTACT",
         u"name": u"FuellstandSensorSuedAktiv",
         u"alias": u"FuellstandSensorSuedAktiv",
         u"address": get_address(),
         u"index": get_index()}]
    channels = entities.Channel.from_channel_dicts(fuellstand_sensor_sued, channels_spec_dict)
    fuellstand_sensor_sued.channels = channels
    ccu.devices.add(fuellstand_sensor_sued)
    for ch in channels:
        ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
                                                    u"default": 0})
        ccu.devices.add(ch)

    # FuellstandSensorWest ShutterContact
    spec = dict()
    spec[u"type"] = u"HM-SCI-3-FM"
    spec[u"name"] = u"FuellstandSensorWest"
    spec[u"address"] = get_address()
    fuellstand_sensor_west = entities.Device.from_dict(ccu, spec)
    channels_spec_dict = [
        {u"type": u"MAINTENANCE",
         u"address": get_address(),
         u"index": get_index(reset=True)},
        {u"type": u"SHUTTER_CONTACT",
         u"name": u"FuellstandSensorWestLeer",
         u"alias": u"FuellstandSensorWestLeer",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SHUTTER_CONTACT",
         u"name": u"FuellstandSensorWestVoll",
         u"alias": u"FuellstandSensorWestVoll",
         u"address": get_address(),
         u"index": get_index()},
        {u"type": u"SHUTTER_CONTACT",
         u"name": u"FuellstandSensorWestAktiv",
         u"alias": u"FuellstandSensorWestAktiv",
         u"address": get_address(),
         u"index": get_index()}]
    channels = entities.Channel.from_channel_dicts(fuellstand_sensor_west, channels_spec_dict)
    fuellstand_sensor_west.channels = channels
    ccu.devices.add(fuellstand_sensor_west)
    for ch in channels:
        ch.values[u"STATE"] = params.Parameter(ch, {u"operations": 7,
                                                    u"default": 0})
        ccu.devices.add(ch)
