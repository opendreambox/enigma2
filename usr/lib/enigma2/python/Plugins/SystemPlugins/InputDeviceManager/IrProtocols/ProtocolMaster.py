# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .JVC import JVC
from .NEC import NEC
from .NEC2 import NEC2
from .NECx2 import NECx2
from .RC5 import RC5
from Tools.Log import Log

class ProtocolMaster(object):
	HANDLER_LUT  = {
		"JVC" : JVC,
		"NEC" : NEC,
		"NEC2" : NEC2,
		"NECx2" : NECx2,
		"RC5" : RC5
	}
	@staticmethod
	def buildProtocol(data):
		protocol = data["protocol"]
		protocolHandler = ProtocolMaster.HANDLER_LUT.get(protocol, None)
		if not protocolHandler:
			Log.w("No Handler for Protocol %s" %(protocol,))
			return [(False,False,False)]
		return protocolHandler.build(data)
