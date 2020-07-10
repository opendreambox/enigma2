#	def buildLircProtocol(self, remote):
##		Log.w("####")
##		Log.w(remote)
##		Log.w("####")
#		repeat = False
#		frequency = remote["frequency"]
#		duty_cycle = remote["duty_cycle"]
#		toggle_bit = remote["toggle_bit"]
#		startbits = remote.get("pre_data_bits", 0)
#		stopbits = remote.get("post_data_bits", 0)
#		gap = remote["gap"]
#		gap = gap[0] if isinstance(gap, list) else gap
#		#print remote["name"], gap
#		header = remote["header"]
#		bits = remote["bits"]
#		one = remote["one"]
#		zero = remote["zero"]
#		stop = remote.get("ptrail", 0)
#
#		carrier_period = 16000000 / frequency
#		carrier_low = carrier_period * duty_cycle / 100
#		toggle_mask = toggle_bit
##		start_ontime = (1 << 15) | (header[0] * 2)
##		start_totaltime = (header[0] + header[1]) * 2
##		one_ontime = (1 << 15) | (one[0] * 2)
##		one_totaltime = (one[0] + one[1]) * 2
##		zero_ontime = (1 << 15) | (zero[0] * 2)
##		zero_totaltime = (zero[0] + zero[1]) * 2
##		stop_ontime = (1 << 15) | (stop * 2)
##		stop_totaltime = stop * 2
#		start_ontime = (1 << 15) | header[0]
#		start_totaltime = header[0] + header[1]
#		one_ontime = (1 << 15) | one[0]
#		one_totaltime = one[0] + one[1]
#		zero_ontime = (1 << 15) | zero[0]
#		zero_totaltime = zero[0] + zero[1]
#		stop_ontime = (1 << 15) | stop
#		stop_totaltime = stop
#
#		repeat_ms = gap / 1000
#		repeat_protocol_id = IrProtocol.IR_PROTO_CUSTOM  #P_REP_CUSTOM if (repeat) else P_CUSTOM
#		protocol_id = IrProtocol.IR_PROTO_CUSTOM # P_CUSTOM
#		make_len = bits
#		break_len = 0
#		protocolData = IrProtocol(
#			carrier_period,
#			carrier_low, 
#			toggle_mask,
#			startbits,
#			start_ontime,
#			start_totaltime,
#			one_ontime,
#			one_totaltime,
#			zero_ontime,
#			zero_totaltime,
#			stopbits,
#			stop_ontime,
#			stop_totaltime,
#			repeat_ms,
#			repeat_protocol_id)
#
#		#Log.w("{remote_name}\n[{carrier_period}, {carrier_low}, {toggle_mask}, {startbits}, {start_ontime}, {start_totaltime}, {one_ontime}, {one_totaltime}, {zero_ontime}, {zero_totaltime} , {stopbits}, {stop_ontime}, {stop_totaltime}, {repeat_ms}, {repeat_protocol_id} ]\n_________________________________________________________________________________\n".format(**data))
#		keyData = []
#		for key, code in remote["codes"].iteritems():
#			make_msg = int(code, 16)
#			if key in self.KNOWN_KEYS:
#				Log.w( "\t\t%s" % ({
#					"key" : key,
#					"code" : code,
#					"make_msg" : make_msg
#				},))
#				data = IrKey(self.KEY_MAP[key], IrProtocol.IR_PROTO_CUSTOM, make_msg, make_len, 0, break_len)
#				keyData.append(data)
#			else:
#				Log.w("Unhandled Key: '%s'" %(key,))
#		return protocolData, keyData
