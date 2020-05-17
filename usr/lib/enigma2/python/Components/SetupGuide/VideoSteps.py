from enigma import eDisplayManager, eTimer

from Components.config import config
from Components.DisplayHardware import DisplayHardware
from Components.SetupGuide.BaseStep import SetupListStep
from Tools.Log import Log

class VideoStepBase(SetupListStep):
	PORT_HDMI = "HDMI"
	NEXT_ITEM_TIMEOUT = 20

	def __init__(self, parent):
		SetupListStep.__init__(self, parent)
		self.port = None
		self.mode = None
		self.rate = None
		self._hw = DisplayHardware.instance
		self._timer = eTimer()
		self.__nextTimer_conn = self._timer.timeout.connect(self._next)
		self._hdmiChangedSigConn = eDisplayManager.getInstance().hdmiChanged.connect(self.hdmiChanged)

	def _next(self):
		#temporarily enable list wrapAround for automatic rotation
		wrapAround = self._list.enableWrapAround
		self._list.enableWrapAround = True

		self._list.selectNext()
		#disable list wraparound in case it was disabled
		self._list.enableWrapAround = wrapAround
		self._timer.startLongTimer(self.NEXT_ITEM_TIMEOUT)

	def prepare(self):
		self._portSelect(self.PORT_HDMI)
		self._timer.startLongTimer(self.NEXT_ITEM_TIMEOUT)
		return True

	def hdmiChanged(self):
		self._portSelect(self.PORT_HDMI)
		self._timer.startLongTimer(self.NEXT_ITEM_TIMEOUT)

	def onOk(self):
		self._timer.stop()
		config.av.videomode[self.port].value = self.mode
		config.av.videorate[self.mode].value = self.rate
		config.av.save()
		return True

	def cancel(self):
		self._timer.stop()
		SetupListStep.cancel(self)

	def buildfunc(self, key, text):
		return [text,key]

	def _portSelect(self, port):
		Log.i(port)
		self.port = port
		if (self.port == ""):
			return

		self.mode = config.av.videomode[self.port].value
		if (self.mode == ""):
			return

		self.rate = config.av.videorate[self.mode].value
		if (self.rate == ""):
			return

		modes = self._listModes()
		if modes:
			mode = modes[self._getIndex(modes, self.mode)][0]
			self.mode = mode
			rates = self._listRates()
			self.rate = rates[self._getIndex(rates, self.rate)][0]
			self._hw.setMode(self.port, self.mode, self.rate)

	def _getIndex(self, items, key):
		index = -1
		for item in items:
			index += 1
			if item[0] == key:
				return index
		return index

	def _listModes(self):
		Log.i("modes for port %s" %(self.port,))
		try:
			modeList = config.av.videomode[self.port].getChoices()
			Log.i(modeList)
			return modeList
		except AttributeError:
			Log.w("modeslist: empty")
			return []

	def _modeSelect(self, mode):
		Log.i("Mode: %s" %(mode,))

		if (mode == ""):
			return

		self.mode = mode

		ratesList = self._listRates()
		if len(ratesList) == 0:
			return

		self.rate = ratesList[0][0]
		self._hw.setMode(self.port, mode, self.rate)

	def _listRates(self):
		if self.mode not in config.av.videorate:
			return []

		rateList = sorted(config.av.videorate[self.mode].getChoices(), key=lambda rate: rate[0], reverse=True)
		Log.i(rateList)
		return rateList

class ResolutionStep(VideoStepBase):
	def __init__(self, parent):
		VideoStepBase.__init__(self, parent)

	def prepare(self):
		VideoStepBase.prepare(self)
		self.title = _("Video Mode\nUse up/down buttons.")
		self.text =  _("Video mode selection\n\nPlease press OK if you can see this page on your TV (or select a different video mode).\n\nThe next video mode will be automatically probed in 20 seconds.")
		return True

	@property
	def listContent(self):
		return self._listModes()

	@property
	def selectedIndex(self):
		return self._getIndex(self._listModes(), self.mode)

	def onSelectionChanged(self):
		current = self._list.current and self._list.current[0]
		if current:
			self._current = current
			self._modeSelect(self._current)

	def _modeSelect(self, mode):
		if mode == "":
			return

		self.mode = mode

		ratesList = self._listRates()
		if len(ratesList) == 0:
			return

		self.rate = ratesList[0][0]
		Log.i("Setting %s-%s-%s" %(self.port, self.mode, self.rate))
		self._hw.setMode(self.port, self.mode, self.rate)

class RateStep(VideoStepBase):
	def __init__(self, parent):
		VideoStepBase.__init__(self, parent)

	def prepare(self):
		VideoStepBase.prepare(self)
		self.title = _("Refresh rate\nUse up/down buttons.")
		self.text =  _("Refresh rate selection\n\nPlease press OK if you can see this page on your TV (or select a different refresh rate).\n\nThe next refresh rate will be automatically probed in 20 seconds.")
		return True

	@property
	def listContent(self):
		return self._listRates()

	@property
	def selectedIndex(self):
		return self._getIndex(self._listRates(), self.rate)

	def onSelectionChanged(self):
		current = self._list.current and self._list.current[0]
		if current:
			self._current = current
			self._rateSelect(self._current)

	def _rateSelect(self, rate):
		self.rate = rate
		Log.i("Setting %s-%s-%s" %(self.port, self.mode, self.rate))
		self._hw.setMode(self.port, self.mode, self.rate)
