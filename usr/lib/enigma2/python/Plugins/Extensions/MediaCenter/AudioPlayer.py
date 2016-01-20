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
from MediaPlayerLCDScreen import MediaPlayerLCDScreen
from Playlist import Playlist
from DatabasePlaylist import DatabasePlaylist
from PlaylistPlayer import PlaylistPlayer

from Tools.Log import Log

from os import path as os_path

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
		<screen position="center,center" size="1280,720" title="Audio Player">
			<widget name="coverArt" position="110,40" size="300,300" pixmap="skin_default/no_coverArt.png" zPosition="1" transparent="1" alphatest="blend" scale="1" />
			<widget name="album" position="110,355" size="300, 25" zPosition="1" font="Regular;20" valign="center" foregroundColor="foreground" backgroundColor="background" transparent="1" />
			<widget name="genre" position="110,385" size="300, 25" zPosition="1" font="Regular;20" valign="center" foregroundColor="foreground" backgroundColor="background" transparent="1" />
			<widget name="year" position="110,415" size="300, 25" zPosition="1" font="Regular;20" valign="center" foregroundColor="foreground" backgroundColor="background" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/button_red.png" position="110,555" size="15,16" alphatest="on" />
			<widget name="red" position="130, 552" size="270, 25" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>

			<ePixmap pixmap="skin_default/buttons/button_green.png" position="110,585" size="15,16" alphatest="on" />
			<widget name="green" position="130, 582" size="270, 25" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>

			<ePixmap pixmap="skin_default/buttons/button_yellow.png" position="110,615" size="15,16" alphatest="on" />
			<widget name="yellow" position="130, 612" size="270, 25" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>

			<ePixmap pixmap="skin_default/buttons/button_blue.png" position="110,645" size="15,16" alphatest="on" />
			<widget name="blue" position="130, 642" size="270, 25" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>

			<!--
			<widget name="repeat" pixmaps="skin_default/repeat_off.png,skin_default/repeat_on.png" position="1160,343" size="50,30" transparent="1" alphatest="blend"/>
			-->

			<widget name="artisttext" position="0,0" size="0,0"/>
			<widget name="albumtext" position="0,0" size="0,0"/>
			<widget name="yeartext" position="0,0" size="0,0"/>
			<widget name="genretext" position="0,0" size="0,0"/>
			<widget name="titletext" position="0,0" size="0,0"/>

			<widget name="title" position="430,45" size="550, 25" zPosition="1" font="Regular;22" valign="top" backgroundColor="background" transparent="1" />
			<widget name="artist" position="830,45" size="200, 25" zPosition="1" font="Regular;22" halign="right" valign="top" foregroundColor="foreground" backgroundColor="background" transparent="1" />

			<widget source="session.CurrentService" render="Label" zPosition="1" position="430,70" size="150,20" font="Regular;18" halign="left" backgroundColor="black" transparent="1">
				<convert type="ServicePosition">Position</convert>
			</widget>
			<widget source="session.CurrentService" render="Label" zPosition="1" position="1030,70" size="150,20" font="Regular;18" halign="right" backgroundColor="black" transparent="1">
				<convert type="ServicePosition">Length</convert>
			</widget>

			<eLabel position="430,93" size="750,7" backgroundColor="foreground" />
			<widget source="session.CurrentService" render="Progress" zPosition="1" position="430,93" size="750,7" pixmap="skin_default/progress_small.png" transparent="1" backgroundColor="foreground">
				<convert type="ServicePosition">Position</convert>
			</widget>

			<widget source="playlist" render="Listbox" position="430,110" size="750,550" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"templates":{
						"default": (55, [
							MultiContentEntryPixmapAlphaTest(pos = (1, 1), size = (53, 53), png = 6),
							MultiContentEntryPixmapAlphaTest(pos = (19, 19), size = (16, 16), png = 1),
							MultiContentEntryText(pos = (60, 3), size = (565, 25), font = 0, flags = RT_VALIGN_CENTER, text = 2),
							MultiContentEntryText(pos = (60, 30), size = (280, 25), font = 1, flags = RT_VALIGN_CENTER, text = 3),
							MultiContentEntryText(pos = (345, 30), size = (280, 25), font = 1, flags = RT_VALIGN_CENTER, text = 4),
							MultiContentEntryText(pos = (625, 3), size = (95, 55), font = 1, flags = RT_VALIGN_CENTER|RT_HALIGN_RIGHT, text = 5),
						]),
						"simple": (55, [
							MultiContentEntryPixmapAlphaTest(pos = (19, 19), size = (16, 16), png = 1),
							MultiContentEntryText(pos = (25, 1), size = (730, 55), font = 0, flags = RT_VALIGN_CENTER, text = 2),
						]),
						},
					"fonts": [gFont("Regular", 24), gFont("Regular", 18)]
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
		self.summaries.setText(artist, 3)
		self.summaries.setText(title, 4)

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

	def createSummary(self):
		return MediaPlayerLCDScreen

	def play(self, playSelected=True):
		Log.i("playSelected=%s" % playSelected)
		if playSelected:
			service = self._playlist.playSelected()
			if not self.service or service.toCompareString() != self.service.toCompareString():
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
		self.service = None
		self._playlist.stop()
		self._updateMusicInformation()
		mediaCore.stop()

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
