# -*- coding: UTF-8 -*-

from Tools.Log import Log
from MoviePlayer import MoviePlayer
from Screens.Screen import Screen

import copy

class MediaCore:
	TYPE_AUDIO = 0
	TYPE_VIDEO = 1
	TYPE_AUDIO_VIDEO = 2

	def __init__(self):
		self._mainMenuItems = []
		self.videoBrowsers = {}
		self.audioBrowsers = {}
		self.refreshFncs = []
		self.playlistAddFnc = None
		self.addAndPlayFnc = None
		self.session = None
		self.type = None

	def addToMainMenu(self, item):
		if self._mainMenuItemSanityCheck(item):
			self._mainMenuItems.append(item)

	def getMainMenuItems(self):
		return self._mainMenuItems

	def _mainMenuItemSanityCheck(self, item):
		#check if the given item is a list like this: ( "Menu Text", ScreenSubclass, { "key" : "menukey", "iconpath" : "blabla", featuresPlaylist: True/False } )
		if len(item) < 3:
			Log.i("item doesn't have enough entries")
			return False
		if not issubclass(item[1], Screen):
			Log.i("item[1] is not a Screen")
			return False
		if not isinstance(item[2], dict):
			Log.i("item[2] is NOT a dict")
			return False
		return True

	def setSession(self, session):
		self.session = session

	#TODO need to determine automatically wether it is audio or video that should be played
	def play(self, service, type=TYPE_AUDIO, args=[]):
		if type == MediaCore.TYPE_AUDIO:
			self.session.nav.playService(service)
		elif type == MediaCore.TYPE_VIDEO:
			self.session.open(MoviePlayer, service, *args)

	def pause(self):
		service = self.session.nav.getCurrentService()
		pausable = service.pause()

		if pausable is not None:
			pausable.pause()
		#TODO message if not pausable

	def unpause(self):
		service = self.session.nav.getCurrentService()
		pausable = service.pause()

		if pausable is not None:
			pausable.unpause()
		#TODO message if not pausable

	def stop(self):
		self.session.nav.stopService()

	def registerBrowser(self, cls, name, type, init_params=None):
		#TODO catch "overwriting" registrations (same name, different cls)
		if init_params == None:
			init_params = []

		b = {
				'class': cls,
				'name': name,
				'params' : init_params
			}

		Log.i("b=%s" %b)
		if type == MediaCore.TYPE_AUDIO or type == MediaCore.TYPE_AUDIO_VIDEO:
			b['type'] = MediaCore.TYPE_AUDIO
			self.audioBrowsers[cls.__name__] = copy.copy(b)

		if type == MediaCore.TYPE_VIDEO or type == MediaCore.TYPE_AUDIO_VIDEO:
			b['type'] = MediaCore.TYPE_VIDEO
			self.videoBrowsers[cls.__name__] = copy.copy(b)

		for fnc in self.refreshFncs:
			fnc()

	def addRefreshCallback(self, callback):
		self.refreshFncs.append(callback)

	def getVideoBrowsers(self):
		return self.videoBrowsers

	def getAudioBrowsers(self):
		return self.audioBrowsers

	def search(self, type, needle):
		browsers = []
		if type == MediaCore.TYPE_VIDEO:
			browsers = self.videoBrowsers
		elif type == MediaCore.TYPE_AUDIO:
			browsers = self.audioBrowsers

		refs = []
		for key, browser in browsers.iteritems():
			cls = browser["class"]
			if cls.FEATURE_SEARCH:
				Log.i("searching %s!" %key)
				refs.extend(cls.search(needle))
		Log.i("Search results total: %s" %len(refs))
		return refs

	def openBrowser(self, type, name, player=None):
		b = None

		if type == MediaCore.TYPE_VIDEO:
			b = self.videoBrowsers.get(name, None)

		elif type == MediaCore.TYPE_AUDIO:
			b = self.audioBrowsers.get(name, None)

		if b != None:
			Log.i(b["params"])
			cls = b["class"]
			params = b["params"]
			type = b["type"]

			if cls.FEATURE_FILTER_TYPE:
				self.session.open(cls, *params, type=type, player=player)
			else:
				self.session.open(cls, *params, player=player)

mediaCore = MediaCore()
