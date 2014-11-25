class HardwareInfo:
	device_name = None

	def __init__(self):
		if HardwareInfo.device_name is not None:
#			print "using cached result"
			return

		HardwareInfo.device_name = "unknown"
		try:
			file = open("/proc/stb/info/model", "r")
			HardwareInfo.device_name = file.readline().strip()
			file.close()
		except:
			pass

	def get_device_name(self):
		return HardwareInfo.device_name
