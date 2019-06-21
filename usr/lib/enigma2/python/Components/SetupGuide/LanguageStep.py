from Components.config import config
from Components.Language import language
from Components.SetupGuide.BaseStep import SetupListStep

from Screens.LanguageSelection import LanguageSelectionBase, _cached

from Tools.Log import Log

class LanguageStep(SetupListStep, LanguageSelectionBase):
	def __init__(self, parent):
		SetupListStep.__init__(self, parent, listStyle="iconized")
		LanguageSelectionBase.__init__(self)
		self.list = self.parent.list
		self._listContent = []

	def prepare(self):
		self._listContent = []
		self.onSelectionChanged()
		return True

	@property
	def listContent(self):
		return self._listContent

	@property
	def selectedIndex(self):
		activeLanguage = language.getActiveLanguage()
		pos = 0
		for x in self._listContent:
			if x[0] == activeLanguage:
				self.list.index = pos
				break
			pos += 1
		return pos

	def buildfunc(self, lang, text, pixmap):
		return [text, pixmap, lang]

	def onSelectionChanged(self):
		lang = self.updateList()
		self.parent.title = self.title = _cached("T2", lang)
		self.parent.text = self.text = _cached("T1", lang)

	def onOk(self):
		self.setOSDLanguage()
		return True

	def setOSDLanguage(self):
		lang = self.list.current[0]
		config.osd.language.value = lang
		config.osd.language.save() # see comment above... selectActiveLanguage

	def updateList(self):
		Log.i("Updating list of languages (current %s)" %(self.list.current,))
		first_time = not self._listContent
		lang = config.osd.language.value if first_time else self.list.current[0]
		langList = self._getLanguageList(lang)

		self._listContent = langList
		if first_time:
			self.list.list = langList
		else:
			self.list.updateList(langList)
		return lang
