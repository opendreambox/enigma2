from enigma import IrProtocol, IrKey
from Tools.Log import Log

from ..InputDeviceIRDatabase import irdb
from .NEC import NECBase

class NEC2(object):
	# {38.0k,564}<1,-1|1,-3>(16,-8,D:8,S:8,F:8,~F:8,1,^108m)+

	@staticmethod
	def build(definition):
		return NECBase.build(definition, 16, IrProtocol.IR_PROTO_CUSTOM)