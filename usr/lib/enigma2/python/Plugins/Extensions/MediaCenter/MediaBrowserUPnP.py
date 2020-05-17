from __future__ import absolute_import
from enigma import eListboxPythonMultiContent, gFont, eServiceReference, eMediaDatabase

from Components.MenuList import MenuList
from Tools.Log import Log

from skin import TemplatedListFonts, componentSizes

from Plugins.SystemPlugins.UPnP.UPnPBrowser import UPnPBrowser
from Plugins.SystemPlugins.UPnP.UPnPCore import Statics

from .MediaCore import MediaCore, mediaCore
from .MediaBrowser import MediaBrowser, MediaBrowserList, MediaBrowserEntryComponent
import six

def getItemTypeFromUPnP(itemtype):
	itemtype = {
		Statics.ITEM_TYPE_SERVER : MediaBrowser.ITEM_TYPE_FOLDER,
		Statics.ITEM_TYPE_CONTAINER : MediaBrowser.ITEM_TYPE_FOLDER,
		Statics.ITEM_TYPE_AUDIO : MediaBrowser.ITEM_TYPE_AUDIO,
		Statics.ITEM_TYPE_VIDEO : MediaBrowser.ITEM_TYPE_VIDEO,
		Statics.ITEM_TYPE_PICTURE : MediaBrowser.ITEM_TYPE_PICTURE,}.get(itemtype, None)

	return itemtype

""" Field Statics
eMediaDatabase.FIELD_PATH
eMediaDatabase.FIELD_FILENAME
eMediaDatabase.FIELD_SIZE
eMediaDatabase.FIELD_DURATION
eMediaDatabase.FIELD_POPULARITY
eMediaDatabase.FIELD_LASTPLAYPOS
eMediaDatabase.FIELD_LASTPLAYED
eMediaDatabase.FIELD_LASTMODIFIED
eMediaDatabase.FIELD_LASTUPDATED
eMediaDatabase.FIELD_TITLE
eMediaDatabase.FIELD_TRACK
eMediaDatabase.FIELD_TRACKS_TOTAL
eMediaDatabase.FIELD_DATE
eMediaDatabase.FIELD_COMMENT
eMediaDatabase.FIELD_ARTIST
eMediaDatabase.FIELD_ALBUM
eMediaDatabase.FIELD_GENRE
eMediaDatabase.FIELD_CODEC
eMediaDatabase.FIELD_CODEC_LONG
eMediaDatabase.FIELD_WIDTH
eMediaDatabase.FIELD_HEIGHT
eMediaDatabase.FIELD_FRAMERATE
eMediaDatabase.FIELD_HD
eMediaDatabase.FIELD_WIDESCREEN
eMediaDatabase.FIELD_RECORDING
eMediaDatabase.FIELD_PLAYLIST_NAME
eMediaDatabase.FIELD_FILE_URI
eMediaDatabase.FIELD_POS
"""

def upnpMeta2DBMeta(meta):
	mapping = {
		Statics.META_ALBUM : eMediaDatabase.FIELD_ALBUM,
		#Statics.META_ALBUM_ART_URI : Statics.META_ALBUM_ART_URI, #TODO
		Statics.META_ARTIST : eMediaDatabase.FIELD_ARTIST,
		#Statics.META_BITRATE : Statics.META_BITRATE, #TODO
		Statics.META_DATE : eMediaDatabase.FIELD_DATE,
		Statics.META_DURATION : eMediaDatabase.FIELD_DURATION,
		Statics.META_GENRE : eMediaDatabase.FIELD_GENRE,
		#Statics.META_METATYPE : Statics.META_METATYPE, #TODO
		#Statics.META_RESOLUTION : Statics.META_RESOLUTION, #CONVERSION required!
		Statics.META_SIZE : eMediaDatabase.FIELD_SIZE,
		Statics.META_TITLE : eMediaDatabase.FIELD_TITLE,
		Statics.META_URI : eMediaDatabase.FIELD_FILE_URI,
	}
	meta_db = {}
	for key, value in six.iteritems(meta):
		if key == Statics.META_RESOLUTION:
			try:
				width, height = value.split("x")
				meta_db[eMediaDatabase.FIELD_WIDTH] = width
				meta_db[eMediaDatabase.FIELD_HEIGHT] = height
			except:
				Log.w("'%s' is no valid resolution!" %(value))
		else:
			newkey = mapping.get(key, None)
			if newkey:
				meta_db[newkey] = value
	return meta_db


