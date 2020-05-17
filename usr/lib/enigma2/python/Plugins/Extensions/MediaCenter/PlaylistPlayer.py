#enigma2 imports
from __future__ import absolute_import
from Components.Playlist import PlaylistIOInternal
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InfoBarGenerics import PlayerBase
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, SCOPE_CONFIG
#plugin imports
from Tools.Log import Log
from .MediaCore import MediaCore, mediaCore
from .DatabasePlaylist import DatabasePlaylist
import six

# when playing audio content no dedicated player class is used
# so here we must inherit from PlayerBase to not break the 
# previous service handling
class PlaylistPlayer(Screen, HelpableScreen, PlayerBase):
	def __init__(self, session, playlist_string, type):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self._playlist_string = playlist_string

		self._playlist = None
		self.service = None

		self._type = type

		self.onClose.append(self.__onClose)

		if type == MediaCore.TYPE_AUDIO:
			PlayerBase.__init__(self)

	def _initPlaylist(self, playlist_id):
		if playlist_id > 0:
			self._playlist = DatabasePlaylist.get(id=playlist_id)

		#the given playlist does not exist anymore. load the first we can find
		if self._playlist is None:
			lists = DatabasePlaylist.getPlaylists(type=self._type)
			Log.i(lists)
			if len(lists) > 0:
				self._playlist = lists[0]

		if self._playlist is None:
			self._createDefaultPlaylist()
		self._playlist.reload()
		self["playlist"] = self._playlist
		self._playlist.setSelectionEnabled(True)

	def _createDefaultPlaylist(self):
		self._playlist = DatabasePlaylist.create(name="Default", type=self._type)
		assert self._playlist is not None
		if not self._playlist.valid:
			self.loadIOPlaylist() #import old filesystem playlist
			self._playlist.save()
		self._onPlaylistCreated(self._playlist)

	def _onPlaylistCreated(self, playlist):
		Log.i("not handled in subclass!")

	def __onClose(self):
		self._playlist.save()

	def loadIOPlaylist(self):
		playlistFile = "playlist_%s.e2pls" % (self._playlist_string)
		playlistIOInternal = PlaylistIOInternal()
		items = playlistIOInternal.open(resolveFilename(SCOPE_CONFIG, playlistFile))
		if items:
			for x in items:
				self._playlist.add(x.ref, isBatch=True)
			self._playlist.listChanged()

	def saveIOPlaylist(self):
		self.playlistIOInternal.clear()
		for x in self._playlist.list:
			self.playlistIOInternal.addService(ServiceReference(x[0]))
		# TODO if self.savePlaylistOnExit:
		try:
			self.playlistIOInternal.save(resolveFilename(SCOPE_CONFIG, self.playlistFile))
		except IOError:
			Log.i("couldn't save %s" % self.playlistFile)

	def _doPlay(self, service):
		if service:
			if not self.service or service.toCompareString() != self.service.toCompareString():
				self.service = service
				self.play(False)
			else:
				Log.w("{%s} is already playing!" %service.toCompareString())
		else:
			self.stop()

	def play(self, playSelected=True):
		raise NotImplementedError("[PlaylistPlayer] Subclasses have to implement play(self, playSelected=True)")

	def stop(self):
		raise NotImplementedError("[PlaylistPlayer] Subclasses have to implement stop(self)")

	def playNext(self):
		self._doPlay(self._playlist.next())

	def playPrev(self):
		self._doPlay(self._playlist.prev())

	def playLast(self):
		self._doPlay(self._playlist.playLast())

	def addToPlaylist(self, serviceref, extra):
		self._playlist.add(serviceref, extra=extra)

	def addAllToPlaylist(self, items):
		for item in items:
			self._playlist.add(item, isBatch=True)
		self._playlist.listChanged()

	def addAndPlay(self, serviceref, extra):
		self.addToPlaylist(serviceref, extra)
		self.playLast()

	def removeSelectedEntry(self):
		return self._playlist.removeSelected()

	def clearPlaylist(self):
		self.session.openWithCallback(self.clearPlaylistCB, MessageBox, _("Do you really want to clear the playlist?"), type=MessageBox.TYPE_YESNO)

	def clearPlaylistCB(self, answer):
		if answer:
			self.stop()
			self._playlist.clear()

	def editPlaylist(self):
		keys = sorted(mediaCore.getVideoBrowsers().keys())
		if len(keys) == 1:
			mediaCore.openBrowser(self._type, keys[0])
		else:
			browsers = {}
			if self._type == MediaCore.TYPE_AUDIO:
				browsers = mediaCore.getAudioBrowsers()
			else:
				browsers = mediaCore.getVideoBrowsers()
			Log.i("browser: %s" %browsers)
			choices = []
			for key, browser in six.iteritems(browsers):
				choices.append( (browser["name"], key) )

			if len(choices) == 1:
				mediaCore.openBrowser(self._type, choices[0][1], player=self)
			elif len(choices) > 1:
				self.session.openWithCallback(self._onBrowserSelected, ChoiceBox, title=_("Please select a media browser"), list = choices, windowTitle = _("Mediabrowser Selection"))

	def _onBrowserSelected(self, choice):
		if choice != None:
			key = choice and choice[1]
			if key:
				mediaCore.openBrowser(self._type, key, player=self)

	def _moveSelectedUp(self):
		self._playlist.moveSelectedUp()

	def _moveSelectedDown(self):
		self._playlist.moveSelectedDown()

	def _moveUp(self):
		self._playlist.moveUp()

	def _moveDown(self):
		self._playlist.moveDown()

	def _pageUp(self):
		self._playlist.pageUp()

	def _pageDown(self):
		self._playlist.pageDown()