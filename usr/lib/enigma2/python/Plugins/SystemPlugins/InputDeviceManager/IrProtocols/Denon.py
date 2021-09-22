from enigma import IrProtocol, IrKey

from Tools.Log import Log
from ..InputDeviceIRDatabase import irdb

from socket import htons

class Denon(object):
 	#{38k,264}<1,-3|1,-7>(D:5,F:8,0:2,1,-165,D:5,~F:8,3:2,1,-165)+ 
	# We use the first half as initial and the second half as repeat message. 
	# Even using just a single half should be enough for the signal to be decoded correctly, but using both will help avoiding spurious decodes

	@staticmethod
	def build(definition):
		frequency = 38000
		timebase = 275 * 2;
		duty_cycle = 33

		carrier_period = 16000000 / frequency
		carrier_low = carrier_period * duty_cycle / 100
		toggle_mask = 0
		startbits = 0
		start_ontime = 0
		start_totaltime = 0
		zero_ontime = 1 << 15 | timebase
		zero_totaltime = timebase * 4
		one_ontime = 1 << 15 | timebase
		one_totaltime = timebase * 8
		stopbits = 1
		stop_ontime = 1 << 15 | timebase
		stop_totaltime = timebase
		repeat_protocol_id = IrProtocol.IR_PROTO_CUSTOM
		repeat_ms = 80

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

		# rep_proto = IrProtocol(
		# 	carrier_period,
		# 	carrier_low,
		# 	toggle_mask,
		# 	startbits,
		# 	start_ontime,
		# 	start_totaltime,
		# 	one_ontime,
		# 	one_totaltime,
		# 	zero_ontime,
		# 	zero_totaltime,
		# 	stopbits,
		# 	stop_ontime,
		# 	stop_totaltime,
		# 	repeat_ms,
		# 	IrProtocol.IR_PROTO_REP_CUSTOM)

		keys = []
		# rep_keys = []
		for key, fnc in definition["keys"].iteritems():
			keycode = irdb.mapKey(key)
			if not keycode:
				continue
			device = definition["device"]
			make_len = 15
			#D:5,F:8,0:2
			make_msg = (device & 0x1f) | (fnc & 0xff) << 5 | 0 << 13
			make_msg = (htons(make_msg) >> 1) & 0x7FFF #htons returns a byte swapped 16 bit interpretation of our msg, we only have 15 bits so we need to shift it 1 bit to the right
			Log.d("Denon initial: {0} : 0x{1:x} : {1:015b} : (D:{2:x} F:{3:x})".format(key, make_msg, device, fnc))
			make_key = IrKey(keycode, IrProtocol.IR_PROTO_CUSTOM, make_msg, make_len, 0, 0)
			keys.append(make_key)

			# #D:5,~F:8,3:2
			# rep_make_msg = (device & 0x1f) | (fnc ^ 0xff) << 5 | 3 << 13
			# rep_make_msg = (htons(rep_make_msg) >> 1) & 0x7FFF #htons returns a byte swapped 16 bit interpretation of our msg, we only have 15 bits so we need to shift it 1 bit to the right
			# Log.i("Denon repeat: {0} : 0x{1:x} : {1:015b}".format(key, rep_make_msg))
			# rep_key = IrKey(keycode, IrProtocol.IR_PROTO_REP_CUSTOM, rep_make_msg, make_len, 0, 0)
			# rep_keys.append(rep_key)

		return [(proto, False, keys),] #(rep_proto, True, rep_keys)
