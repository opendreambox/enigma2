from Screens.Screen import Screen
from Components.Label import Label

class ConfigSetHelpDialog(Screen):
	def __init__(self, session, configSet):
		self._configSet = configSet
		Screen.__init__(self, session)
		self["help1"] = Label(text=_("Use left/right to iterate through all available values.\nUse any of the 0-9 or <> keys to enable or (disable)"))
		c = [str(x) for x in self._configSet.choices]
		allChoices = " ".join(c)
		self["help2"] = Label(text=_("Available values: %s" %(allChoices)))