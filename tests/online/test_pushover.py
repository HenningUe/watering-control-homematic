'''
Created on 06.04.2017

@author: HenningUe
'''

import pmatic
from pmatic import notify
#from pmatic import entities, ccu

ccu = pmatic.CCU()
notify.Pushover.set_default_tokens(api_token=u"afx1tgyh3quxic22n5r77hz1zpgd9n", 
                                   user_token=u"ud9ujk7p43pwxpejkeerm9b9jj3ra6")
notify.Pushover.send(u"my msg", u"my title")