# -*- coding: UTF-8 -*-
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport

from Components.ActionMap import ActionMap

from Tools.Log import Log
from MediaPlayerLCDScreen import MediaPlayerLCDScreen

class MoviePlayer(Screen, InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service, infoCallback=None, getNextService=None, getPrevService=None, stopCallback=None):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		InfoBarSeek.__init__(self)
		InfoBarShowHide.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarCueSheetSupport.__init__(self)
		#TODO FIX THIS HACK
		# currently we just want to be able to resume playback (if supported by e2),
		# for now we don't care about cutting or jumpmarks or anything like that...
		del self["CueSheetActions"]

		self.session = session
		self.service = service
		self.infoCallback = infoCallback
		self.getNextServiceCB = getNextService
		self.getPrevServiceCB = getPrevService
		self.stopCB = stopCallback
		self.callback = None
		self.screen_timeout = 5000
		self.nextservice = None
		self.is_closing = False

		self["actions"] = ActionMap(["MediaCenterActions"],
		{
				"cancel": self.leavePlayer,
				"stop": self.leavePlayer,
				"playpauseService": self.playpauseService,
				"previous":  self.playPrev,
				"next": self.playNext,
#				"showentInfo": self.showVideoInfo,
			}, -2)

		self.returning = False


		self.onShown.append(self.play)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		if self.stopCB != None:
				self.stopCB()
		self.session.nav.stopService()

	def createSummary(self):
		return MediaPlayerLCDScreen

	def playNext(self):
		if self.getNextServiceCB != None:
			newservice = self.getNextServiceCB()
			Log.i("newservice is %s" % newservice)
			if newservice:
				self.playService(newservice)
				return

		self.leavePlayerConfirmed([True, "quit"])

	def playPrev(self):
		if self.getPrevServiceCB != None:
			newservice = self.getPrevServiceCB()
			Log.i("newservice is %s" % newservice)
			if newservice:
				self.playService(newservice)

		self.leavePlayerConfirmed([True, "quit"])

	def playAgain(self):
		print "playAgain"
		self.stopCurrent()
		self.play()

	def playService(self, newservice):
		self.stopCurrent()
		self.service = newservice
		self.play()

	def play(self):
		text = self.service.getPath()
		text = text.split('/')[-1]
		Log.i("text=%s" % text)
		self.summaries.setText(text, 3)

		self.session.nav.playService(self.service)
		if self.shown:
			self.checkSkipShowHideLock()

	def stopCurrent(self):
		print "stopCurrent"
		self.session.nav.stopService()

	def showVideoInfo(self):
		if self.infoCallback != None:
			self.infoCallback(self.service)

	def handleLeave(self, ask=True, error=False, title=_("Choose an action")):
		self.is_closing = True
		if ask:
			list = [(_("Close the player"), "quit"),
					(_("Play this video again"), "playAgain")]

			if self.getNextServiceCB != None:
				list.append((_("Play the next video"), "playnext"))
			if self.getPrevServiceCB != None:
				list.append((_("Play the previous video"), "playprev"))

			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=title, list=list)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("This video cannot be played! Choose an action"), list=list)
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
		if not playing :
			return
		self.handleLeave(title=_("End of video. Close the Player?"))
