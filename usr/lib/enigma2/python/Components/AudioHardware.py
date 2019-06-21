from enigma import eAudioManager, eDVBServicePMTHandler
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigSelectionNumber
from Components.SystemInfo import SystemInfo
from Tools.Log import Log


class AudioHardware:
	instance = None
	def __init__(self):
		assert(not AudioHardware.instance)
		AudioHardware.instance = self
		self.initHardware()
		self.initConfig()
		self.setupNotifiers()

	def initHardware(self):
		self._audioManager = eAudioManager.getInstance()
		self._audioManager.load()

	def initConfig(self):
		SystemInfo["CanDownmixAC3"] = self._audioManager.hasMode(eAudioManager.OUTPUT_HDMI, eAudioManager.MODE_DOWNMIX, eAudioManager.FMT_AC3)
		SystemInfo["HasAC3PlusSupport"] = self._audioManager.hasFormat(eAudioManager.FMT_AC3_PLUS)
		SystemInfo["SupportsAC3PlusTranscode"] = self._audioManager.hasMode(eAudioManager.OUTPUT_HDMI, eAudioManager.MODE_FORCE_AC3, eAudioManager.FMT_AC3_PLUS)

		defaultAC3 = self._audioManager.getDefaultMode(eAudioManager.OUTPUT_HDMI, eAudioManager.FMT_AC3) == eAudioManager.MODE_DOWNMIX
		config.av.defaultac3 = ConfigYesNo(default = defaultAC3)
		if SystemInfo["CanDownmixAC3"]:
			config.av.downmix_ac3 = ConfigYesNo(default = defaultAC3)
		ac3delay = self._audioManager.getGeneralDelayRange(eAudioManager.OUTPUT_HDMI, eAudioManager.FMT_AC3)
		config.av.generalAC3delay = ConfigSelectionNumber(ac3delay.min, ac3delay.max, 25, default = ac3delay.defaultValue)
		pcmDelay = self._audioManager.getGeneralDelayRange(eAudioManager.OUTPUT_HDMI, eAudioManager.FMT_PCM_STEREO)
		config.av.generalPCMdelay = ConfigSelectionNumber(pcmDelay.min, pcmDelay.max, 25, default = pcmDelay.defaultValue)
		if SystemInfo["HasAC3PlusSupport"]:
			eDVBServicePMTHandler.setDDPSupport(True)
			if SystemInfo["SupportsAC3PlusTranscode"]:
				ac3plusmodes = self._audioManager.getAvailableModes(eAudioManager.OUTPUT_HDMI, eAudioManager.FMT_AC3_PLUS)

				choices = []
				if eAudioManager.MODE_AUTO in ac3plusmodes:
					choices.append((self.modeToKey(eAudioManager.MODE_AUTO), self.modeToString(eAudioManager.MODE_AUTO)))
				if eAudioManager.MODE_FORCE_AC3 in ac3plusmodes:
					choices.append((self.modeToKey(eAudioManager.MODE_FORCE_AC3), self.modeToString(eAudioManager.MODE_FORCE_AC3)))

				if not choices:
					SystemInfo["SupportsAC3PlusTranscode"] = False
					return

				Log.w("%s" %(choices,))
				config.av.convert_ac3plus = ConfigSelection(
					choices = choices,
					default = self.modeToKey(self._audioManager.getDefaultMode(eAudioManager.OUTPUT_HDMI, eAudioManager.FMT_AC3_PLUS))
				)

	def setupNotifiers(self):
		if SystemInfo["CanDownmixAC3"]:
			config.av.downmix_ac3.addNotifier(self.setAC3Downmix)

		if SystemInfo["SupportsAC3PlusTranscode"]:
			config.av.convert_ac3plus.addNotifier(self.setAC3PlusConvert)

	def setAC3Downmix(self, cfgelement):
		mode = eAudioManager.MODE_DOWNMIX if cfgelement.value else eAudioManager.MODE_AUTO
		self._audioManager.setMode(eAudioManager.OUTPUT_HDMI, mode, eAudioManager.FMT_AC3)

	def setAC3PlusConvert(self, cfgelement):
		mode = self.modeToIndex(cfgelement.value)
		self._audioManager.setMode(eAudioManager.OUTPUT_HDMI, mode, eAudioManager.FMT_AC3_PLUS)

	def modeToString(self, index):
		return {
			eAudioManager.MODE_AUTO:		_("controlled by HDMI"),
			eAudioManager.MODE_FORCE_AC3:	_("always")
		}[index]
	def modeToKey(self, index):
		return {
			eAudioManager.MODE_AUTO:		"use_hdmi_caps",
			eAudioManager.MODE_FORCE_AC3:	"always"
		}[index]
	def modeToIndex(self, mode):
		return {
			"use_hdmi_caps":	eAudioManager.MODE_AUTO,
			"always":			eAudioManager.MODE_FORCE_AC3,
		}[mode]

AudioHardware()
