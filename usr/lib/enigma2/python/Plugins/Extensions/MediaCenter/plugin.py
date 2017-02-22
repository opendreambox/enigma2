# -*- coding: UTF-8 -*-
from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List

from Tools.Directories import resolveFilename, pathExists, SCOPE_PLUGINS, SCOPE_CURRENT_SKIN
from Tools.Log import Log

from AudioPlayer import AudioPlayer
from VideoPlayer import VideoPlayer
from Helpers import EasyPixmap
from MediaCore import MediaCore, mediaCore

class MediaCenterMenuSummary(Screen):
	skin = ("""
	<screen name="MediaCenterMenuSummary" position="0,0" size="132,64" id="1">
		<widget source="Title" render="Label" position="6,0" size="120,32" font="Display;15" halign="center" valign="top"/>
		<widget source="parent.menulist" render="Label" position="6,32" size="120,32" font="Display;16" halign="center" valign="center">
			<convert type="StringListSelection" />
		</widget>
	</screen>""",
	"""<screen name="MediaCenterMenuSummary" position="0,0" size="96,64" id="2">
		<widget source="Title" render="Label" position="0,0" size="96,32" font="Display;14" halign="center" valign="top"/>
		<widget source="parent.menulist" render="Label" position="0,32" size="96,32" font="Display;16" halign="center" valign="center">
			<convert type="StringListSelection" />
		</widget>
	</screen>
	""")

	def __init__(self, session, parent, windowTitle=_("MediaCenter")):
		Screen.__init__(self, session, parent, windowTitle)

class MainMenu(Screen):
	icon_path = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaCenter/icons/")

	skin = """
			<screen name="MainMenu" position="center,120" size="720,520" title="MediaCenter Menu">
				<ePixmap position="10,5" size="300,500" pixmap="skin_default/menu.png" zPosition="-1"/>
				<widget name="header" position="320,10" size="390,50" halign="center" font="Regular;45" transparent="1"/>
				<eLabel position="330,65" size="370,2" backgroundColor="grey" />
				<widget name="subheader" position="30,350" size="260,70" halign="center" valign="center" font="Regular;26" backgroundColor="background" transparent="1"/>
				<widget source="menulist" render="Listbox" position="320,100" size="390,450" enableWrapAround="1" scrollbarMode="showOnDemand">
					<convert type="TemplatedMultiContent">
						{"template": [
								MultiContentEntryText(pos = (5,0), size = (640,45), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 0), # index 0 is the name
							],
						"fonts": [gFont("Regular", 30)],
						"itemHeight": 45
						}
					</convert>
				</widget>
				<widget name="menuIcon" position="65,50" size="192,192" alphatest="on" />
				<ePixmap pixmap="skin_default/icons/dmm_logo.png" position="20,470" size="280,17" alphatest="on" />
			</screen>
		"""

	def __init__(self, session, type=None, playlist=None):
		Screen.__init__(self, session)
		self.session = session

		self.list = []
		self["menuIcon"] = EasyPixmap(cached=True)
		self["menulist"] = List(self.list, True)
		self["header"] = Label(_("MediaCenter"))
		self["subheader"] = Label(_("Video, audio and pictures"))

		self["actions"] = ActionMap(["WizardActions", "MenuActions"],
			{	"ok" : self.ok,
				"back" : self._close,
				"up" : self.up,
				"down" : self.down,
				"menu" : self.menu
			}, -1);

		self.onFirstExecBegin.append(self._onFirstExecBegin)
		self.onShown.append(self._onItemChanged)

		self.type = type
		self.playlist = playlist
		if self.type != None and self.playlist != None:
			self.onShown.append(self.runOnFirstExec)

	def menu(self):
		try:
			from Plugins.SystemPlugins.MediaDatabaseManager.MediaDatabaseManager import MediaDatabaseManager
			self.session.open(MediaDatabaseManager)
		except:
			pass

	def createSummary(self):
		return MediaCenterMenuSummary

	def runOnFirstExec(self):
		self["menulist"].setIndex(self.type)

		playlist = self.playlist
		self.type = None
		self.playlist = None

		i = 0
		for fnc in self.onShown:
			if fnc == self.runOnFirstExec:
				self.onShown.pop(i)
			i = i + 1

		self.ok(playlist)

	def _onFirstExecBegin(self):
		l = mediaCore.getMainMenuItems()
		self.list = l
		self["menulist"].setList(l)
		self["menulist"].setIndex(0)

	def ok(self, playlist=None):
		choice = self["menulist"].getCurrent()
		if choice != None:
			if choice[2].get("featuresPlaylist", False):
				self.session.open(choice[1], playlist)
			else:
				self.session.open(choice[1])

	def _close(self):
		self.close()

	def _onItemChanged(self):
		if self.list and len(self.list) > 0:
			choice = self["menulist"].getCurrent()

			iconPath = choice[2].get("icon", None)
			if iconPath is not None:
				self["menuIcon"].setPicturePath(iconPath)
			else:
				self["menuIcon"].setDefaultPicture()

	def up(self):
		self["menulist"].selectPrevious()
		self._onItemChanged()

	def down(self):
		self["menulist"].selectNext()
		self._onItemChanged()

