# -*- coding: UTF-8 -*-

from Screens.Screen import Screen

from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap

from Tools.Log import Log

class ConfigScreen(ConfigListScreen, Screen):
	IS_DIALOG = True
	skin = """
		<screen name="ConfigScreen" position="center,120" size="820,520" title="MediaCenter: Main Settings">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40"  />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40"  />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])
		self.createSetup()

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

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
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def createSetup(self):
		Log.i("called")
		configlist = []
		self["config"].setList(configlist)

	def layoutFinished(self):
		Log.i("called")
		self.setTitle(_("MediaCenter: Main Settings"))

	def save(self):
		Log.i("called")
		for x in self["config"].list:
			x[1].save()
		self.close(True, self.session)

	def cancel(self):
		Log.i("called")
		for x in self["config"].list:
			x[1].cancel()
		self.close(False, self.session)


