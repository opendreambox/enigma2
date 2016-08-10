from enigma import eServiceReference
from Components.FileList import FileList

from Tools.Log import Log
from MediaBrowser import MediaBrowser, MediaBrowserList
from MediaCore import MediaCore, mediaCore

class MediaBrowserFileList(FileList, MediaBrowserList):
	filter_audio = "(?i)^.*\.(mp2|mp3|ogg|wav|wave|m4a|flac)"
	filter_video = "(?i)^.*\.(mpg|vob|avi|divx|m4v|mkv|mp4|dat|mov|ts)"
	filter_media = "(?i)^.*\.(mp2|mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov)"

	def __init__(self, type):
		MediaBrowserList.__init__(self, type)
		if self._type == MediaCore.TYPE_AUDIO:
			self.filter = MediaBrowserFileList.filter_audio
		elif self._type == MediaCore.TYPE_VIDEO:
			self.filter = MediaBrowserFileList.filter_video
		else:
			self.filter = MediaBrowserFileList.filter_media

		defaultDir = None
		FileList.__init__(self, defaultDir, matchingPattern=self.filter, useServiceRef=True)

	def canDescend(self):
		return self.canDescent()

	def descend(self):
		return self.descent()

	def getItemName(self, item=None):
		if item is None:
			return self.getFilename()
		else:
			if isinstance(item, str):
				return item
			elif isinstance(item, eServiceReference):
				return item.getPath()
			elif isinstance(item[0], eServiceReference):
				return item[0].getPath()
		return None

	def getMeta(self, item):
		return None

class MediaBrowserFile(MediaBrowser):
	FEATURE_FILTER_TYPE = True
	FEATURE_ADD_FOLDER = True
	TITLE = _("File Browser")

	def __init__(self, session, type=type, player=None):
		MediaBrowser.__init__(self, session, type, player=player)
		self._setList(MediaBrowserFileList(type))

	def addFolderToPlaylist(self, folder, recursive=True):
		if folder == '/':
			Log.w("refusing to operate on /")
			return False
		filelist = FileList(folder, matchingPattern=self._list.filter, useServiceRef=True, showMountpoints=False, isTop=True)
		for x in filelist.getFileList():
			if x[0][1] == True: #isDir
				if recursive:
					if x[0][0] != folder:
						self.addFolderToPlaylist(x[0][0])
			else:
				self.addToPlaylist(x[0][0])

		return True

mediaCore.registerBrowser(MediaBrowserFile, _("Filesystem"), MediaCore.TYPE_AUDIO_VIDEO)
