from Components.Harddisk import harddiskmanager
from enigma import eDeviceEventManager
from os.path import basename

class Hotplug(object):
	def __init__(self):
		print "starting hotplug handler"
		self.__eventCallbacks = []
		self.__eventManager = eDeviceEventManager()
		self.__conn = self.__eventManager.event.connect(self.__hotplugEvent)
		self.__eventManager.addSubsystemFilter("block")
		self.__eventManager.monitor()
		self.__eventManager.trigger()

	def release(self):
		print "stopping hotplug handler"
		self.__conn = None
		self.__eventManager = None

	def __hotplugEvent(self, v):
		subsystem = v.get('SUBSYSTEM')
		if subsystem == 'block':
			self.__blockDeviceEvent(v)

	def __blockDeviceEvent(self, v):
		harddiskmanager.blockDeviceEvent(v)

		action = v.get('ACTION')
		devpath = v.get('DEVPATH')
		if not devpath or action not in ("add", "change", "remove"):
			return

		dev = basename(devpath)
		for callback in self.__eventCallbacks:
			try:
				callback(dev, action)
			except AttributeError:
				unregisterEventCallback(callback)

	def registerEventCallback(self, callback):
		self.__eventCallbacks.append(callback)

	def unregisterEventCallback(self, callback):
		self.__eventCallbacks.remove(callback)
