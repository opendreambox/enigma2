from Screens.Screen import Screen
from Components.Label import Label
from Components.MenuList import MenuList
from enigma import eListbox

class ConfigSetHelpDialog(Screen):
	def __init__(self, session, configSet):
		self._configSet = configSet
		Screen.__init__(self, session)
		self["help1"] = Label(text=_("Use left/right to iterate through all available values.\nUse any of the OK, 0-9 or <> keys to enable or (disable)"))
		c = [str(x) for x in self._configSet.choices]
		allChoices = " ".join(c)
		self["help2"] = Label(text=_("Available values: %s" %(allChoices)))

		items = [str(x) for x in self._configSet.description]
		self["list"] = MenuList(items,enableWrapAround=False, mode=eListbox.layoutHorizontal, itemSize=50)

		self._configSet.onSelectedIndexChanged.append(self._onSelectedIndexChanged)
		self.onLayoutFinish.append(self._onLayoutFinish)
		self.onClose.append(self._onClose)

	def _onLayoutFinish(self):
		self._onSelectedIndexChanged(self._configSet.pos)

	def _onClose(self):
		self._configSet.onSelectedIndexChanged.remove(self._onSelectedIndexChanged)

	def _onSelectedIndexChanged(self, index):
		self["list"].selectionEnabled(index >= 0)
		self["list"].moveToIndex(index)
