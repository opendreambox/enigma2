from enigma import IrProtocol, IrKey

from Tools.Log import Log
from ..InputDeviceIRDatabase import irdb

class JVC(object):
	# {38.0k,564}<1,-1|1,-3>(16,-8,D:8,S:8,F:8,~F:8,1,^108m,(16,-4,1,^108m)*)

	@staticmethod
	def build(definition):
		proto = IrProtocol.IR_PROTO_JVC;
		keys = []
		for key, cmd in definition["keymap"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue
			make_msg = definition["device"] << 16 | cmd
			Log.i("{0:s} : {1:x}".format(key,make_msg))
			make_len = 16
			key = IrKey(keycode, proto, make_msg, make_len, 0, 0)
			keys.append(key)
		return [(None, False, keys)]