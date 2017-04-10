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
		<screen position="center,80" size="1200,610" title="Audio Player">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<widget name="red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"  shadowColor="black" shadowOffset="-2,-2" />
			<widget name="blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="global.CurrentTime" render="Label" position="1130,12" size="60,25" font="Regular;22" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="820,12" size="300,25" font="Regular;22" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Format:%A %d. %B</convert>
			</widget>
			<eLabel position="10,50" size="1180,1" backgroundColor="grey" />
			<eLabel position="380,50" size="1,555" backgroundColor="grey" />
			<widget name="coverArt" position="40,55" size="300,300" pixmap="skin_default/no_coverArt.png" />
			<widget name="artist" position="30,490" size="330,25" font="Regular;22" backgroundColor="background"/>
			<widget name="album" position="30,520" size="330,25" font="Regular;20" />
			<widget name="genre" position="30,550" size="330,25" font="Regular;20" />
			<widget name="year" position="30,580" size="330,25" font="Regular;20" />
			<widget name="title" position="30,365" size="330,50" halign="center" valign="center" font="Regular;22" backgroundColor="background" />
			<eLabel position="30,433" size="330,2" backgroundColor="grey" />
			<widget source="session.CurrentService" render="Progress" position="30,430" size="330,8" zPosition="1" pixmap="skin_default/progress.png" transparent="1">
				<convert type="ServicePosition">Position</convert>
			</widget>
			<widget source="session.CurrentService" render="Label" position="30,450" size="70,20" font="Regular;18" noWrap="1">
				<convert type="ServicePosition">Position</convert>
			</widget>
			<widget source="session.CurrentService" render="Label" position="290,450" size="70,20" font="Regular;18" halign="right" noWrap="1">
				<convert type="ServicePosition">Length</convert>
			</widget>
			<widget source="playlist" render="Listbox" position="400,70" size="790,530" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"templates":{
						"default": (53, [
							MultiContentEntryPixmapAlphaTest(pos = (1, 1), size = (53, 53), png = 6),
							MultiContentEntryPixmapAlphaTest(pos = (740, 3), size = (20, 20), png = 1),
							MultiContentEntryText(pos = (60, 1), size = (650, 28), font = 0, flags = RT_VALIGN_CENTER, text = 2),
							MultiContentEntryText(pos = (60, 30), size = (290, 22), font = 1, flags = RT_VALIGN_CENTER, text = 3,color=0xa0a0a0),
							MultiContentEntryText(pos = (355, 30), size = (290, 22), font = 1, flags = RT_VALIGN_CENTER, text = 4,color=0xa0a0a0),
							MultiContentEntryText(pos = (670, 30), size = (100, 22), font = 1, flags = RT_VALIGN_CENTER|RT_HALIGN_RIGHT, text = 5,color=0xa0a0a0),
						]),
						"simple": (53, [
							MultiContentEntryPixmapAlphaTest(pos = (19, 19), size = (16, 16), png = 1),
							MultiContentEntryText(pos = (25, 0), size = (760, 53), font = 0, flags = RT_VALIGN_CENTER, text = 2),
						]),
						},
					"fonts": [gFont("Regular", 22), gFont("Regular", 18)]
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
				iPlayableService.evUser + 13: self["coverArt"].embeddedCoverArt
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
