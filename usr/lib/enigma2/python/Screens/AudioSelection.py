from Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, getConfigListEntry, ConfigNothing, ConfigSelection, ConfigOnOff
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.Boolean import Boolean
from Components.SystemInfo import SystemInfo
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from enigma import iPlayableService, iSubtitleFilterType_ENUMS, iSubtitleType_ENUMS as iSt, iGstSubtitleType_ENUMS as iGSt, iAudioType_ENUMS as iAt

from Tools.ISO639 import LanguageCodes
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap

FOCUS_CONFIG, FOCUS_STREAMS = range(2)
[PAGE_AUDIO, PAGE_SUBTITLES] = ["audio", "subtitles"]

#{key: (shortname, display name, default sort rank)}
AUDIO_FORMATS = {
	iAt.atDTSHD:  ("DTS-HD",_("DTS-HD"),1),
	iAt.atDTS:    ("DTS",   _("DTS"),   2),
	iAt.atAACHE:  ("AACHE", _("HE-AAC"),3),
	iAt.atAAC:    ("AAC",   _("AAC"),   4),
	iAt.atDDP:    ("DDP",   _("AC3+"),  5),
	iAt.atAC3:    ("AC3",   _("AC3"),   6),
	iAt.atMPEG:   ("MPEG",  _("MPEG"),  7),
	iAt.atMP3:    ("MP3",   _("MP3"),   8),
	iAt.atLPCM:   ("LPCM",  _("LPCM"),  9),
	iAt.atPCM:    ("PCM",   _("PCM"),  10),
	iAt.atWMA:    ("WMA",   _("WMA"),  11),
	iAt.atFLAC:   ("FLAC",  _("FLAC"), -1),
	iAt.atOGG:    ("OGG",   _("OGG"),  -1),
	iAt.atTRUEHD: ("TrueHD",_("TrueHD"), -1),
	iAt.atUnknown:("unknown",_("<unknown>"), -1)
}

SUB_FORMATS = {
	iSt.DVB:   ("DVB", _("DVB"), 1),
	iSt.TTX:   ("TTX", _("TTX"), 2),
	iSt.DVD:   ("DVD", _("DVD"), 3),
	iSt.GST:   ("GST",  ("GST"), -1),
	iSt.NONE:  ("unknown", _("<unknown>"), -1)
}

GST_SUB_FORMATS = {
	iGSt.stPGS:      ("PGS",    _("PGS Bluray subs"), 11),
	iGSt.stVOB:      ("VOB",    _("DVD subtitles"), 12),
	iGSt.stASS:      ("AAS",    _("AAS Advanced SSA"), 13),
	iGSt.stSSA:      ("SSA",    _("SSA Substation Alpha"), 14),
	iGSt.stPlainText:("plain",  _("plain text subtitles"), 15),
	iGSt.stUnknown:  ("unknown",_("<unknown>"), -1)
}

selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/selectioncross.png"))

class SelectionTrackinfoEntry():
	def __init__(self, idx, info):
		self.idx = idx
		self.info = info

