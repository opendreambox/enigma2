from enigma import hdmi_cec

class Hdmi_Cec:
	def __receivedStandby(self):
		print "HDMI-CEC: Standby Received!"

	def __init__(self):
		self.instance = hdmi_cec.getInstance()
		self.instance.receivedStandby.get().append(self.__receivedStandby)

	def otp_source_enable(self):
		self.instance.cec_otp_source_enable()

	def ss_standby(self):
		self.instance.cec_ss_standby(0)

hdmi_cec = Hdmi_Cec()
