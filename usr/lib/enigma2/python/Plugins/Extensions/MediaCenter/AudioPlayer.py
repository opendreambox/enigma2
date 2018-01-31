from enigma import iPlayableService, iServiceInformation
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker

from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications
from Screens.MessageBox import MessageBox

from Helpers import EasyPixmap
from MediaCore import MediaCore, mediaCore
from Playlist import Playlist
from DatabasePlaylist import DatabasePlaylist
from PlaylistPlayer import PlaylistPlayer

from Tools.Log import Log

from os import path as os_path
from Components.Sources.StaticText import StaticText

class MediaPixmap(EasyPixmap):
	def folderCoverArtPath(self, path):
		if path.startswith("/"):
			path = "%s/" %(os_path.dirname(path))
			self.setPicturePath(path)

	def embeddedCoverArt(self):
		Log.i("found")
		self.pictureFileName = "/tmp/.id3coverart"
		self.picload.startDecode(self.pictureFileName)

class AudioPlayer(PlaylistPlayer, InfoBarNotifications):
	SEEK_STATE_PLAY = 0
	SEEK_STATE_PAUSE = 1
	SEEK_STATE_IDLE = 2

	ITEM_CLEAR_PLAYLIST = 0
	ITEM_SAVE_PLAYLIST = 1
	ITEM_LOAD_PLAYLIST = 2
	ITEM_CREATE_PLAYLIST = 3

	skin = """
		<screen name="AudioPlayer" position="0,0" size="1280,720" flags="wfNoBorder">
			<eLabel backgroundColor="grey" position="10,80" size="1260,1" zPosition="2"/>
			<eLabel backgroundColor="grey" position="620,80" size="1,960" zPosition="2"/>
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,25" size="200,40" zPosition="2" transparent="1"/>
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,25" size="200,40" zPosition="2" transparent="1"/>
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,25" size="200,40" zPosition="2" transparent="1"/>
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,25" size="220,40" scale="stretch" zPosition="2" transparent="1"/>
			<widget name="red" position="10,25" size="200,40" zPosition="3" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="green" position="210,25" size="200,40" zPosition="3" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="yellow" position="410,25" size="200,40" zPosition="3" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white"  shadowColor="black" shadowOffset="-2,-2" />
			<widget name="blue" position="610,25" size="220,40" zPosition="3" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="coverArt" pixmap="Default-FHD/skin_default/no_coverArt.svg" position="1020,90" size="230,230" zPosition="2"/>
			<widget name="coverBack" position="620,80" size="660,660"/>
			<ePixmap pixmap="Default-FHD/skin_default/back.png" position="620,80" size="660,660" scale="stretch" />
			<widget backgroundColor="#200d1940" foregroundColor="white" source="global.CurrentTime" render="Label" position="1040,20" size="200,55" font="Regular;50" halign="right" zPosition="2" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;44" name="artist" position="650,210" size="360,100" valign="bottom" transparent="1" zPosition="2"/>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;30" name="album" position="650,340" size="360,70" valign="top" transparent="1" zPosition="2"/>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;30" name="genre" position="650,410" size="540,35" transparent="1" zPosition="2"/>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;30" name="year" position="650,450" size="540,35" transparent="1" zPosition="2"/>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;26" name="title" position="650,530" valign="bottom" size="570,62" transparent="1" zPosition="2" />
			<widget pixmap="skin_default/progress.png" borderWidth="1" position="650,610" render="Progress" size="570,10" source="session.CurrentService" transparent="1" zPosition="2">
				<convert type="ServicePosition">Position</convert>
			</widget>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;28" position="650,630" render="Label" size="120,35" source="session.CurrentService" transparent="1" zPosition="2">
				<convert type="ServicePosition">Length</convert>
			</widget>
			<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;28" position="1100,630" halign="right" render="Label" size="120,35" source="session.CurrentService" transparent="1" zPosition="2">
				<convert type="ServicePosition">Remaining,Negate</convert>
			</widget>
			<widget enableWrapAround="1" source="playlist" render="Listbox" position="20,105" size="590,600" scrollbarMode="showOnDemand" zPosition="2">
				<convert type="TemplatedMultiContent">
				{"templates":{
					"default": (50,[
						MultiContentEntryPixmapAlphaTest(pos=(2,1),size=(52,52),png=6),
						MultiContentEntryPixmapAlphaTest(pos=(485,4),size=(16,16),png=1),
						MultiContentEntryText(pos=(60,1),size=(400,24),font=0,flags=RT_VALIGN_CENTER,text=2),
						MultiContentEntryText(pos=(60,26),size=(240,24),font=0,flags=RT_VALIGN_CENTER,text=3,color=0xbababa),
						MultiContentEntryText(pos=(320,26),size=(255,24),font=0,flags=RT_VALIGN_CENTER|RT_HALIGN_RIGHT,text=4,color=0xbababa),
						MultiContentEntryText(pos=(505,1),size=(70,24),font=0,flags=RT_VALIGN_CENTER|RT_HALIGN_RIGHT,text=5),]),
					"simple": (25,[
						MultiContentEntryPixmapAlphaTest(pos=(5,5),size=(15,15),png=1),
						MultiContentEntryText(pos=(25,0),size=(550,25),font=0,flags=RT_VALIGN_CENTER,text=2),]),
					},
				"fonts": [gFont("Regular",18)]
				}
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session, playlist):
		PlaylistPlayer.__init__(self, session, "audio", MediaCore.TYPE_AUDIO)
		InfoBarNotifications.__init__(self)

		self._playlist = None
		self._initPlaylist(config.plugins.mediacenter.audio.last_playlist_id.value)

		self.seekState = self.SEEK_STATE_IDLE
		self._repeat = Playlist.REPEAT_NONE
		self._browser = None

		self["artisttext"] = Label(_("Artist") + ':')
		self["artist"] = Label("")
		self["titletext"] = Label(_("Title") + ':')
		self["title"] = Label("")
		self["albumtext"] = Label(_("Album") + ':')
		self["album"] = Label("")
		self["yeartext"] = Label(_("Year") + ':')
		self["year"] = Label("")
		self["genretext"] = Label(_("Genre") + ':')
		self["genre"] = Label("")
		self["coverArt"] = MediaPixmap()
		self["coverBack"] = MediaPixmap()

		self["red"] = Label(_("Remove"))
		self["green"] = Label(_("Add"))
		self["yellow"] = Label(_("Shuffle - Off"))
		self["blue"] = Label(_("Repeat - None"))
		self._summary_list = StaticText("")
		self["summary_list"] = self._summary_list

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedInfo: self._evUpdatedInfo,
				iPlayableService.evEOF: self._evEOF,
				iPlayableService.evUser + 10: self._evAudioDecodeError,
				iPlayableService.evUser + 11: self._evVideoDecodeError,
				iPlayableService.evUser + 12: self._evPluginError,
				iPlayableService.evUser + 13: self._embeddedCoverArt,
			})

		self["MediaCenterActions"] = HelpableActionMap(self, "MediaCenterActions",
		{
			"menu" : (self._showMenu, _("Open Menu")),
			"ok" : (self.play, _("Play Selected Entry")),
			"cancel" : (self._close, _("Close MediaCenter Audioplayer")),
			"red" : (self._removeSelectedPlaylistEntry, _("Remove Selected Entry From Playlist")),
			"green" : (self.editPlaylist, _("Add file(s) to Playlist")),
			"yellow" : (self._toggleShuffle, _("Toggle Shuffle")),
			"blue" : (self._toggleRepeat, _("Toggle Repeat-Modes (None / All / Single)")),
			"playpause": (self.playpause, _("Play/Pause")),
			"stop": (self.stop, _("Stop Playback")),
			"next": (self.playNext, _("Play Next Entry")),
			"previous":  (self.playPrev, _("Play Previous Entry")),
			"moveUp": self._moveUp,
			"moveDown" : self._moveDown,
			"pageUp": self._pageUp,
			"pageDown": self._pageDown,
			"channelUp": (self._moveSelectedUp, _("Move selected item up")),
			"channelDown": (self._moveSelectedDown, _("Move selected item down")),
		}, -2);

		if playlist != None:
			self.addAllToPlaylist(playlist)

	def _embeddedCoverArt(self):
		self["coverArt"].embeddedCoverArt()
		self["coverBack"].embeddedCoverArt()

	def _evEOF(self):
		self.playNext()

	def _evUpdatedInfo(self):
		self._readTitleInformation()

	def _evAudioDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
		Log.i("audio-codec %s can't be decoded by hardware" % (sTagAudioCodec))
		self.session.open(MessageBox, _("This Dreambox can't decode %s streams!") % sTagAudioCodec, type=MessageBox.TYPE_INFO, timeout=20)

	def _evVideoDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
		Log.i("video-codec %s can't be decoded by hardware" % (sTagVideoCodec))
		self.session.open(MessageBox, _("This Dreambox can't decode %s streams!") % sTagVideoCodec, type=MessageBox.TYPE_INFO, timeout=20)

	def _evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser + 12)
		Log.i(message)
		self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=20)

	def _showMenu(self):
		menu = ((_("Save Playlist"), self.ITEM_SAVE_PLAYLIST),
				(_("Load Playlist"), self.ITEM_LOAD_PLAYLIST),
				(_("Clear Playlist"), self.ITEM_CLEAR_PLAYLIST),
				(_("Create New Playlist"), self.ITEM_CREATE_PLAYLIST),
			)
		self.session.openWithCallback(self._onMenuItemSelected, ChoiceBox, list=menu, windowTitle=_("MediaCenter - Menu"))

	def _onMenuItemSelected(self, entry):
		if entry != None:
			item = entry[1]
			if item is self.ITEM_CLEAR_PLAYLIST:
				self.clearPlaylist()
			elif item is self.ITEM_LOAD_PLAYLIST:
				self.session.openWithCallback(self._onPlaylistSelected, DatabasePlaylist.PlaylistChoice, MediaCore.TYPE_AUDIO)
			elif item is self.ITEM_SAVE_PLAYLIST:
				if self._playlist.save():
					self.session.open(MessageBox, _("Playlist has been saved!"), type=MessageBox.TYPE_INFO)
				else:
					self.session.open(MessageBox, _("An unexpected error occured when trying to save the Playlist!"), type=MessageBox.TYPE_ERROR)
			elif item is self.ITEM_CREATE_PLAYLIST:
				DatabasePlaylist.PlaylistCreate(self.session, MediaCore.TYPE_AUDIO, self._onPlaylistCreated)
			else:
				self.session.open(MessageBox, _("Not implemented, yet!"), type=MessageBox.TYPE_WARNING)

	def _onPlaylistCreated(self, playlist):
		if playlist != None:
			self._playlist.load(playlist.id, playlist.name)
			config.plugins.mediacenter.audio.last_playlist_id.value = playlist.id
			config.plugins.mediacenter.audio.save()
		else:
			self.session.open(MessageBox, _("This Playlist already exists!"), MessageBox.TYPE_ERROR)

	def _onPlaylistSelected(self, entry):
		playlist = entry and entry[1]
		if playlist != None:
			self._playlist.load(playlist.id, playlist.name)
			config.plugins.mediacenter.audio.last_playlist_id.value = playlist.id
			config.plugins.mediacenter.audio.save()
		else:
			Log.w("ERROR LOADING PLAYLIST")

	def lockShow(self):
		pass

	def _readTitleInformation(self):
		currPlay = self.session.nav.getCurrentService()
		if currPlay is not None:
			sTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
			sAlbum = currPlay.info().getInfoString(iServiceInformation.sTagAlbum)
			sGenre = currPlay.info().getInfoString(iServiceInformation.sTagGenre)
			sArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
			sYear = currPlay.info().getInfoString(iServiceInformation.sTagDate)
			self._updateMusicInformation(sArtist, sTitle, sAlbum, sYear, sGenre, clear=False)
		else:
			self._updateMusicInformation()

	def _updateMusicInformation(self, artist="", title="", album="", year="", genre="", clear=True):
		self.updateLabel("artist", artist, clear)
		self.updateLabel("title", title, clear)
		self.updateLabel("album", album, clear)
		self.updateLabel("year", year, clear)
		self.updateLabel("genre", genre, clear)

		if clear:
			self["coverArt"].setDefaultPicture()

	def updateLabel(self, name, info, clear):
		if info != "" or clear:
			if self[name].getText() != info:
				self[name].setText(info)

	def _close(self):
		self.close()

	def play(self, playSelected=True):
		Log.i("playSelected=%s" % playSelected)
		if playSelected:
			service = self._playlist.playSelected()
			if not self.service or not service or service.toCompareString() != self.service.toCompareString():
				self.service = service
				self._updateMusicInformation(clear=True)
			else:
				self.playpause()
				return

		if self.service:
			path = self.service.getPath()
			if path.startswith("/"):
				self["coverArt"].folderCoverArtPath(path)
			self.seekState = self.SEEK_STATE_PLAY
			mediaCore.play(self.service)

	def pause(self):
		self.seekState = self.SEEK_STATE_PAUSE
		self._playlist.pause()
		mediaCore.pause()

	def unpause(self):
		self.seekState = self.SEEK_STATE_PLAY
		self._playlist.play(resume=True)
		mediaCore.unpause()

	def playpause(self):
		if self.seekState == self.SEEK_STATE_PLAY:
			self.pause()
		elif self.seekState == self.SEEK_STATE_IDLE:
			self.play()
		else:
			if self.seekState == self.SEEK_STATE_PAUSE:
				self.unpause()
			else:
				self.stop()

	def stop(self):
		self.seekState = self.SEEK_STATE_IDLE
		self._playlist.stop()
		if self.service:
			mediaCore.stop()
			self.service = None
		self._updateMusicInformation()

	def _toggleShuffle(self):
		if self._playlist.toggleShuffle():
			self["yellow"].setText(_("Shuffle - On") )
		else:
			self["yellow"].setText(_("Shuffle - Off") )

	def _toggleRepeat(self):
		#NONE -> ALL -> SINGLE
		if self._repeat == Playlist.REPEAT_NONE:
			self._repeat = Playlist.REPEAT_ALL
			self["blue"].setText(_("Repeat - All"))
		elif self._repeat == Playlist.REPEAT_ALL:
			self._repeat = Playlist.REPEAT_SINGLE
			self["blue"].setText(_("Repeat - Single"))
		else:
			self._repeat = Playlist.REPEAT_NONE
			self["blue"].setText(_("Repeat - None"))
		self._playlist.repeat(self._repeat)

	def _removeSelectedPlaylistEntry(self):
		if self.removeSelectedEntry() and self.seekState == self.SEEK_STATE_PLAY:
			self.play()
