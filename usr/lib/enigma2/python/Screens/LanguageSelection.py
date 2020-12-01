from Screen import Screen

from Components.ActionMap import ActionMap
from Components.Language import language
from Components.config import config
from Components.Sources.List import List
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.language_cache import LANG_TEXT

def _cached(x, lang=None):
	return LANG_TEXT.get(lang or config.osd.language.value, {}).get(x, LANG_TEXT.get("en_GB").get(x, x))

from Screens.Rc import Rc

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

from Tools.LoadPixmap import LoadPixmap

def LanguageEntryComponent(file, name, index, png_cache):
	png = png_cache.get(file, None)
	if png is None:
		png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/" + file + ".png"))
		png_cache[file] = png
	if png is None:
		png = png_cache.get("missing", None)
		if png is None:
			png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/missing.png"))
			png_cache["missing"] = png
	return (index, name, png)

class LanguageSelection(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.multicontentlist = []
		self["languages"] = List(self.multicontentlist)
		self["languages"].onSelectionChanged.append(self.changed)

		self.png_cache = { }
		self.updateList()
		self.onLayoutFinish.append(self.selectActiveLanguage)

		self["actions"] = ActionMap(["OkCancelActions"], 
		{
			"ok": self.save,
			"cancel": self.cancel,
		}, -1)

	# called from external Components/SetupDevices.py!!
	def selectActiveLanguage(self, listname = "languages"):
		activeLanguage = language.getActiveLanguage()
		pos = 0
		for x in self.multicontentlist:
			if x[0] == activeLanguage:
				self[listname].index = pos
				break
			pos += 1

	def setOSDLanguage(self, listname = "languages"):
		lang = self[listname].getCurrent()[0]
		config.osd.language.value = lang
		config.osd.language.save() # see comment above... selectActiveLanguage

	def save(self, listname = "languages"):
		self.setOSDLanguage(listname)
		self.close()

	def cancel(self):
		self.close()

	def run(self):
		pass

	def updateList(self, listname = "languages"):
		print "update list"
		first_time = not self.multicontentlist

		if first_time:
			lang = config.osd.language.value
		else:
			lang = self[listname].getCurrent()[0]

		languageList = language.getLanguageList()
		if not languageList: # no language available => display only english
			list = [ LanguageEntryComponent("en", _cached("en_GB", lang), "en_GB", self.png_cache) ]
		else:
			list = [ LanguageEntryComponent(file = x[1][2].lower(), name = _cached(x[1][3], lang), index = x[0], png_cache = self.png_cache) for x in languageList]
		self.multicontentlist = list

		if first_time:
			self[listname].list = list
		else:
			self[listname].updateList(list)
		print "done"
		return lang

	def changed(self):
		lang = self.updateList()

		self.setTitle(_cached("T2", lang))

class LanguageWizard(LanguageSelection, Rc):
	def __init__(self, session):
		LanguageSelection.__init__(self, session)
		Rc.__init__(self)
		self.onLayoutFinish.append(self.selectKeys)
		self["wizard"] = Pixmap()
		self["text"] = Label()
		self.setText(config.osd.language.value)

	def selectKeys(self):
		self.clearSelectedKeys()
		self.selectKey("UP")
		self.selectKey("DOWN")

	def changed(self):
		self.updateList()
		self.setText()

	def setText(self, lang=None):
		self["text"].setText(_cached("T1", lang or self["languages"].getCurrent()[0]))

	def save(self):
		LanguageSelection.save(self)
		config.misc.languageselected.value = 0
		config.misc.languageselected.save()
