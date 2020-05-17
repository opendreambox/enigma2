from __future__ import absolute_import
from enigma import eServiceReference
from Components.FileList import FileList

from Tools.Log import Log
from .MediaBrowser import MediaBrowser, MediaBrowserList
from .MediaCore import MediaCore, mediaCore

class MediaBrowserFileList(FileList, MediaBrowserList):
	audio_ext = ["mp2", "mp3", "flac", "wma", "fla", "flc", "m4a", "aac", "ogg", "wav", "wave", "pcm"]
	video_ext = ["mpg", "mpeg", "avi", "divx", "vob", "m4v", "mkv", "mp4", "dat", "mov", "ts", "wmv", "mts", "m2ts", "e2pls", "m2t", "xvid"]

	filter_audio = "(?i)^.*\.(%s)" %("|".join(audio_ext),)
	filter_video = "(?i)^.*\.(%s)" %("|".join(video_ext),)
	filter_media = "(?i)^.*\.(%s|%s)" %("|".join(audio_ext), "|".join(video_ext))

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
