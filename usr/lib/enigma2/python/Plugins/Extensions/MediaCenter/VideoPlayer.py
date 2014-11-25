from Components.config import config
from Components.ActionMap import HelpableActionMap

from MediaCore import MediaCore, mediaCore
from MediaPlayerLCDScreen import MediaPlayerLCDScreen
from PlaylistPlayer import PlaylistPlayer

class VideoPlayer(PlaylistPlayer):
	title = _("Video Player")
	add = _("Add")
	clear = _("Clear List")
	remove = _("Remove")

	skin = """
		<screen position="center,center" size="780,500"  title="%s" >
			<widget source="playlist" render="Listbox" position="10,5" size="760,440" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"templates":{
						"default": (55, [
							MultiContentEntryText(pos = (5, 1), size = (750, 55), font = 0, flags = RT_VALIGN_CENTER, text = 2),
						]),
						"simple": (55, [
							MultiContentEntryText(pos = (5, 1), size = (750, 55), font = 0, flags = RT_VALIGN_CENTER, text = 2),
						]),
						},
					"fonts": [gFont("Regular", 26), gFont("Regular", 18), gFont("Regular", 13)]
					}
				</convert>
			</widget>

			<ePixmap pixmap="skin_default/buttons/button_red.png" position="10,470" size="15,16" alphatest="on" />
			<eLabel text="%s" position="30, 460" size="100, 40" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>

			<ePixmap pixmap="skin_default/buttons/button_green.png" position="140,470" size="15,16" alphatest="on" />
			<eLabel text="%s" position="160, 460" size="100, 40" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>

			<ePixmap pixmap="skin_default/buttons/button_blue.png" position="270,470" size="15,16" alphatest="on" />
			<eLabel text="%s" position="290, 460" size="100, 40" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>
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
			self.summaries.setText(text, 2)
		else:
			self.summaries.setText("", 2)

	def _close(self):
		self.close()

	def createSummary(self):
		return MediaPlayerLCDScreen

	def play(self, playSelected=True):
		if playSelected:
			self.service = self["playlist"].playSelected()
		if self.service:
			self.hide()
			mediaCore.play(self.service, MediaCore.TYPE_VIDEO, [None, self.playNext, self.playPrev, self.stop])

	def pause(self):
		self["playlist"].pause()

	def stop(self):
		self["playlist"].stop()
		self.show()

	def removeSelectedPlaylistEntry(self):
		self.removeSelectedEntry()
