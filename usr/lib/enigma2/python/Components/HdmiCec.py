from enigma import hdmi_cec

from Components.config import config, ConfigSubsection, ConfigOnOff

config.cec = ConfigSubsection()
config.cec.sendpower = ConfigOnOff(default=True)
config.cec.receivepower = ConfigOnOff(default=False)
config.cec.volume_forward = ConfigOnOff(default=False)

class HdmiCec:
	KEY_ID_MUTE = 113
	KEY_ID_VOLUME_DOWN = 114
	KEY_ID_VOLUME_UP = 115

	CEC_KEY_MAP = {
		KEY_ID_MUTE: 0x43,
		KEY_ID_VOLUME_DOWN: 0x42,
		KEY_ID_VOLUME_UP: 0x41,
	}

	POWER_STATE_ON = hdmi_cec.POWER_STATE_ON
	POWER_STATE_STANDBY = hdmi_cec.POWER_STATE_STANDBY
	POWER_STATE_TRANSITION_STANDBY_TO_ON = hdmi_cec.POWER_STATE_TRANSITION_STANDBY_TO_ON
	POWER_STATE_TRANSITION_ON_TO_STANDBY = hdmi_cec.POWER_STATE_TRANSITION_ON_TO_STANDBY

	def __init__(self):
		self.instance = hdmi_cec.getInstance()

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

	def setPowerState(self, newstate):
		self.instance.set_powerstate(newstate)

hdmi_cec = HdmiCec()
