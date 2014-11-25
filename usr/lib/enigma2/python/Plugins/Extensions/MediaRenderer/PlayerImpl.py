# -*- coding: UTF-8 -*-
from Screens.MessageBox import MessageBox
from Plugins.SystemPlugins.UPnP.UPnPMediaRenderer import UPnPPlayer
from Tools.Log import Log

from VideoGUI import VideoGUI
from AudioGUI import AudioGUI

class PlayerImpl(UPnPPlayer):
	IMAGE_CACHE_PATH = "/tmp/"

	def __init__(self, session):
		UPnPPlayer.__init__(self, session, handlePlayback=True)
		self._oldService = None
		self._reset()# initialize some stuff

	def _reset(self):
		if self._oldService:
			Log.i("Restoring previous service")
			self.session.nav.playService(self._oldService)
		self._videoGUI = None
		self._audioGUI = None
		self._picView = None
		self._isPic = False
		self._currentGui = None
		self._oldService = None

	def _openGUI(self):
		if self.mimetype is None:
			self.mimetype = "video/mpeg"

		#picture are using the picviewer plugin
		if self.mimetype.startswith("image"):
			self.showPicture()
		else:#video or audio
			self._isPic = False
			if self._picView is not None:
				self._picView.close()

		#audio & video
		if not self._oldService:
			self._oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.mimetype.startswith('audio'):
			if self._audioGUI == None:
				Log.i("Starting AudioGUI")
				self._audioGUI = self.session.open(AudioGUI, self)
				self._audioGUI.onClose.append(self._reset)
				self._currentGui = self._audioGUI
			return self._audioGUI
		elif self.mimetype.startswith('video'):
		#if True:
			if self._videoGUI == None:
				Log.i("Starting VideoGUI")
				self._videoGUI = self.session.open(VideoGUI, self)
				self._videoGUI.onClose.append(self._reset)
				self._currentGui = self._videoGUI
			return self._videoGUI

	def play(self):
		self._openGUI()
		if self.mimetype and self.mimetype.startswith('image'):
			UPnPPlayer.play(self, avoidPlayback=True)
		else:
			UPnPPlayer.play(self, avoidPlayback=False)
		self._currentGui.play()

	def pause(self):
		if UPnPPlayer.pause(self):
			self._currentGui.pause()
			return True
		return False

	def unpause(self):
		if UPnPPlayer.unpause(self):
			self._currentGui.unpause()
			return True
		return False

	def getMetadata(self):
		return self.metadata

	def showPicture(self):
		Log.i()
		from twisted.web.client import downloadPage
		import time, mimetypes, os

		if self._picView is not None:
			try:
				os.remove(self._imageFile)
			except:
				pass
			self._imageFile = None
		self._isPic = True

		extension = mimetypes.guess_extension(self.mimetype, strict=False)
		self._imageFile = "%s%s%s" %(self.IMAGE_CACHE_PATH, time.time(), extension)
		d = downloadPage(self.uri, self._imageFile)
		d.addCallbacks(self._onPictureReady, self._onPictureLoadFailed)

	def _onPictureReady(self, nothing):
		Log.i("file=%s" %self._imageFile)
		try:
			from PictureGUI import PictureGUI
			path = "%s/" %( "/".join( self._imageFile.split("/")[0:-1] ) )
			name = self._imageFile.split("/")[-1]
			filelist = [((self._imageFile, False), None)]

			Log.i("path=%s, name=%s, filelist=%s" %(path, name, filelist))
			if self._picView is None:
				self._picView = self.session.open(PictureGUI, filelist, 0, path)
				self._currentGui = self._picView
			else:
				self._picView.setFileList(filelist, 0, path)
			self._picView.onClose.append(self._reset)
		except Exception as e:
			Log.w(e)
			msgbox = self.session.open(MessageBox, _("Showing a picture from '%s' failed!") %self.uri, type=MessageBox.TYPE_ERROR, timeout=20)
			msgbox.setTitle( _("UPnP/DLNA - Failed to show picture") )

	def _onPictureLoadFailed(self):
		Log.w("Loading picture from '%s' failed!" %self.uri)
		self._imageFile = None
		msgbox = self.session.open(MessageBox, _("Loading a picture from '%s' failed!") %self.uri, type=MessageBox.TYPE_ERROR, timeout=20)
		msgbox.setTitle( _("UPnP/DLNA - Failed to load picture") )

	def _onStop(self, isEof):
		Log.i()
		UPnPPlayer.stop(self, isEof)

	def _onPause(self, resumed):
		Log.i("resume=%s" %resumed)
		if resumed:
			UPnPPlayer.play(self)
		else:
			UPnPPlayer.pause(self)

	def stop(self):
		if self._currentGui != None:
			self._currentGui.delayedClose()
		self._onStop(False)

	def playpause(self, pause):
		"""
		return True if paused, False if playing
		"""
		if pause:
			return not self.pause()
		else:
			return self.unpause()

	def getInfo(self):
		return None
