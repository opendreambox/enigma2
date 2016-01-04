from Screen import Screen
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry
from Components.Sources.StaticText import StaticText
class ChannelSelectionDisplaySettings(Screen, ConfigListScreen):
	skin = """
		<screen name="ChannelSelectionDisplaySettings" position="center,center" size="600,400" title="ChannelSelection Display Settings" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="20,50" size="560,330" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("ChannelSelection Display Settings"))


		self.createConfig()

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"left": self.keyLeft,
			"right": self.keyRight,
		}, -2)
		self["key_blue"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session)
		self.createSetup("config")

	def keyCancel(self):
		config.usage.configselection_bigpicons.cancel()
		config.usage.configselection_secondlineinfo.cancel()
		ConfigListScreen.cancelConfirm(self, True)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		config.usage.configselection_bigpicons.save()
		config.usage.configselection_secondlineinfo.save()
		self.close()

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur and (cur == self.additionEventInfoEntry or cur == self.columnStyleEntry or cur == self.showEventProgressEntry or cur == self.showPiconsEntry or cur == self.showServiceNameEntry):
			self.createSetup("config")
		if cur and (cur == self.piconPathEntry or cur == self.showPiconsEntry):
			if self.showpicons.value:
				if self.piconpath.getIndex() > 0:
					config.usage.configselection_bigpicons.value = True
				else:
					config.usage.configselection_bigpicons.value = False
			self.createSetup("config")

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def createConfig(self):
		self.additionEventInfo = config.usage.configselection_showadditionaltimedisplay
		self.columnStyle = config.usage.configselection_columnstyle
		self.progressbarposition = config.usage.configselection_progressbarposition
		self.showeventprogress = config.usage.show_event_progress_in_servicelist
		self.showpicons = config.usage.configselection_showpicons
		self.showservicename = config.usage.configselection_showservicename
		self.showbigpicons = config.usage.configselection_bigpicons
		self.piconpath = config.usage.configselection_piconspath

	def createSetup(self, widget):
		self.list = []
		self.columnStyleEntry = getConfigListEntry(_("Column style"), self.columnStyle)
		self.list.append(self.columnStyleEntry)
#		self.list.append(getConfigListEntry(_("Show settings in channel context menu"), config.usage.configselection_showsettingsincontextmenu))
		self.list.append(getConfigListEntry(_("Show recordings"), config.usage.configselection_showrecordings))
		self.list.append(getConfigListEntry(_("Show service numbers"), config.usage.configselection_showlistnumbers))
		self.showPiconsEntry = getConfigListEntry(_("Show Picons"), self.showpicons)
		self.list.append(self.showPiconsEntry)
		if self.showpicons.value:
			self.piconPathEntry = getConfigListEntry(_("Picons path"), self.piconpath)
			self.list.append(self.piconPathEntry)
		else:
			config.usage.configselection_bigpicons.value = False
			self.piconPathEntry = None
		if self.columnStyle.value:
			self.list.append(getConfigListEntry(_("2nd line info"), config.usage.configselection_secondlineinfo))
			self.showServiceNameEntry = getConfigListEntry(_("Show service name"), self.showservicename)
			self.list.append(self.showServiceNameEntry)
		else:
			self.showServiceNameEntry = None
			config.usage.configselection_secondlineinfo.value = "0"
		self.showEventProgressEntry = getConfigListEntry(_("Show event-progress"), self.showeventprogress)
		self.list.append(self.showEventProgressEntry)
		if self.columnStyle.value and self.showservicename.value:
			self.progressbarposition.setChoices([("0",_("After service number")),("1",_("After service name")), ("2",_("After event description"))])
		else:
			self.progressbarposition.setChoices([("0",_("After service number")), ("2",_("After event description"))])
		if self.showeventprogress.value:
			self.list.append(getConfigListEntry(_("Event-progessbar position"), self.progressbarposition))
		if self.columnStyle.value:
			self.list.append(getConfigListEntry(_("Service name column width"), config.usage.configselection_servicenamecolwidth))
		self.additionEventInfoEntry = getConfigListEntry(_("Additional event-time info"), self.additionEventInfo)
		self.list.append(self.additionEventInfoEntry)
		if self.additionEventInfo.value != "0":
			self.list.append(getConfigListEntry(_("Additional event-time position"), config.usage.configselection_additionaltimedisplayposition))
		self[widget].list = self.list
		self[widget].l.setList(self.list)


