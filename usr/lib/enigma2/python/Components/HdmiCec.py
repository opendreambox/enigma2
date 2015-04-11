from enigma import eCec

from Components.config import config, ConfigSubsection, ConfigOnOff
from Tools.Log import Log

config.cec = ConfigSubsection()
config.cec.sendpower = ConfigOnOff(default=True)
config.cec.avr_power_explicit = ConfigOnOff(default=False)
config.cec.receivepower = ConfigOnOff(default=False)
config.cec.enable_vendor_quirks = ConfigOnOff(default=False)
config.cec.receive_remotekeys = ConfigOnOff(default=True)
config.cec.volume_forward = ConfigOnOff(default=False)
config.cec.activate_on_routing_info = ConfigOnOff(default=True)
config.cec.activate_on_routing_change = ConfigOnOff(default=True)
config.cec.activate_on_active_source = ConfigOnOff(default=True)
config.cec.activate_on_stream = ConfigOnOff(default=True)
config.cec.activate_on_tvpower = ConfigOnOff(default=True)

class HdmiCec:
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

	def getVolumeTarget(self):
		return self.instance.getVolumeTarget()

	def sendKey(self, dest, keyid):
		self.instance.sendKey(dest, keyid)

	def setPowerState(self, newstate):
		self.instance.setPowerstate(newstate)

	def giveSystemAudioStatus(self):
		self.instance.giveSystemAudioStatus()

	def systemAudioRequest(self):
		self.instance.systemAudioRequest()

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
