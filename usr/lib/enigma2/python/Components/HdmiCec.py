from enigma import eCec

from Components.config import config, ConfigSubsection, ConfigOnOff
from Tools.Log import Log

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

	POWER_STATE_ON = eCec.POWER_STATE_ON
	POWER_STATE_STANDBY = eCec.POWER_STATE_STANDBY
	POWER_STATE_TRANSITION_STANDBY_TO_ON = eCec.POWER_STATE_TRANSITION_STANDBY_TO_ON
	POWER_STATE_TRANSITION_ON_TO_STANDBY = eCec.POWER_STATE_TRANSITION_ON_TO_STANDBY

	def __init__(self):
		self.instance = eCec.getInstance()

	def otpEnable(self):
		self.instance.otpEnable()

	def otpDisable(self):
		self.instance.otpDisable()

	def systemStandby(self, target=0x0f):
		self.instance.systemStandby(target)

	def sendSystemAudioKey(self, keyid):
		self.sendKey(self.instance.getVolumeTarget(), keyid)

	def sendKey(self, dest, keyid):
		if keyid in self.CEC_KEY_MAP.keys():
			code = self.CEC_KEY_MAP[keyid]
			self.instance.sendKey(dest, int(code))

	def setPowerState(self, newstate):
		self.instance.setPowerstate(newstate)

#Deprecated compat API
	def otp_source_enable(self):
		Log.w("deprecated method call")
		self.otpEnable()

	def otp_source_disable(self):
		Log.w("deprecated method call")
		self.otpDisable()

	def ss_standby(self):
		Log.w("deprecated method call")
		self.systemStandby()


hdmi_cec = HdmiCec()
