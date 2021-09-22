from Components.Sources.Source import Source
from enigma import eInputDeviceManager
from Components.Element import cached

from Tools.Log import Log
class InputDevice(Source):
	def __init__(self):
		Source.__init__(self)
		self._ipdm = None

	@property
	def range(self):
		return 100

	def _onDevicesChanged(self, *args):
		self.changed((self.CHANGED_ALL,))

	def _getFirst(self):
		if not self._ipdm:
			self._ipdm = eInputDeviceManager.getInstance()
			self.__deviceListChanged_conn = self._ipdm.deviceListChanged.connect(self._onDevicesChanged)
			self.__deviceStateChanged_conn = self._ipdm.deviceStateChanged.connect(self._onDevicesChanged)
		for dev in self._ipdm.getConnectedDevices():
			if dev.connected():
				Log.d(dev)
				return dev
		Log.d("No connected device found!")
		return None

	@cached
	def isConnected(self):
		return self._getFirst() != None
	boolean = property(isConnected)

	def getBatteryLevel(self):
		remote = self._getFirst()
		if not remote:
			return 0
		return remote.batteryLevel()
	batteryLevel = property(getBatteryLevel)

	def getRSSI(self):
		remote = self._getFirst()
		if not remote:
			return -100
		return remote.rssi()
	rssi = property(getRSSI)

