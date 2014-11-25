# -*- coding: UTF-8 -*-
from enigma import iPlayableService
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from MediaPixmap import MediaPixmap
from Plugins.SystemPlugins.UPnP.UPnPCore import Statics

from MediaGUI import MediaGUI

class AudioGUI(MediaGUI, InfoBarNotifications, InfoBarSeek):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	skin = """
		<screen name="AudioGUI" position="center,center" size="700,265" title="UPnP Audio Player">
			<widget name="coverArt" position="10,10" size="250,250" pixmap="skin_default/no_coverArt.png" zPosition="1" transparent="1" alphatest="blend" />

			<widget name="title" position="280,10" size="300, 35" zPosition="1" font="Regular;27" valign="top" backgroundColor="background" transparent="1" />
			<widget name="artist" position="280,55" size="300, 25" zPosition="1" font="Regular;22" valign="top" foregroundColor="foreground" backgroundColor="background" transparent="1" />
			<widget name="album" position="280,85" size="300, 25" zPosition="1" font="Regular;22" valign="top" foregroundColor="foreground" backgroundColor="background" transparent="1" />
			<widget name="year" position="280,135" size="300, 25" zPosition="1" font="Regular;22" valign="top" foregroundColor="foreground" backgroundColor="background" transparent="1" />
			<widget name="genre" position="280,175" size="300, 25" zPosition="1" font="Regular;22" valign="top" foregroundColor="foreground" backgroundColor="background" transparent="1" />

			<widget source="session.CurrentService" render="Progress" zPosition="-1" position="0,258" size="700,7" pixmap="skin_default/progress_small.png" transparent="1">
				<convert type="ServicePosition">Position</convert>
			</widget>
		</screen>
		"""

	def __init__(self, session, master):
		MediaGUI.__init__(self, session, master)
		InfoBarNotifications.__init__(self)
		InfoBarSeek.__init__(self)
		self.setTitle(_("UPnP/DLNA Audio Player"))

		self["artist"] = Label("")
		self["title"] = Label("")
		self["album"] = Label("")
		self["year"] = Label("")
		self["genre"] = Label("")
		self["coverArt"] = MediaPixmap()

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUser + 13: self["coverArt"].embeddedCoverArt
			})

	def _actionOk(self):
		self.playpause()

	def lockShow(self):
		pass

	def unlockShow(self):
		pass

	def setMetadata(self):
		metadata = self._getMetadata()
		if metadata is not None:
			title = metadata.get(Statics.META_TITLE, "")
			artist = metadata.get(Statics.META_ARTIST, "")
			album = metadata.get(Statics.META_ALBUM, "")
			genre = metadata.get(Statics.META_GENRE, "")
			year = metadata.get(Statics.META_DATE, "")

			self["title"].setText(title)
			self["artist"].setText(artist)
			self["album"].setText(album)
			self["genre"].setText(genre)
			self["year"].setText(year)

		MediaGUI.setMetadata(self)