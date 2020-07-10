from enigma import IrProtocol, IrKey
from Tools.Log import Log

from ..InputDeviceIRDatabase import irdb

class NECBase(object):

	@staticmethod
	def build(definition, ontime, repeatProtocol):
		frequency = 38000
		timebase = 564 * 2;
		duty_cycle = 33

		carrier_period = 16000000 / frequency
		carrier_low = carrier_period * duty_cycle / 100
		toggle_mask = 0
		startbits = 1
		start_ontime = 1 << 15 | ( timebase * ontime)
		start_totaltime = timebase * (ontime + 8)
		zero_ontime = 1 << 15 | timebase
		zero_totaltime = timebase * 2
		one_ontime = 1 << 15 | timebase
		one_totaltime = timebase * 4
		stopbits = 1
		stop_ontime = 1 << 15 | timebase
		stop_totaltime = timebase
		repeat_protocol_id = repeatProtocol
		repeat_ms = 108

		proto = IrProtocol(
			carrier_period,
			carrier_low,
			toggle_mask,
			startbits,
			start_ontime,
			start_totaltime,
			one_ontime,
			one_totaltime,
			zero_ontime,
			zero_totaltime,
			stopbits,
			stop_ontime,
			stop_totaltime,
			repeat_ms,
			repeat_protocol_id)

		keys = []
		for key, cmd in definition["keys"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue
			subdevice = definition["subdevice"]
			subdevice = subdevice if subdevice != -1 else definition["device"]^0xFF
			make_msg = definition["device"] << 24 | subdevice << 16 | cmd << 8 | (cmd^0xff)
			Log.i("{0:s} : {1:x}".format(key,make_msg))
			make_len = 32
			key = IrKey(keycode, IrProtocol.IR_PROTO_CUSTOM, make_msg, make_len, 0, 0)
			keys.append(key)
		return [(proto, False, keys)]

class NEC(object):
	# {38.0k,564}<1,-1|1,-3>(16,-8,D:8,S:8,F:8,~F:8,1,^108m,(16,-4,1,^108m)*)
	@staticmethod
	def build(definition):
		return NECBase.build(definition, 16, IrProtocol.IR_PROTO_REP_NEC)
