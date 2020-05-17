from __future__ import absolute_import
from Components.config import config, ConfigSubsection, ConfigSlider, ConfigYesNo, ConfigNothing
from enigma import eDBoxLCD
from Components.SystemInfo import SystemInfo

class LCD:
	def __init__(self):
		pass

	def setBright(self, value):
		value *= 255
		value /= 10
		if value > 255:
			value = 255
		eDBoxLCD.getInstance().setLCDBrightness(value)

	def setContrast(self, value):
		# not implemented
		pass

	def setInverted(self, value):
		eDBoxLCD.getInstance().setInverted(value)

	def isOled(self):
		return eDBoxLCD.getInstance().isOled()

def leaveStandby():
	config.lcd.bright.apply()

def standbyCounterChanged(configElement):
	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)
	config.lcd.standby.apply()

def InitLcd():
	instance = eDBoxLCD.getInstance()
	if instance:
		detected = instance.detected()
	else:
		detected = False
	SystemInfo["Display"] = detected
	config.lcd = ConfigSubsection();
	if detected:
		def setLCDbright(configElement):
			ilcd.setBright(configElement.value);

		def setLCDinverted(configElement):
			ilcd.setInverted(configElement.value);

		standby_default = 0

		ilcd = LCD()

		config.lcd.contrast = ConfigNothing()
		if ilcd.isOled():
			standby_default = 1

		config.lcd.standby = ConfigSlider(default=standby_default, limits=(0, 10))
		config.lcd.standby.addNotifier(setLCDbright);
		config.lcd.standby.apply = lambda : setLCDbright(config.lcd.standby)

		config.lcd.bright = ConfigSlider(default=SystemInfo["DefaultDisplayBrightness"], limits=(0, 10))
		config.lcd.bright.addNotifier(setLCDbright, call_on_save_or_cancel=True);
		config.lcd.bright.apply = lambda : setLCDbright(config.lcd.bright)

		config.lcd.invert = ConfigYesNo(default=False)
		config.lcd.invert.addNotifier(setLCDinverted);
	else:
		def doNothing():
			pass
		config.lcd.contrast = ConfigNothing()
		config.lcd.bright = ConfigNothing()
		config.lcd.standby = ConfigNothing()
		config.lcd.bright.apply = lambda : doNothing()
		config.lcd.standby.apply = lambda : doNothing()

	config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

