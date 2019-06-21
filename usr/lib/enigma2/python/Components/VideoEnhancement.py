from enigma import eVideoManager, IntList
from Components.config import config, ConfigSubsection, ConfigSlider, ConfigSelection, ConfigNothing, NoSave

class VideoEnhancement:
	instance = None
	firstRun = True

	def __init__(self):
		assert(not VideoEnhancement.instance)
		VideoEnhancement.instance = self
		self.last_modes_preferred =  [ ]
		self.initHardware()
		self.initConfig()

	def initHardware(self):
		self._videoManager = eVideoManager.getInstance()
		self._videoManager.load()

	def initConfig(self, *args):
		config.pep = ConfigSubsection()
		config.pep.configsteps = NoSave(ConfigSelection(choices=[1, 5, 10, 25], default = 1))

		if self._videoManager.hasContrast():
			contrastRange = self._videoManager.getContrastRange()
			config.pep.contrast = ConfigSlider(default=contrastRange.defaultValue, limits=(contrastRange.min,contrastRange.max))
			config.pep.contrast.addNotifier(self.setContrast)
		else:
			config.pep.contrast = NoSave(ConfigNothing())

		if self._videoManager.hasSaturation():
			saturationRange = self._videoManager.getSaturationRange()
			config.pep.saturation = ConfigSlider(default=saturationRange.defaultValue, limits=(saturationRange.min,contrastRange.max))
			config.pep.saturation.addNotifier(self.setSaturation)
		else:
			config.pep.saturation = NoSave(ConfigNothing())

		if self._videoManager.hasHue():
			hueRange = self._videoManager.getHueRange()
			config.pep.hue = ConfigSlider(default=hueRange.defaultValue, limits=(hueRange.min,hueRange.max))
			config.pep.hue.addNotifier(self.setHue)
		else:
			config.pep.hue = NoSave(ConfigNothing())

		if self._videoManager.hasBrightness():
			brightnessRange = self._videoManager.getBrightnessRange()
			config.pep.brightness = ConfigSlider(default=brightnessRange.defaultValue, limits=(brightnessRange.min,brightnessRange.max))
			config.pep.brightness.addNotifier(self.setBrightness)
		else:
			config.pep.brightness = NoSave(ConfigNothing())

		try:
			x = config.av.scaler_sharpness.value
		except KeyError:
			if self._videoManager.hasScalerSharpness():
				scalerSharpnessRange = self._videoManager.getScalerSharpnessRange()
				try:
					y = config.av
				except KeyError:
					config.av = ConfigSubsection()
				config.av.scaler_sharpness = ConfigSlider(default=scalerSharpnessRange.defaultValue, limits=(scalerSharpnessRange.min,scalerSharpnessRange.max))
				config.av.scaler_sharpness.addNotifier(self.setScalerSharpness)

		if self._videoManager.hasSplitMode():
			splitModes = IntList()
			self._videoManager.getAvailableSplitModes(splitModes)
			config.pep.split = ConfigSelection(choices = [(self.splitModeIndexToKey(mode), self.splitModeIndexToString(mode)) for (mode) in splitModes],
				default = self.splitModeIndexToKey(self._videoManager.getSplitModeDefault()))
			config.pep.split.addNotifier(self.setSplitMode)
		else:
			config.pep.split = NoSave(ConfigNothing())

		if self._videoManager.hasSharpness():
			sharpnessRange = self._videoManager.getSharpnessRange()
			config.pep.sharpness = ConfigSlider(default=sharpnessRange.defaultValue, limits=(sharpnessRange.min,sharpnessRange.max))
			config.pep.sharpness.addNotifier(self.setSharpness)
		else:
			config.pep.sharpness = NoSave(ConfigNothing())

		if self._videoManager.hasAutoFlesh():
			autoFleshRange = self._videoManager.getAutoFleshRange()
			config.pep.auto_flesh = ConfigSlider(default=autoFleshRange.defaultValue, limits=(autoFleshRange.min,autoFleshRange.max))
			config.pep.auto_flesh.addNotifier(self.setAutoFlesh)
		else:
			config.pep.auto_flesh = NoSave(ConfigNothing())

		if self._videoManager.hasGreenBoost():
			greenBoostRange = self._videoManager.getGreenBoostRange()
			config.pep.green_boost = ConfigSlider(default=greenBoostRange.defaultValue, limits=(greenBoostRange.min,greenBoostRange.max))
			config.pep.green_boost.addNotifier(self.setGreenBoost)
		else:
			config.pep.green_boost = NoSave(ConfigNothing())

		if self._videoManager.hasColorTemp():
			colorTempRange = self._videoManager.getColorTempRange()
			config.pep.color_temp = ConfigSlider(default=colorTempRange.defaultValue, limits=(colorTempRange.min,colorTempRange.max))
			config.pep.color_temp.addNotifier(self.setColorTemp)
		else:
			config.pep.color_temp = NoSave(ConfigNothing())

		if self._videoManager.hasBlueBoost():
			blueBoostRange = self._videoManager.getBlueBoostRange()
			config.pep.blue_boost = ConfigSlider(default=blueBoostRange.defaultValue, limits=(blueBoostRange.min,blueBoostRange.max))
			config.pep.blue_boost.addNotifier(self.setBlueBoost)
		else:
			config.pep.blue_boost = NoSave(ConfigNothing())

		if self._videoManager.hasDynamicContrast():
			dynamicContrastRange = self._videoManager.getDynamicContrastRange()
			config.pep.dynamic_contrast = ConfigSlider(default=dynamicContrastRange.defaultValue, limits=(dynamicContrastRange.min,dynamicContrastRange.max))
			config.pep.dynamic_contrast.addNotifier(self.setDynamicContrast)
		else:
			config.pep.dynamic_contrast = NoSave(ConfigNothing())

		if self._videoManager.hasBlockNoiseReduction():
			blockNoiseReductionRange = self._videoManager.getBlockNoiseReductionRange()
			config.pep.block_noise_reduction = ConfigSlider(default=blockNoiseReductionRange.defaultValue, limits=(blockNoiseReductionRange.min,blockNoiseReductionRange.max))
			config.pep.block_noise_reduction.addNotifier(self.setBlockNoiseReduction)
		else:
			config.pep.block_noise_reduction = NoSave(ConfigNothing())

		if self._videoManager.hasMosquitoNoiseReduction():
			mosquitoNoiseReductionRange = self._videoManager.getMosquitoNoiseReductionRange()
			config.pep.mosquito_noise_reduction = ConfigSlider(default=mosquitoNoiseReductionRange.defaultValue, limits=(mosquitoNoiseReductionRange.min,mosquitoNoiseReductionRange.max))
			config.pep.mosquito_noise_reduction.addNotifier(self.setMosquitoNoiseReduction)
		else:
			config.pep.mosquito_noise_reduction = NoSave(ConfigNothing())

		if self._videoManager.hasDigitalContourRemoval():
			digitalContourRemovalRange = self._videoManager.getDigitalContourRemovalRange()
			config.pep.digital_contour_removal = ConfigSlider(default=digitalContourRemovalRange.defaultValue, limits=(digitalContourRemovalRange.min,digitalContourRemovalRange.max))
			config.pep.digital_contour_removal.addNotifier(self.setDigitalContourRemoval)
		else:
			config.pep.digital_contour_removal = NoSave(ConfigNothing())

		if VideoEnhancement.firstRun:
			self.setConfiguredValues()

		VideoEnhancement.firstRun = False

	def setContrast(self, cfgelement):
		self._videoManager.setContrast(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setSaturation(self, cfgelement):
		self._videoManager.setSaturation(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setHue(self, cfgelement):
		self._videoManager.setHue(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setBrightness(self, cfgelement):
		self._videoManager.setBrightness(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setScalerSharpness(self, cfgelement):
		self._videoManager.setScalerSharpness(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setSplitMode(self, cfgelement):
		self._videoManager.setSplitMode(self.splitModeKeyToIndex(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setSharpness(self, cfgelement):
		self._videoManager.setSharpness(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setAutoFlesh(self, cfgelement):
		self._videoManager.setAutoFlesh(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setGreenBoost(self, cfgelement):
		self._videoManager.setGreenBoost(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setColorTemp(self, cfgelement):
		self._videoManager.setColorTemp(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setBlueBoost(self, cfgelement):
		self._videoManager.setBlueBoost(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setDynamicContrast(self, cfgelement):
		self._videoManager.setDynamicContrast(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setBlockNoiseReduction(self, cfgelement):
		self._videoManager.setBlockNoiseReduction(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setMosquitoNoiseReduction(self, cfgelement):
		self._videoManager.setMosquitoNoiseReduction(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setDigitalContourRemoval(self, cfgelement):
		self._videoManager.setDigitalContourRemoval(int(cfgelement.value))
		if not VideoEnhancement.firstRun:
			self.setConfiguredValues()

	def setConfiguredValues(self):
		self._videoManager.applyChanges()

	def setDeinterlaceMode(self, mode):
		self._videoManager.setDeinterlaceMode(int(mode))

	def getDeinterlaceMode(self):
		self._videoManager.getDeinterlaceMode()


	def splitModeIndexToString(self, index):
		return {
			eVideoManager.SM_OFF:				_("Off"),
			eVideoManager.SM_LEFT:				_("Left"),
			eVideoManager.SM_RIGHT:				_("Right")
		}[index]
	def splitModeIndexToKey(self, index):
		return {
			eVideoManager.SM_OFF:				"off",
			eVideoManager.SM_LEFT:				"left",
			eVideoManager.SM_RIGHT:				"right"
		}[index]
	def splitModeKeyToIndex(self, mode):
		return {
			"off":							eVideoManager.SM_OFF,
			"left":							eVideoManager.SM_LEFT,
			"right":						eVideoManager.SM_RIGHT
		}[mode]

	def deinterlaceModeIndexToKey(self, index):
		return {
			eVideoManager.DM_OFF:			"off",
			eVideoManager.DM_ON:			"on",
			eVideoManager.DM_AUTO:			"auto",
			eVideoManager.DM_BOB:			"bob"
		}[index]
	def deinterlaceModeKeyToIndex(self, mode):
		return {
			"off":							eVideoManager.DM_OFF,
			"on":							eVideoManager.DM_ON,
			"auto":							eVideoManager.DM_AUTO,
			"bob":							eVideoManager.DM_BOB
		}[mode]

VideoEnhancement()