class AudioSelection(Screen, ConfigListScreen):
	def __init__(self, session, infobar=None, page=PAGE_AUDIO):
		Screen.__init__(self, session)

		self["streams"] = List([])
		self["key_red"] = Boolean(False)
		self["key_green"] = Boolean(False)
		self["key_yellow"] = Boolean(True)
		self["key_blue"] = Boolean(False)
		self["key_menu"] = Boolean(False)
		self["help_label"] = Label()

		ConfigListScreen.__init__(self, [])
		self.infobar = infobar or self.session.infobar

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evSubtitleListChanged: self.__subtitleListChanged,
				iPlayableService.evAudioListChanged: self.__audioListChanged,
				iPlayableService.evUpdatedInfo: self.__audioListChanged,
				iPlayableService.evUpdatedEventInfo: self.__audioListChanged
			})
		self.cached_subtitle_checked = False
		self.plugincallerdict = {}
		self["actions"] = NumberActionMap(["ColorActions", "SetupActions", "DirectionActions", "MenuActions", "InfobarAudioSelectionActions"],
		{
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"menu": self.keyMenu,
			"ok": self.keyOk,
			"cancel": self.cancel,
			"audioSelection": self.cancel,
			"up": self.keyUp,
			"down": self.keyDown,
			"previousSection": self.enablePrevious,
			"nextSection": self.enableNext,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"upUp": self.doNothing,
			"downUp": self.doNothing,
			"leftUp": self.doNothing,
			"rightUp": self.doNothing
		}, -2)

		self.settings = ConfigSubsection()
		choicelist = [(PAGE_AUDIO,_("Subtitles")), (PAGE_SUBTITLES,_("audio tracks"))]
		self.settings.menupage = ConfigSelection(choices = choicelist, default=page)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __updatedInfo(self):
		self.fillList()

	def __subtitleListChanged(self):
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.fillList()

	def __audioListChanged(self):
		if self.settings.menupage.getValue() == PAGE_AUDIO:
			self.fillList()

	def __layoutFinished(self):
		self["config"].instance.setSelectionEnable(False)
		self.focus = FOCUS_STREAMS
		self.restyleMultiContentTemplate()
		self.settings.menupage.addNotifier(self.menupageChanged)

	def menupageChanged(self, arg):
		self.fillList()
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setToggleSubsFilterKey()
		self.restyleMultiContentTemplate()
		self.setHelpLabel()

	def fillList(self, preselected_idx=None):
		streams = []
		conflist = []
		playing_idx = None

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

				playing_idx = self.audioTracks.getCurrentTrack()
				for idx in range(n):
					s_number = str(idx + 1)
					trackinfo = audio.getTrackInfo(idx)
					languages = trackinfo.getLanguage().split('/')
					s_codec = AUDIO_FORMATS[trackinfo.getType()][1]
					s_description = trackinfo.getDescription() or ""
					s_language = ""
					selected = idx == playing_idx

					if selected:
						playing_idx = idx

					cnt = 0
					for lang in languages:
						if cnt:
							s_language += ' / '
						if LanguageCodes.has_key(lang):
							s_language += _(LanguageCodes[lang][0])
						elif lang == "und":
							_("<unknown>")
						else:
							s_language += lang
						cnt += 1

					streams.append((SelectionTrackinfoEntry(idx, trackinfo), s_number, s_language, s_codec, s_description, selected and selectionpng or None))

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

			if self.infobar.subtitles_enabled:
				playing_idx = self.infobar.selected_subtitle
			else:
				playing_idx = None

			subs = self.infobar.getCurrentServiceSubtitle()
			n = subs and subs.getNumberOfSubtitleTracks() or 0

			for idx in range(n):
				trackinfo = subs.getSubtitleTrackInfo(idx)
				s_number = str(idx + 1)
				s_codec = "?"
				s_language = _("<unknown>")
				flags = []
				selected = idx == playing_idx

				if selected:
					playing_idx = idx

				lang = trackinfo.getLanguage()
				if lang != "und":
					if LanguageCodes.has_key(lang):
						s_language = _(LanguageCodes[lang][0])
					else:
						s_language = lang

				if trackinfo.getType() == iSt.GST:
					s_codec = GST_SUB_FORMATS[trackinfo.getGstSubtype()][1]
				else:
					s_codec = SUB_FORMATS[trackinfo.getType()][1]

				if trackinfo.getType() in [iSt.GST, iSt.DVD]:
					if trackinfo.isDefault():
						flags.append(_("Default"))
					if trackinfo.isForced():
						flags.append(_("Forced"))
					if trackinfo.getType() == iSt.DVD or trackinfo.getGstSubtype() in [iGSt.stPGS, iGSt.stVOB]:
						if trackinfo.getFilter() & iSubtitleFilterType_ENUMS.SUB_FILTER_SHOW_FORCED_ONLY:
							flags.append(_("forced only"))
						if trackinfo.getFilter() & iSubtitleFilterType_ENUMS.SUB_FILTER_SHOW_ALL:
							flags.append(_("show all"))
				if trackinfo.isSaved():
					flags.append(_("Saved"))
				s_flags = (", ").join(flags)

				if s_codec == "TTX":
					s_codec += " %x%x" %(trackinfo.getMagazineNumber(), trackinfo.getPageNumber())

				stream = (SelectionTrackinfoEntry(idx, trackinfo), s_number, s_language, s_codec, s_flags, selected and selectionpng or None)
				streams.append(stream)

		conflist.append(getConfigListEntry(_("Menu"), self.settings.menupage))

		if hasattr(self.infobar, "runPlugin"):
			class PluginCaller:
				def __init__(self, fnc, *args):
					self.fnc = fnc
					self.args = args
				def __call__(self, *args, **kwargs):
					self.fnc(*self.args)
			audioPlugins = [ (p.name, PluginCaller(self.infobar.runPlugin, p)) for p in plugins.getPlugins(where = PluginDescriptor.WHERE_AUDIOMENU) ]
			if len(audioPlugins) > 0:
				self["key_blue"].setBoolean(True)
				text, fnc = audioPlugins[0]
				conflist.append(getConfigListEntry(text, ConfigNothing()))
				self.plugincallerdict[text] = fnc
			if len(audioPlugins) > 1:
				self["key_menu"].setBoolean(True)
				if len(audioPlugins) == 2:
					text, fnc = audioPlugins[1]
					self.plugincallerdict[text] = fnc
					conflist.append(getConfigListEntry(text, ConfigNothing()))
				else:
					self._extendedAudioPlugins = audioPlugins[1:]
					text, fnc = _("More ..."), self.showExtendedAudioPluginChoice
					audioPlugins.append([text, fnc])
					conflist.append(getConfigListEntry(text, ConfigNothing()))
					self.plugincallerdict[text] = fnc
					for text, fnc in audioPlugins[1:]:
						self.plugincallerdict[text] = fnc

		self["config"].list = conflist
		self["config"].l.setList(conflist)

		self["streams"].list = streams
		if isinstance(preselected_idx, int):
			self["streams"].setIndex(preselected_idx)
		elif isinstance(playing_idx, int):
			self["streams"].setIndex(playing_idx)
		self.setToggleSubsFilterKey()

	def showExtendedAudioPluginChoice(self):
		self.session.openWithCallback(self.onExtendedAudioPluginChoice, ChoiceBox, list=self._extendedAudioPlugins, windowTitle=_("Audio Plugin Selection"))

	def onExtendedAudioPluginChoice(self, choice):
		if choice:
			choice[1]()

	def changeAC3Downmix(self, downmix):
		if downmix.getValue() == True:
			config.av.downmix_ac3.value = True
		else:
			config.av.downmix_ac3.value = False
		config.av.downmix_ac3.save()

	def changeMode(self, mode):
		if mode is not None and self.audioChannel:
			self.audioChannel.selectChannel(int(mode.getValue()))

	def changeAudio(self, stream_entry):
		if isinstance(stream_entry, SelectionTrackinfoEntry):
			if self.session.nav.getCurrentService().audioTracks().getNumberOfTracks() > stream_entry.idx:
				self.audioTracks.selectTrack(stream_entry.idx)
			self.__updatedInfo()

	def doNothing(self):
		pass

	def keyLeft(self):
		if self.focus == FOCUS_CONFIG:
			ConfigListScreen.keyLeft(self)
		elif self.focus == FOCUS_STREAMS:
			self["streams"].setIndex(0)

	def keyRight(self, config = False):
		if config or self.focus == FOCUS_CONFIG:
			if self["config"].getCurrentIndex() < 3:
				ConfigListScreen.keyRight(self)
			else:
				cur = self["config"].getCurrent() or None
				if cur and cur[0] in self.plugincallerdict:
					self.plugincallerdict[cur[0]]()
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

	def keyMenu(self):
		if self["key_menu"].getBoolean():
			self.colorkey(4)

	def colorkey(self, idx):
		self["config"].setCurrentIndex(idx)
		self.keyRight(True)

	def restyleMultiContentTemplate(self):
		selected = self.focus == FOCUS_STREAMS
		if self.settings.menupage.getValue() == PAGE_AUDIO:
			if selected:
				self["streams"].style = "default"
			else:
				self["streams"].style = "notselected"
		elif self.settings.menupage.getValue() == PAGE_SUBTITLES:
			if selected:
				self["streams"].style = "subs"
			else:
				self["streams"].style = "subs_notselected"

	def keyUp(self):
		if self.focus == FOCUS_CONFIG:
			self["config"].instance.moveSelection(self["config"].instance.moveUp)
		elif self.focus == FOCUS_STREAMS:
			if self["streams"].getIndex() == 0:
				self["config"].instance.setSelectionEnable(True)
				self["config"].setCurrentIndex(len(self["config"].getList())-1)
				self.focus = FOCUS_CONFIG
				self.restyleMultiContentTemplate()
			else:
				self.selectPrevious()
		self.setHelpLabel()

	def keyDown(self):
		if self.focus == FOCUS_CONFIG:
			if self["config"].getCurrentIndex() < len(self["config"].getList())-1:
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
			else:
				self["config"].instance.setSelectionEnable(False)
				self.focus = FOCUS_STREAMS
				self.restyleMultiContentTemplate()
		elif self.focus == FOCUS_STREAMS:
			self.selectNext()
		self.setHelpLabel()

	def keyNumberGlobal(self, number):
		if number <= len(self["streams"].list):
			self["streams"].setIndex(number-1)
			self.keyOk()

	def keyOk(self, close=True):
		if self.focus == FOCUS_STREAMS and self["streams"].list:
			cur = self["streams"].getCurrent()
			page = cur is not None and self.settings.menupage.getValue()
			if page == PAGE_AUDIO:
				self.changeAudio(cur[0])
			elif page == PAGE_SUBTITLES:
				self.changeSubs(cur[0])
			if close:
				self.close(0)
			else:
				self.__updatedInfo()
		elif self.focus == FOCUS_CONFIG:
			self.keyRight()

	def selectPrevious(self):
		self["streams"].selectPrevious()
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setToggleSubsFilterKey()

	def selectNext(self):
		self["streams"].selectNext()
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setToggleSubsFilterKey()

	def enablePrevious(self):
		if self.focus == FOCUS_STREAMS:
			self.selectPrevious()
			self.keyOk(close=False)

	def enableNext(self):
		if self.focus == FOCUS_STREAMS:
			self.selectNext()
			self.keyOk(close=False)

	def setHelpLabel(self):
		text = ""
		if self.focus == FOCUS_CONFIG:
			cur = self["config"].getCurrent()
			if cur and cur[0]:
				text = _("Press OK to toggle %s") % (cur[0])
		else:
			cur = self["streams"].getCurrent()
			if isinstance(cur, tuple):
				if self.settings.menupage.getValue() == PAGE_SUBTITLES:
					action = _("enable")
					if self.infobar.subtitles_enabled:
						if self.infobar.selected_subtitle == cur[0].idx:
							action = _("disable")
					text = _("Press OK to %s the subtitle track %s and close") % (action, str(cur[1]))
				else:
					text = _("Press OK to switch to audio track %s and close") % str(cur[1])
		self["help_label"].setText(text)

	def setToggleSubsFilterKey(self, arg=None):
		if self.settings.menupage.getValue() == PAGE_SUBTITLES:
			cur = self["streams"].getCurrent()
			sel_sub = cur and isinstance(cur[0], SelectionTrackinfoEntry) and cur[0].info
			conflist = self["config"].list
			if sel_sub and (sel_sub.getType() == iSt.DVD or sel_sub.getType() == iSt.GST and sel_sub.getGstSubtype() in [iGSt.stPGS, iGSt.stVOB]):
				forcefilter = str(sel_sub.getFilter())
				choicelist = [(str(iSubtitleFilterType_ENUMS.SUB_FILTER_SHOW_FORCED_ONLY), "forced only"), (str(iSubtitleFilterType_ENUMS.SUB_FILTER_SHOW_ALL), "show all")]
				togglesubsfilter = ConfigSelection(choices = choicelist, default = forcefilter)
				togglesubsfilter.addNotifier(boundFunction(self.toggleSubsFilter, cur[0]), initial_call = False)
				self["key_green"].setBoolean(True)
				conflist[1] = getConfigListEntry(_("Toggle Subtitle Filter"), togglesubsfilter)
			else:
				self["key_green"].setBoolean(False)
				togglesubsfilter = None
				conflist[1] = (('',))
			self["config"].l.setList(conflist)

	def toggleSubsFilter(self, stream_entry, togglesubsfilter):
		if togglesubsfilter and isinstance(stream_entry, SelectionTrackinfoEntry):
			val = int(togglesubsfilter.getValue())
			stream_entry.info.setFilter(val)
			if self.infobar.subtitles_enabled:
				playing_idx = self.infobar.selected_subtitle
				if stream_entry.idx == playing_idx:
					subtitle = self.infobar.getCurrentServiceSubtitle()
					subtitle.enableSubtitles(self.infobar.subtitle_window.instance, stream_entry.idx)
			self.fillList(preselected_idx=stream_entry.idx)

	def changeSubs(self, stream_entry):
		if isinstance(stream_entry, SelectionTrackinfoEntry):
			playing_idx = self.infobar.selected_subtitle
			if self.infobar.subtitles_enabled and stream_entry.idx == playing_idx:
				self.infobar.subtitles_enabled = False
			else:
				self.infobar.selected_subtitle = stream_entry.idx
				self.infobar.subtitles_enabled = True

	def cancel(self):
		self.close(0)

class SubtitleSelection(AudioSelection):
	def __init__(self, session, infobar=None):
		AudioSelection.__init__(self, session, infobar, page=PAGE_SUBTITLES)
		self.skinName = ["AudioSelection"]
