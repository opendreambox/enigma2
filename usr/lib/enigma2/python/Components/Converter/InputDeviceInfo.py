from enigma import eInputDeviceManager
from Components.Converter.Converter import Converter

class InputDeviceInfo(Converter, object):
	RSSI = 0
	BATTERY_LEVEL = 2

	MAX_RSSI = -30
	MIN_RSSI = -100

	def __init__(self, converterType):
		Converter.__init__(self, converterType)
		if converterType == "rssi":
			self.type = InputDeviceInfo.RSSI
		else:
			self.type = InputDeviceInfo.BATTERY_LEVEL
		self.range = 100

	def _getFirst(self):
		ipdm = eInputDeviceManager.getInstance()
		connected = ipdm.getConnectedDevices()
		for dev in connected:
			if dev.ready():
				return dev
		return None

	def getText(self):
		if self.type == InputDeviceInfo.RSSI:
			return "%s dBm" %(self.source.rssi,)
		return "%s%%" %(self.source.batteryLevel,)
	text = property(getText)

	def getValue(self):
		if self.type == InputDeviceInfo.BATTERY_LEVEL:
			return self.source.batteryLevel
		#RSSI
		val = self.source.rssi
		#Rescale RSSI to %
		factor = float(100) / abs(self.MIN_RSSI - self.MAX_RSSI)
		if val < self.MIN_RSSI:
			val = self.MIN_RSSI
		if val > self.MAX_RSSI:
			val = self.MAX_RSSI
		val = int((val - self.MIN_RSSI) * factor)
		return val

	value = property(getValue)
