from enigma import eSize

from Screen import Screen

from Components.ActionMap import ActionMap
from Components.Language import language
from Components.config import config
from Components.Sources.List import List
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.language_cache import LANG_TEXT
from Components.Timezones import timezones
from Tools.Log import Log

def _cached(x, lang=None):
	return LANG_TEXT.get(lang or config.osd.language.value, {}).get(x, "")

from Screens.Rc import Rc

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

from Tools.LoadPixmap import LoadPixmap

def LanguageEntryComponent(fileName, name, index, png_cache):
	png = png_cache.get(fileName, None)
	if png is None:
		png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/" + fileName + ".svg"), size=eSize(210,140))
		png_cache[fileName] = png
	if png is None:
		png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/" + fileName + ".png"))
		png_cache[fileName] = png
	if png is None:
		png = png_cache.get("missing", None)
		if png is None:
			png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/missing.png"))
			png_cache["missing"] = png
	return (index, name, png)

class LanguageSelectionBase(object):
	def __init__(self):
		self._png_cache = {}

	def _getLanguageList(self, lang):
		languageList = language.getLanguageList()
		if not languageList: # no language available => display only english
			langList = [ LanguageEntryComponent("en", _cached("en_EN", lang), "en_EN", self._png_cache) ]
		else:
			langList = []
			defaultCountry = timezones.defaultCountry
			for x in languageList:
				entry = LanguageEntryComponent(fileName = x[1][2].lower(), name = _cached("%s_%s" % x[1][1:3], lang), index = x[0], png_cache = self._png_cache)
				defaults = []
				if x[1][2] == defaultCountry:
					defaults.append(entry)
					continue
				if x[1][2] == "en":
					defaults.insert(0, entry)
					continue
				langList.append(entry)
			defaults.extend(langList)
			langList = defaults
		return langList

class LanguageSelection(Screen, LanguageSelectionBase):
	def __init__(self, session):
		Screen.__init__(self, session)
		LanguageSelectionBase.__init__(self)

		self.multicontentlist = []
		self["languages"] = List(self.multicontentlist)
		self["languages"].onSelectionChanged.append(self.changed)

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
		Log.i("update list")
		first_time = not self.multicontentlist
		lang = config.osd.language.value if first_time else self[listname].getCurrent()[0]

		langList = self._getLanguageList(lang)
		self.multicontentlist = langList

		if first_time:
			self[listname].list = langList
		else:
			self[listname].updateList(langList)
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
