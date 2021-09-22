# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from enigma import iPlayableService
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from .MediaPixmap import MediaPixmap
from Plugins.SystemPlugins.UPnP.UPnPCore import Statics

from .MediaGUI import MediaGUI

class AudioGUI(MediaGUI, InfoBarNotifications, InfoBarSeek):
	ENABLE_RESUME_SUPPORT = True

	skin = """
		<screen name="AudioGUI" position="0,0" size="1280,720" flags="wfNoBorder">
		<widget name="coverArt" pixmap="Default-FHD/skin_default/no_coverArt.svg" position="120,300" size="300,300" zPosition="2"/>
		<ePixmap pixmap="Default-FHD/skin_default/icons/dmm_logo.svg" position="30,630" size="480,30" zPosition="2"/>
		<widget name="coverBack" position="center,center" size="1300,1300" zPosition="1"/>
		<ePixmap pixmap="skin_default/display_bg.png" position="0,0" size="1280,768" />
		<ePixmap pixmap="Default-FHD/skin_default/back.png" position="0,0" size="1280,720" zPosition="1"/>
		<widget backgroundColor="#200d1940" foregroundColor="white" source="global.CurrentTime" render="Label" position="1040,40" size="200,55" font="Regular;50" halign="right" zPosition="2" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;50" name="artist" position="640,210" size="540,110" valign="bottom" transparent="1" zPosition="2"/>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;30" name="album" position="640,340" size="540,70" valign="top" transparent="1" zPosition="2"/>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;30" name="genre" position="640,410" size="540,35" transparent="1" zPosition="2"/>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;30" name="year" position="640,450" size="540,35" transparent="1" zPosition="2"/>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;26" name="title" position="640,530" valign="bottom" size="540,62" transparent="1" zPosition="2" />
		<widget pixmap="skin_default/progress.png" borderWidth="1" position="640,610" render="Progress" size="540,10" source="session.CurrentService" transparent="1" zPosition="2">
			<convert type="ServicePosition">Position</convert>
		</widget>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;28" position="640,630" render="Label" size="120,35" source="session.CurrentService" transparent="1" zPosition="2">
			<convert type="ServicePosition">Length</convert>
		</widget>
		<widget backgroundColor="#200d1940" foregroundColor="white" font="Regular;28" position="1060,630" halign="right" render="Label" size="120,35" source="session.CurrentService" transparent="1" zPosition="2">
			<convert type="ServicePosition">Remaining,Negate</convert>
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
		self["coverBack"] = MediaPixmap()

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUser + 13: self._embeddedCoverArt
			})

	def _embeddedCoverArt(self):
		self["coverBack"].embeddedCoverArt()
		self["coverArt"].embeddedCoverArt()


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