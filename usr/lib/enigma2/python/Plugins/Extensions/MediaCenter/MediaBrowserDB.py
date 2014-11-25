from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, gFont, eServiceReference, eMediaDatabase, StringList

from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap

from MediaCore import MediaCore, mediaCore
from Tools.Log import Log
from MediaBrowser import MediaBrowser, MediaBrowserList

ITEM_KEY_HANDLE = "handle"
ITEM_KEY_TITLE = "__item_title"
ITEM_KEY_TYPE = "type"

ITEM_TITLE_ALL = "-- %s --" %_("All")

def DBEntryComponent(item, type=MediaBrowser.ITEM_TYPE_FOLDER):
	res = [ (item, True, type) ]
	res.append(MultiContentEntryText(pos=(35, 1), size=(570, 30), flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=item[ITEM_KEY_TITLE]))
	pixmap = MediaBrowser.ITEM_PIXMAPS.get(type, None)
	png = None
	if pixmap:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, pixmap))
	if png:
		res.append(MultiContentEntryPixmapAlphaBlend(pos=(10, 5), size=(20, 20), png=png))

	return res

#defines the required interface for navigation menu handles (see NavigationHandle and RootNavigationHandle for specific implementations
class MediaBrowserNavigationHandle(object):
	def __init__(self, fnc):
		self._fnc = fnc
		self._lastItem = None

	def isUpEntry(self, item):
		return False

	def isAllEntry(self, item):
		return False

	def hasAllHandle(self):
		return False

	def canAscend(self):
		return False

	def ascend(self, owner):
		return False

	def canDescend(self, item):
		raise NotImplementedError("[MediaBrowserNavigationHandle] Subclasses have to implement canDescend(self, item)")

	def descend(self, owner, item):
		raise NotImplementedError("[MediaBrowserNavigationHandle] Subclasses have to implement descend(self, owner, item)")

	def getItemTitle(self, item):
		raise NotImplementedError("[MediaBrowserNavigationHandle] Subclasses have to implement getItemTitle(self, item)")

	def getItems(self, item=None):
		raise NotImplementedError("[MediaBrowserNavigationHandle] Subclasses have to implement getItems(self, item)")

	def getAllItems(self, owner, item):
		raise NotImplementedError("[MediaBrowserNavigationHandle] Subclasses have to implement getAllItems(self) IF they return 'True' in hasAllHandle(self)")

	def getLastItem(self):
		return self._lastItem or {}

class NavigationHandle(MediaBrowserNavigationHandle):
	def __init__(self, listFnc, titleKeys=["title"]):
		MediaBrowserNavigationHandle.__init__(self, listFnc)
		self._descendHandle = None
		self._ascendHandle = None
		self._allItemHandle = None
		self._titleKeys = titleKeys

	def link(self, desc=None, asc=None, all=None):
		self._descendHandle = desc
		self._ascendHandle = asc
		self._allItemHandle = all

	def isUpEntry(self, item):
		return item and item.get(ITEM_KEY_TYPE, None) == MediaBrowser.ITEM_TYPE_UP

	def isAllEntry(self, item):
		return item and item.get(ITEM_KEY_TYPE, None) == MediaBrowser.ITEM_TYPE_ALL

	def hasAllHandle(self):
		return self._allItemHandle is not None

	def canAscend(self):
		return self._ascendHandle is not None

	def ascend(self, owner):
		if self._ascendHandle:
			owner.setNavHandle(self._ascendHandle)
			return self._ascendHandle.getItems()
		return False

	def canDescend(self, item):
		return self._descendHandle is not None

	def descend(self, owner, item):
		if self.isUpEntry(item):
			return self.ascend(owner)

		if self.isAllEntry(item):
			return self.getAllItems(owner, item)

		if self._descendHandle:
			owner.setNavHandle(self._descendHandle)
			return self._descendHandle.getItems(item)
		return False

	def getItemTitle(self, item):
		title = []
		for key in self._titleKeys:
			value = item.get(key, None)
			if value:
				title.append(value)
		if len(title) is 0:
			title = ["-- %s --" %_("Unknown")]
		return " - ".join(title)

	def getItems(self, item=None):
		if item is not None:
			self._lastItem = item
		self._fnc(self._lastItem)

	def getAllItems(self, owner, item):
		if self._allItemHandle:
			owner.setNavHandle(self._allItemHandle)
			return self._allItemHandle.getItems(item)
		return False

