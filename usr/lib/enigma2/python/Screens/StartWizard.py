from Wizard import wizardManager
from Screens.WizardLanguage import WizardLanguage
from Screens.ScanSetup import DefaultSatLists
from Screens.DefaultWizard import DefaultWizard
from Screens.Rc import Rc
from Screens.LanguageSelection import LanguageSelection, _cached

from Components.Pixmap import Pixmap
from Components.config import config, ConfigBoolean, configfile, ConfigSubsection

from Components.NimManager import nimmanager

config.misc.firstrun = ConfigBoolean(default = True)
config.misc.startwizard = ConfigSubsection()
config.misc.startwizard.shownimconfig = ConfigBoolean(default = True)
config.misc.startwizard.doservicescan = ConfigBoolean(default = True)
config.misc.languageselected = ConfigBoolean(default = True)

class StartWizard(DefaultSatLists, LanguageSelection, Rc):
	def __init__(self, session, silent = True, showSteps = False, neededTag = None):
		self.xmlfile = ["startwizard.xml", "defaultsatlists.xml"]
		DefaultWizard.__init__(self, session, silent, showSteps, neededTag = "services", default = True)
		WizardLanguage.__init__(self, session, showSteps = False, showMulticontentList = True)
		Rc.__init__(self)
		self["wizard"] = Pixmap()

		# needed for LanguageSelection
		self.png_cache = { }

	def markDone(self):
		config.misc.firstrun.value = 0
		config.misc.firstrun.save()
		configfile.save()

	def setLanguageList(self):
		LanguageSelection.updateList(self, listname = "multicontentlist")
		self["multicontentlist"].updateList(self.multicontentlist)
		LanguageSelection.selectActiveLanguage(self, listname = "multicontentlist")

	def onLanguageSelect(self):
		LanguageSelection.updateList(self, listname = "multicontentlist")
		self.setTitle(_cached("T2", self["multicontentlist"].getCurrent()[0]))
		self["text"].setText(_cached("T1", self["multicontentlist"].getCurrent()[0]))

	def languageSave(self, lang):
		LanguageSelection.setOSDLanguage(self, "multicontentlist")
		WizardLanguage.updateLanguageDescription(self)

	def setTunerText(self, step):
		index = {"nima": 0, "nimb": 1, "nimc": 2, "nimd": 3}.get(step, None)
		text = ""
		if index == 0:
			text += _("Use the left and right buttons to change an option.") + "\n\n"
		text += _("Please set up tuner %s") % nimmanager.getNimSlotInputName(index)
		
		return text

wizardManager.registerWizard(StartWizard, config.misc.firstrun.value, priority = 20)
