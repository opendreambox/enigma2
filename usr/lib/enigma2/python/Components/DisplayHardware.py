from enigma import eDisplayManager, IntList, eVideoPorts
from Components.config import config, ConfigSelection, ConfigSubDict, ConfigSubsection, ConfigSlider, ConfigBoolean, ConfigNothing
from Components.SystemInfo import SystemInfo
from collections import defaultdict, OrderedDict


class DisplayHardware:
	instance = None
	def __init__(self):
		assert(not DisplayHardware.instance)
		DisplayHardware.instance = self
		self.initHardware()
		self.initConfig()
		self.setConfiguredMode()
		self.setupNotifiers()
		self._contentFramerateChangedSigConn = self._displayManager.contentFramerateChanged.connect(self.contentFramerateChanged)
		self._hdmiChangedSigConn = self._displayManager.hdmiChanged.connect(self.hdmiChanged)

	def initHardware(self):
		self._displayManager = eDisplayManager.getInstance()
		self._displayManager.load()
		self.availablePorts = eVideoPorts()
		self._displayManager.getAvailablePorts(self.availablePorts)

	def getGroupedModeList(self, port_name, preferredOnly = False):
		grouped_modes = OrderedDefaultDict(list)
		for mode in self.getSortedModeList(port_name):
			if preferredOnly and mode.preferred == False:
				continue
			grouped_modes[mode.name].append(mode)

		return grouped_modes

	def initConfig(self):
		config.misc.videowizardenabled = ConfigBoolean(default = True)

		try:
			x = config.av
		except KeyError:
			config.av = ConfigSubsection()
		config.av.preferred_modes_only = ConfigBoolean(default = True, descriptions = {False: _("no"), True: _("yes")})

		config.av.videomode = ConfigSubDict()
		config.av.videomode_preferred = ConfigSubDict()
		config.av.videorate = ConfigSubDict()

		policy_standard = IntList()
		policy_widescreen = IntList()
		aspects = IntList()
		osd_alpha_range = IntList()
		scaler_sharpness_range = IntList()
		hlg_support_modes = IntList()
		hdr10_support_modes = IntList()
		allow_10Bit_modes = IntList()
		allow_12Bit_modes = IntList()

		self._displayManager.getAvailableStandardPolicies(policy_standard)
		self._displayManager.getAvailableWidescreenPolicies(policy_widescreen)
		self._displayManager.getAvailableAspects(aspects)
		SystemInfo["CanChangeOsdAlpha"] = self._displayManager.hasOSDAlpha()
		osd_alpha_range = self._displayManager.getOSDAlphaRange()
		SystemInfo["CanChangeScalerSharpness"] = self._displayManager.hasScalerSharpness()
		scaler_sharpness_range = self._displayManager.getScalerSharpnessRange()
		SystemInfo["HDRSupport"] = self._displayManager.hasHDRSupport()
		self._displayManager.getAvailableHLGSupportModes(hlg_support_modes)
		self._displayManager.getAvailableHDR10SupportModes(hdr10_support_modes)
		self._displayManager.getAvailableHDR10BitModes(allow_10Bit_modes)
		self._displayManager.getAvailableHDR12BitModes(allow_12Bit_modes)

		lst_port = []
		for port_name, port in self.availablePorts.items():
			lst_port.append((port_name, port_name))
			self.updateModes(port_name)

		config.av.videoport = ConfigSelection(choices = lst_port)

		config.av.aspect = ConfigSelection(choices = [(self.aspectIndexToKey(aspect), self.aspectIndexToString(aspect)) for (aspect) in aspects],
			default = self.aspectIndexToKey(self._displayManager.getAspectDefault()))

		config.av.policy_43 = ConfigSelection(choices = [(self.policyIndexToKey(policy), self.policyIndexToString(policy)) for (policy) in policy_standard],
			default = self.policyIndexToKey(self._displayManager.getStandardPolicyDefault()))
		config.av.policy_169 = ConfigSelection(choices = [(self.policyIndexToKey(policy), self.policyIndexToString(policy)) for (policy) in policy_widescreen],
			default = self.policyIndexToKey(self._displayManager.getWidescreenPolicyDefault()))

		if SystemInfo["CanChangeOsdAlpha"]:
			config.av.osd_alpha = ConfigSlider(default=osd_alpha_range.defaultValue, increment=(osd_alpha_range.max/20), limits=(osd_alpha_range.min,osd_alpha_range.max))

		if SystemInfo["CanChangeScalerSharpness"]:
			config.av.scaler_sharpness = ConfigSlider(default=scaler_sharpness_range.defaultValue, limits=(scaler_sharpness_range.min,scaler_sharpness_range.max))

		if SystemInfo["HDRSupport"]:
			config.av.hlg_support = ConfigSelection(choices = [(self.hlgIndexToKey(mode), self.hlgIndexToString(mode)) for (mode) in hlg_support_modes],
				default = self.hlgIndexToKey(self._displayManager.getHLGSupportDefault()))
			config.av.hdr10_support = ConfigSelection(choices = [(self.hdrIndexToKey(mode), self.hdrIndexToString(mode)) for (mode) in hdr10_support_modes],
				default = self.hdrIndexToKey(self._displayManager.getHDR10SupportDefault()))
			if len(allow_10Bit_modes):
				config.av.allow_10bit = ConfigSelection(choices = [(self.propertyIndexToKey(mode), self.propertyIndexToString(mode)) for (mode) in allow_10Bit_modes],
					default = self.propertyIndexToKey(self._displayManager.getHDR10BitDefault()))
			else:
				config.av.allow_10bit = ConfigNothing()
			if len(allow_12Bit_modes):
				config.av.allow_12bit = ConfigSelection(choices = [(self.propertyIndexToKey(mode), self.propertyIndexToString(mode)) for (mode) in allow_12Bit_modes],
					default = self.propertyIndexToKey(self._displayManager.getHDR12BitDefault()))
			else:
				config.av.allow_12bit = ConfigNothing()

	def setupNotifiers(self):
		config.av.aspect.addNotifier(self.updateAspect, False)
		config.av.policy_43.addNotifier(self.updateAspect, False)
		config.av.policy_169.addNotifier(self.updateAspect, False)
		config.av.preferred_modes_only.addNotifier(self.refreshModes)

		if SystemInfo["CanChangeOsdAlpha"]:
			config.av.osd_alpha.addNotifier(self.setOSDAlpha)

		if SystemInfo["CanChangeScalerSharpness"]:
			config.av.scaler_sharpness.addNotifier(self.setScalerSharpness)

		if SystemInfo["HDRSupport"]:
			config.av.hlg_support.addNotifier(self.setHlgSupport)
			config.av.hdr10_support.addNotifier(self.setHdr10Support)
			if not isinstance(config.av.allow_10bit, ConfigNothing):
				config.av.allow_10bit.addNotifier(self.setHdr10Bit)
			if not isinstance(config.av.allow_12bit, ConfigNothing):
				config.av.allow_12bit.addNotifier(self.setHdr12Bit)

	def setConfiguredMode(self):
		currentPort = config.av.videoport.value
		currentMode = config.av.videomode[config.av.videoport.value].value
		if currentMode == "":
			# sometimes the preferred modes aren't ready when setConfiguredMode is called by hdmiChanged
			# -> ignore and wait until hdmiChanged is called again (i.e. when the preferred modes are existant)
			return
		currentRate = config.av.videorate[currentMode].value
		self.setMode(currentPort, currentMode, currentRate)

	def contentFramerateChanged(self, contentFramerate):
		currentPort = config.av.videoport.value
		currentMode = config.av.videomode[config.av.videoport.value].value
		if currentMode == "":
			return
		currentRate = config.av.videorate[currentMode].value
		if currentRate != self.rateIndexToKey(eDisplayManager.RATE_AUTO):
			return

		self.setMode(currentPort, currentMode, currentRate)

	def hdmiChanged(self):
		from Screens.Standby import inStandby
		if inStandby is None:
			self.initHardware()
			self.initConfig()
			self.setConfiguredMode()

	def getAvailablePortNames(self):
		return [name for (name, port) in self.availablePorts.items()]

	def getSortedModeList(self, port_name):
		unsorted_modes = self.availablePorts[port_name].modes
		if port_name == "HDMI-PC":
			sorted_modes = sorted(unsorted_modes, key = lambda mode: mode.width * mode.height)
		else:
			sorted_modes = sorted(unsorted_modes, key = lambda mode: (mode.height, -mode.lineMode), reverse = True)
		return sorted_modes

	def getCurrentModeByValue(self, port_value, mode_value, rate_value):
		currentPort = self.availablePorts[port_value]

		if port_value == "HDMI-PC":
			for mode in currentPort.modes:
				resolution = (str(mode.width) + "x" + str(mode.height))
				if(mode.name == mode_value and resolution == str(rate_value)):
					return mode
		else:
			for mode in currentPort.modes:
				if(mode.name == mode_value and mode.rate == self.rateKeyToIndex(rate_value)):
					return mode

	def setMode(self, port_value, mode_value, rate_value):
		if(rate_value == self.rateIndexToKey(eDisplayManager.RATE_AUTO)):
			contentFramerate = self._displayManager.getCurrentContentFramerate()
			if contentFramerate != 0:
				groupedModes = self.getGroupedModeList(config.av.videoport.value, True)
				currentModeRates = [ mode.rate for mode in groupedModes[config.av.videomode[config.av.videoport.value].value] ]

				if contentFramerate in [ eDisplayManager.RATE_25HZ, eDisplayManager.RATE_50HZ]:
					if eDisplayManager.RATE_50HZ in currentModeRates:
						rate_value = self.rateIndexToKey(eDisplayManager.RATE_50HZ)
					elif eDisplayManager.RATE_25HZ in currentModeRates:
						rate_value = self.rateIndexToKey(eDisplayManager.RATE_25HZ)

				elif contentFramerate in [ eDisplayManager.RATE_23_976HZ, eDisplayManager.RATE_24HZ, eDisplayManager.RATE_29_970HZ, eDisplayManager.RATE_30HZ, eDisplayManager.RATE_59_940HZ, eDisplayManager.RATE_60HZ ]:
					if eDisplayManager.RATE_60HZ in currentModeRates:
						rate_value = self.rateIndexToKey(eDisplayManager.RATE_60HZ)
					elif eDisplayManager.RATE_59_940HZ in currentModeRates:
						rate_value = self.rateIndexToKey(eDisplayManager.RATE_59_940HZ)
					elif eDisplayManager.RATE_30HZ in currentModeRates:
						rate_value = self.rateIndexToKey(eDisplayManager.RATE_30HZ)
					elif eDisplayManager.RATE_50HZ in currentModeRates:
						rate_value = self.rateIndexToKey(eDisplayManager.RATE_50HZ)
			else:
				print "Couldnt get content framerate, fallback to 50 hz"
				rate_value = self.rateIndexToKey(eDisplayManager.RATE_50HZ) # 50hz default


		newMode = self.getCurrentModeByValue(port_value, mode_value, rate_value)
		activeMode = self._displayManager.getCurrentMode()

		if (newMode.value != activeMode.value):
			print "-> setting (port, mode, rate) => ", port_value, mode_value, rate_value
			self._displayManager.setCurrentMode(newMode)

		self.updateAspect(None)

	def isForceWidescreen(self, mode_name):
		# some modes (720p, 1080i, etc) are always widescreen. Don't let the user select something here, "auto" is not what he wants.
		return self._displayManager.isWidescreen(mode_name)

	def isStandardScreen(self, mode_name):
		return config.av.aspect.value == self.aspectIndexToKey(eDisplayManager.ASPECT_4_3)

	def isWidescreen(self, mode_name):
		return self.isForceWidescreen(mode_name) or config.av.aspect.value in (self.aspectIndexToKey(eDisplayManager.ASPECT_16_9), self.aspectIndexToKey(eDisplayManager.ASPECT_16_10))

	def updateAspect(self, cfgelement):
		current_port = config.av.videoport.value

		if(current_port == ""):
			return

		aspect = config.av.aspect.value
		policy_standard = config.av.policy_43.value
		policy_widescreen = config.av.policy_169.value

		print "-> setting (aspect, policy, policy2) => ", aspect, policy_standard, policy_widescreen
		if(aspect != ""):
			self._displayManager.setAspect(self.aspectKeyToIndex(aspect))

		if(policy_standard != "" and policy_widescreen != ""):
			self._displayManager.setPolicies(self.policyKeyToIndex(policy_standard), self.policyKeyToIndex(policy_widescreen))
		else:
			print "Error: Couldnt set video policy!"

	def updateModes(self, port_name):
		# group by name, e.g. key=1080p, value=(1080p, 1080p20, 1080p25, ...)
		grouped_modes = self.getGroupedModeList(port_name, config.av.preferred_modes_only.value)
		config.av.videomode[port_name] = ConfigSelection(choices = [(mode_name, mode_name) for (mode_name) in grouped_modes.keys()])

		for(mode_name, modes) in grouped_modes.items():
			if(mode_name == "PC"):
				config.av.resolution = ConfigSelection(choices = [ str(mode.width) + "x" + str(mode.height) for (mode) in modes ])
			else:
				unsorted_rate_list = [ (self.rateIndexToKey(mode.rate), self.rateIndexToString(mode.rate)) for (mode) in modes ]
				rate_list = []

				has_auto_rates = [ mode.rate for mode in modes if mode.preferred ]
				if len(has_auto_rates) >= 2:
					rate_list.append((self.rateIndexToKey(eDisplayManager.RATE_AUTO), self.rateIndexToString(eDisplayManager.RATE_AUTO)))

				rate_list.extend(sorted(unsorted_rate_list, key=lambda rate: rate[0], reverse=False))
				config.av.videorate[mode_name] = ConfigSelection(choices = rate_list)

	def refreshModes(self, cfgelement):
		self.updateModes(config.av.videoport.value)

	def setHlgSupport(self, cfgelement):
		self._displayManager.setHLGSupport(self.hlgKeyToIndex(cfgelement.value))

	def setHdr10Support(self, cfgelement):
		self._displayManager.setHDR10Support(self.hdrKeyToIndex(cfgelement.value))

	def setHdr10Bit(self, cfgelement):
		self._displayManager.setHDR10Bit(self.propertyKeyToIndex(cfgelement.value))

	def setHdr12Bit(self, cfgelement):
		self._displayManager.setHDR12Bit(self.propertyKeyToIndex(cfgelement.value))

	def setOSDAlpha(self, cfgelement):
		self._displayManager.setOSDAlpha(cfgelement.value)

	def setScalerSharpness(self, cfgelement):
		self._displayManager.setScalerSharpness(cfgelement.value)

	def saveMode(self, port, mode, rate):
		print "saveMode", port, mode, rate
		config.av.videoport.value = port
		config.av.videoport.save()
		if port in config.av.videomode:
			config.av.videomode[port].value = mode
			config.av.videomode[port].save()
		if mode in config.av.videorate:
			config.av.videorate[mode].value = rate
			config.av.videorate[mode].save()

	def policyIndexToString(self, index):
		return {
#				# TRANSLATORS: (aspect ratio policy: black bars on top/bottom) in doubt, keep english term.
			eDisplayManager.PM_LETTERBOX:		_("Letterbox"),
#				# TRANSLATORS: (aspect ratio policy: black bars on left/right) in doubt, keep english term.
			eDisplayManager.PM_PILLARBOX:		_("Pillarbox"),
#				# TRANSLATORS: (aspect ratio policy: cropped content on left/right) in doubt, keep english term
			eDisplayManager.PM_PANSCAN:			_("Pan&Scan"),
#				# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the left/right)
			eDisplayManager.PM_NONLINEAR:		_("Nonlinear"),
#				# TRANSLATORS: (aspect ratio policy: display as fullscreen, even if this breaks the aspect)
			eDisplayManager.PM_BESTFIT:			_("Just Scale"),

			eDisplayManager.PM_COMBINED:		_("Combined")
		}[index]
	def policyIndexToKey(self, index):
		return {
			eDisplayManager.PM_LETTERBOX:		"letterbox",
			eDisplayManager.PM_PILLARBOX:		"pillarbox",
			eDisplayManager.PM_PANSCAN:			"panscan",
			eDisplayManager.PM_NONLINEAR:		"nonlinear",
			eDisplayManager.PM_BESTFIT:			"scale",

			eDisplayManager.PM_COMBINED:		"combined"
		}[index]
	def policyKeyToIndex(self, policy):
		return {
			"letterbox":						eDisplayManager.PM_LETTERBOX,
			"pillarbox":						eDisplayManager.PM_PILLARBOX,
			"panscan":							eDisplayManager.PM_PANSCAN,
			"nonlinear":						eDisplayManager.PM_NONLINEAR,
			"scale":							eDisplayManager.PM_BESTFIT,

			"combined":							eDisplayManager.PM_COMBINED
		}[policy]

	def aspectIndexToString(self, index):
		return {
			eDisplayManager.ASPECT_ANY:			_("Automatic"),
			eDisplayManager.ASPECT_4_3:			_("4:3"),
			eDisplayManager.ASPECT_16_9:		_("16:9"),
			eDisplayManager.ASPECT_16_10:		_("16:10")
		}[index]
	def aspectIndexToKey(self, index):
		return {
			0:									"",
			eDisplayManager.ASPECT_ANY:			"auto",
			eDisplayManager.ASPECT_4_3:			"4_3",
			eDisplayManager.ASPECT_16_9:		"16_9",
			eDisplayManager.ASPECT_16_10:		"16_10"
		}[index]
	def aspectKeyToIndex(self, aspect):
		return {
			"auto":								eDisplayManager.ASPECT_ANY,
			"4_3":								eDisplayManager.ASPECT_4_3,
			"16_9":								eDisplayManager.ASPECT_16_9,
			"16_10":							eDisplayManager.ASPECT_16_10
		}[aspect]

	def hlgIndexToString(self, index):
		return {
			eDisplayManager.HLG_FORCE_ON:		_("force enabled"),
			eDisplayManager.HLG_FORCE_OFF:		_("force disabled"),
			eDisplayManager.HLG_AUTO:			_("controlled by HDMI")
		}[index]
	def hlgIndexToKey(self, index):
		return {
			eDisplayManager.HLG_FORCE_ON:		"yes",
			eDisplayManager.HLG_FORCE_OFF:		"no",
			eDisplayManager.HLG_AUTO:			"auto(EDID)"
		}[index]
	def hlgKeyToIndex(self, hlg):
		return {
			"yes":								eDisplayManager.HLG_FORCE_ON,
			"no":								eDisplayManager.HLG_FORCE_OFF,
			"auto(EDID)":						eDisplayManager.HLG_AUTO
		}[hlg]

	def hdrIndexToString(self, index):
		return {
			eDisplayManager.HDR_FORCE_ON:		_("force enabled"),
			eDisplayManager.HDR_FORCE_OFF:		_("force disabled"),
			eDisplayManager.HDR_AUTO:			_("controlled by HDMI")
		}[index]
	def hdrIndexToKey(self, index):
		return {
			eDisplayManager.HDR_FORCE_ON:		"yes",
			eDisplayManager.HDR_FORCE_OFF:		"no",
			eDisplayManager.HDR_AUTO:			"auto(EDID)"
		}[index]
	def hdrKeyToIndex(self, hdr):
		return {
			"yes":								eDisplayManager.HDR_FORCE_ON,
			"no":								eDisplayManager.HDR_FORCE_OFF,
			"auto(EDID)":						eDisplayManager.HDR_AUTO
		}[hdr]

	def propertyIndexToString(self, index):
		return {
			eDisplayManager.PROPERTY_DISABLED:	_("no"),
			eDisplayManager.PROPERTY_ENABLED:	_("yes")
		}[index]
	def propertyIndexToKey(self, index):
		return {
			eDisplayManager.PROPERTY_DISABLED:	"1",
			eDisplayManager.PROPERTY_ENABLED:	"0"
		}[index]
	def propertyKeyToIndex(self, prop):
		return {
			"1":								eDisplayManager.PROPERTY_DISABLED,
			"0":								eDisplayManager.PROPERTY_ENABLED
		}[prop]

	def rateIndexToString(self, index):
		return {
			eDisplayManager.RATE_24HZ:			"24Hz",
			eDisplayManager.RATE_25HZ:			"25Hz",
			eDisplayManager.RATE_30HZ:			"30Hz",
			eDisplayManager.RATE_50HZ:			"50Hz",
			eDisplayManager.RATE_60HZ:			"60Hz",
			eDisplayManager.RATE_AUTO:			_("Automatic")
		}[index]
	def rateIndexToKey(self, index):
		return {
			eDisplayManager.RATE_24HZ:			"24Hz",
			eDisplayManager.RATE_25HZ:			"25Hz",
			eDisplayManager.RATE_30HZ:			"30Hz",
			eDisplayManager.RATE_50HZ:			"50Hz",
			eDisplayManager.RATE_60HZ:			"60Hz",
			eDisplayManager.RATE_AUTO:			"multi"
		}[index]
	def rateKeyToIndex(self, rate):
		return {
			"24Hz": eDisplayManager.RATE_24HZ,
			"25Hz": eDisplayManager.RATE_25HZ,
			"30Hz": eDisplayManager.RATE_30HZ,
			"50Hz": eDisplayManager.RATE_50HZ,
			"60Hz": eDisplayManager.RATE_60HZ,
			"multi": eDisplayManager.RATE_AUTO
		}[rate]


class OrderedDefaultDict(OrderedDict, defaultdict):
	def __init__(self, default_factory=None, *args, **kwargs):
		super(OrderedDefaultDict, self).__init__(*args, **kwargs)
		self.default_factory = default_factory

DisplayHardware()