def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath
	mediatypes = [
		Scanner(mimetypes=["video/mpeg", "video/MP2T", "video/x-msvideo", "video/x-matroska"],
			paths_to_scan=
				[
					ScanPath(path="", with_subdirs=False),
				],
			name="MediaCenter Movies",
			description=_("View Movies... (MediaCenter)"),
			openfnc=filescan_open_video,
		),
		Scanner(mimetypes=["audio/mpeg", "audio/x-wav", "application/ogg", "audio/x-flac", "audio/x-matroska"],
			paths_to_scan=
				[
					ScanPath(path="", with_subdirs=False),
				],
			name="MediaCenter Music",
			description=_("Play Music... (MediaCenter)"),
			openfnc=filescan_open_audio,
		)]
	return mediatypes

def filescan_open_video(filelist, session, **kwargs):
	filescan_open(MediaCore.TYPE_VIDEO, filelist, session, **kwargs)

def filescan_open_audio(filelist, session, **kwargs):
	filescan_open(MediaCore.TYPE_AUDIO, filelist, session, **kwargs)

def filescan_open(type, filelist, session, **kwargs):
	from enigma import eServiceReference
	mediaCore.setSession(session)

	playlist = []
	for file in filelist:
		if file.mimetype == "video/MP2T":
			stype = eServiceReference.idDVB
		else:
			stype = eServiceReference.idGST
		ref = eServiceReference(stype, 0, file.path)
		playlist.append(ref)

	session.open(MainMenu, type, playlist)

def getIcon(key):
	filename = resolveFilename(SCOPE_CURRENT_SKIN, "menu/mc_%s.svg" %key)
	if not pathExists(filename):
		filename = resolveFilename(SCOPE_CURRENT_SKIN, "menu/mc_%s.png" %key)
	if pathExists(filename):
		return filename
	else:
		return resolveFilename(SCOPE_PLUGINS, "Extensions/MediaCenter/icons/%s.png" %key)

def addDefaultMenuItems():
	mediaCore.addToMainMenu((
		_("Music and Audiobooks"),
		AudioPlayer,
		{
			"key" : "music",
			"icon": getIcon("music"),
			"featuresPlaylist" : True
		}
	))
	mediaCore.addToMainMenu((
		_("Videos"),
		VideoPlayer,
		{
			"key" : "movies",
			"icon" : getIcon("movies"),
			"featuresPlaylist" : True
		}
	))
	try:
		from Plugins.Extensions.PicturePlayer.plugin import picshow
		mediaCore.addToMainMenu((
			_("Pictures"),
			picshow,
			{
				"key" : "pictures",
				"icon": getIcon("pictures"),
				"featuresPlaylist" : False
			}
		))
	except:
		Log.w("PicturePlayer is not available")

addDefaultMenuItems()
def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("MediaCenter"), main, "mediacenter", 20)]
	return []

def main(session, **kwargs):
	mediaCore.setSession(session)
	session.open(MainMenu)

from Plugins.Plugin import PluginDescriptor
def Plugins(**kwargs):
	return [
			PluginDescriptor(name="MediaCenter",
							  description="Play and watch all your media",
							  icon="plugin.png",
							  where=[ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
							  fnc=main),

			PluginDescriptor(name="MediaCenter",
							  description="Play and watch all your media",
							  where=PluginDescriptor.WHERE_MENU,
							  fnc=menu),

			PluginDescriptor(name="MediaCenter",
							  where=PluginDescriptor.WHERE_FILESCAN,
							  fnc=filescan)
			]
