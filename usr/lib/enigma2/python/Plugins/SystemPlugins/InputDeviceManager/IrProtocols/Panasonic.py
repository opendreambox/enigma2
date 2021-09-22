from enigma import IrProtocol, IrKey

from Tools.Log import Log
from ..InputDeviceIRDatabase import irdb
class Panasonic(object):
	#{37k,432}<1,-1|1,-3>(8,-4,2:8,32:8,D:8,S:8,F:8,(D^S^F):8,1,-173)+
	M = 2
	N = 32

	@staticmethod
	def build(definition):
		frequency = 37000
		timebase = 432 * 2
		duty_cycle = 33

		carrier_period = 16000000 / frequency
		carrier_low = carrier_period * duty_cycle / 100
		toggle_mask = 0
		startbits = 1
		start_ontime = 1 << 15 | ( timebase * 8)
		start_totaltime = timebase * 12
		zero_ontime = 1 << 15 | timebase
		zero_totaltime = timebase * 2
		one_ontime = 1 << 15 | timebase
		one_totaltime = timebase * 4
		stopbits = 1
		stop_ontime = 1 << 15 | timebase
		stop_totaltime = timebase
		repeat_protocol_id = IrProtocol.IR_PROTO_CUSTOM
		repeat_ms = 80*2

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
		for key, fnc in definition["keys"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue
			device = definition["device"]
			subdevice = definition["subdevice"]
			M = Panasonic.M
			N = Panasonic.N
			checksum = (device^subdevice^fnc) & 0xff
			make_msg = M | N << 8 | device << 16 | subdevice << 24 | fnc << 32| checksum << 40
			make_len = 48
			key = IrKey(keycode, IrProtocol.IR_PROTO_CUSTOM, make_msg, make_len, 0, 0)
			keys.append(key)

		return [(proto, False, keys)]
