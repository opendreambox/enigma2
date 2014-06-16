from enigma import hdmi_cec
from Components.config import config, ConfigSubsection, ConfigEnableDisable

config.cec = ConfigSubsection()
config.cec.sendpower = ConfigEnableDisable(default=True)
config.cec.receivepower = ConfigEnableDisable(default=False)
config.cec.volume_forward = ConfigEnableDisable(default=False)

class Hdmi_Cec:
	KEY_ID_MUTE = 113
	KEY_ID_VOLUME_DOWN = 114
	KEY_ID_VOLUME_UP = 115

	CEC_KEY_MAP = {
		KEY_ID_MUTE: 0x43,
		KEY_ID_VOLUME_DOWN: 0x42,
		KEY_ID_VOLUME_UP: 0x41,
	}

	def __receivedStandby(self):
		print "HDMI-CEC: Standby Received!"

	def __init__(self):
		self.instance = hdmi_cec.getInstance()
		self.instance.receivedStandby.get().append(self.__receivedStandby)
		self.volumeControl = True

	def otp_source_enable(self):
		self.instance.cec_otp_source_enable()

	def otp_source_disable(self):
		self.instance.cec_otp_source_disable()

	def ss_standby(self):
		self.instance.cec_ss_standby(0x0f)

	def sendSystemAudioKey(self, keyid):
		self.sendKey(self.instance.get_volume_control_dest(), keyid)

	def sendKey(self, dest, keyid):
		if keyid in self.CEC_KEY_MAP.keys():
			code = self.CEC_KEY_MAP[keyid]
			self.instance.cec_sendkey(dest, int(code))

hdmi_cec = Hdmi_Cec()
