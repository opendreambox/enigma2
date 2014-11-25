from Netlink import Netlink
from BDPoll import BDPoll

class Hotplug(object):
	def __init__(self):
		print "starting hotplug handler"
		self.__bdpoll = BDPoll()
		self.__netlink = Netlink(self.__bdpoll)

	def release(self):
		print "stopping hotplug handler"
		self.__netlink.release()
		self.__netlink = None
		if self.__bdpoll:
			self.__bdpoll.running = False
			self.__bdpoll.timeout() # XXX: I assume the timer is shut down before it executes again, so release the semaphore manually
			self.__bdpoll.join()
			self.__bdpoll = None

	def registerEventCallback(self, callback):
		self.__netlink.registerEventCallback(callback)

	def unregisterEventCallback(self, callback):
		self.__netlink.unregisterEventCallback(callback)
