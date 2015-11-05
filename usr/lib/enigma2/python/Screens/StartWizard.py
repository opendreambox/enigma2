from Wizard import wizardManager
from Screens.WizardLanguage import WizardLanguage
from Screens.ScanSetup import DefaultSatLists
from Screens.DefaultWizard import DefaultWizard
from Screens.Rc import Rc
from Screens.LanguageSelection import LanguageSelection, _cached

from Components.config import config, ConfigBoolean, configfile, ConfigSubsection
from Components.Label import Label
from Components.NimManager import nimmanager
from Components.Pixmap import Pixmap
from Components.ResourceManager import resourcemanager
from Components.Sources.Boolean import Boolean

config.misc.firstrun = ConfigBoolean(default = True)
config.misc.startwizard = ConfigSubsection()
config.misc.startwizard.shownimconfig = ConfigBoolean(default = True)
config.misc.startwizard.doservicescan = ConfigBoolean(default = True)
config.misc.languageselected = ConfigBoolean(default = True)

emptyWizardList = []

# empty classes if the plugins are not present for not being forced to use dynamic inheritance
# we need a generator function here since multiple inheritance of the same class is not allowed in python
def makeEmptyWizard():
	global emptyWizardList
	class EmptyWizard(object):
		pass
	emptyWizardList.append(EmptyWizard)
	return EmptyWizard

NetworkWizardNew = resourcemanager.getResource("NetworkWizard.NetworkWizardNew", makeEmptyWizard())
VideoWizard = resourcemanager.getResource("videomode.videowizard", makeEmptyWizard())

class StartWizard(NetworkWizardNew, VideoWizard, DefaultSatLists, LanguageSelection, Rc):
	def __init__(self, session, silent = True, showSteps = False, neededTag = None):
		self.xmlfile = ["startwizard.xml", "defaultsatlists.xml"]
		DefaultWizard.__init__(self, session, silent, showSteps, neededTag = "services", default = True)
		WizardLanguage.__init__(self, session, showSteps = False, showMulticontentList = True)
		Rc.__init__(self)

		self["wizard"] = Pixmap()

		# needed for LanguageSelection
		self.png_cache = { }

		self["button_green"] = Boolean(False)
		self["button_green_text"] = Label()
		self["button_green_text"].hide()
		self["button_yellow"] = Boolean(False)
		self["button_yellow_text"] = Label()
		self["button_yellow_text"].hide()
		self["button_blue"] = Boolean(False)
		self["button_blue_text"] = Label()
		self["button_blue_text"].hide()

		self["state_label"] = Label()
		self["state"] = Label()
		self.showState(False)

		NetworkWizardNew.__init__(self)
		self.networkWizardAvailable = NetworkWizardNew not in emptyWizardList

		self["portpic"] = Pixmap()
		VideoWizard.__init__(self)
		self.videoWizardAvailable = VideoWizard not in emptyWizardList

	def _buildListEntry(self, *args, **kwargs):
		return (args[1], args[0])

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
		self.updateTexts()

	def setTunerText(self, step):
		index = {"nima": 0, "nimb": 1, "nimc": 2, "nimd": 3}.get(step, None)
		text = ""
		if index == 0:
			text += _("Use the left and right buttons to change an option.") + "\n\n"
		text += _("Please set up tuner %s") % nimmanager.getNimSlotInputName(index)
		
		return text

	def showHideButtons(self, green = False, yellow = False, blue = False):
		if green:
			self["button_green"].boolean = True
			self["button_green_text"].show()
		else:
			self["button_green"].boolean = False
			self["button_green_text"].hide()

		if yellow:
			self["button_yellow"].boolean = True
			self["button_yellow_text"].show()
		else:
			self["button_yellow"].boolean = False
			self["button_yellow_text"].hide()

		if blue:
			self["button_blue"].boolean = True
			self["button_blue_text"].show()
		else:
			self["button_blue"].boolean = False
			self["button_blue_text"].hide()

	def showState(self, show = False):
		if show:
			self["state"].show()
			self["state_label"].show()
		else:
			self["state"].hide()
			self["state_label"].hide()

wizardManager.registerWizard(StartWizard, config.misc.firstrun.value, priority = 20)
