# -*- coding: UTF-8 -*-

from Screens.Screen import Screen

from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap

from Tools.Log import Log

class ConfigScreen(ConfigListScreen, Screen):
	IS_DIALOG = True
	skin = """
		<screen name="ConfigScreen" position="center,center" size="560,400" title="MediaCenter: Main Settings">
			<widget name="config" position="5,5" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
			<ePixmap pixmap="skin_default/buttons/button_red.png" position="5,370" size="15,16" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/button_green.png" position="195,370" size="15,16" alphatest="on" />
			<widget source="key_red" render="Label" position="25,370" zPosition="1" size="140,20" font="Regular;18" halign="left" valign="top" transparent="1" foregroundColor="white" backgroundColor="background"/>
			<widget source="key_green" render="Label" position="215,370" zPosition="1" size="140,20" font="Regular;18" halign="left" valign="top" transparent="1" foregroundColor="white" backgroundColor="background"/>
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


