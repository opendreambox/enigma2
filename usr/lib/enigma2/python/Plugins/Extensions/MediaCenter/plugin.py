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
from MediaPlayerLCDScreen import MediaPlayerLCDScreen

class MainMenu(Screen):
	icon_path = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaCenter/icons/")

	skin = """
			<screen name="MainMenu" flags="wfNoBorder" position="0,0" size="1280,720" zPosition="1" transparent="0">
				<widget name="header" position="50,50" size="800, 80" font="Regular;72" />
				<widget name="subheader" position="50,140" size="800, 50" font="Regular;36" />

				<widget source="menulist" render="Listbox" position="320,300" zPosition="7" size="640,250" scrollbarMode="showOnDemand" transparent="0">
					<convert type="TemplatedMultiContent">
						{"template": [
								MultiContentEntryText(pos = (5, 0), size = (640, 52), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 0 is the name
							],
						"fonts": [gFont("Regular", 48)],
						"itemHeight": 52
						}
					</convert>
				</widget>
				<widget name="menuIcon" position="20,233" size="255,255" alphatest="on" pixmap="skin_default/no_coverArt.png" transparent="1" />
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
		return MediaPlayerLCDScreen

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
		self.summaries.setText("MediaCenter", 1)

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
			self.summaries.setText(choice[0], 2)

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
			stype = 1
		else:
			stype = 4097
		ref = eServiceReference(stype, 0, file.path)
		playlist.append(ref)

	session.open(MainMenu, type, playlist)

def getIcon(key):
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
		return [(_("MediaCenter"), main, "mediacenter", 45)]
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
