# -*- coding: UTF-8 -*-
from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label, MultiColorLabel
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Components.Sources.Boolean import Boolean
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from skin import componentSizes

from MediaCore import MediaCore

from Tools.Log import Log
from Components.Sources.StaticText import StaticText

class MediaBrowser(Screen):
	ITEM_TYPE_FOLDER = 0
	ITEM_TYPE_AUDIO = 1
	ITEM_TYPE_VIDEO = 2
	ITEM_TYPE_PICTURE = 3
	ITEM_TYPE_UP = 1000
	ITEM_TYPE_ALL = 1001

	ITEM_TEXT_UP = _("[up]")

	ITEM_PIXMAPS = 	{
		ITEM_TYPE_FOLDER: "extensions/directory.png",
		ITEM_TYPE_AUDIO: "extensions/music.png",
		ITEM_TYPE_VIDEO: "extensions/movie.png"
	}

	IS_DIALOG = True

	FEATURE_FILTER_TYPE = False
	FEATURE_ADD_FOLDER = False
	FEATURE_SEARCH = False
	TITLE = _("Browser")

	skin = """
		<screen name="MediaBrowser" position="center,120" size="820,520" title="Browser">
			<widget name="list" position="10,5" size="800,420" enableWrapAround="1" scrollbarMode="showOnDemand"/>
			<eLabel backgroundColor="grey" position="10,430" size="800,1" />
			<widget name="status" position="10,440" size="800,20" font="Regular;18" halign="left" foregroundColors="white,white,white" backgroundColors="background,#1f771f,#9f1313"/>
			<eLabel backgroundColor="grey" position="10,470" size="800,1" />
			<ePixmap pixmap="skin_default/buttons/button_off.png" zPosition="1" position="10,490" size="20,20" />
			<widget source="button_green" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_green.png" position="10,490" size="20,20">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="add" position="40,480" size="200,40" font="Regular;18" halign="left" valign="center">
			</widget>
			<ePixmap pixmap="skin_default/buttons/button_off.png" zPosition="1" position="240,490" size="20,20"  />
			<widget source="button_blue" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_blue.png" position="240,490" size="20,20">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="add_and_play" position="270,480" size="400,40" font="Regular;18" halign="left" valign="center"/>
		</screen>"""

	def __init__(self, session, type=MediaCore.TYPE_AUDIO, player=None):
		Screen.__init__(self, session)
		self.skinName = "MediaBrowser"

		self._player = player
		self._type = type
		if type == MediaCore.TYPE_AUDIO:
			self.title = "%s - %s" % (self.TITLE, _("Music"))
		elif type == MediaCore.TYPE_VIDEO:
			self.title = "%s - %s" % (self.TITLE, _("Video"))
		else:
			self.title = self.TITLE
		self.setTitle(self.title)

		self._list = None

		self["button_green"] = Boolean(False)
		self["button_blue"] = Boolean(False)

		self["add"] = Label(_("Add"))
		self["add_and_play"] = Label(_("Add & play"))
		self["status"] = MultiColorLabel("")
		self._summary_list = StaticText("")
		self["summary_list"] = self._summary_list

		self["actions"] = ActionMap(["ListboxActions", "OkCancelActions", "ColorActions"],
		{
			"ok" : self.ok,
			"cancel" : self._close,
			"green" : self.addCurrentToPlaylist,
			"blue" : self.addAndPlaySelected
		}, -99);

		self._loadMessageBox = None

		self.onFirstExecBegin.append(self.__onFirstExecBegin)

	def _setList(self, lst):
		self._list = lst
		self["list"] = self._list

	def _close(self):
		self._list.onParentClose()
		self.close()

	def __onFirstExecBegin(self):
		self._list.onParentShow()
		if not self._selectionChanged in self._list.onSelectionChanged:
			self._list.onSelectionChanged.append(self._selectionChanged)
		self._selectionChanged()

		if self._list.IS_ASYNC:
			self._list.onListLoad.append(self._onListLoad)
			self._list.onListReady.append(self._onListReady)

	def _onListLoad(self):
		self._loadMessageBox = self.session.open(MessageBox, _("Loading data. Please wait"), title=_("Loading..."), type=MessageBox.TYPE_INFO)

	def _onListReady(self):
		if self._loadMessageBox:
			self._loadMessageBox.close()
			self._loadMessageBox = None

	def ok(self):
		if self._list.canDescend():
			self._list.descend()
		else:
			self.addCurrentToPlaylist()

	def _setButtonsEnabled(self, enabled):
		self["button_green"].setBoolean(enabled)
		self["button_blue"].setBoolean(enabled)

	def _selectionChanged(self):
		self._setButtonsEnabled( self.canAddSelected() )
		item = self._list.getSelectedItem()
		if item:
			self._summary_list.text = self.getItemName(item)

	def getSelectedItemData(self):
		item = self._list.getSelectedItem()
		if not item:
			return None, None, None, None
		itemName = self._list.getItemName()
		ref = self._list.getServiceRef()
		extra = self._list.getMeta(item)

		return item, itemName, ref, extra

	def getItemName(self, item=None):
		return self._list.getItemName(item)

	def addAndPlaySelected(self):
		return self.addCurrentToPlaylist(play=True)

	def addCurrentToPlaylist(self, play=False):
		Log.i("called")
		if self.canAddSelected():
			if self._list.canDescend():
				folder = self._list.getSelectedItem()
				if self.addFolderToPlaylist(folder):
					self.setStatus(self.getItemName(folder))
					return True
				else:
					self.setStatus(self.getItemName(folder), error=True)
			else:
				item, itemName, ref, extra = self.getSelectedItemData()
				if not item:
					self.setStatus(_("Nothing to add..."))
				else:
					if self._list.isValidType(item):
						if play:
							fnc = self.addAndPlay
						else:
							fnc = self.addToPlaylist
						if fnc(ref, extra):
							self.setStatus(itemName)
							return True
						else:
							self.setStatus(itemName, error=True)
					else:
						if self._type == MediaCore.TYPE_AUDIO:
							self.setStatus(_("Cannot add this file. It's not audio!"), error=True)
						if self._type == MediaCore.TYPE_VIDEO:
							self.setStatus(_("Cannot add this file. It's no video!"), error=True)
		return False

	def setStatus(self, item, error=False):
		if error:
			self["status"].setText(_("ERROR: Cannot add '%s'") % item)
			self["status"].setForegroundColorNum(2)
			self["status"].setBackgroundColorNum(2)
		else:
			self["status"].setText(_("Added '%s'") % item)
			self["status"].setForegroundColorNum(1)
			self["status"].setBackgroundColorNum(1)

	def addToPlaylist(self, ref, extra=None):
		if ref and ref.valid():
			self._player.addToPlaylist(ref, extra)
			return True
		else:
			Log.i("ERROR: No valid ref!")
			return False

	def addAndPlay(self, ref, extra=None):
		if ref and ref.valid():
			self._player.addAndPlay(ref, extra)
		else:
			Log.i("ERROR: No valid ref!")
			return False
		self._close()
		return True

	def canAddSelected(self):
		return not self._list.canDescend() or self.FEATURE_ADD_FOLDER

	def addFolderToPlaylist(self, folder, recursive=True):
		return False

	@staticmethod
	def search(needle):
		raise NotImplementedError("[MediaBRowser] Subclass has FEATURE_SEARCH=True but not implementation of @staticmethod search(needle)")