class RootNavigationHandle(MediaBrowserNavigationHandle):
	def __init__(self, fnc):
		MediaBrowserNavigationHandle.__init__(self, fnc)

	def canDescend(self, item):
		return True

	def descend(self, owner, item):
		handle = item[ITEM_KEY_HANDLE]
		owner.setNavHandle(handle)
		return handle.getItems(item)

	def getItemTitle(self, item):
		return item[ITEM_KEY_TITLE]

	def getItems(self, unused=None):
		return self._fnc(unused=unused)

class MediaBrowserDBList(MenuList, MediaBrowserList):
	def __init__(self, type):
		MenuList.__init__(self, [], True, eListboxPythonMultiContent)
		MediaBrowserList.__init__(self, type)

		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(30)
		self.l.setBuildFunc(self._buildListEntry)

		self._db = eMediaDatabase.getInstance()
		self._rootHandle = RootNavigationHandle(self._navRoot)

		if type == MediaCore.TYPE_AUDIO:
			#Artist -> Album -> Titles
			self._artistHandle = NavigationHandle(self.__getArtists, [eMediaDatabase.FIELD_ARTIST])
			self._artistAlbumHandle = NavigationHandle(self.__getAlbumsByArtist, [eMediaDatabase.FIELD_ARTIST, eMediaDatabase.FIELD_ALBUM])
			self._artistAllHandle = NavigationHandle(self.__filterByArtist, [eMediaDatabase.FIELD_ARTIST, eMediaDatabase.FIELD_ALBUM, eMediaDatabase.FIELD_TITLE])
			self._artistAlbumTitleHandle = NavigationHandle(self.__filterByArtistAlbum, [eMediaDatabase.FIELD_ARTIST, eMediaDatabase.FIELD_TITLE])

			self._artistHandle.link(desc=self._artistAlbumHandle, asc=self._rootHandle)
			self._artistAlbumHandle.link(desc=self._artistAlbumTitleHandle, asc=self._artistHandle, all=self._artistAllHandle)
			self._artistAllHandle.link(asc=self._artistAlbumHandle)
			self._artistAlbumTitleHandle.link(asc=self._artistAlbumHandle)

			#Album -> Titles
			self._albumHandle = NavigationHandle(self.__getAllAlbums, [eMediaDatabase.FIELD_ARTIST, eMediaDatabase.FIELD_ALBUM])
			self._albumTitleHandle = NavigationHandle(self.__filterByArtistAlbum, [eMediaDatabase.FIELD_ARTIST, eMediaDatabase.FIELD_TITLE])
			self._albumHandle.link(desc=self._albumTitleHandle, asc=self._rootHandle)
			self._albumTitleHandle.link(asc=self._albumHandle)

			#All
			self._allHandle = NavigationHandle(self.__getAll, [eMediaDatabase.FIELD_ARTIST, eMediaDatabase.FIELD_ALBUM, eMediaDatabase.FIELD_TITLE])
			self._allHandle.link(asc=self._rootHandle)

			#set navigation handle items
			self._navitems = [{
					ITEM_KEY_TITLE : _("Artists"),
					ITEM_KEY_HANDLE: self._artistHandle,
				},
				{
					ITEM_KEY_TITLE : _("Albums"),
					ITEM_KEY_HANDLE: self._albumHandle,
				},
				{
					ITEM_KEY_TITLE : _("All"),
					ITEM_KEY_HANDLE: self._allHandle,
				}]
		elif type == MediaCore.TYPE_VIDEO:
			self._recordingHandle = NavigationHandle(self.__getAllRecordings, [eMediaDatabase.FIELD_TITLE])
			self._allVideoHandle = NavigationHandle(self.__getAllVideos, [eMediaDatabase.FIELD_TITLE])
			self._unseenVideoHandle = NavigationHandle(self.__getUnseenVideos, [eMediaDatabase.FIELD_TITLE])
			self._hdVideoHandle = NavigationHandle(self.__getHDVideos, [eMediaDatabase.FIELD_TITLE])
			self._sdVideoHandle = NavigationHandle(self.__getSDVideos, [eMediaDatabase.FIELD_TITLE])

			self._recordingHandle.link(asc=self._rootHandle)
			self._allVideoHandle.link(asc=self._rootHandle)
			self._unseenVideoHandle.link(asc=self._rootHandle)
			self._hdVideoHandle.link(asc=self._rootHandle)
			self._sdVideoHandle.link(asc=self._rootHandle)

			self._navitems = [{
					ITEM_KEY_TITLE : _("Unseen"),
					ITEM_KEY_HANDLE: self._unseenVideoHandle,
				},
				{
					ITEM_KEY_TITLE : _("Recordings"),
					ITEM_KEY_HANDLE: self._recordingHandle,
				},
				{
					ITEM_KEY_TITLE : _("All Videos"),
					ITEM_KEY_HANDLE: self._allVideoHandle,
				},
				{
					ITEM_KEY_TITLE : _("Only HD"),
					ITEM_KEY_HANDLE: self._hdVideoHandle,
				},
				{
					ITEM_KEY_TITLE : _("Only SD"),
					ITEM_KEY_HANDLE: self._sdVideoHandle,
				},]

		self.__currentNavHandle = self._rootHandle
		self.__prevNavHandle = None
		self._currentHandleItem = None
		self.__getFolderContent = None

	def _navRoot(self, unused=None):
		self.__getFolderContent = None
		return self._setList(self._navitems)

	def __setCurrentNavHandle(self, handle):
		self.__prevNavHandle = self.__currentNavHandle
		self.__currentNavHandle = handle

	def __getCurrentNavHandle(self):
		return self.__currentNavHandle
	_currentNavHandle = property(__getCurrentNavHandle, __setCurrentNavHandle)

	def __getPrevNavHandle(self):
		return self.__prevNavHandle
	_prevNavHandle = property(__getPrevNavHandle)

	def _onShow(self):
		self._currentNavHandle.getItems()

	def _onClose(self):
		pass

	def _setList(self, l):
		lst = []
		prev_title = None
		if self._prevNavHandle:
			prev_title = self._prevNavHandle.getLastItem().get(ITEM_KEY_TITLE, None)
		restoreindex = 0
		idx = 0

		if self._currentNavHandle.canAscend():
			lst.append(({ITEM_KEY_TITLE : MediaBrowser.ITEM_TEXT_UP, ITEM_KEY_TYPE : MediaBrowser.ITEM_TYPE_UP}, MediaBrowser.ITEM_TYPE_UP))
			idx += 1

		if self._currentNavHandle.hasAllHandle():
			lastitem = self._currentNavHandle.getLastItem() or {}
			item = dict( lastitem.items() + {ITEM_KEY_TITLE : ITEM_TITLE_ALL, ITEM_KEY_TYPE : MediaBrowser.ITEM_TYPE_ALL}.items() )
			lst.append((item, MediaBrowser.ITEM_TYPE_FOLDER))
			if prev_title == ITEM_TITLE_ALL:
				restoreindex = idx
			idx += 1

		canDescend = self._currentNavHandle.canDescend(None)
		for item in l:
			item = dict(item)
			title = self._currentNavHandle.getItemTitle(item)
			item[ITEM_KEY_TITLE] = title

			if title == prev_title:
				restoreindex = idx

			if canDescend:
				item_type = MediaBrowser.ITEM_TYPE_FOLDER
			else:
				item_type = MediaBrowser.ITEM_TYPE_AUDIO

			lst.append((item, item_type))
			idx += 1
		self.l.setList(lst)
		self.moveToIndex(restoreindex)

	def _buildListEntry(self, item, item_type):
		return DBEntryComponent(item, item_type)

	def _processResult(self, res):
		if res and not res.error():
			data = res.data()
			self._setList(data)
			return
		elif res:
			Log.w("%s\n%s" %(res.errorDriverText(), res.errorDatabaseText()))
		self._setList([])

	def __getArtists(self, item):
		self.__getFolderContent = self.__filterByArtist
		res = self._db.getAllArtists()
		self._processResult(res)

	def __getAllAlbums(self, item):
		self.__getFolderContent = self.__filterByArtistAlbum
		res = self._db.getAllAlbums()
		self._processResult(res)

	def __getAlbumsByArtist(self, item):
		self.__getFolderContent = self.__filterByArtistAlbum
		artist = item.get(eMediaDatabase.FIELD_ARTIST)
		res = self._db.getAlbumsByArtist(artist)
		self._processResult(res)

	def __filterByArtistAlbum(self, item, only_get=False):
		self.__getFolderContent = None
		artist = item.get(eMediaDatabase.FIELD_ARTIST)
		album = item.get(eMediaDatabase.FIELD_ALBUM)
		res = self._db.filterByArtistAlbum(artist, album)
		if only_get:
			return res.data()
		self._processResult(res)

	def __filterByArtist(self, item, only_get=False):
		self.__getFolderContent = None
		artist = item.get(eMediaDatabase.FIELD_ARTIST)
		res = self._db.filterByArtist(artist)
		if only_get:
			return res.data()
		self._processResult(res)

	def __getAll(self, item):
		self.__getFolderContent = None
		res = self._db.getAllAudio()
		self._processResult(res)

	def __getAllVideos(self, item):
		self.__getFolderContent = None
		res = self._db.getAllVideos()
		self._processResult(res)

	def __getAllRecordings(self, item):
		self.__getFolderContent = None
		res = self._db.getAllRecordings()
		self._processResult(res)

	def __getUnseenVideos(self, item):
		self.__getFolderContent = None
		res = self._db.query("SELECT * from video WHERE lastplaypos=?;", StringList(["0"]))
		self._processResult(res)

	def __getHDVideos(self, item):
		self.__getFolderContent = None
		res = self._db.query("SELECT * from video WHERE hd=?;", StringList(["1"]))
		self._processResult(res)

	def __getSDVideos(self, item):
		self.__getFolderContent = None
		res = self._db.query("SELECT * from video WHERE hd=?;", StringList(["0"]))
		self._processResult(res)

	def setNavHandle(self, handle):
		self._currentNavHandle = handle

	def canDescend(self):
		item = self.getSelectedItem()
		return self._currentNavHandle.canDescend(item) or self._currentNavHandle.isUpEntry(item)

	def ascend(self):
		self._currentHandleItem = None
		return self._currentNavHandle.ascend(self)

	def descend(self):
		self._currentHandleItem = self.getSelectedItem()
		return self._currentNavHandle.descend(self, self._currentHandleItem)

	def getSelectedItem(self):
		item = self.l.getCurrentSelection()
		if item is None:
			return None
		return item[0]

	def getMeta(self, item):
		return self.getSelectedItem()

	def getItemName(self, item=None):
		if item is None:
			item = self.getSelectedItem()
		return self._currentNavHandle.getItemTitle(item)

	def getServiceRef(self, item=None):
		if item is None:
			item = self.getSelectedItem()
		if item is None:
			return eServiceReference()

		file = "%s/%s" %(item[eMediaDatabase.FIELD_PATH], item[eMediaDatabase.FIELD_FILENAME])
		ref = eServiceReference(4097, 0, file)
		ref.setName(item[eMediaDatabase.FIELD_TITLE])
		return ref

	def canAddSelected(self):
		item = self.getSelectedItem()
		canDescend = self.canDescend()
		retVal = canDescend and self.__getFolderContent is not None and not self._currentNavHandle.isAllEntry(item) and not self._currentNavHandle.isUpEntry(item)
		return retVal or not canDescend

	def getAllForSelected(self):
		if self.__getFolderContent is not None:
			return self.__getFolderContent(self.getSelectedItem(), only_get=True)
		else:
			return []

