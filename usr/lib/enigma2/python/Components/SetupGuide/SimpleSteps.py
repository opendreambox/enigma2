from Components.SetupGuide.BaseStep import SetupListStepConfigSelection, SetupTextStep, SetupListStep
from Components.config import config
from Screens.ScanSetup import ScanSimple, ScanSetup
from Components.NimManager import nimmanager

class WelcomeStep(SetupTextStep):
	def __init__(self, parent):
		SetupTextStep.__init__(self, parent)

	def prepare(self):
		self.title = _("Welcome...")
		self.text = _("to your new Dreambox!\nLet's start setting it up...\n\n[Press OK]")
		return True

class AutomaticStandbyStep(SetupListStepConfigSelection):
	def prepare(self):
		self._configSelection = config.usage.inactivity_shutdown
		self.title = _("Auto Standby")
		self.text = _("Automatic standby mode\n\nIf you don't press any button on the remote control, your Dreambox can enter the standby mode automatically. You can choose the period after which the standby mode will be activated or disable this functionality now.")
		return True

	def onOk(self):
		config.usage.inactivity_shutdown_initialized.value = True
		config.usage.inactivity_shutdown_initialized.save()
		return SetupListStepConfigSelection.onOk(self)

class UsageLevelStep(SetupListStepConfigSelection):
	def prepare(self):
		self._configSelection = config.usage.setup_level
		self.title = _("User Level")
		self.text = _("Your Dreambox offers three levels of configuration options:\n\nSimple - We suggest this level if this is your first contact with a Dreambox.\nIntermediate - This level enables you to change some more options, mainly the graphical user interface and the behaviour of your Dreambox.\nExpert - This gives you full control over all available settings of your Dreambox.\n\nWarning: Higher levels may lead to increased usage complexity.")
		return True

class FinishGuideStep(SetupListStep):
	OPTION_NOTHING = "noting"
	OPTION_SCAN_AUTOMATIC = "scan_auto"
	OPTION_SCAN_MANUAL = "scan_manual"

	def __init__(self, parent):
		SetupListStep.__init__(self, parent)
		self.session = self.parent.session
		self._options = []

	def prepare(self):
		self.title = _("Inital Setup Finished!")
		self.text = _("Your Dreambox is now fully set up!")
		if nimmanager.somethingConnected():
			self.text = _("Your Dreambox is now fully set up!\nWhat do you want to do?")
		self._options = [
			(self.OPTION_NOTHING, _("Close")),
		]
		if nimmanager.somethingConnected():
			self._options = [
				(self.OPTION_NOTHING, _("Finish without further actions")),
				(self.OPTION_SCAN_AUTOMATIC,_("Automatic service scan")),
				(self.OPTION_SCAN_MANUAL,_("Manual service scan")),
			]
		return True

	@property
	def listContent(self):
		return self._options

	def buildfunc(self, option, entry):
		return [entry,option]

	def onOk(self):
		config.misc.firstrun.value = False
		config.save()
		lst = self.parent.list
		current = lst.current and lst.current[0]
		if current:
			if current == self.OPTION_SCAN_AUTOMATIC:
				self.session.open(ScanSimple, noSetupAfterScan = True)
				return False # stay in the SetupGuide step after scan is finished/aborted
			elif current == self.OPTION_SCAN_MANUAL:
				self.session.open(ScanSetup)
				return False # stay in the SetupGuide step after scan is finished/aborted
		return True
