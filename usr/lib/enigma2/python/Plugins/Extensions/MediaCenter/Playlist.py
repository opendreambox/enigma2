from enigma import eServiceReference, eServiceCenter, iServiceInformation, eMediaDatabase, StringMap, StringMapVector

from Components.Sources.List import List
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
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

class DatabasePlaylistEntry(PlayListEntry):
	@staticmethod
	def get(ref, state, data):
		artist = data.get(eMediaDatabase.FIELD_ARTIST, "")
		title = data.get(eMediaDatabase.FIELD_TITLE, "")
		album = data.get(eMediaDatabase.FIELD_ALBUM, "")
		seconds = int(data.get(eMediaDatabase.FIELD_DURATION, 0))

		if seconds > 0:
			minutes, seconds = divmod(seconds, 60)
			duration = "%02d:%02d" % (minutes, seconds)
		else:
			duration = "--:--"

		entry = (data, "", title, artist, album, duration, DefaultCoverArt)
		entry = AudioPlaylistEntry.updateState(entry, state)

		return entry

class DatabasePlaylist(Playlist):
	FEATURE_LISTABLE = True

	class PlaylistChoice(ChoiceBox):
		def __init__(self, session, type=MediaCore.TYPE_AUDIO):
			menu = []
			playlists = DatabasePlaylist.getPlaylists(type)
			for playlist in playlists:
				menu.append( (playlist.name, playlist) )
			ChoiceBox.__init__(self, session, list=menu)
			self.setTitle(_("Playlists"))

	class PlaylistCreate:
		def __init__(self, session, type, callback):
			self._callback = callback
			self._type = type
			inputbox = session.openWithCallback(self._onInput, InputBox, title="Playlist name")
			inputbox.setTitle("Create New Playlist")

		def _onInput(self, name):
			Log.i(name)
			if name != None:
				p = DatabasePlaylist.create(name, type=self._type)
				self._callback(p)

	def __init__(self, id, name=_("Default"), type=MediaCore.TYPE_AUDIO, enableWrapAround=True, entryHelper=DatabasePlaylistEntry):
		Playlist.__init__(self, name, type, enableWrapAround=enableWrapAround, entryHelper=entryHelper)
		self._id = id

	@staticmethod
	def getPlaylists(type=MediaCore.TYPE_AUDIO):
		Log.i("")
		res = eMediaDatabase.getInstance().getPlaylists(type)
		playlists = []
		if res:
			for item in res.data():
				playlists.append((
					DatabasePlaylist( int(item[eMediaDatabase.FIELD_ID]), name=item[eMediaDatabase.FIELD_PLAYLIST_NAME], type=int(item[eMediaDatabase.FIELD_TYPE]) )
				))
		return playlists

	@staticmethod
	def get(id=-1, name=None, type=MediaCore.TYPE_AUDIO, create=False):
		# If we'er called with only the name given we'll try to get the id.
		# If we cannot find a matching playlist, we return None
		db = eMediaDatabase.getInstance()
		if id < 0:
			res = db.getPlaylistByName(name, type)
		else:
			res = db.getPlaylist(id)
		if res.error() or not res.data(): #Playlist unkown (not yet saved/created!)
			Log.w("%s / %s" %(res.errorDatabaseText(), res.errorDriverText()))
			if create:
				Log.i("creating new playlist")
				return DatabasePlaylist.create(name, type)
			else:
				Log.w("Unkown Playlist for id=%s, name=%s and type=%s" %(id, name, type))
				return None

		data = res.data()[0]
		id = int(data[eMediaDatabase.FIELD_ID])
		name = data[eMediaDatabase.FIELD_NAME]
		Log.i("Playlist %s found. Id is %s" %(name, id))
		playlist = DatabasePlaylist(id, name=name, type=type)
		playlist.reload()
		return playlist

	@staticmethod
	def create(name, type=MediaCore.TYPE_AUDIO):
		Log.i("name=%s, type=%s" %(name, type))
		db = eMediaDatabase.getInstance()
		res = db.getPlaylistByName(name, type)
		if not res or res.error() or res.data():
			Log.w("%s / %s / %s" %(res.data(), res.errorDatabaseText(), res.errorDriverText()))
			return None

		playlist = DatabasePlaylist(-1, name=name, type=type)
		playlist.save()
		return playlist

	def add(self, ref, extra=None, isBatch=False):
		data = extra
		if extra is None or extra.get(eMediaDatabase.FIELD_FILE_ID, 0) <= 0:
			data = self.getDetailsByRef(ref) or data
		if data is None:
			path, filename = os_path.split(ref.getPath())
			data = { "file_uri" : ref.getPath(), "title" : filename, }
		Playlist.add(self, ref, data, isBatch)

	def getDetailsByRef(self, ref):
		path, filename = os_path.split(ref.getPath())
		#if we get only a reference or an entry with "extra data" but no file id yet we ask the database to enrich the data
		if path.startswith("/"):
			Log.i("Asking database for details!")
			if path.endswith("/"):
				path = path[0:len(path)-1]
			db = eMediaDatabase.getInstance()
			res = db.getFileByPath(path, filename)
			if res and res.data() and not res.error() :
				return dict(res.data()[0])
			else:
				Log.i("ERROR: %s :: %s" %(res.errorDatabaseText(), res.errorDriverText()))
		else:
			Log.i("%s is not an absolute local path, skip querying the database" % path)

		return None

	def load(self, id, name):
		Log.i("Loading playlist with id=%s and name=%s" %(id, name))
		self._id = id
		self._name = name
		self.reload()

	def reload(self):
		self._list = []
		db = eMediaDatabase.getInstance()
		res = None
		if self._id < 0: #no @staticmethod get() used, probably....
			self._valid = False
			self.listChanged()
			Log.w("A Playlist with the name/id %s/%s does not exist!" %(self._name, self._id))
			return

		res = db.getPlaylistItemsById(self._id)
		if res and not res.error():
			for data in res.data():
				data = dict(data)
				file_uri = data.get(eMediaDatabase.FIELD_FILE_URI, None)
				if not file_uri:
					Log.w("Playlist entry invalid, %s" % data)
					continue
				ref = eServiceReference(4097, 0, file_uri)
				self.add(ref, data, True)
			self._valid = True
		else:
			Log.i("Error loading playlist %s:%s\n%s\n%s" % (self._id, self._name, res.errorDatabaseText(), res.errorDriverText()))
			self._valid = False
		self.listChanged()

	def save(self):
		#c-ify
		vector = StringMapVector()
		pos = 1
		for item in self._list:
			item = item[2]
			stringMap = StringMap()
			for k, v in item.iteritems():
				stringMap[k] = str(v)
			stringMap[eMediaDatabase.FIELD_POS] = str(pos)
			pos += 1
			vector.append(stringMap)
		db = eMediaDatabase.getInstance()
		res = db.savePlaylist(self._id, self._name, self._type, vector)
		error = res.error()
		if error:
			Log.w("Error saving playlist %s\n%s\n%s" % (self._id, res.errorDatabaseText(), res.errorDriverText()))
			return not error
		if self._id < 0:
			self._id = res.lastInsertId()

		self._valid = not error
		if not error:
			Log.i("Playlist '%s (%s)' saved" %(self._name, self._id))
		return not error

	def _getId(self):
		return self._id
	id = property(_getId)