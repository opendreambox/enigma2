from enigma import eStreamServer, eTimer
from Components.Console import Console
from Tools.Log import Log

class WatchDog(object):
	DAEMON_TIMEOUT = 7
	DAEMON_NAME = "dreamrtspserver"

	instance = None
	def __init__(self):
		assert self.instance is None
		WatchDog.instance = self
		self.start()

	def start(self):
		Log.w("Streamserver Watchdog is starting!")
		self._ping_conn = eStreamServer.getInstance().ping.connect(self._onPing)
		self._timer = eTimer()
		self._timer_conn = self._timer.timeout.connect(self._onTimeout)
		self._console = Console()

	def _onPing(self):
		Log.d()
		self._timer.stop()
		self._timer.startLongTimer(self.DAEMON_TIMEOUT)

	def _onTimeout(self):
		Log.w()
		self._killDaemon()

	def _killDaemon(self):
		Log.w()
		self._console.ePopen("killall -9 %s" %(self.DAEMON_NAME,))