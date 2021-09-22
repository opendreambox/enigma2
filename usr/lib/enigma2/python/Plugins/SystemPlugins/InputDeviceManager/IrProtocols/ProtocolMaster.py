# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .Denon import Denon
from .JVC import JVC
from .NEC import NEC
from .NEC2 import NEC2
from .NECx2 import NECx2
from .RC5 import RC5
from .Sony import Sony12, Sony15, Sony20
from .Panasonic import Panasonic
from .Pioneer import Pioneer
from Tools.Log import Log

class ProtocolMaster(object):
	HANDLER_LUT  = {
		"Denon" : Denon,
		"JVC" : JVC,
		"NEC" : NEC,
		"NEC2" : NEC2,
		"NECx2" : NECx2,
		"RC5" : RC5,
		"Panasonic" : Panasonic,
		"Pioneer" : Pioneer,
		"Sony12" : Sony12,
		"Sony15" : Sony15,
		"Sony20" : Sony20,
	}

	@staticmethod
	def buildProtocol(data):
		protocol = data["protocol"]
		protocolHandler = ProtocolMaster.HANDLER_LUT.get(protocol, None)
		if not protocolHandler:
			Log.w("No Handler for Protocol %s" %(protocol,))
			return [(False,False,False)]
		return protocolHandler.build(data)
