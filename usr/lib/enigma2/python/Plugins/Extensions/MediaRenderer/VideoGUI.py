# -*- coding: UTF-8 -*-
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport
from MediaGUI import MediaGUI

class VideoGUI(MediaGUI, InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, master):
		MediaGUI.__init__(self, session, master)
		InfoBarNotifications.__init__(self)
		InfoBarSeek.__init__(self)
		InfoBarShowHide.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarCueSheetSupport.__init__(self)
		self.skinName = "MoviePlayer"
		self.setTitle(_("UPnP/DLNA Video Player"))
		# TODO FIX THIS HACK
		# currently we just want to be able to resume playback (if supported by e2),
		# for now we don't care about cutting or jumpmarks or anything like that...
		del self["CueSheetActions"]

	def _actionOk(self):
		self.toggleShow()
