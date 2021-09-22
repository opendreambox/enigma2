from enigma import IrProtocol, IrKey
from Tools.Log import Log

from .NEC import NECBase

class Pioneer(object):
	# {40k,564}<1,-1|1,-3>(16,-8,D:8,S:8,F:8,~F:8,1,^108m)+

	@staticmethod
	def build(definition):
		return NECBase.build(definition, 16, IrProtocol.IR_PROTO_CUSTOM, frq=40000, repeatMs=27)