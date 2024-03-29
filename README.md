# ![Watering can](watering-can.png) watering-control-homematic
**_Scripts running on homematic's CCU2 to automate garden watering_**

### Table of Contents- 
**[What is this about?](#What-is-this-about)**<br>
**[My requirements](#my-requirements)**<br>
**[Equipment](#Equipment)**<br>
**[How to make this run offline?](#how-to-make-this-run-offline)**<br>
**[How to make this run online on local PC?](#how-to-make-this-run-online-on-local-pc)**<br>
**[How to make this run online on CCU2?](#how-to-make-this-run-online-on-ccu2)**<br>

#### What is this about
At home we have eight flower boxes - four on each balcony - which are exposed to the full sun. The agreement between my wife and me was as follows: The high-maintenance flower boxes may only hang if I am allowed to tinker with the automation :-). What I have done and expanded.

#### My requirements
* Garden water supply should be switchable on/off via manual switch. I.e. also for the manual water withdrawal the pressure should be switched on only on demand
* The water supply (pressure) should be deactivated again after a specified time after pressing the switch (timer).
* The flower boxes shall have water level sensors that can detect the water level empty and full.  Based on the sensor values the watering is started and stopped.
* Additional watering circuits (e.g. for the lawn) should be easy to integrate.
* Additional trigger events (switch, humidity) shall be easy to implement and integrate 
* The system should run autonomously and be easy to maintain and extend
* \[Due to these requirements I implemented my own watering script instead of using something off-the-shelf like OpenSprinkler\]

#### Equipment
* Most of the watering hardware is from Gardena, e.g. 24V watering valves
* Most of the electrical equipment is from ELV's homematic product line, like wireless relays, wireless switches and so on
* ELV's CCU2 is used as control center, i.e. the automation code is running on
* Software is based on https://github.com/LarsMichelsen/pmatic

#### How to make this run offline
1. Make sure py 2.7 is installed
2. Install virtualenv:
    * Detailed explanation is given here: https://learnpython.com/blog/how-to-use-virtualenv-python/
    * navigate to ```%PathToYourPyVersion%/Scripts```
    * Call "pip install virtualenv"
3. Create virtual environment
    * navigate to ```%PathToYourPyVersion%/Scripts```
    * Call ```virtualenv -p python "%PathWhereYourVirtEnvResides%\watering"```
4. Install requirements
    * navigate to ```%PathToYourPyVersion%/Scripts```
    * Call ```pip install -r /path/to/requirements.txt``` ("requirements.txt" is part of this repo)
5. Copy files manually to virtenv
    * copy "watering.py", "offsim/" and "tests/" to folder  ```%PathToYourPyVersion%/Scripts``` 
6. Execute scenario
    * navigate to ```%PathToYourPyVersion%/Scripts```
    * call ```python "%PathToTestScript%"```, e.g. ```python "%TEMP%"\water\Scripts\tests\offline\n40_beweassern_auto\n020_bewaess_automatic.py"```
    * Note: Not all scripts under ```./tests/offline/.``` are maintained, i.e. some may not be executable

#### How to make this run online on local PC
1. Make sure py 2.7 is installed
2. Prepare environment as described above.
2. Create ```ccu_connection.py``` next to ```watering.py``` and add credentionals and CCU-URL.
3. Execute ```python watering.py```

#### How to make this run online on CCU2
1. Follow the instructions on https://larsmichelsen.github.io/pmatic/doc/install.html#installation-on-the-ccu2 to install package
2. Navigate to http://your.ccu2.url:9120/
3. Upload ```ccu_connection.py``` and ```watering.py```
4. Add a schedule to make ```watering.py``` run on every CCU2-start

