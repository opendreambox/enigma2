from enigma import IrProtocol, IrKey
from Tools.Log import Log

from ..InputDeviceIRDatabase import irdb

class RC5(object):
	# {36k,msb,889}<1,-1|-1,1>(1,~F:1:6,T:1,D:5,F:6,^114m)+

	@staticmethod
	def build(definition):
		proto = IrProtocol.IR_PROTO_RC5
		keys = []
		for key, cmd in definition["keys"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue
			make_msg = (definition["device"] & 0x1F) << 6 | cmd & 0x3F #start and togglebit are handled by the integrated RC5 protocol
			Log.i("{0:s} : {1:x}".format(key,make_msg))
			make_len = 11
			key = IrKey(keycode, proto, make_msg, make_len, 0, 0)
			keys.append(key)
		return [(None, False, keys)]