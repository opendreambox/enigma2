from Screen import Screen
from Components.ActionMap import NumberActionMap
from Components.config import config, ConfigNothing
from Components.SystemInfo import SystemInfo
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Tools.Directories import resolveFilename, SCOPE_DATADIR

import xml.etree.cElementTree

try:
	# first we search in the current path
	setupfile = file('data/setup.xml', 'r')
except:
	# if not found in the current path, we use the global datadir-path
	setupfile = file(resolveFilename(SCOPE_DATADIR, "setup.xml"), 'r')
setupdom = xml.etree.cElementTree.parse(setupfile)
setupfile.close()

class SetupError(Exception):
	def __init__(self, message):
		self.msg = message

	def __str__(self):
		return self.msg

class SetupSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		self["SetupTitle"] = StaticText(_(parent.setup_title) if parent.setup_title else parent["Title"].text)
		self["SetupEntry"] = StaticText("")
		self["SetupValue"] = StaticText("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onConfigEntryChanged.append(self.selectionChanged)
		self.parent["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def removeWatcher(self):
		self.parent.onConfigEntryChanged.remove(self.selectionChanged)
		self.parent["config"].onSelectionChanged.remove(self.selectionChanged)

	def selectionChanged(self):
		self["SetupEntry"].text = self.parent.getCurrentEntry()
		self["SetupValue"].text = self.parent.getCurrentValue()

class Setup(ConfigListScreen, Screen):

	ALLOW_SUSPEND = True

	def removeNotifier(self):
		config.usage.setup_level.removeNotifier(self.levelChanged)

	def _detachNotifiers(self):
		for elem in self._notifiers:
			elem.removeNotifier(self.levelChanged)
		self._notifiers = []

	def levelChanged(self, configElement):
		listItems = []
		self.refill(listItems)
		self["config"].setList(listItems)

	def refill(self, listItems):
		xmldata = setupdom.getroot()
		for x in xmldata.findall("setup"):
			if x.get("key") != self.setup:
				continue
			self.addItems(listItems, x);
			self.setup_title = x.get("title", "").encode("UTF-8")

	def __init__(self, session, setup):
		Screen.__init__(self, session)
		# for the skin: first try a setup_<setupID>, then Setup
		self.skinName = ["setup_" + setup, "Setup" ]
		ConfigListScreen.__init__(self, [], session = session)
		self._notifiers = []
		self.setup = setup
		self.levelChanged(None)

		#check for list.entries > 0 else self.close
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["actions"] = NumberActionMap(["SetupActions"], 
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}, -2)

		self._changedEntry()
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self._detachNotifiers)

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def addItems(self, listItems, parentNode):
		self._detachNotifiers()
		for x in parentNode:
			if x.tag == 'item':
				item_level = int(x.get("level", 0))

				if not self.levelChanged in config.usage.setup_level.notifiers:
					config.usage.setup_level.addNotifier(self.levelChanged, initial_call = False)
					self.onClose.append(self.removeNotifier)

				if item_level > config.usage.setup_level.index:
					continue

				requires = x.get("requires")
				if requires and not SystemInfo.get(requires, False):
					continue;

				item_text = _(x.get("text", "??").encode("UTF-8"))
				b = eval(x.text or "str('')");
				#add to configlist
				item = b
				# the first b is the item itself, ignored by the configList.
				# the second one is converted to string.
				if isinstance(item, ConfigNothing):
					continue
				if item:
					entry = (item_text, item)
					notify = x.get("notify")
					if notify and notify == "true":
						item.addNotifier(self.levelChanged, initial_call = False)
						self._notifiers.append(item)
				else:
					entry = (item_text,)
				listItems.append(entry)

def getSetupTitle(setupId):
	xmldata = setupdom.getroot()
	for x in xmldata.findall("setup"):
		if x.get("key") == setupId:
			return x.get("title", "").encode("UTF-8")
	raise SetupError("unknown setup id '%s'!" % repr(setupId))
