from Components.config import ConfigText, ConfigPassword, ConfigInteger, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Log import Log


class MultiInputBox(Screen, ConfigListScreen):
	TYPE_TEXT = 0
	TYPE_PASSWORD = 1
	TYPE_PIN = 2

	skin = """
		<screen position="center,center" size="700,120"  title="Input">
			<widget source="title" render="Label" position="5,0" zPosition="1" size="690,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="background" transparent="1" />
			<widget name="config" position="15,30" size="690,80" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	default_config = [
		{
			"key" : "User",
			"value" : "",
			"title" : _("User"),
			"required" : True,
			"type" : TYPE_TEXT,
			"alternative" : None
		},
		{
			"key" : "Password",
			"value" : "",
			"title" : _("Password"),
			"required" : True,
			"type" : TYPE_PASSWORD,
			"alternatives" : None
		},
	]

	def __init__(self, session, title="", windowTitle=_("Input"), config=default_config):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session)

		self._config = config
		self._title = title

		self["title"] = StaticText(self._title)
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"save": self._ok,
			"cancel": self._cancel,
			"ok" : self._ok,
		}, -2)

		self._configElements = []
		self._createConfigElements()

		self.onExecBegin.append(self.__onExcecBegin)
		self.onShow.append(self._createSetup)
		self.onShown.append(boundFunction(self.setTitle, windowTitle))
		self.onClose.append(self.__onClose)

	def __onExcecBegin(self):
		self.saveKeyboardMode()
		self.setKeyboardModeAscii()

	def __onClose(self):
		self.restoreKeyboardMode()

	def _createConfigElements(self):
		append = self._configElements.append
		for item in self._config:
			Log.i(item)
			if item["type"] == self.TYPE_TEXT:
				append((ConfigText(default=item["value"], fixed_size=False), item))
			elif item["type"] == self.TYPE_PASSWORD:
				append((ConfigPassword(default=item["value"], fixed_size=False), item))
			elif item["type"] == self.TYPE_PIN:
				val = item["value"] or 0
				append((ConfigInteger(default=int(val)), item))

	def _createSetup(self):
		lst = []
		for config, item in self._configElements:
			lst.append(getConfigListEntry(item["title"], config))
		self["config"].setList(lst)

	def _ok(self):
		if self._checkInput():
			ret = {}
			for config, item in self._configElements:
				ret[item["key"]] = str(config.value)
			self.close(ret)
		else:
			self.close(None)

	def _checkInput(self):
		return True

	def _checkSingleInput(self, value, config):
		return value != None and value != ""

	def _cancel(self):
		self.close(None)

