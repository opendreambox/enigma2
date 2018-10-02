from enigma import eTimer
from Components.Converter.Converter import Converter

class Poll(object):
	def __init__(self):
		self.__poll_timer = eTimer()
		self.__poll_timer_conn = self.__poll_timer.timeout.connect(self.poll)
		self.__interval = 1000
		self.__enabled = False

	def __setInterval(self, interval):
		self.__interval = interval
		suspended = getattr(self, "suspended", False) #won't exist whenever Converter.__init__ is called after Poll.__init__
		if self.__enabled and not suspended:
			self.__poll_timer.start(self.__interval)
		else:
			self.__poll_timer.stop()
	
	def __setEnable(self, enabled):
		self.__enabled = enabled
		self.poll_interval = self.__interval

	poll_interval = property(lambda self: self.__interval, __setInterval)
	poll_enabled = property(lambda self: self.__enabled, __setEnable)

	def poll(self):
		self.changed((self.CHANGED_POLL,))

	def doSuspend(self, suspended):
		if self.__enabled:
			if suspended:
				self.__poll_timer.stop()
			else:
				self.poll()
				self.poll_enabled = True

	def destroy(self):
		self.__poll_timer_conn = None

class PollConverter(Poll, Converter):
	def __init__(self, converterType):
		Converter.__init__(self, converterType)
		Poll.__init__(self)
