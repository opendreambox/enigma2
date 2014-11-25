from enigma import eServiceCenter, iServiceInformation

from Components.Sources.List import List
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Tools.Log import Log

from MediaCore import MediaCore

from os import path as os_path
import random

STATE_PLAY = 0
STATE_PAUSE = 1
STATE_STOP = 2
STATE_REWIND = 3
STATE_FORWARD = 4
STATE_NONE = 5

PlayIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_play.png"))
PauseIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_pause.png"))
StopIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_stop.png"))
RewindIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_rewind.png"))
ForwardIcon = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_forward.png"))
NoneIcon = LoadPixmap("")
DefaultCoverArt = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/no_coverArt.png"))

class PlayListEntry(object):
	@staticmethod
	def get(ref, state, unused):
		"""create a playlist entry for the given reference and state
		"""
		title = ref.getName()
		if title is "":
			title = os_path.split(ref.getPath().split('/')[-1])[1]
		entry = (ref, "", title, "", "", "", DefaultCoverArt)
		entry = PlayListEntry.updateState(entry, state)

		return entry

	@staticmethod
	def updateState(entry, state):
		"""update the state of a given playlist entry
		"""
		png = None
		if state == STATE_PLAY:
			png = PlayIcon
		elif state == STATE_PAUSE:
			png = PauseIcon
		elif state == STATE_STOP:
			png = StopIcon
		elif state == STATE_REWIND:
			png = RewindIcon
		elif state == STATE_FORWARD:
			png = ForwardIcon
		else:
			png = NoneIcon

		entry = list(entry)
		entry[1] = png
		return tuple(entry)

class AudioPlaylistEntry(PlayListEntry):
	@staticmethod
	def get(ref, state, serviceHandler, durationInSeconds=False):
		info = serviceHandler.info(ref)
		artist = info.getInfoString(ref, iServiceInformation.sTagArtist);
		title = info.getInfoString(ref, iServiceInformation.sTagTitle) or info.getName(ref)
		album = info.getInfoString(ref, iServiceInformation.sTagAlbum);
		seconds = info.getLength(ref)
		if durationInSeconds:
			duration = seconds
		else:
			if seconds > 0:
				minutes, seconds = divmod(info.getLength(ref), 60)
				duration = "%02d:%02d" % (minutes, seconds)
			else:
				duration = "--:--"
		Log.i("artist=%s, album=%s" %(artist, album))
		if(artist != "" or album != ""):
			entry = (ref, "", title, artist, album, duration, DefaultCoverArt)
			entry = PlayListEntry.updateState(entry, state)
			return entry
		else:
			return PlayListEntry.get(ref, state, serviceHandler)

