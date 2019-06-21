from Components.SetupGuide.LanguageStep import LanguageStep
from Components.SetupGuide.SimpleSteps import AutomaticStandbyStep, UsageLevelStep, FinishGuideStep
from Components.SetupGuide.DefaultServicelistStep import DefaultServicelistStep
from Components.SetupGuide.ParentalControlStep import ParentalControlStep
from Components.SetupGuide.VideoSteps import ResolutionStep, RateStep
from Components.SetupGuide.AutomaticUpdatesStep import AutomaticUpdatesStep
from Components.SetupGuide.TimezoneStep import TimezoneStep

class InitialSetupSteps(object):
	PRIO_VIDEO = 0x10
	PRIO_LANGUAGE = 0x20
	PRIO_SETTINGS_RESTORE = 0x30
	PRIO_WELCOME = 0x40
	PRIO_NETWORK = 0x50
	PRIO_TIMEZONE = 0x60
	PRIO_INPUT = 0x70
	PRIO_TUNER = 0x80
	PRIO_DEFAULT_SERVICES = 0x90
	PRIO_PARENTAL_CONTROL = 0x100
	PRIO_AUTO_STANDBY = 0x110
	PRIO_USAGE_LEVEL = 0x120
	PRIO_AUTOMATIC_UPDATES = 0x130
	PRIO_FINISH = 0x140

	def __init__(self):
		self.steps = [{
			InitialSetupSteps.PRIO_VIDEO : [ResolutionStep, RateStep],
			InitialSetupSteps.PRIO_LANGUAGE : LanguageStep,
			InitialSetupSteps.PRIO_TIMEZONE : TimezoneStep,
			InitialSetupSteps.PRIO_DEFAULT_SERVICES : DefaultServicelistStep,
			InitialSetupSteps.PRIO_PARENTAL_CONTROL : ParentalControlStep,
			InitialSetupSteps.PRIO_AUTO_STANDBY : AutomaticStandbyStep,
			InitialSetupSteps.PRIO_USAGE_LEVEL : UsageLevelStep,
			InitialSetupSteps.PRIO_AUTOMATIC_UPDATES : AutomaticUpdatesStep,
			InitialSetupSteps.PRIO_FINISH : FinishGuideStep,
		}]
		#Plugin dependent steps
		self._initOptionalSteps()
		self.onPrepare = []

	def _initOptionalSteps(self):
		# Settings Restore - Requires SoftwareManager
		try:
			from Components.SetupGuide.SettingsRestoreStep import SettingsRestoreStep
			self.steps[0][InitialSetupSteps.PRIO_SETTINGS_RESTORE] = SettingsRestoreStep
		except:
			pass
		# InputDevice Setup - Requires InputDeviceManagment
		try:
			from Components.SetupGuide.InputDeviceSteps import InputDeviceCheckFirmwareStep, InputDeviceConnectStep
			self.steps[0][InitialSetupSteps.PRIO_INPUT] = [InputDeviceCheckFirmwareStep, InputDeviceConnectStep]
		except:
			pass
		# Network - Requires NetworkManager
		try:
			from Components.SetupGuide.NetworkSteps import NetworkTechnologyStep, NetworkServicesStep
			self.steps[0][InitialSetupSteps.PRIO_NETWORK] = [NetworkTechnologyStep, NetworkServicesStep]
		except:
			pass
		# Automatic Updates - Requires SoftwareManager - but does the check in prepare() because of required inlined imports

	def add(self, steps):
		self.steps.append(steps)

	def prepare(self):
		for fnc in self.onPrepare:
			fnc()

initialSetupSteps = InitialSetupSteps()