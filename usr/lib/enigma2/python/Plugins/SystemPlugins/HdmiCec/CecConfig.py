from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

class CecConfig(ConfigListScreen, Screen):
	skin = """
		<screen name="CecConfig" position="center,center" size="560,400" title="HDMI CEC: Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)

		ConfigListScreen.__init__(self, [])
		self._createSetup()

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		# SKIN Compat HACK!
		self["key_yellow"] = StaticText("")
		# EO SKIN Compat HACK!
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self._createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self._createSetup()

	def _createSetup(self):
		list = [
			getConfigListEntry(_("Send HDMI CEC Power Events"), config.plugins.cec.sendpower),
			getConfigListEntry(_("Handle received HDMI CEC Power Events"), config.plugins.cec.receivepower),
		]
		self["config"].list = list
		self["config"].l.setList(list)

	def layoutFinished(self):
		self.setTitle(_("HDMI CEC: Setup"))

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close(True, self.session)

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False, self.session)

