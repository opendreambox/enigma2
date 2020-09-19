from Components.Sources.Source import Source
from enigma import eInputDeviceManager
from Components.Element import cached

class InputDevice(Source):
	def __init__(self):
		Source.__init__(self)
		ipdm = eInputDeviceManager.getInstance()
		if ipdm:
			self.__deviceListChanged_conn = ipdm.deviceListChanged.connect(self._onDevicesChanged)
			self.__deviceStateChanged_conn = ipdm.deviceStateChanged.connect(self._onDevicesChanged)

	@property
	def range(self):
		return 100

	def _onDevicesChanged(self, *args):
		self.changed((self.CHANGED_ALL,))

	def _getFirst(self):
		ipdm = eInputDeviceManager.getInstance()
		for dev in ipdm.getConnectedDevices():
			if dev.ready():
				return dev
		return None

	@cached
	def isConnected(self):
		return self._getFirst() != None
	boolean = property(isConnected)

	@cached
	def getBatteryLevel(self):
		remote = self._getFirst()
		if not remote:
			return 0
		return remote.batteryLevel()
	batteryLevel = property(getBatteryLevel)

	@cached
	def getRSSI(self):
		remote = self._getFirst()
		if not remote:
			return -100
		return remote.rssi()
	rssi = property(getRSSI)

