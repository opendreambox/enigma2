from Components.config import config
from Components.ActionMap import HelpableActionMap

from MediaCore import MediaCore, mediaCore
from MediaCenterLCDScreen import MediaCenterLCDScreen
from PlaylistPlayer import PlaylistPlayer

class VideoPlayer(PlaylistPlayer):
	title = _("Video Player")
	add = _("Add")
	clear = _("Clear List")
	remove = _("Remove")

	skin = """
		<screen position="center,120" size="820,520"  title="%s" >
			<widget source="playlist" render="Listbox" position="5,60" size="810,450" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"templates":{
						"default": (45, [
							MultiContentEntryText(pos = (5, 1), size = (800, 45), font = 0, flags = RT_VALIGN_CENTER, text = 2),
						]),
						"simple": (45, [
							MultiContentEntryText(pos = (5, 1), size = (800, 45), font = 0, flags = RT_VALIGN_CENTER, text = 2),
						]),
						},
					"fonts": [gFont("Regular", 26), gFont("Regular", 18), gFont("Regular", 13)]
					}
				</convert>
			</widget>
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,0" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,0" size="200,40" alphatest="on" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<eLabel text="%s" position="10,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<eLabel text="%s" position="210,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<eLabel text="%s" position="610,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
		</screen>""" % (title, clear, add, remove)

	def __init__(self, session, playlist=None):
		PlaylistPlayer.__init__(self, session, "video", MediaCore.TYPE_VIDEO)
		self.service = None

		self._initPlaylist(config.plugins.mediacenter.video.last_playlist_id.value)
		self._playlist.setSelectionEnabled(True)

		self["actions"] = HelpableActionMap(self, "MediaCenterActions",
		{
			"ok" : (self.play, _("Play Selected Entry")),
			"playpause" : (self.play, _("Play Selected Entry")),
			"editPlaylist" : (self.editPlaylist, _("Add file(s) to Playlist")),
			"removeFromPlaylist" : (self.removeSelectedPlaylistEntry, _("Remove Selected Entry From Playlist")),
			"cancel" : (self._close, _("Close MediaCenter Video Player")),
			"green" : (self.editPlaylist, _("Add file(s) to Playlist")),
			"red" : (self.clearPlaylist, _("Clear Playlist")),
			"blue" : (self.removeSelectedPlaylistEntry, _("Remove Selected Entry From Playlist")),
			"channelUp": self._moveSelectedUp,
			"channelDown": self._moveSelectedDown,
		});

		self["playlist"].onSelectionChanged.append(self.__onSelectionChanged)
		self.onShown.append(self._onShown)

		if playlist != None:
			self.addAllToPlaylist(playlist)

	def _onShown(self):
		self.__onSelectionChanged()

	def __onSelectionChanged(self):
		#Update LCD Stuff
		ref = self["playlist"].getSelection()
		if ref:
			text = ref.getPath()
			text = text.split('/')[-1]
			self.summaries.setText(text, 3)
		else:
			self.summaries.setText("", 3)

	def _close(self):
		self.close()

	def createSummary(self):
		return MediaCenterLCDScreen

	def play(self, playSelected=True):
		if playSelected:
			self.service = self["playlist"].playSelected()
		if self.service:
			self.hide()
			mediaCore.play(self.service, MediaCore.TYPE_VIDEO, restoreService=True, infoCallback=None, getNextService=self.playNext, getPrevService=self.playPrev, stopCallback=self.stop)

	def pause(self):
		self["playlist"].pause()

	def stop(self):
		self["playlist"].stop()
		self.session.nav.stopService()
		self.show()

	def removeSelectedPlaylistEntry(self):
		self.removeSelectedEntry()
