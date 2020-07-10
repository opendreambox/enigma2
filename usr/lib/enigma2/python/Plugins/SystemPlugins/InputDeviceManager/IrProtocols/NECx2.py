from enigma import IrProtocol, IrKey
from Tools.Log import Log

from ..InputDeviceIRDatabase import irdb
from .NEC import NECBase

class NECx2(object):
	# {38.0k,564}<1,-1|1,-3>(8,-8,D:8,S:8,F:8,~F8,1,^108m)+

	@staticmethod
	def build(definition):
		return NECBase.build(definition, 8, IrProtocol.IR_PROTO_CUSTOM)
