from Components.ActionMap import ActionMap
from Components.Sensors import sensors
from Components.Sources.Sensor import SensorSource
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry
from enigma import getDesktop, eSize
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.FanControl import fancontrol

sz_w = getDesktop(0).size().width()

class TempFanControl(Screen, ConfigListScreen):
	if sz_w == 1920:
		skin = """
		<screen name="TempFanControl" position="center,170" size="1200,685" title="Fan Control" >
		<widget source="red" render="Label" backgroundColor="#9f1313" font="Regular;24" halign="center" position="20,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="275,60" valign="center" />
		<widget source="green" render="Label" backgroundColor="#1f771f" font="Regular;24" halign="center" position="315,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="275,60" valign="center" />
		<widget source="yellow" render="Label" backgroundColor="#a08500" font="Regular;24" halign="center" position="610,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="275,60" valign="center" />
		<widget source="blue" render="Label" backgroundColor="#18188b" font="Regular;24" halign="center" position="905,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="275,60" valign="center" />
		<eLabel position="20,80" size="1160,1" backgroundColor="grey" />
		<widget name="config" position="20,90" size="1160,200" enableWrapAround="1" scrollbarMode="showOnDemand" />
		<eLabel position="20,280" size="1160,1" backgroundColor="grey" />
		<widget source="SensorText" render="Label" font="Regular;28" halign="left" position="20,295" size="280,30"/>
		<widget source="TemperatureText" render="Label" font="Regular;28" halign="left" position="320,295" size="280,30"/>
		<widget source="FanText" render="Label" font="Regular;28" halign="left" position="620,295" size="280,30"/>
		<widget source="SpeedText" render="Label" font="Regular;28" halign="left" position="920,295" size="260,30"/>
		<eLabel position="20,340" size="1160,1" backgroundColor="grey" />
		<widget source="SensorTempText0" render="Label" position="20,360" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp0" render="Label" position="320,360" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText0" render="Label" position="620,360" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan0" render="Label" position="920,360" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText1" render="Label" position="20,400" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp1" render="Label" position="320,400" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText1" render="Label" position="620,400" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan1" render="Label" position="920,400" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText2" render="Label" position="20,440" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp2" render="Label" position="320,440" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText2" render="Label" position="620,440" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan2" render="Label" position="920,440" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText3" render="Label" position="20,480" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp3" render="Label" position="320,480" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText3" render="Label" position="620,480" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan3" render="Label" position="920,480" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText4" render="Label" position="20,520" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp4" render="Label" position="320,520" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText4" render="Label" position="620,520" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan4" render="Label" position="920,520" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText5" render="Label" position="20,560" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp5" render="Label" position="320,560" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText5" render="Label" position="620,560" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan5" render="Label" position="920,560" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText6" render="Label" position="20,600" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp6" render="Label" position="320,600" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText6" render="Label" position="620,600" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan6" render="Label" position="920,600" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText7" render="Label" position="20,640" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorTemp7" render="Label" position="320,640" size="280,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText7" render="Label" position="620,640" size="280,30" font="Regular;28" halign="left"/>
		<widget source="SensorFan7" render="Label" position="920,640" size="260,30" font="Regular;28" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		</screen>"""
	else:
		skin = """
		<screen name="TempFanControl" position="center,120" size="720,510" title="Fan Control" >
		<widget source="red" render="Label" backgroundColor="#9f1313" font="Regular;16" halign="center" position="15,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="165,40" valign="center" />
		<widget source="green" render="Label" backgroundColor="#1f771f" font="Regular;16" halign="center" position="190,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="165,40" valign="center" />
		<widget source="yellow" render="Label" backgroundColor="#a08500" font="Regular;16" halign="center" position="365,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="165,40" valign="center" />
		<widget source="blue" render="Label" backgroundColor="#18188b" font="Regular;16" halign="center" position="545,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="165,40" valign="center" />
		<eLabel position="10,60" size="700,1" backgroundColor="grey" />
		<widget name="config" position="10,70" size="700,120" enableWrapAround="1" scrollbarMode="showOnDemand" />
		<eLabel position="10,200" size="700,1" backgroundColor="grey" />
		<widget source="SensorText" render="Label" font="Regular;20" halign="left" position="20,215" size="150,24"/>
		<widget source="TemperatureText" render="Label" font="Regular;20" halign="left" position="180,215" size="170,24"/>
		<widget source="FanText" render="Label" font="Regular;20" halign="left" position="390,215" size="170,24"/>
		<widget source="SpeedText" render="Label" font="Regular;20" halign="left" position="590,215" size="150,24"/>
		<eLabel position="10,250" size="700,1" backgroundColor="grey" />
		<widget source="SensorTempText0" render="Label" position="20,270" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp0" render="Label" position="180,270" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText0" render="Label" position="390,270" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan0" render="Label" position="590,270" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText1" render="Label" position="20,300" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp1" render="Label" position="180,300" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText1" render="Label" position="390,300" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan1" render="Label" position="590,300" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText2" render="Label" position="20,330" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp2" render="Label" position="180,330" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText2" render="Label" position="390,330" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan2" render="Label" position="590,330" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText3" render="Label" position="20,360" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp3" render="Label" position="180,360" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText3" render="Label" position="390,360" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan3" render="Label" position="590,360" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText4" render="Label" position="20,390" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp4" render="Label" position="180,390" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText4" render="Label" position="390,390" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan4" render="Label" position="590,390" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText5" render="Label" position="20,420" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp5" render="Label" position="180,420" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText5" render="Label" position="390,420" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan5" render="Label" position="590,420" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText6" render="Label" position="20,450" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp6" render="Label" position="180,450" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText6" render="Label" position="390,450" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan6" render="Label" position="590,450" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorTempText7" render="Label" position="20,480" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorTemp7" render="Label" position="180,480" size="120,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		<widget source="SensorFanText7" render="Label" position="390,480" size="120,25" font="Regular;20" halign="left"/>
		<widget source="SensorFan7" render="Label" position="590,480" size="150,25" font="Regular;20" halign="left">
			<convert type="SensorToText"></convert>
		</widget>
		</screen>"""

	def __init__(self, session, args = None):
		self.skin = TempFanControl.skin
		Screen.__init__(self, session)
		
		templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
		self.tempcount = len(templist)
		fanlist = sensors.getSensorsList(sensors.TYPE_FAN_RPM)
		self.fancount = len(fanlist)
		self.onShown.append(self.setWindowTitle)
		self.onLayoutFinish.append(self.onLayoutEnd)
		
		self["red"] = StaticText(_("Cancel"))
		self["green"] = StaticText(_("OK"))
		self["yellow"] = StaticText("")
		self["blue"] = StaticText("")	
		self["SensorText"] = StaticText(_("Sensor"))
		self["TemperatureText"] = StaticText(_("Temperature"))
		fanstr=_("Fan %d") % 1
		fanstr=fanstr.rstrip(" 1")
		self["FanText"] = StaticText(fanstr)
		self["SpeedText"] = StaticText(_("Speed"))
		
		for count in range(8):
			if count < self.tempcount:
				id = templist[count]
				self["SensorTempText%d" % count] = StaticText(sensors.getSensorName(id))
				self["SensorTemp%d" % count] = SensorSource(sensorid = id)
			else:
				self["SensorTempText%d" % count] = StaticText("")
				self["SensorTemp%d" % count] = SensorSource()
				
			if count < self.fancount:
				id = fanlist[count]
				self["SensorFanText%d" % count] = StaticText(sensors.getSensorName(id))
				self["SensorFan%d" % count] = SensorSource(sensorid = id)
			else:
				self["SensorFanText%d" % count] = StaticText("")
				self["SensorFan%d" % count] = SensorSource()
		
		# explizit check on every entry
		self.onChangedEntry = []
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.save,
			"cancel": self.revert,
			"red": self.revert,
			"green": self.save,
			"yellow": self.yellowKey,
			"blue": self.blueKey
		}, -1)

	def createSetup(self):
		self.list = []
		for count in range(fancontrol.getFanCount()):
			self.list.append(getConfigListEntry(_("Fan %d Voltage") % (count + 1), fancontrol.getConfig(count).vlt))
			self.list.append(getConfigListEntry(_("Fan %d PWM") % (count + 1), fancontrol.getConfig(count).pwm))
			self.list.append(getConfigListEntry(_("Standby Fan %d Voltage") % (count + 1), fancontrol.getConfig(count).vlt_standby))
			self.list.append(getConfigListEntry(_("Standby Fan %d PWM") % (count + 1), fancontrol.getConfig(count).pwm_standby))
			self["config"].list = self.list
			self["config"].l.setList(self.list)

	def changedEntry(self):
		choice = self["config"].getCurrent()
		if choice != None:
			self.createSetup()

	def setWindowTitle(self):
		self.setTitle(_("Temperature and Fan control"))

	def onLayoutEnd(self,status=None):
		count=self.fancount
		# get current skin width and height to prevent resizing full screen skins
		sw = self.instance.size().width()
		sh = self.instance.size().height()
		if self.tempcount > count:
			count=self.tempcount
		w=sw
		if sz_w == 1920:
			if sw==1920 and sh==1280:
				h=sh
			else:
				h=sh-((8-count)*40)-60 # 40 pixels per fan in FHD skin
		else:
			w=sw
			if sw==1280 and sh==720:
				h=sh
			else:
				h=sh-((8-count)*30)-40 # 30 pixels per fan in HD skin
		if self.instance is not None:
			print "[TempFanControl] resizes for %d temperatures and %d fans to width %d and height %d" % (self.tempcount, self.fancount,w,h)
			self.instance.resize(eSize(*(w, h)))

	def save(self):
		for count in range(fancontrol.getFanCount()):
			fancontrol.getConfig(count).vlt.save()
			fancontrol.getConfig(count).pwm.save()
			fancontrol.getConfig(count).vlt_standby.save()
			fancontrol.getConfig(count).pwm_standby.save()
		self.close()

	def revert(self):
		for count in range(fancontrol.getFanCount()):
			fancontrol.getConfig(count).vlt.load()
			fancontrol.getConfig(count).pwm.load()
			fancontrol.getConfig(count).vlt_standby.load()
			fancontrol.getConfig(count).pwm_standby.load()
		self.close()

	def yellowKey(self):
		print "[TempFanControl] yellow pressed ..."

	def blueKey(self):
		print "[TempFanControl] blue pressed ..."

def main(session, **kwargs):
	session.open(TempFanControl)

def startMenu(menuid):
	if menuid != "devices" and menuid != "extended":
		return []
	return [(_("Temperature and Fan control"), main, "tempfancontrol", 80)]

def Plugins(**kwargs):
	return PluginDescriptor(name = "Temperature and Fan control", description = _("Temperature and Fan control"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc = startMenu)
