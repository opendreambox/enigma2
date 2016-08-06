from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

class HbbTVSetup(ConfigListScreen, Screen):
	skin = """
		<screen name="HbbtvSetup" position="center,120" size="820,520" title="HbbTV Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<widget render="Label" source="key_red" position="10,5" size="200,40" zPosition="5" valign="center" halign="center" backgroundColor="#9f1313" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="210,5" size="200,40" zPosition="5" valign="center" halign="center" backgroundColor="#1f771f" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self.cancel,
			"green" : self.close,
			"cancel": self.cancel,
			"ok" : self.close,
		}, -2)

		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		config.plugins.hbbtv.enabled.addNotifier(self._enabledChanged, initial_call = False)
		self.onClose.append(self._onClose)
		self._save = True

	def _onClose(self):
		config.plugins.hbbtv.enabled.removeNotifier(self._enabledChanged)
		if self._save:
			for x in self["config"].list:
				x[1].save()

	def cancel(self):
		self._save = False
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def createSetup(self):
		list = [getConfigListEntry(_("HbbTV functionality"), config.plugins.hbbtv.enabled)]
		if config.plugins.hbbtv.enabled.value:
			list.extend( [
				getConfigListEntry(_("HbbTV Text"), config.plugins.hbbtv.text),
				getConfigListEntry(_("Show HbbTV Browser"), config.plugins.hbbtv.testsuite),
			])

		self["config"].list = list
		self["config"].l.setList(list)

	def _enabledChanged(self, enabled):
		self.createSetup()

	def layoutFinished(self):
		self.setTitle(_("HbbTV Setup"))
