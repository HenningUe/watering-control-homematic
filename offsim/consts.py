# encoding: utf-8

import datetime


class ActorConstants(object):
    dauer_uebertragung_an_geraet = 1.5
    dauer_relais_schalten = 1.5


class TimeConstants(object):
    # general
    dauer_entwaesserung = 4.0  # sec
    dauer_entwaesserung_lang = 12.0  # sec
    dauer_hauptventil_alleine = 6.0  # sec
    dauer_hauptventil_alleine_max = 18.0  # sec

    # balconies
    autowatering_warte_zeit_bevor_start = 3.0  # sec
    autowatering_max_waterings_zeit = 8.0
    autowatering_max_delta_zeit_zwischen_balkonen = 15
    autowatering_max_zeit_ohne_watering = 15
    history_flushing_time_span = 40

    # flower beds
    autowatering_beds_times = [datetime.time(hour=18, minute=0,),
                               datetime.time(hour=8, minute=0,), ]
    autwatering_bed_lower_watering_time = 3  # sec
    autwatering_bed_upper_watering_time = 3  # sec
