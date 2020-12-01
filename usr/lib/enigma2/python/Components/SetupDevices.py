from config import config, ConfigSelection, ConfigSubsection, ConfigOnOff, ConfigText
from Components.Timezones import timezones
from Components.Language import language
from Components.Keyboard import keyboard
from Components.config import ConfigInteger

def InitSetupDevices():
	
	def timezoneNotifier(configElement):
		timezones.activateTimezone(configElement.index)

	config.timezone = ConfigSubsection();
	config.timezone.version = ConfigInteger(default=0)
	timezones.checkUpgrade()
	config.timezone.val = ConfigSelection(default = timezones.getDefaultTimezone(), choices = timezones.getTimezoneList())
	config.timezone.val.addNotifier(timezoneNotifier)

	def keyboardNotifier(configElement):
		keyboard.activateKeyboardMap(configElement.index)

	config.keyboard = ConfigSubsection();
	config.keyboard.keymap = ConfigSelection(default = keyboard.getDefaultKeyboardMap(), choices = keyboard.getKeyboardMaplist())
	config.keyboard.keymap.addNotifier(keyboardNotifier)

	def languageNotifier(configElement):
		language.activateLanguage(configElement.value)

	config.osd = ConfigSubsection()
	config.osd.language = ConfigText(default = "en_GB");
	config.osd.language.addNotifier(languageNotifier, immediate_feedback=False, call_on_save_or_cancel=True, initial_call=True)

	config.parental = ConfigSubsection();
	config.parental.lock = ConfigOnOff(default = False)
	config.parental.setuplock = ConfigOnOff(default = False)

	config.expert = ConfigSubsection();
	config.expert.satpos = ConfigOnOff(default = True)
	config.expert.fastzap = ConfigOnOff(default = True)
	config.expert.skipconfirm = ConfigOnOff(default = False)
	config.expert.hideerrors = ConfigOnOff(default = False)
	config.expert.autoinfo = ConfigOnOff(default = True)
