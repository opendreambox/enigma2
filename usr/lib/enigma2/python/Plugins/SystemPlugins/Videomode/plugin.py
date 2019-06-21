from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.SystemInfo import SystemInfo
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigNothing
from Components.Sources.StaticText import StaticText

from Components.DisplayHardware import DisplayHardware
from Components.AudioHardware import AudioHardware


class VideoSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		# for the skin: first try VideoSetup, then Setup, this allows individual skinning
		self.skinName = ["VideoSetup", "Setup" ]
		self.setup_title = _("A/V Settings")
		self.onChangedEntry = [ ]
		self.display_hw = DisplayHardware.instance
		self.audio_hw = AudioHardware.instance

		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		from Components.ActionMap import ActionMap
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.apply
			}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.createSetup()
		self.grabLastGoodPortMode()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def getCurrentPortModeRateValues(self):
		currentPort = config.av.videoport.value
		currentMode = config.av.videomode[config.av.videoport.value].value

		if(currentPort == "HDMI-PC"):
			currentRate = config.av.resolution.value
		else:
			currentRate = config.av.videorate[currentMode].value
		return (currentPort, currentMode, currentRate)

	def createSetup(self):
		level = config.usage.setup_level.index

		self.list = [
			getConfigListEntry(_("Video")),
			getConfigListEntry(_("Video Output"), config.av.videoport),
			getConfigListEntry(_("Preferred modes only"), config.av.preferred_modes_only)
		]

		port_name = config.av.videoport.value
		
		self.list.append(getConfigListEntry(_("Mode"), config.av.videomode[port_name]))
		
		mode_name = config.av.videomode[port_name].value
		if mode_name == "PC":
			self.list.append(getConfigListEntry(_("Resolution"), config.av.resolution))
		else:
			self.list.append(getConfigListEntry(_("Refresh Rate"), config.av.videorate[mode_name]))

		if not self.display_hw.isForceWidescreen(mode_name) and len(config.av.aspect.getChoices()) > 0:
			self.list.append(getConfigListEntry(_("Aspect Ratio"), config.av.aspect))

		if self.display_hw.isWidescreen(mode_name):
			self.list.extend((
				getConfigListEntry(_("Display 4:3 content as"), config.av.policy_43),
				getConfigListEntry(_("Display >16:9 content as"), config.av.policy_169)
			))
		elif self.display_hw.isStandardScreen(mode_name):
			self.list.append(getConfigListEntry(_("Display 16:9 content as"), config.av.policy_169))

		if SystemInfo["CanChangeOsdAlpha"]:
			self.list.append(getConfigListEntry(_("OSD visibility"), config.av.osd_alpha))

		if SystemInfo["CanChangeScalerSharpness"]:
			self.list.append(getConfigListEntry(_("Scaler sharpness"), config.av.scaler_sharpness))

		if level >= 1:
			if SystemInfo["HDRSupport"]:
				self.list.append(getConfigListEntry(_("HLG Support"), config.av.hlg_support))
				self.list.append(getConfigListEntry(_("HDR10 Support"), config.av.hdr10_support))
				if not isinstance(config.av.allow_12bit, ConfigNothing):
					self.list.append(getConfigListEntry(_("Allow 12bit"), config.av.allow_12bit))
				if not isinstance(config.av.allow_10bit, ConfigNothing):
					self.list.append(getConfigListEntry(_("Allow 10bit"), config.av.allow_10bit))
			
			self.list.append(getConfigListEntry(_("Audio")))
			self.list.append(getConfigListEntry(_("AC3 default"), config.av.defaultac3))
			if SystemInfo["CanDownmixAC3"]:
				self.list.append(getConfigListEntry(_("AC3 downmix"), config.av.downmix_ac3))
			self.list.append(getConfigListEntry(_("General AC3 Delay"), config.av.generalAC3delay))
			self.list.append(getConfigListEntry(_("General PCM Delay"), config.av.generalPCMdelay))
			if SystemInfo["SupportsAC3PlusTranscode"]:
				self.list.append(getConfigListEntry(_("Convert AC3+ to AC3"), config.av.convert_ac3plus))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def confirm(self, confirmed):
		if not confirmed:
			config.av.videoport.value = self.last_good[0]

			config.av.videomode[self.last_good[0]].value = self.last_good[1]


			if(config.av.videoport.value == "HDMI-PC"):
				config.av.resolution = self.last_good[2]
			else:
				config.av.videorate[self.last_good[1]].value = self.last_good[2]

			pmr = self.getCurrentPortModeRateValues()
			self.display_hw.setMode(pmr[0], pmr[1], pmr[2])
			self.createSetup()
		else:
			self.keySave()

	def grabLastGoodPortMode(self):
		self.last_good = self.getCurrentPortModeRateValues()

	def apply(self):
		print "Current PMR: " + str(self.getCurrentPortModeRateValues())
		print("Last Good PMR: " + str(self.last_good))
		if(self.getCurrentPortModeRateValues() != self.last_good):
			pmr = self.getCurrentPortModeRateValues()
			self.display_hw.setMode(pmr[0], pmr[1], pmr[2])
			from Screens.MessageBox import MessageBox
			self.session.openWithCallback(self.confirm, MessageBox, _("Is this videomode ok?"), MessageBox.TYPE_YESNO, timeout = 20, default = False)
		else:
			self.keySave()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

def videoSetupMain(session, **kwargs):
	session.open(VideoSetup)

def startSetup(menuid):
	if menuid != "osd_video_audio":
		return [ ]

	return [(_("A/V Settings"), videoSetupMain, "av_setup", 20)]

def VideoWizard(*args, **kwargs):
	from VideoWizard import VideoWizard
	return VideoWizard(*args, **kwargs)

def Plugins(**kwargs):
	list = [
		PluginDescriptor(name=_("Video Setup"), description=_("Advanced Video Setup"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=startSetup)
	]
	return list
