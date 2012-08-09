from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

class HbbTVSetup(ConfigListScreen, Screen):
	skin = """
		<screen name="HbbtvSetup" position="center,center" size="560,400" title="HbbTV Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
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
				getConfigListEntry(_("Show HbbTV Testsuite"), config.plugins.hbbtv.testsuite),
			])

		self["config"].list = list
		self["config"].l.setList(list)

	def _enabledChanged(self, enabled):
		self.createSetup()

	def layoutFinished(self):
		self.setTitle(_("HbbTV Setup"))
