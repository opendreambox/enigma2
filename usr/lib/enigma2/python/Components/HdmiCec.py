from enigma import eCec

from Components.config import config, ConfigSubsection, ConfigOnOff, ConfigSelection, ConfigText, ConfigSelectionNumber
from Tools.Log import Log
from Tools.HardwareInfo import HardwareInfo

class HdmiCec:
	POWER_STATE_ON = eCec.POWER_STATE_ON
	POWER_STATE_STANDBY = eCec.POWER_STATE_STANDBY
	POWER_STATE_TRANSITION_STANDBY_TO_ON = eCec.POWER_STATE_TRANSITION_STANDBY_TO_ON
	POWER_STATE_TRANSITION_ON_TO_STANDBY = eCec.POWER_STATE_TRANSITION_ON_TO_STANDBY
	VOLUME_TARGET_DYNAMIC = "dynamic"
	VOLUME_TARGET_AVR = "avr"
	VOLUME_TARGET_AVR_FORCE = "avr_forced"
	VOLUME_TARGET_TV = "tv"
	VOLUME_TARGET_TV_FORCE = "tv_forced"

	VOLUME_TARGETS = {
			VOLUME_TARGET_DYNAMIC : _("Dynamic"),
			VOLUME_TARGET_AVR : _("Audio System"),
			VOLUME_TARGET_AVR_FORCE : _("Audio System (force)"),
			VOLUME_TARGET_TV : _("TV"),
			VOLUME_TARGET_TV_FORCE : _("TV (force)"),
		}

	config.cec = ConfigSubsection()
	config.cec.enabled = ConfigOnOff(default=True)
	config.cec.name = ConfigText(default=HardwareInfo().get_device_name(), fixed_size = False)
	config.cec.sendpower = ConfigOnOff(default=True)
	config.cec.enable_avr = ConfigOnOff(default=True)
	config.cec.avr_power_explicit = ConfigOnOff(default=False)
	config.cec.receivepower = ConfigOnOff(default=False)
	config.cec.enable_vendor_quirks = ConfigOnOff(default=True)
	config.cec.enable_experimental_vendor_quirks = ConfigOnOff(default=False)
	config.cec.receive_remotekeys = ConfigOnOff(default=True)
	config.cec.volume_forward = ConfigOnOff(default=False)
	config.cec.volume_target = ConfigSelection(VOLUME_TARGETS, default=VOLUME_TARGET_DYNAMIC)
	config.cec.remote_repeat_delay = ConfigSelectionNumber(50, 300, 50, default=100, wraparound=True)
	config.cec.activate_on_routing_info = ConfigOnOff(default=True)
	config.cec.activate_on_routing_change = ConfigOnOff(default=True)
	config.cec.activate_on_active_source = ConfigOnOff(default=True)
	config.cec.activate_on_stream = ConfigOnOff(default=True)
	config.cec.activate_on_tvpower = ConfigOnOff(default=True)
	config.cec.ignore_powerstates = ConfigOnOff(default=False)
	config.cec.ignore_active_source_nontv = ConfigOnOff(default=False)
	config.cec.ignore_ready_state = ConfigOnOff(default=False)

	def __init__(self):
		self.instance = eCec.getInstance()
		self.instance.setName(config.cec.name.value)

	def isReady(self):
		return self.instance.isReady()

	def otpEnable(self):
		self.instance.otpEnable()

	def otpDisable(self):
		self.instance.otpDisable()

	def systemStandby(self, target=0x0f):
		self.instance.systemStandby(target)

	def isVolumeForwarded(self):
		return self.sendSystemAudioKey(0, test=True)

	def sendSystemAudioKey(self, keyid, test=False):
		ret = False
		if config.cec.enabled.value and config.cec.volume_forward.value:
			target = self.instance.getVolumeTarget()
			config_target = config.cec.volume_target.value
			if config_target == self.VOLUME_TARGET_DYNAMIC:
				ret = True
			elif config_target == self.VOLUME_TARGET_AVR and target == eCec.ADDR_AUDIO_SYSTEM:
				ret = True
			elif config_target == self.VOLUME_TARGET_AVR_FORCE:
				target = eCec.ADDR_AUDIO_SYSTEM
				ret = True
			elif config_target == self.VOLUME_TARGET_TV and target == eCec.ADDR_TV:
				ret = True
			elif config_target == self.VOLUME_TARGET_TV_FORCE:
				target = eCec.ADDR_TV
				ret = True
		if ret and not test:
			self.sendKey(target, keyid)
		return ret

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
