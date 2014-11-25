from Components.Console import Console
from Components.Harddisk import harddiskmanager
from enigma import eDeviceEventManager
from os.path import basename

class Netlink(object):
	def __init__(self, bdpoll):
		self.__bdpoll = bdpoll
		self.__eventCallbacks = []
		self.__eventManager = eDeviceEventManager()
		self.__conn = self.__eventManager.event.connect(self.__hotplugEvent)
		self.__eventManager.addSubsystemFilter("block")
		self.__eventManager.monitor()
		self.__eventManager.trigger()

	def release(self):
		self.__conn = None
		self.__eventManager = None

	def __hotplugEvent(self, v):
		subsystem = v.get('SUBSYSTEM')
		if subsystem == 'block':
			self.__blockDeviceEvent(v)

	def __blockDeviceEvent(self, v):
		devpath = v.get('DEVPATH')
		if not devpath:
			return

		dev = basename(devpath)
		action = v.get('ACTION')
		if action in ("add", "change"):
			removable, is_cdrom, medium_found = harddiskmanager.addHotplugPartition(dev, v)
			if self.__bdpoll and removable or is_cdrom:
				self.__bdpoll.addDevice(dev, is_cdrom, medium_found)
		elif action == "remove":
			if self.__bdpoll:
				self.__bdpoll.removeDevice(dev)
			harddiskmanager.removeHotplugPartition(dev, v)
		else:
			return

		for callback in self.__eventCallbacks:
			try:
				callback(dev, action)
			except AttributeError:
				unregisterEventCallback(callback)

	def registerEventCallback(self, callback):
		self.__eventCallbacks.append(callback)

	def unregisterEventCallback(self, callback):
		self.__eventCallbacks.remove(callback)
