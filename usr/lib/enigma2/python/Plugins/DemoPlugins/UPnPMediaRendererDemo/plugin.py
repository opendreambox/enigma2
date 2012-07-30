# -*- coding: UTF-8 -*-
from Components.ResourceManager import resourcemanager
from Screens.MessageBox import MessageBox
from Plugins.SystemPlugins.UPnP.UPnPMediaRenderer import UPnPMediaRenderer, UPnPPlayer
from Plugins.Plugin import PluginDescriptor
from MoviePlayer import MoviePlayer

from enigma import eServiceReference

class ExtendedPlayer(UPnPPlayer):
	IMAGE_CACHE_PATH = "/tmp/"

	def __init__(self, session):
		UPnPPlayer.__init__(self, session, handlePlayback=False)
		self._reset() # initialize some stuff

	def _reset(self):
		self._moviePlayer = None
		self._picView = None
		self._isPic = False

	def play(self):
		if self.mimetype.startswith("image"): # it's a picture
			self.showPicture()
		else:#video or audio
			self._isPic = False
			if self._picView is not None:
				self._picView.close()
			service = eServiceReference(4097, 0, self.uri)
			if self._moviePlayer == None:
				self._moviePlayer = self.session.open(MoviePlayer, service, restoreService = True, stopCallback = self._onStop, pauseCallback = self._onPause)
				self._moviePlayer.onClose.append(self._reset)
			else:
				if self.unpause():
					return
				self._moviePlayer.playService(service)
		UPnPPlayer.play(self)

	def showPicture(self):
		print "[ExtendedPlayer.showPicture]"
		from twisted.web.client import downloadPage
		import time, mimetypes, os

		if self._picView is not None:
			self._picView.close()
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
		print "[ExtendedPlayer._onPictureReady] file=%s" %self._imageFile
		try:
			from Plugins.Extensions.PicturePlayer.plugin import Pic_Full_View
			path = "%s/" %( "/".join( self._imageFile.split("/")[0:-1] ) )
			name = self._imageFile.split("/")[-1]
			filelist = [((self._imageFile, False), None)]

			print "[ExtendedPlayer._onPictureReady] path=%s, name=%s, filelist=%s" %(path, name, filelist)
			self._picView = self.session.open(Pic_Full_View, filelist, 0, path)
			self._picView.onClose.append(self._reset)
		except Exception as e:
			print e
			msgbox = self.session.open(MessageBox, _("Showing a picture from '%s' failed!") %self.uri, type=MessageBox.TYPE_ERROR, timeout=20)
			msgbox.setTitle( _("UPnP/DLNA - Failed to show picture") )

	def _onPictureLoadFailed(self):
		print "[ExtendedPlayer._onPictureLoadFailed] Loading picture from '%s' failed!" %self.uri
		self._imageFile = None
		msgbox = self.session.open(MessageBox, _("Loading a picture from '%s' failed!") %self.uri, type=MessageBox.TYPE_ERROR, timeout=20)
		msgbox.setTitle( _("UPnP/DLNA - Failed to load picture") )

	def _onStop(self):
		print "[ExtendedPlayer._onStop]"
		UPnPPlayer.stop(self)

	def _onPause(self, resumed):
		print "[ExtendedPlayer._onPause] resume=%s" %resumed
		if resumed:
			UPnPPlayer.play(self)
		else:
			UPnPPlayer.pause(self)

	def stop(self):
		print "[ExtendedPlayer._onStop]"
		if self._moviePlayer != None:
			self._moviePlayer.leavePlayerConfirmed([True,"quit"])
		self._onStop()

	def pause(self):
		print "[ExtendedPlayer.pause]"
		res = False
		if self._moviePlayer != None:
			if self._moviePlayer.seekstate == self._moviePlayer.SEEK_STATE_PLAY:
				self._moviePlayer.playpause()
				res = True
		return res

	def unpause(self):
		print "[ExtendedPlayer.unpause]"
		res = False
		if self._moviePlayer != None:
			if self._moviePlayer.seekstate != self._moviePlayer.SEEK_STATE_PLAY:
				self._moviePlayer.playpause()
				res = True
		return res

global instance
instance = None

def start(reason, **kwargs):
	global instance
	session = kwargs.get('session', None)
	if session and reason == 0:
		cp = resourcemanager.getResource("UPnPControlPoint")
		if cp:
			instance = cp.registerRenderer(UPnPMediaRenderer, session=session, player=ExtendedPlayer(session))
	else:
		if instance != None:
			instance.unregister()

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=start) ]