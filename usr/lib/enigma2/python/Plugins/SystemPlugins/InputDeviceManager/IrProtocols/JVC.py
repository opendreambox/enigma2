from enigma import IrProtocol, IrKey

from Tools.Log import Log
from ..InputDeviceIRDatabase import irdb

class JVC(object):
	# {38k,525}<1,-1|1,-3>(16,-8,(D:8,F:8,1,-45)+)

	@staticmethod
	def build(definition):
		keys = []
		for key, cmd in definition["keys"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue
			make_msg = definition["device"] | cmd << 8
			Log.i("JVC - {0:s} : {1:x} : {1:016b}".format(key, make_msg))
			make_len = 16
			key = IrKey(keycode, IrProtocol.IR_PROTO_JVC, make_msg, make_len, 0, 0)
			keys.append(key)
		return [(None, False, keys)]
