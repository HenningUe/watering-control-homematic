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
    autobewsrng_warte_zeit_bevor_start = 3.0  # sec
    autobewsrng_max_bewaesserungs_zeit = 8.0
    autobewsrng_max_delta_zeit_zwischen_balkonen = 15
    autobewsrng_max_zeit_ohne_bewaesserung = 15
    history_flushing_time_span = 40

    # flower beds
    autowatering_beds_times = [datetime.time(hour=18, minute=0,),
                               datetime.time(hour=8, minute=0,), ]
    autwatering_bed_lower_watering_time = 3  # sec
    autwatering_bed_upper_watering_time = 3  # sec
