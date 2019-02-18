from Components.Sources.Source import Source
from enigma import eInputDeviceManager
from Components.Element import cached

class InputDevice(Source):
	def __init__(self):
		Source.__init__(self)
		ipdm = eInputDeviceManager.getInstance()
		if ipdm:
			self.__deviceListChanged_conn = ipdm.deviceStateChanged.connect(self._onDeviceStateChanged)

	def _onDeviceStateChanged(self, device, newstate):
		self.changed((self.CHANGED_ALL,))

	def _getFirst(self):
		ipdm = eInputDeviceManager.getInstance()
		if not ipdm:
			return None
		connected = ipdm.getConnectedDevices()
		for dev in connected:
			if dev.ready():
				return dev
		return None

	@cached
	def isConnected(self):
		dev = self._getFirst()
		return dev and dev.ready()
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

