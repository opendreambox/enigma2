# -*- coding: UTF-8 -*-
from enigma import eTimer
from Components.ActionMap import ActionMap
from Plugins.SystemPlugins.UPnP.UPnPCore import Statics
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport

from Helpers import debug

class MoviePlayer(Screen, InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service, restoreService=True, infoCallback=None, getNextService=None, getPrevService=None, stopCallback=None, pauseCallback=None, getMetadata=None):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		InfoBarSeek.__init__(self)
		InfoBarShowHide.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarCueSheetSupport.__init__(self)
		# TODO FIX THIS HACK
		# currently we just want to be able to resume playback (if supported by e2),
		# for now we don't care about cutting or jumpmarks or anything like that...
		del self["CueSheetActions"]

		self.session = session
		self.service = service
		self.infoCallback = infoCallback
		self.getNextServiceCB = getNextService
		self.getPrevServiceCB = getPrevService
		self.stopCB = stopCallback
		self.pauseCB = pauseCallback
		self.callback = None
		self.screen_timeout = 5000
		self.nextservice = None
		self.is_closing = False
		self.restoreService = restoreService
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.getMetadata = getMetadata

		self.__delayed_close_timer = eTimer()
		self.__delayed_close_timer.callback.append(self.close)

		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
				"cancel": self.leavePlayer,
				"stop": self.leavePlayer,
				"playpauseService": self.playpause,
				"previous":  self.playPrev,
				"next": self.playNext,
				"showEventInfo": self.showVideoInfo,
			}, -2)

		self.returning = False

		self.onShown.append(self.play)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		if self.stopCB != None:
				self.stopCB(False)
		self.session.nav.stopService()
		if self.restoreService:
			self.session.nav.playService(self.oldService)

	def createSummary(self):
		return SimpleLCDScreen

	def delayedClose(self):
		debug(self, "delayedClose")
		self.__delayed_close_timer.stop()
		self.__delayed_close_timer.startLongTimer(4)

	def playNext(self):
		debug(self, "playNext")
		if self.getNextServiceCB != None:
			newservice = self.getNextServiceCB()
			debug(self, "playNext", "newservice is %s" % newservice)
			if newservice:
				self.playService(newservice)
				return
		self.delayedClose()

	def playPrev(self):
		debug(self, "playPrev")
		if self.getPrevServiceCB != None:
			newservice = self.getPrevServiceCB()
			debug(self, "playPrev", "newservice is %s" % newservice)
			if newservice:
				self.playService(newservice)
				return
		self.delayedClose()

	def playAgain(self):
		debug(self, "playAgain")
		self.stopCurrent()
		self.play()

	def playService(self, newservice):
		self.__delayed_close_timer.stop()
		if self.service.toCompareString() != newservice.toCompareString():
			self.service = newservice
			self.play()

	def play(self):
		self.__delayed_close_timer.stop()
		self.setMetadata()
		self.session.nav.playService(self.service)
		if self.shown:
			self.checkSkipShowHideLock()

	def setMetadata(self):
		if self.getMetadata:
			metadata = self.getMetadata()
			if metadata is not None:
				title = metadata[Statics.META_TITLE]
				artist = metadata[Statics.META_ARTIST]
				album = metadata[Statics.META_ALBUM]
				if title:
					self.summaries.setText(title, 1)
					if artist:
						self.summaries.setText(artist, 2)
					if album:
						self.summaries.setText(album, 3)
					return
		self.summaries.setText(self.service.getName(), 1)

	def playpause(self):
		self.playpauseService()
		if self.pauseCB != None:
			self.pauseCB(self.seekstate == self.SEEK_STATE_PLAY)

	def stopCurrent(self):
		debug(self, "stopCurrent")
		self.session.nav.stopService()
		self.summaries.clear()
		if self.stopCB != None and self.seekstate != self.SEEK_STATE_EOF:
			self.stopCB(False)

	def showVideoInfo(self):
		if self.infoCallback != None:
			self.infoCallback(self.service)

	def handleLeave(self, ask=True, error=False):
		self.is_closing = True
		if ask:
			list = [(_("Yes"), "quit"),
					(_("No, but play video again"), "playAgain")]

			if self.getNextServiceCB != None:
				list.append((_("Yes, but play next service"), "playnext"))
			if self.getPrevServiceCB != None:
				list.append((_("Yes, but play previous service"), "playprev"))

			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=list)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("No playable video found! Stop playing this movie?"), list=list)
		else:
			self.leavePlayerConfirmed([True, "quit"])

	def leavePlayer(self):
		self.handleLeave()

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "quit":
			self.close()

		elif answer == "playnext":
			self.playNext()

		elif answer == "playprev":
			self.playPrev()

		elif answer == "playAgain":
			self.playAgain()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return

		self.playNext()
		if self.stopCB != None:
			self.stopCB(True)

# -*- coding: UTF-8 -*-

from Components.Label import Label
from Screens.Screen import Screen

class SimpleLCDScreen(Screen):
	skin = (
	"""<screen name="MediaPlayerLCDScreen" position="0,0" size="132,64" id="1">
		<widget name="text1" position="4,0" size="132,18" font="Regular;14"/>
		<widget name="text2" position="4,20" size="132,14" font="Regular;11"/>
		<widget name="text3" position="4,36" size="132,14" font="Regular;11"/>
	</screen>""",
	"""<screen name="MediaPlayerLCDScreen" position="0,0" size="96,64" id="2">
		<widget name="text1" position="0,0" size="96,18" font="Regular;13"/>
		<widget name="text2" position="0,20" size="96,14" font="Regular;10"/>
		<widget name="text3" position="0,36" size="96,14" font="Regular;10"/>
	</screen>""")

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label("")
		self["text2"] = Label("")
		self["text3"] = Label("")

	def setText(self, text, line):
		if line == 1:
			if len(text) > 18:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 15:
					text = text[-15:]
		else:
			if len(text) > 20:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 20:
					text = text[-20:]
		empty = "	"
		text = text + empty * 10
		if line == 1:
			self["text1"].setText(text)
		elif line == 2:
			self["text2"].setText(text)
		elif line == 3:
			self["text3"].setText(text)
		else:
			print "SimpleLCDScreen line %s does not exist!"

	def clear(self):
		self["text1"].setText("")
		self["text2"].setText("")
		self["text3"].setText("")