class Playlist(List):
	MAX_HISTORY_SIZE = 100

	REPEAT_NONE = 0
	REPEAT_SINGLE = 1
	REPEAT_ALL = 2

	FEATURE_LISTABLE = False

	listable = []

	def __init__(self, name, type, enableWrapAround=True, entryHelper=PlayListEntry):
		List.__init__(self, enableWrapAround=enableWrapAround, item_height=55, buildfunc=self._buildfunc)
		self._playing = -1
		self._list = []
		self._history = []
		self._lastPlayed = -1
		self.serviceHandler = eServiceCenter.getInstance()
		self._entryHelper = entryHelper

		self._name = name
		self._type = type
		self._valid = False
		self._shuffle = False
		self._repeat = self.REPEAT_NONE

		self.style = "default"

		if self.FEATURE_LISTABLE and not self.__class__ in Playlist.listable:
			Playlist.listable.append(self.__class__)

	def _buildfunc(self, ref, state, extra):
		return self._entryHelper.get(ref, state, extra)

	def toggleShuffle(self):
		self._shuffle = not self._shuffle
		return self._shuffle

	def repeat(self, repeat):
		self._repeat = repeat

	def clear(self):
		self.stop()
		self._list = []
		self.listChanged()

	def getSelection(self):
		service = self.current and self.current[0]
		if service:
			return service
		return None

	def add(self, ref, extra=None, isBatch=False):
		if extra is None:
			extra = self.serviceHandler
		self._list.append((ref, STATE_NONE, extra))
		if not isBatch:
			self.listChanged()

	def update(self, index, ref, extra=None):
		if extra is None:
			extra = self.serviceHandler
		if index < len(self._list):
			self._list[index] = (ref, STATE_NONE, extra)
			self.listChanged()

	def remove(self, index):
		if index is None:
			return
		if self._playing >= index:
			self._playing -= 1
		if self._list:
			del self._list[index]
		self.listChanged()

	def removeSelected(self):
		if self.index is None or not self._list:
			return False
		current = self.index == self._playing
		oldindex = self.index
		self.remove(self.index)
		self.index = oldindex
		return current

	def playSelected(self):
		return self.play(self.index)

	def playLast(self):
		return self.play(index=len(self) - 1)

	def _updateEntryState(self, entry, state):
		entry = list(entry)
		entry[1] = state
		return tuple(entry)

	def updateState(self, state):
		#cleanup icon for previously played item "lastplayed" if not done yet
		if self._lastPlayed != -1 and self._lastPlayed < len(self._list):
			entry = self._list[self._lastPlayed]
			if(entry[1] != STATE_NONE):
				entry = self._updateEntryState(entry, STATE_NONE)
				self.modifyEntry(self._lastPlayed, entry)
		#set icon for currently playing item if not done yet
		if self._playing != -1 and self._playing < len(self._list):
			entry = self._list[self._playing]
			if(entry[1] != state):
				entry = self._updateEntryState(entry, state)
				self.modifyEntry(self._playing, entry)

	def modifyEntry(self, index, data):
		self._list[index] = data
		List.modifyEntry(self, index, data)

	def play(self, index=-1, resume=False):
		if not resume:
			if index is -1:
				index = self.index
			if index < 0:
				return None
			self._lastPlayed = self._playing
			self._playing = index

		self.updateState(STATE_PLAY)
		return self.service

	def pause(self):
		self.updateState(STATE_PAUSE)

	def stop(self):
		self._playing = -1
		self._lastPlayed = -1
		self._history = []
		self.updateState(STATE_STOP)

	def next(self):
		#not playing atm
		if self._playing < 0 or len(self._list) < 2:
			return None

		#repeat single
		if self._repeat == self.REPEAT_SINGLE:
			self.stop()
			return self.play()

		index = self._playing + 1
		#everyday i'm shuffling!
		if self._shuffle:
			cntPlayed = 0
			if self._playing >= 0:
				self._history.append(self._playing)
				cntPlayed = len(self._history)
				if cntPlayed > self.MAX_HISTORY_SIZE:
					self._history.pop(0)

			cntTotal = len(self._list)
			cntUnplayed = cntTotal - cntPlayed
			playedLut = {}
			Log.i("total: %i, played: %i" % (cntTotal, cntPlayed))
			if cntUnplayed > 0:
				for h in self._history:
					playedLut[h] = True
			else:
				if self._repeat == self.REPEAT_ALL:
					self._history = []
					cntUnplayed = cntTotal
					cntPlayed = 0
				else:
					return None

			stepsize = 2 if (cntUnplayed > 1) else 1
			index = random.randrange(0, cntUnplayed, stepsize)
			while playedLut.get(index, False):
				index += 1
				if index > cntTotal - 1:
					index = 0
			return self.play(index)

		#no shuffle, just boring standard play
		if index >= len(self._list): #End of list?
			Log.i("index %s>=%s, self.repeat=%s" %(index, len(self._list), self._repeat))
			if self._repeat == self.REPEAT_ALL:
				index = 0
			else:
				return None
		return self.play(index)

	def prev(self):
		#not playing atm
		if self._playing < 0 or len(self._list) < 2:
			return None

		#Shuffling? Pop history as long as there is one!
		if self._shuffle:
			if len(self._history) > 0:
				return self.play( self._history.pop() )
			else:
				return None

		index = self._playing - 1
		if index < 0: #begin of list, wrap to end
			index = len(self._list) -1
		return self.play(index)

	def rewind(self):
		self.updateState(STATE_REWIND)

	def forward(self):
		self.updateState(STATE_FORWARD)

	def listChanged(self):
		self.list = self._list

	def getServiceIndex(self):
		return self._playing

	def getService(self):
		Log.i("self._playing=%s" % self._playing)
		if self._playing >= 0 and len(self.list) > self._playing:
			service = self._list[self._playing][0]
			if service:
				return service
		Log.w("NO SERVICE!")
		return None

	def _moveSelectedItem(self, newindex):
		self._list[newindex], self._list[self.index] = self._list[self.index], self._list[newindex]
		self.listChanged()
		self.index = newindex

	def moveSelectedUp(self):
		if len(self._list) <= 1:
			return
		if self.index > 0:
			newindex = self.index - 1
		else:
			newindex = len(self._list) - 1
		self._moveSelectedItem(newindex)

	def moveSelectedDown(self):
		if len(self._list) <= 1:
			return
		if self.index < len(self._list) - 1:
			newindex = self.index + 1
		else:
			newindex = 0
		self._moveSelectedItem(newindex)

	def moveUp(self):
		self.moveSelection("moveUp")

	def moveDown(self):
		self.moveSelection("moveDown")

	service = property(getService)

	def __len__(self):
		return len(self.list)

	def reload(self):
		pass

	def _getName(self):
		return self._name

	def _getType(self):
		return self._type

	def _isValid(self):
		return self._valid

	valid = property(_isValid)
	name = property(_getName)
	type = property(_getType)


	@staticmethod
	def getPlaylists(type=MediaCore.TYPE_AUDIO):
		"""getPlaylists has to be implemented in any subclass having FEATURE_LISTABLE set to true.
		It shall return all available playlists as a list of instantiated playlist objects for the specific implementation
		"""
		playlists = []
		for playlist in Playlist.listable:
			try:
				playlists.extend( playlist.getPlaylists(type=type) )
			except:
				raise NotImplementedError("%s has to implement @staticmethod getPlaylists(type={default}) if FEATURE_LISTABLE is set to True" %(playlist.__class__.__name__))
		return playlists
