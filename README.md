# watering-control-homematic
#### Scripts running on homematic's CCU2 to automate garden watering

What is this about? At home we have eight flower boxes - four on each balcony - which are exposed to the full sun. The agreement between my wife and me was as follows: The high-maintenance flower boxes may only hang if I am allowed to tinker with the automation :-). What I have done and expanded.

# My requirements
* Garden water supply should be switchable on/off via manual switch. I.e. also for the manual water withdrawal the pressure should be switched on only on demand
* The water supply (pressure) should be deactivated again after a specified time after pressing the switch (timer).
* The flower boxes shall have water level sensors that can detect the water level empty and full.  Based on the sensor values the watering is started and stopped.
* Additional watering circuits (e.g. for the lawn) should be easy to integrate.
* Additional trigger events (switch, humidity) shall be easy to implement and integrate 
* The system should run autonomously and be easy to maintain and extend


# Equipment
* Most of the watering hardware is from Gardena, e.g. 24V watering valves
* Most of the electrical equipment is from ELV's homematic product line, like wireless relays, wireless switches and so on
* ELV's CCU2 is used as control center, i.e. the automation code is running on
* Software is based on https://github.com/LarsMichelsen/pmatic

# How 
