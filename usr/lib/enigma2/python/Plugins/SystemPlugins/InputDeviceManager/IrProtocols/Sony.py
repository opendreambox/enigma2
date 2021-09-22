from enigma import IrProtocol, IrKey
from Tools.Log import Log

from ..InputDeviceIRDatabase import irdb

class SonyBase(object): # for Sony12 to Sony20
	FUNCTION_BITS = 7

	@staticmethod
	def build(definition, deviceBits=5, subdeviceBits=0): # default is Sony12
		keys = []
		for key, fnc in definition["keys"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue

			if subdeviceBits:
				sdShift =  SonyBase.FUNCTION_BITS + deviceBits
				make_msg = (fnc & 0x7f) | definition["device"] << SonyBase.FUNCTION_BITS |  definition["subdevice"] << sdShift
			else:
				make_msg = (fnc & 0x7f) | definition["device"] << SonyBase.FUNCTION_BITS

			make_len = SonyBase.FUNCTION_BITS + deviceBits + subdeviceBits
			key = IrKey(keycode, IrProtocol.IR_PROTO_SIRC, make_msg, make_len, 0, 0)
			keys.append(key)
		return [(None, False, keys)]

# Sony12 IRP notation: {40k,600}<1,-1|2,-1>(4,-1,F:7,D:5,^45m)+
class Sony12(SonyBase):
	@staticmethod
	def build(definition):
		return SonyBase.build(definition)

# Sony15 IRP notation: {40k,600}<1,-1|2,-1>(4,-1,F:7,D:8,^45m)+
class Sony15(SonyBase):
	@staticmethod
	def build(definition):
		return SonyBase.build(definition, deviceBits=8)

# Sony20 IRP notation: {40k,600}<1,-1|2,-1>(4,-1,F:7,D:5,S:8,^45m)+
class Sony20(SonyBase):
	@staticmethod
	def build(definition):
		return SonyBase.build(definition, subdeviceBits=8)
