# -*- coding: UTF-8 -*-
from enigma import eTimer
from Components.ActionMap import ActionMap
from Plugins.SystemPlugins.UPnP.UPnPCore import Statics
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox

from Tools.Log import Log
from LCDScreen import MediaRendererLCDScreen

class MediaGUI(Screen):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, master):
		Screen.__init__(self, session)

		self._master = master
		self._getInfo = self._master.getInfo
		self._play = self._master.play
		self._stop = self._master.stop
		self._playpause = self._master.playpause
		self._screen_timeout = 5000
		self._is_closing = False
		self._getMetadata = self._master.getMetadata

		self.__delayed_close_timer = eTimer()
		self.__delayed_close_timer_conn = self.__delayed_close_timer.timeout.connect(self.close)

		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
				"ok": self._actionOk,
				"cancel": self._actionCancel,
				"stop": self._actionStop,
				"playpauseService": self._actionPlaypause,
				"showEventInfo": self._actionShowInfo,
			}, -2)

		self.returning = False
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.stopCurrent()

	def _actionOk(self):
		Log.i("Nothing to do for OK")

	def _actionCancel(self):
		self.leavePlayer()

	def _actionStop(self):
		self.leavePlayer()

	def _actionPlaypause(self):
		self.playpause()

	def _actionShowInfo(self):
		self.showInfo()

	def createSummary(self):
		return MediaRendererLCDScreen

	def delayedClose(self):
		Log.i()
		self.__delayed_close_timer.stop()
		self.__delayed_close_timer.startLongTimer(4)

	def playAgain(self):
		Log.i()
		self.stopCurrent()
		self.play()

	def play(self):
		Log.i()
		self.setSeekState(self.SEEK_STATE_PLAY, onlyGUI=True)
		self.__delayed_close_timer.stop()
		self.setMetadata()
		if self.shown:
			self.checkSkipShowHideLock()

	def pause(self):
		Log.i()
		self.setSeekState(self.SEEK_STATE_PAUSE, onlyGUI=True)

	def unpause(self):
		Log.i()
		self.setSeekState(self.SEEK_STATE_PLAY, onlyGUI=True)

	def setMetadata(self):
		Log.i()
		metadata = self._getMetadata()
		if metadata is not None:
			title = metadata.get(Statics.META_TITLE, None)
			artist = metadata.get(Statics.META_ARTIST, None)
			album = metadata.get(Statics.META_ALBUM, None)
			if title:
				self.summaries.setText(title, 1)
				if artist:
					self.summaries.setText(artist, 2)
				if album:
					self.summaries.setText(album, 3)
				return

	def playpause(self):
		if self._playpause(self.seekstate == self.SEEK_STATE_PLAY):
			self.setSeekState(self.SEEK_STATE_PAUSE, onlyGUI=True)
		else:
			self.setSeekState(self.SEEK_STATE_PLAY, onlyGUI=True)

	def stopCurrent(self):
		Log.i()
		self.summaries.clear()
		if self.seekstate != self.SEEK_STATE_EOF:
			self._stop()

	def showInfo(self):
		if self._getInfo != None:
			self._getInfo()

	def handleLeave(self, ask=True, error=False):
		self._is_closing = True
		if ask:
			lst = [(_("Yes"), "quit"),
					(_("No, but play again"), "playAgain")]

			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=lst)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("No playable video found! Stop playing this movie?"), list=lst)
		else:
			self.leavePlayerConfirmed([True, "quit"])

	def leavePlayer(self):
		self.handleLeave(ask=False)

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "quit":
			self.close()
		elif answer == "playAgain":
			self.playAgain()
