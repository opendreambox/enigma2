from __future__ import absolute_import
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigOnOff, ConfigText
from Components.Timezones import timezones
from Components.Language import language
from Components.Keyboard import keyboard
from Components.config import ConfigInteger
from Tools.Log import Log

def InitSetupDevices():
	def getZoneChoices():
		zones = [(zone.key, zone.name) for zone in timezones.regionalZones(config.timezone.region.value)]
		if timezones.defaultRegion != config.timezone.region.value:
			defaultZone = zones[0][0]
		else:
			defaultZone = timezones.defaultZone
		return zones, defaultZone

	def initTimezoneSettings():
		def timezoneNotifier(configElement):
			timezones.activateTimezone(configElement.value)

		def timezoneRegionNotifier(configElement):
			zones, defaultZone = getZoneChoices()
			config.timezone.zone.setChoices(default=defaultZone, choices=zones)

		#region
		config.timezone = ConfigSubsection();
		config.timezone.region = ConfigSelection(default = timezones.defaultRegion, choices = timezones.regions)
		config.timezone.region.save_disabled = True
		#zone
		zones, defaultZone = getZoneChoices()
		config.timezone.zone = ConfigSelection(default = defaultZone, choices = zones)

		config.timezone.region.addNotifier(timezoneRegionNotifier)
		config.timezone.zone.addNotifier(timezoneNotifier)
		config.timezone.version = ConfigInteger(default=0)
		timezones.checkUpgrade()
	initTimezoneSettings()

	def updateTimezoneDefaults():
		Log.i("%s / %s / %s" %(timezones.defaultRegion, timezones.defaultZone, timezones.defaultCountry))
		config.timezone.region.setChoices(default = timezones.defaultRegion, choices = timezones.regions)
		zones, defaultZone = getZoneChoices()
		config.timezone.zone.setChoices(default=defaultZone, choices=zones)
	timezones.onGeoIpReady.append(updateTimezoneDefaults)

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