class MediaBrowserDB(MediaBrowser):
	FEATURE_FILTER_TYPE = True
	FEATURE_ADD_FOLDER = True
	FEATURE_SEARCH = True
	TITLE = _("Media Database Browser")

	def __init__(self, session, type=type, player=None):
		MediaBrowser.__init__(self, session, type, player=player)
		self._setList(MediaBrowserDBList(type=type))

	def addFolderToPlaylist(self, folder, recursive=True):
		Log.i("called")
		items = self._list.getAllForSelected()
		if not items:
			return False

		for item in items:
			item = dict(item)
			self.addToPlaylist(self._list.getServiceRef(item=item), item)
		return True

	def canAddSelected(self):
		return self._list.canAddSelected()

	@staticmethod
	def search(needle):
		db = eMediaDatabase.getInstance()
		res = db.filterAudio(needle, 0, 250)
		if res.error():
			return []
		items = []
		for item in res.data():
			filename = "%s/%s" %(item[eMediaDatabase.FIELD_PATH], item[eMediaDatabase.FIELD_FILENAME])
			ref = eServiceReference(4097, 0, filename)
			ref.setName("%s - %s" %(item[eMediaDatabase.FIELD_ARTIST], item[eMediaDatabase.FIELD_TITLE]))
			items.append( (ref.getName(), (ref, dict(item))) )
		return items

mediaCore.registerBrowser(MediaBrowserDB, _("Media Database"), MediaCore.TYPE_AUDIO)
mediaCore.registerBrowser(MediaBrowserDB, _("Media Database"), MediaCore.TYPE_VIDEO)
