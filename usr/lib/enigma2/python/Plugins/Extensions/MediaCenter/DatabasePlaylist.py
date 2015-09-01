from enigma import eMediaDatabase, eServiceReference, StringMap, StringMapVector
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Tools.Log import Log

from MediaCore import MediaCore
from Playlist import Playlist, PlayListEntry, AudioPlaylistEntry, DefaultCoverArt

from os import path as os_path

class DatabasePlaylistEntry(PlayListEntry):
	@staticmethod
	def get(ref, state, data):
		artist = data.get(eMediaDatabase.FIELD_ARTIST, "")
		title = data.get(eMediaDatabase.FIELD_TITLE, "")
		album = data.get(eMediaDatabase.FIELD_ALBUM, "")
		seconds = int(data.get(eMediaDatabase.FIELD_DURATION, 0))
		cover_art_id = int(data.get(eMediaDatabase.FIELD_COVER_ART_ID, 0))
		cover_art = DefaultCoverArt
		cover = None
		if cover_art_id:
			cover = eMediaDatabase.getInstance().getCoverArt(cover_art_id)
		if cover:
			cover_art = cover

		if seconds > 0:
			minutes, seconds = divmod(seconds, 60)
			duration = "%02d:%02d" % (minutes, seconds)
		else:
			duration = "--:--"

		entry = (data, "", title, artist, album, duration, cover_art)
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
		path = ref.getPath()
		#if we get only a reference or an entry with "extra data" but no file id yet we ask the database to enrich the data
		if path.startswith("/"):
			Log.i("Asking database for details!")
			db = eMediaDatabase.getInstance()
			res = db.getFileByPath(path)
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
				if file_uri.endswith('.ts'):
					ref = eServiceReference(1, 0, file_uri)
				elif file_uri.endswith('.m2ts'):
					ref = eServiceReference(3, 0, file_uri)
				else:
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
		#if self._id <= 0:
		data = res.data()
		self._id = -1
		if data and len(data) > 0:
			self._id = int(res.data()[0].get(eMediaDatabase.FIELD_ID, -1))
		if self._id == -1:
			error = True
		self._valid = not error
		if not error:
			Log.i("Playlist '%s (%s)' saved" %(self._name, self._id))
		else:
			Log.w("Error saving playlist!")
		return not error

	def _getId(self):
		return self._id
	id = property(_getId)