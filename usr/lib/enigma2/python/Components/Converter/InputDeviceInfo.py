from __future__ import division
from enigma import eInputDeviceManager
from Components.Converter.Converter import Converter
from Tools.Log import Log

class InputDeviceInfo(Converter, object):
	RSSI = 0
	BATTERY_LEVEL = 2

	def __init__(self, converterType):
		Converter.__init__(self, converterType)
		if converterType.lower() == "rssi":
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

	@property
	def boolean(self):
		return self._getFirst() != None

	def getText(self):
		if self.type == InputDeviceInfo.RSSI:
			return "%s dBm" %(self.source.rssi,)
		return "%s%%" %(self.source.batteryLevel,)
	text = property(getText)

	def calcRssi(self, base, min_rssi, max_rssi, val):
		factor = float(base) / abs(min_rssi - max_rssi)
		if val < min_rssi:
			val = min_rssi
		if val > max_rssi:
			val = max_rssi
		val = int((val - min_rssi) * factor)
		Log.d(val)
		return val

	def getValue(self):
		if self.type == InputDeviceInfo.BATTERY_LEVEL:
			return self.source.batteryLevel
		#RSSI
		val = self.source.rssi
		# Rescale RSSI (this is an approximation!)
		# -30dBm to -67dBm can be considered "high signal strength, which we consider to be at least at 75%
		# Considered that a perfect signal (-30dBm) is pretty much impossible, we start at -35dBm
		# from -67dBm to -96dbM (the minimal signal the nordic can detect) signal degradation is almost linear, this is scaled between 0 and 74% (it's not but it's close enough for a UI)
		if val > -67:
			return 75 + self.calcRssi(25, -67, -35, val)
		return self.calcRssi(74, -96, -67, val)

	value = property(getValue)
