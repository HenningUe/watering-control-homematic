
# encoding: utf-8

from ..pmaticpatched import params, events
from . import _sensortrigger

#
# def simulate(ccu):
#     SCENARIO = 20
#
#     # Hauptventil
#     if SCENARIO == 1:
#         from offsim.simulator.scenarios.n10_hauptventil import n001_hauptventil_einschalten
#         n001_hauptventil_einschalten.simulate(ccu)
#     elif SCENARIO == 2:
#         from offsim.simulator.scenarios.n10_hauptventil import n002_hauptventil_einschalten_2_druck_normal
#         n002_hauptventil_einschalten_2_druck_normal.simulate(ccu)
#     elif SCENARIO == 3:
#         from offsim.simulator.scenarios.n10_hauptventil import n003_hauptventil_einschalten_3_druck_normal
#         n003_hauptventil_einschalten_3_druck_normal.simulate(ccu)
#     elif SCENARIO == 31:
#         from offsim.simulator.scenarios.n10_hauptventil import n003a_hauptventil_einschalten_3_druck_normal_unterbr
#         n003a_hauptventil_einschalten_3_druck_normal_unterbr.simulate(ccu)
#     elif SCENARIO == 4:
#         from offsim.simulator.scenarios.n10_hauptventil import n004_hauptventil_einschalten_3_druck_kurz
#         n004_hauptventil_einschalten_3_druck_kurz.simulate(ccu)
#     elif SCENARIO == 5:
#         from offsim.simulator.scenarios.n10_hauptventil import n005_hauptventil_einschalten__unterbr_entws
#         n005_hauptventil_einschalten__unterbr_entws.simulate(ccu)
#     elif SCENARIO == 6:
#         from offsim.simulator.scenarios.n10_hauptventil import n006_hauptventil_einschalten_schalter_schuppen
#         n006_hauptventil_einschalten_schalter_schuppen.simulate(ccu)
#     elif SCENARIO == 7:
#         from offsim.simulator.scenarios.n10_hauptventil import n007_hauptventil_einschalten_schalter_wechselnd_lang
#         n007_hauptventil_einschalten_schalter_wechselnd_lang.simulate(ccu)
#     elif SCENARIO == 8:
#         from offsim.simulator.scenarios.n10_hauptventil import n008_hauptventil_einschalten_viele_druecke
#         n008_hauptventil_einschalten_viele_druecke.simulate(ccu)
#     elif SCENARIO == 9:
#         from offsim.simulator.scenarios.n10_hauptventil import n009_hauptventil_einschalten_2x_entwaess
#         n009_hauptventil_einschalten_2x_entwaess.simulate(ccu)
#     elif SCENARIO == 91:
#         from offsim.simulator.scenarios.n20_entwaessern import n009a_entwaess_2x
#         n009a_entwaess_2x.simulate(ccu)
#
#     # Watering
#     elif SCENARIO == 10:
#         from offsim.simulator.scenarios.n30_bewaessern import n010_bewaess_gesamt
#         n010_bewaess_gesamt.simulate(ccu)
#     elif SCENARIO == 11:
#         from offsim.simulator.scenarios.n30_bewaessern import n011_bewaess_sued
#         n011_bewaess_sued.simulate(ccu)
#     elif SCENARIO == 111:
#         from offsim.simulator.scenarios.n30_bewaessern import n011a_bewaess_sued_unterbr_fortsetzen
#         n011a_bewaess_sued_unterbr_fortsetzen.simulate(ccu)
#     elif SCENARIO == 12:
#         from offsim.simulator.scenarios.n30_bewaessern import n012_bewaess_west
#         n012_bewaess_west.simulate(ccu)
#     elif SCENARIO == 13:
#         from offsim.simulator.scenarios.n30_bewaessern import n013_bewaess_gesamt_unterbr_regulaer_1
#         n013_bewaess_gesamt_unterbr_regulaer_1.simulate(ccu)
#     elif SCENARIO == 14:
#         from offsim.simulator.scenarios.n30_bewaessern import n014_bewaess_gesamt_unterbr_regulaer_2
#         n014_bewaess_gesamt_unterbr_regulaer_2.simulate(ccu)
#     elif SCENARIO == 15:
#         from offsim.simulator.scenarios.n30_bewaessern import n015_bewaess_gesamt_unterbr_irregul_1
#         n015_bewaess_gesamt_unterbr_irregul_1.simulate(ccu)
#     elif SCENARIO == 16:
#         from offsim.simulator.scenarios.n30_bewaessern import n016_bewaess_gesamt_unterbr_irregul_2
#         n016_bewaess_gesamt_unterbr_irregul_2.simulate(ccu)
#     elif SCENARIO == 17:
#         from offsim.simulator.scenarios.n30_bewaessern import n017_bewaess_gesamt_unterbr_irregul_3
#         n017_bewaess_gesamt_unterbr_irregul_3.simulate(ccu)
#     elif SCENARIO == 171:
#         from offsim.simulator.scenarios.n30_bewaessern import n017a_bewaess_gesamt_unterbr_irregul_4
#         n017a_bewaess_gesamt_unterbr_irregul_4.simulate(ccu)
#     elif SCENARIO == 18:
#         from offsim.simulator.scenarios.n30_bewaessern import n018_bewaess_gesamt_unterbr_irregul_2x_1
#         n018_bewaess_gesamt_unterbr_irregul_2x_1.simulate(ccu)
#
#     # Auto-Watering
#     elif SCENARIO == 20:
#         from offsim.simulator.scenarios.n40_beweassern_auto import n020_bewaess_automatic
#         n020_bewaess_automatic.simulate(ccu)
#
#     # Watering + Steuerung Hauptventil
#     elif SCENARIO == 30:
#         from offsim.simulator.scenarios.n30_bewaessern import n030_bewaess_gesamt_regul__und_hauptv
#         n030_bewaess_gesamt_regul__und_hauptv.simulate(ccu)
#
#     else:
#         raise Exception(u"Szenario gibt's nicht")
