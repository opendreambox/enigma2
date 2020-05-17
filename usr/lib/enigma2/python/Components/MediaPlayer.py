from __future__ import absolute_import
from Components.MenuList import MenuList

from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from os import path

from enigma import eListboxPythonMultiContent, RT_VALIGN_CENTER, gFont, eServiceCenter

from Tools.LoadPixmap import LoadPixmap
from skin import TemplatedListFonts, componentSizes

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
ForwardIcon = LoadPixmap(path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_forward.png"))

def PlaylistEntryComponent(serviceref, state):
	sizes = componentSizes[PlayList.SKIN_COMPONENT_KEY]
	iconWidth = sizes.get(PlayList.SKIN_COMPONENT_ICON_WIDTH, 20)
	iconHeight = sizes.get(PlayList.SKIN_COMPONENT_ICON_HEIGHT, 16)
	iconHPos = sizes.get(PlayList.SKIN_COMPONENT_ICON_HPOS, 3)
	configEntryWidth = sizes.get(componentSizes.ITEM_WIDTH, 1000)
	configEntryHeight = sizes.get(componentSizes.ITEM_HEIGHT, 22)

	res = [ serviceref ]
	text = serviceref.getName()
	if text is "":
		text = path.split(serviceref.getPath().split('/')[-1])[1]
		if len(text) == 0:
			text = serviceref.getPath()
	res.append((eListboxPythonMultiContent.TYPE_TEXT,iconWidth, 0, configEntryWidth, configEntryHeight, 0, RT_VALIGN_CENTER, text))
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

	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 2, iconHPos, iconWidth,iconHeight, png))

	return res

class PlayList(MenuList):
	SKIN_COMPONENT_KEY = "MediaplayerPlayList"
	SKIN_COMPONENT_ICON_HEIGHT = "iconHeight"
	SKIN_COMPONENT_ICON_WIDTH = "iconWidth"
	SKIN_COMPONENT_ICON_HPOS = "iconHPos"

	def __init__(self, enableWrapAround = False):
		MenuList.__init__(self, [], enableWrapAround, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 23))
		self.currPlaying = -1
		self.oldCurrPlaying = -1
		self.serviceHandler = eServiceCenter.getInstance()

	def clear(self):
		del self.list[:]
		self.l.setList(self.list)
		self.currPlaying = -1
		self.oldCurrPlaying = -1

	def getSelection(self):
		return self.l.getCurrentSelection()[0]

	def addFile(self, serviceref):
		self.list.append(PlaylistEntryComponent(serviceref, STATE_NONE))

	def updateFile(self, index, newserviceref):
		if index < len(self.list):
		    self.list[index] = PlaylistEntryComponent(newserviceref, STATE_NONE)

	def deleteFile(self, index):
		if self.currPlaying >= index:
			self.currPlaying -= 1
		del self.list[index]

	def setCurrentPlaying(self, index):
		self.oldCurrPlaying = self.currPlaying
		self.currPlaying = index
		self.moveToIndex(index)

	def updateState(self, state):
		if len(self.list) > self.oldCurrPlaying and self.oldCurrPlaying != -1:
			self.list[self.oldCurrPlaying] = PlaylistEntryComponent(self.list[self.oldCurrPlaying][0], STATE_NONE)
		if self.currPlaying != -1 and self.currPlaying < len(self.list):
			self.list[self.currPlaying] = PlaylistEntryComponent(self.list[self.currPlaying][0], state)
		self.updateList()

	def playFile(self):
		self.updateState(STATE_PLAY)

	def pauseFile(self):
		self.updateState(STATE_PAUSE)
		
	def stopFile(self):
		self.updateState(STATE_STOP)

	def rewindFile(self):
		self.updateState(STATE_REWIND)

	def forwardFile(self):
		self.updateState(STATE_FORWARD)

	def updateList(self):
		self.l.setList(self.list)

	def getCurrentIndex(self):
		return self.currPlaying

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and self.serviceHandler.info(l[0]).getEvent(l[0])

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	def getServiceRefList(self):
		return [ x[0] for x in self.list ]

	def __len__(self):
		return len(self.list)
