# -*- coding: UTF-8 -*-

from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins

from Components.ActionMap import ActionMap
from Components.ServiceEventTracker import InfoBarBase

from Tools.Log import Log
from Screens.SimpleSummary import SimpleSummary

class MoviePlayer(Screen, InfoBarBase, InfoBarSeek, InfoBarShowHide, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarNotifications):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service, restoreService = True, infoCallback = None, getNextService = None, getPrevService = None, stopCallback = None, pauseCallback = None, streamMode = False, askBeforeLeaving=True):
		Screen.__init__(self, session)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self)
		InfoBarShowHide.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarCueSheetSupport.__init__(self)
		InfoBarServiceErrorPopupSupport.__init__(self)
		InfoBarExtensions.__init__(self)
		InfoBarPlugins.__init__(self)
		InfoBarNotifications.__init__(self)
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
		self.pauseCB = pauseCallback
		self.callback = None
		self.screen_timeout = 5000
		self.nextservice = None
		self.is_closing = False

		if not restoreService: # lastservice is handled by PlayerBase which is inherited by InfoBarSeek
			# take care... when a zap timer want to zap to a service the player is closed and lastservice is changed in onClose callback of PlayerBase!
			self.lastservice = None

		self.streamMode = streamMode

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
		self._askBeforeLeaving = askBeforeLeaving

		self.onFirstExecBegin.append(self.play)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		if self.stopCB != None:
			self.stopCB()

	def createSummary(self):
		return SimpleSummary

	def playNext(self):
		if self.getNextServiceCB != None:
			newservice = self.getNextServiceCB()
			Log.i("newservice is %s" %newservice)
			if newservice:
				self.playService(newservice)
				return

		self.leavePlayerConfirmed([True, "quit"])

	def playPrev(self):
		if self.getPrevServiceCB != None:
			newservice = self.getPrevServiceCB()
			Log.i("newservice is %s" %newservice)
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
		self.session.nav.playService(self.service)
		if self.shown:
			self.checkSkipShowHideLock()

	def playpause(self):
		self.playpauseService()
		if self.pauseCB != None:
			self.pauseCB()

	def stopCurrent(self):
		print "stopCurrent"
		self.session.nav.stopService()
		if self.stopCB != None:
			self.stopCB()

	def showVideoInfo(self):
		if self.infoCallback != None:
			self.infoCallback(self.service)

	def handleLeave(self, ask = True, error = False):
		self.is_closing = True
		if ask:
			list = [(_("Yes"), "quit"),
					(_("No, but play video again"), "playAgain")]

			if self.getNextServiceCB != None:
				list.append( (_("Yes, but play next service"), "playnext") )
			if self.getPrevServiceCB != None:
				list.append( (_("Yes, but play previous service"), "playprev") )

			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("No playable video found! Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, "quit"])

	def leavePlayer(self):
		self.handleLeave(ask=self._askBeforeLeaving)

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
		if not self.streamMode:
			self.playNext()
