from Components.ActionMap import ActionMap
from Components.Sensors import sensors
from Components.Sources.Sensor import SensorSource
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry

from Screens.Screen import Screen

from Plugins.Plugin import PluginDescriptor
from Components.FanControl import fancontrol

class TempFanControl(Screen, ConfigListScreen):
	skin = """
		<screen position="center,120" size="720,520" title="Fan Control" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<widget render="Label" source="red" position="10,5" size="200,40" zPosition="5" valign="center" halign="center" backgroundColor="#9f1313" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="green" position="210,5" size="200,40" zPosition="5" valign="center" halign="center" backgroundColor="#1f771f" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<eLabel position="10,50" size="700,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="700,160" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<eLabel position="10,230" size="700,1" backgroundColor="grey" />
			<widget source="SensorTempText0" render="Label" position="10,250" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp0" render="Label" position="150,250" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText1" render="Label" position="10,280" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp1" render="Label" position="150,280" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText2" render="Label" position="10,310" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp2" render="Label" position="150,310" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText3" render="Label" position="10,340" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp3" render="Label" position="150,340" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText4" render="Label" position="10,370" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp4" render="Label" position="150,370" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText5" render="Label" position="10,400" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp5" render="Label" position="150,400" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText6" render="Label" position="10,430" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp6" render="Label" position="150,430" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorTempText7" render="Label" position="10,460" size="120,25" font="Regular;20"/>
			<widget source="SensorTemp7" render="Label" position="150,460" size="120,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText0" render="Label" position="380,250" size="120,25" font="Regular;20"/>
			<widget source="SensorFan0" render="Label" position="500,250" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText1" render="Label" position="380,280" size="120,25" font="Regular;20"/>
			<widget source="SensorFan1" render="Label" position="500,280" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText2" render="Label" position="380,310" size="120,25" font="Regular;20"/>
			<widget source="SensorFan2" render="Label" position="500,310" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText3" render="Label" position="380,340" size="120,25" font="Regular;20"/>
			<widget source="SensorFan3" render="Label" position="500,340" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText4" render="Label" position="380,370" size="120,25" font="Regular;20"/>
			<widget source="SensorFan4" render="Label" position="500,370" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText5" render="Label" position="380,400" size="120,25" font="Regular;20"/>
			<widget source="SensorFan5" render="Label" position="500,400" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText6" render="Label" position="380,430" size="120,25" font="Regular;20"/>
			<widget source="SensorFan6" render="Label" position="500,430" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
			<widget source="SensorFanText7" render="Label" position="380,460" size="120,25" font="Regular;20"/>
			<widget source="SensorFan7" render="Label" position="500,460" size="150,25" font="Regular;19" halign="right">
				<convert type="SensorToText"></convert>
			</widget>
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		
		templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
		tempcount = len(templist)
		fanlist = sensors.getSensorsList(sensors.TYPE_FAN_RPM)
		fancount = len(fanlist)
		
		self["red"] = StaticText(_("Cancel"))
		self["green"] = StaticText(_("OK"))
		self["yellow"] = StaticText("")
		self["blue"] = StaticText("")	
		
		for count in range(8):
			if count < tempcount:
				id = templist[count]
				self["SensorTempText%d" % count] = StaticText(sensors.getSensorName(id))		
				self["SensorTemp%d" % count] = SensorSource(sensorid = id)
			else:
				self["SensorTempText%d" % count] = StaticText("")
				self["SensorTemp%d" % count] = SensorSource()
				
			if count < fancount:
				id = fanlist[count]
				self["SensorFanText%d" % count] = StaticText(sensors.getSensorName(id))		
				self["SensorFan%d" % count] = SensorSource(sensorid = id)
			else:
				self["SensorFanText%d" % count] = StaticText("")
				self["SensorFan%d" % count] = SensorSource()
		
		self.list = []
		for count in range(fancontrol.getFanCount()):
			self.list.append(getConfigListEntry(_("Fan %d Voltage") % (count + 1), fancontrol.getConfig(count).vlt))
			self.list.append(getConfigListEntry(_("Fan %d PWM") % (count + 1), fancontrol.getConfig(count).pwm))
			self.list.append(getConfigListEntry(_("Standby Fan %d Voltage") % (count + 1), fancontrol.getConfig(count).vlt_standby))
			self.list.append(getConfigListEntry(_("Standby Fan %d PWM") % (count + 1), fancontrol.getConfig(count).pwm_standby))
		
		ConfigListScreen.__init__(self, self.list, session = self.session)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"ok": self.save,
			"cancel": self.revert,
			"red": self.revert,
			"green": self.save
		}, -1)

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

def main(session, **kwargs):
	session.open(TempFanControl)

def startMenu(menuid):
	if menuid != "system":
		return []
	return [(_("Temperature and Fan control"), main, "tempfancontrol", 80)]

def Plugins(**kwargs):
	return PluginDescriptor(name = "Temperature and Fan control", description = _("Temperature and Fan control"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc = startMenu)
