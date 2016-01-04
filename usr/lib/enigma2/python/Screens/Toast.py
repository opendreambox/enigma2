from enigma import ePoint, eSize, eTimer

from Components.Label import Label
from Screens.Screen import Screen
from Tools.Log import Log

class Toast(Screen):
	DURATION_SHORT = 5
	DURATION_MEDIUM = 10
	DURATION_LONG = 30
	DURATION_VERY_LONG = 60

	skin = ""
	def __init__(self, session, text, duration):
		Screen.__init__(self, session)
		self.duration = duration
		self["text"] = Label(text)
		self.onLayoutFinish.append(self._onLayoutFinish)

	def _onLayoutFinish(self):
		orgwidth = self.instance.size().width()
		orgpos = self.instance.position()
		textsize = self["text"].getSize()

		# y size still must be fixed in font stuff...
		textsize = (textsize[0] + 20, textsize[1] + 15)

		self.instance.resize(eSize(*textsize))
		self["text"].instance.resize(eSize(*textsize))

		# center window
		newwidth = textsize[0]
		self.instance.move(ePoint(orgpos.x() + (orgwidth - newwidth) / 2, orgpos.y()))

class ToastManager(object):
	def __init__(self, session):
		self._session = session
		self._queue = []
		self._deleteQueue = []
		self._currentToast = None
		self._hideAnimConns = []
		self._toastTimer = eTimer()
		self._toastTimer_conn = self._toastTimer.timeout.connect(self._onTimeout)

	def showToast(self, text, duration=Toast.DURATION_SHORT):
		screen = self._session.instantiateDialog(Toast, text, duration, zPosition=9999)
		screen.setShowHideAnimation("simple_fade")
		self.show(screen)
		return screen

	def show(self, screen):
		self._queue.append(screen)
		self._processQueue()

	def hide(self, screen):
		if screen == self._currentToast:
			self._onTimeout()
		elif screen in self._queue:
			self._queue.remove(screen)
		else:
			Log.w("Screen is not a toast or already about to be deleted %s" %(screen,))

	def _onTimeout(self):
		if self._currentToast:
			self._deleteQueue.append(self._currentToast)
			self._currentToast.onHideFinished.append(self._processQueue)
			self._currentToast.hide()
			self._currentToast = None
		self._processQueue()

	def _processQueue(self):
		unfinished = []
		for toast in self._deleteQueue:
			if not toast.instance.isFading():
				Log.i("Removing expired toast!")
				toast.onHideFinished.remove(self._processQueue)
				self._session.deleteDialog(toast)
			else:
				unfinished.append(toast)
		self._deleteQueue = unfinished

		if self._currentToast or not self._queue:
			return
		self._currentToast = self._queue.pop(0)
		self._currentToast.show()
		if hasattr(self._currentToast, "duration"):
			duration = self._currentToast.duration
		else:
			duration = Toast.DURATION_SHORT
		self._toastTimer.startLongTimer(duration)
