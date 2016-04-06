from Screen import Screen
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, getConfigListEntry, ConfigNothing, ConfigSelection, ConfigOnOff, ConfigBoolean
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.Boolean import Boolean
from Components.SystemInfo import SystemInfo

from enigma import iPlayableService, eServiceMP3

from Tools.ISO639 import LanguageCodes
from Tools.BoundFunction import boundFunction
FOCUS_CONFIG, FOCUS_STREAMS = range(2)
[PAGE_AUDIO, PAGE_SUBTITLES] = ["audio", "subtitles"]

def subs_equal(s1, s2):
	if s1[0] != s2[0]:
		return False
	if s1[0] == 1:
		return s1[2] == s2[2] and s1[3] == s2[3]
	return s1[1] == s2[1]

class AudioSelection(Screen, ConfigListScreen):
	def __init__(self, session, infobar=None, page=PAGE_AUDIO):
		Screen.__init__(self, session)

		self["streams"] = List([])
		self["key_red"] = Boolean(False)
		self["key_green"] = Boolean(False)
		self["key_yellow"] = Boolean(True)
		self["key_blue"] = Boolean(False)
		self["help_label"] = Label()

		ConfigListScreen.__init__(self, [])
		self.infobar = infobar or self.session.infobar

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedInfo: self.__updatedInfo
			})
		self.cached_subtitle_checked = False
		self["actions"] = NumberActionMap(["ColorActions", "SetupActions", "DirectionActions"],
		{
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"ok": self.keyOk,
			"cancel": self.cancel,
			"up": self.keyUp,
			"down": self.keyDown,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -2)

		self.settings = ConfigSubsection()
		choicelist = [(PAGE_AUDIO,_("Subtitles")), (PAGE_SUBTITLES,_("audio tracks"))]
		self.settings.menupage = ConfigSelection(choices = choicelist, default=page)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		self["config"].instance.setSelectionEnable(False)
		self.focus = FOCUS_STREAMS
		self.settings.menupage.addNotifier(self.menupageChanged)

	def menupageChanged(self, arg):
		self.fillList()
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setToggleSubsKey()
		self.setHelpLabel()

	def fillList(self):
		streams = []
		conflist = []
		selectedidx = None

		if self.settings.menupage.getValue() == PAGE_AUDIO:
			self.setTitle(_("Select audio track"))
			service = self.session.nav.getCurrentService()
			self.audioTracks = audio = service and service.audioTracks()
			n = audio and audio.getNumberOfTracks() or 0
			if SystemInfo["CanDownmixAC3"]:
				self.settings.downmix = ConfigOnOff(default=config.av.downmix_ac3.value)
				self.settings.downmix.addNotifier(self.changeAC3Downmix, initial_call = False)
				conflist.append(getConfigListEntry(_("AC3 downmix"), self.settings.downmix))
				self["key_red"].setBoolean(True)

			if n > 0:
				self.audioChannel = service.audioChannel()
				if self.audioChannel:
					choicelist = [("0",_("left")), ("1",_("stereo")), ("2", _("right"))]
					self.settings.channelmode = ConfigSelection(choices = choicelist, default = str(self.audioChannel.getCurrentChannel()))
					self.settings.channelmode.addNotifier(self.changeMode, initial_call = False)
					conflist.append(getConfigListEntry(_("Channel"), self.settings.channelmode))
					self["key_green"].setBoolean(True)
				else:
					conflist.append(('',))
					self["key_green"].setBoolean(False)
				selectedAudio = self.audioTracks.getCurrentTrack()
				for x in range(n):
					number = str(x + 1)
					i = audio.getTrackInfo(x)
					languages = i.getLanguage().split('/')
					description = i.getDescription() or _("<unknown>")
					selected = ""
					language = ""

					if selectedAudio == x:
						selected = _("Running")
						selectedidx = x

					cnt = 0
					for lang in languages:
						if cnt:
							language += ' / '
						if LanguageCodes.has_key(lang):
							language += LanguageCodes[lang][0]
						elif lang == "und":
							_("<unknown>")
						else:
							language += lang
						cnt += 1

					streams.append((x, "", number, description, language, selected))

			else:
				streams = []
				conflist.append(('',))
				self["key_green"].setBoolean(False)

		elif self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setTitle(_("Subtitle selection"))
			conflist.append(('',))
			conflist.append(('',))
			self["key_red"].setBoolean(False)
			self["key_green"].setBoolean(False)

			if self.subtitlesEnabled():
				sel = self.infobar.selected_subtitle
			else:
				sel = None

			idx = 0
			
			subtitlelist = self.getSubtitleList()

			if len(subtitlelist):
				for streamtup in subtitlelist:
					x = list(streamtup)
					number = str(x[1])
					description = "?"
					language = _("<unknown>")
					selected = ""

					if sel and subs_equal(sel, x):
						selected = _("Running")
						if x[0] == 2 and x[3] & eServiceMP3.SUB_FILTER_SHOW_FORCED_ONLY:
							selected = _("forced only")
						if x[0] == 2 and x[3] & eServiceMP3.SUB_FILTER_SHOW_ALL:
							selected = _("show all")
						selectedidx = idx

					if x[4] != "und":
						if LanguageCodes.has_key(x[4]):
							language = LanguageCodes[x[4]][0]
						else:
							language = x[4]

					if x[5] > eServiceMP3.GST_MATROSKA_TRACK_ENABLED:
						language += " ("
						if x[5] & eServiceMP3.GST_MATROSKA_TRACK_DEFAULT:
							language += _("default")
						if x[5] & eServiceMP3.GST_MATROSKA_TRACK_FORCED:
							if x[5] & eServiceMP3.GST_MATROSKA_TRACK_DEFAULT:
								language += ', '
							language += "forced"
						language += ")"

					if x[0] == 0:
						description = "DVB"
						number = "%x" % (x[1])

					elif x[0] == 1:
						description = "TTX"
						number = "%x%02x" % (x[3],x[2])

					elif x[0] == 2:
						types = (_("<unknown>"), "UTF-8 text", "SSA", "AAS", ".SRT file", "VOB", "PGS")
						description = types[x[2]]

					streams.append((tuple(x), "", number, description, language, selected))
					idx += 1
			
			else:
				streams = []

		conflist.append(getConfigListEntry(_("Menu"), self.settings.menupage))
		
		from Components.PluginComponent import plugins
		from Plugins.Plugin import PluginDescriptor
		
		if hasattr(self.infobar, "runPlugin"):
			class PluginCaller:
				def __init__(self, fnc, *args):
					self.fnc = fnc
					self.args = args
				def __call__(self, *args, **kwargs):
					self.fnc(*self.args)

			Plugins = [ (p.name, PluginCaller(self.infobar.runPlugin, p)) for p in plugins.getPlugins(where = PluginDescriptor.WHERE_AUDIOMENU) ]

			if len(Plugins):
				self["key_blue"].setBoolean(True)
				conflist.append(getConfigListEntry(Plugins[0][0], ConfigNothing()))
				self.plugincallfunc = Plugins[0][1]
			if len(Plugins) > 1:
				print "plugin(s) installed but not displayed in the dialog box:", Plugins[1:]

		self["config"].list = conflist
		self["config"].l.setList(conflist)

		self["streams"].list = streams
		if isinstance(selectedidx, int):
			self["streams"].setIndex(selectedidx)

	def __updatedInfo(self):
		self.fillList()

	def getSubtitleList(self):
		s = self.infobar and self.infobar.getCurrentServiceSubtitle()
		l = s and s.getSubtitleList() or [ ]
		return l

	def subtitlesEnabled(self):
		return self.infobar.subtitles_enabled

	def enableSubtitle(self, subtitles):
		if self.infobar.selected_subtitle != subtitles:
			self.infobar.subtitles_enabled = False
			self.infobar.selected_subtitle = subtitles
			if subtitles:
				self.infobar.subtitles_enabled = True

	def changeAC3Downmix(self, downmix):
		if downmix.getValue() == True:
			config.av.downmix_ac3.value = True
		else:
			config.av.downmix_ac3.value = False
		config.av.downmix_ac3.save()

	def changeMode(self, mode):
		if mode is not None and self.audioChannel:
			self.audioChannel.selectChannel(int(mode.getValue()))

	def changeAudio(self, audio):
		track = int(audio)
		if isinstance(track, int):
			if self.session.nav.getCurrentService().audioTracks().getNumberOfTracks() > track:
				self.audioTracks.selectTrack(track)

	def keyLeft(self):
		if self.focus == FOCUS_CONFIG:
			ConfigListScreen.keyLeft(self)
		elif self.focus == FOCUS_STREAMS:
			self["streams"].setIndex(0)

	def keyRight(self, config = False):
		if config or self.focus == FOCUS_CONFIG:
			if self["config"].getCurrentIndex() < 3:
				ConfigListScreen.keyRight(self)
			elif hasattr(self, "plugincallfunc"):
				self.plugincallfunc()
		if self.focus == FOCUS_STREAMS and self["streams"].count() and config == False:
			self["streams"].setIndex(self["streams"].count()-1)

	def keyRed(self):
		if self["key_red"].getBoolean():
			self.colorkey(0)

	def keyGreen(self):
		if self["key_green"].getBoolean():
			self.colorkey(1)
		self.setHelpLabel()

	def keyYellow(self):
		if self["key_yellow"].getBoolean():
			self.colorkey(2)

	def keyBlue(self):
		if self["key_blue"].getBoolean():
			self.colorkey(3)

	def colorkey(self, idx):
		self["config"].setCurrentIndex(idx)
		self.keyRight(True)

	def keyUp(self):
		if self.focus == FOCUS_CONFIG:
			self["config"].instance.moveSelection(self["config"].instance.moveUp)
		elif self.focus == FOCUS_STREAMS:
			if self["streams"].getIndex() == 0:
				self["config"].instance.setSelectionEnable(True)
				self["streams"].style = "notselected"
				self["config"].setCurrentIndex(len(self["config"].getList())-1)
				self.focus = FOCUS_CONFIG
			else:
				self.selectPrevious()
		self.setHelpLabel()

	def keyDown(self):
		if self.focus == FOCUS_CONFIG:
			if self["config"].getCurrentIndex() < len(self["config"].getList())-1:
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
			else:
				self["config"].instance.setSelectionEnable(False)
				self["streams"].style = "default"
				self.focus = FOCUS_STREAMS
		elif self.focus == FOCUS_STREAMS:
			self.selectNext()
		self.setHelpLabel()

	def keyNumberGlobal(self, number):
		if number <= len(self["streams"].list):
			self["streams"].setIndex(number-1)
			self.keyOk()

	def keyOk(self):
		if self.focus == FOCUS_STREAMS and self["streams"].list:
			cur = self["streams"].getCurrent()
			if self.settings.menupage.getValue() == PAGE_AUDIO and cur[0] is not None:
				self.changeAudio(cur[0])
				self.__updatedInfo()
			if self.settings.menupage.getValue() == PAGE_SUBTITLES and cur[0] is not None:
				self.toggleSubs()
			self.close(0)
		elif self.focus == FOCUS_CONFIG:
			self.keyRight()

	def selectPrevious(self):
		self["streams"].selectPrevious()
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setToggleSubsKey()

	def selectNext(self):
		self["streams"].selectNext()
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setToggleSubsKey()

	def setHelpLabel(self):
		text = ""
		if self.focus == FOCUS_CONFIG:
			cur = self["config"].getCurrent()
			if cur and cur[0]:
				text = _("Press OK to toggle %s") % (cur[0])
		else:
			cur = self["streams"].getCurrent()
			if cur:
				text = _("Press OK to switch to audio track %s and close") % str(cur[0])
				if self.settings.menupage.getValue() == PAGE_SUBTITLES:
					status = ("enable") #_()
					if self.subtitlesEnabled():
						sel = self.infobar.selected_subtitle
						if sel and subs_equal(sel, cur[0]) and (self.settings.togglesubs is None or int(self.settings.togglesubs.getValue()) == cur[0][3]):
							status = ("disable")  #_()
					text = _("Press OK to %s the subtitle track %s and close") % (status, str(cur[2]))
		self["help_label"].setText(text)

	def setToggleSubsKey(self, arg=None):
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			cur = self["streams"].getCurrent()
			conflist = self["config"].list
			if cur and cur[0] > 1 and cur[0][5] > 0:
				default = False
				choicelist = []
				forcefilter = ""
				if cur[0][3] & eServiceMP3.SUB_FILTER_SHOW_FORCED_ONLY:
					forcefilter = "1"
				if cur[0][3] & eServiceMP3.SUB_FILTER_SHOW_ALL:
					forcefilter = "2"
				choicelist = [("1", "forced only"), ("2", "show all")]
				self.settings.togglesubs = ConfigSelection(choices = choicelist, default = forcefilter)
				self["key_green"].setBoolean(True)
				conflist[1] = getConfigListEntry(_("Toggle Subtitle Filter"), self.settings.togglesubs)
			else:
				self["key_green"].setBoolean(False)
				self.settings.togglesubs = None
				conflist[1] = (('',))
			self["config"].l.setList(conflist)

	def toggleSubs(self):
		cur = self["streams"].getCurrent()
		val = True
		if self.settings.togglesubs:
			val = int(self.settings.togglesubs.getValue())
		if self.subtitlesEnabled():
			sel = self.infobar.selected_subtitle
			if sel and subs_equal(sel, cur[0]) and (sel[0] < 2 or sel[3] == val):
				val = False
		if val and cur and isinstance(cur[0], tuple):
			x = list(cur[0])
			if type(True) != type(val): # this is a check if val is a boolean type! ... not int
				x[3] = val
			self.enableSubtitle(tuple(x))
		else:
			self.enableSubtitle (None)
		self.__updatedInfo()

	def cancel(self):
		self.close(0)

class SubtitleSelection(AudioSelection):
	def __init__(self, session, infobar=None):
		AudioSelection.__init__(self, session, infobar, page=PAGE_SUBTITLES)
		self.skinName = ["AudioSelection"]