class MediaBrowserList(object):
	IS_ASYNC = False

	def __init__(self, type):
		self._type = type
		self.onListLoad = []
		self.onListReady = []

	def onParentShow(self):
		self._onShow()

	def onParentClose(self):
		self._onClose()

	def getSelectedItem(self):
		item = self.l.getCurrentSelection()
		if item is None:
			return None
		return item[0][0]

	def isValidType(self, item):
		return True

	def _onShow(self):
		Log.i("Subclass of MediaBrowserList has no implementation of _onShow")

	def _onClose(self):
		Log.i("Subclass of MediaBrowserList has no implementation of _onClose")

	def canDescend(self):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement canDescend(self, item)")

	def descend(self):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement descend(self, item)")

	def moveToIndex(self, idx):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement moveToIndex(self, idx)")

	def pageUp(self):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement pageUp(self)")

	def pageDown(self):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement pageDown(self)")

	def getMeta(self, item):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement getMeta(self, item)")

	def getItemName(self, item=None):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement getItemName(self)")

	def getServiceRef(self, item=None):
		raise NotImplementedError("[MediaBrowserList] Subclasses have to implement getServiceRef(self, item=None)")

def MediaBrowserEntryComponent(item, title, type=MediaBrowser.ITEM_TYPE_FOLDER):
	res = [ (item, True, type) ]

	sizes = componentSizes[componentSizes.FILE_LIST]
	tx = sizes.get("textX", 35)
	ty = sizes.get("textY", 0)
	tw = sizes.get("textWidth", 1000)
	th = sizes.get("textHeight", 25)
	pxw = sizes.get("pixmapWidth", 20)
	pxh = sizes.get("pixmapHeight", 20)

	res.append(MultiContentEntryText(pos=(tx, ty), size=(tw, th), flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=title))
	pixmap = MediaBrowser.ITEM_PIXMAPS.get(type, None)
	png = None
	if pixmap:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, pixmap))
	if png:
		res.append(MultiContentEntryPixmapAlphaBlend(pos=(10, (th-pxh)/2), size=(pxw, pxh), png=png))

	return res