class MediaBrowserUPnPList(MenuList, MediaBrowserList):
	IS_ASYNC = True

	def __init__(self, type):
		MenuList.__init__(self, [], True, eListboxPythonMultiContent)
		MediaBrowserList.__init__(self, type)

		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		itemHeight = componentSizes.itemHeight(componentSizes.FILE_LIST, 30)
		self.l.setItemHeight(itemHeight)
		self.l.setBuildFunc(self._buildListEntry)

		self._browser = UPnPBrowser()
		self._browser.onMediaServerDetected.append(self._onMediaServerListChanged)
		self._browser.onMediaServerRemoved.append(self._onMediaServerListChanged)
		self._browser.onListReady.append(self._onListReady)
		self._browser.onBrowseError.append(self._onBrowseError)

	def _onShow(self):
		self._browser.browse()

	def _onListLoad(self):
		if self.IS_ASYNC:
			self.selectionEnabled(False)
			for fnc in self.onListLoad:
				fnc()

	def __onListReady(self):
		if self.IS_ASYNC:
			self.selectionEnabled(True)
			for fnc in self.onListReady:
				fnc()

	def _onClose(self):
		self._browser.onMediaServerDetected.remove(self._onMediaServerListChanged)
		self._browser.onMediaServerRemoved.remove(self._onMediaServerListChanged)
		self._browser.onListReady.remove(self._onListReady)
		self._browser.onBrowseError.remove(self._onBrowseError)

	def _onBrowseError(self, error):
		Log.w(error)
		self.__onListReady()

	def canDescend(self):
		item = self.getSelectedItem()
		if not item:
			return False
		if item == MediaBrowser.ITEM_TYPE_UP:
			return True
		return self._browser.canDescend(item)

	def descend(self):
		item = self.getSelectedItem()
		if not item:
			return False
		if item == MediaBrowser.ITEM_TYPE_UP and self._browser.canAscend():
			self._onListLoad()
			self._browser.ascend()
			return True
		if self.canDescend():
			self._onListLoad()
			self._browser.descend(item)
			return True
		return False

	def isValidType(self, item):
		if item == MediaBrowser.ITEM_TYPE_UP or item is None:
			return False
		type = self._browser.getItemMetadata(item)[Statics.META_TYPE]
		if self._type == MediaCore.TYPE_AUDIO and type != Statics.ITEM_TYPE_AUDIO:
			return False
		if self._type == MediaCore.TYPE_VIDEO and type != Statics.ITEM_TYPE_VIDEO:
			return False
		return True

	def _onMediaServerListChanged(self, udn, client=None):
		#If we cannot ascend anymore we are showing the server list
		#that's the only point where we want to react immediately on server list updates
		if not self._browser.canAscend():
			self._browser.refresh()

	def _buildListEntry(self, item, *args):
		if item == MediaBrowser.ITEM_TYPE_UP:
			return MediaBrowserEntryComponent( None, MediaBrowser.ITEM_TEXT_UP, MediaBrowser.ITEM_TYPE_UP)
		return MediaBrowserEntryComponent( item, self._browser.getItemTitle(item), getItemTypeFromUPnP(self._browser.getItemType(item)) )

	def _onListReady(self, items):
		self.__onListReady()

		l = []
		if self._browser.canAscend():
			l.append( (MediaBrowser.ITEM_TYPE_UP,) )
		for item in items:
			l.append((item,))
		self.l.setList(l)
		if len(items) > 1:
			self.moveToIndex(1)
		else:
			self.moveToIndex(0)

	def getSelectedItem(self):
		item = self.l.getCurrentSelection()
		if item is None:
			return None
		return item[0]

	def getMeta(self, item):
		return upnpMeta2DBMeta(self._browser.getItemMetadata(item))

	def getItemName(self, item=None):
		if not item:
			item = self.getSelectedItem()
		if item:
			if item == MediaBrowser.ITEM_TYPE_UP:
				return MediaBrowser.ITEM_TEXT_UP
			meta = self._browser.getItemMetadata(item)
			return meta[Statics.META_TITLE]
		return "--- error getting item name ---"

	def getServiceRef(self):
		item = self.getSelectedItem()
		if item is None:
			return eServiceReference()

		meta = self._browser.getItemMetadata(item)
		filename = meta[Statics.META_URI]
		if filename.endswith('.ts'):
			ref = eServiceReference(eServiceReference.idDVB,0,filename)
		elif filename.endswith('.m2ts'):
			ref = eServiceReference(3,0,filename)
		else:
			ref = eServiceReference(eServiceReference.idGST,0,filename)
		ref.setName(meta[Statics.META_TITLE])
		return ref

class MediaBrowserUPnP(MediaBrowser):
	FEATURE_FILTER_TYPE = True
	FEATURE_ASYNC = True
	TITLE = _("UPnP/DLNA Browser")

	def __init__(self, session, type=type, player=None):
		MediaBrowser.__init__(self, session, type, player=player)
		self._setList(MediaBrowserUPnPList(type=type))

	def canAddSelected(self):
		return self._list.isValidType(self._list.getSelectedItem())

mediaCore.registerBrowser(MediaBrowserUPnP, _("DLNA / UPnP"), MediaCore.TYPE_AUDIO_VIDEO)
