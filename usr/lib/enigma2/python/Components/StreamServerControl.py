import dbus

class StreamServerControl(object):
	INTERFACE = 'com.dreambox.RTSPserver'
	OBJECT = '/com/dreambox/RTSPserver'
	PROP_AUDIO_BITRATE = 'audioBitrate'
	PROP_VIDEO_BITRATE = 'videoBitrate'
	PROP_FRAMERATE = 'framerate'
	PROP_XRES = 'xres'
	PROP_YRES = 'yres'
	PROP_STATE = 'state'

	FRAME_RATE_25 = 25
	FRAME_RATE_30 = 30
	FRAME_RATE_50 = 50
	FRAME_RATE_60 = 60

	FRAME_RATES = [FRAME_RATE_25, FRAME_RATE_30, FRAME_RATE_50, FRAME_RATE_60]

	RES_1080 = (1920, 1080)
	RES_720 = (1280, 720)
	RES_PAL = (720, 576)

	RESOLUTIONS = {
			"1080p"	: RES_1080,
			"720p"	: RES_720,
			"576p"	: RES_PAL,
		}

	RESOLUTION_KEY = {
		RES_1080: "1080p",
		RES_720 : "720p",
		RES_PAL : "576p",
	}

	AUDIO_BITRATE_LIMITS = [32, 512]
	VIDEO_BITRATE_LIMITS = [256, 10000]

	def __init__(self):
		self._connected = False
		self.reconnect()

	def reconnect(self):
		try:
			self._bus = dbus.SystemBus()
			self._proxy = self._bus.get_object(self.INTERFACE, self.OBJECT)
			self._interface = dbus.Interface(self._proxy, self.INTERFACE)
			self._connected = True
		except:
			self._connected = False

	def isConnected(self):
		return self._connected

	def setEnabled(self, enabled):
		try:
			return self._interface.setEnabled(enabled)
		except:
			self.reconnect()
			return False

	def isEnabled(self):
		return self._getProperty(self.PROP_STATE)

	enabled = property(isEnabled, setEnabled)

	def getAudioBitrate(self):
		try:
			rate = int(self._getProperty(self.PROP_AUDIO_BITRATE))
		except:
			self.reconnect()
			return 128
		return rate

	def setAudioBitrate(self, bitrate):
		if bitrate < self.AUDIO_BITRATE_LIMITS[0] or bitrate > self.AUDIO_BITRATE_LIMITS[1]:
			return False
		return self._setProperty(self.PROP_AUDIO_BITRATE, bitrate)

	audioBitrate = property(getAudioBitrate, setAudioBitrate)

	def getVideoBitrate(self):
		try:
			rate = self._getProperty(self.PROP_VIDEO_BITRATE)
		except:
			self.reconnect()
			return 2000
		return rate

	def setVideoBitrate(self, bitrate):
		if bitrate < self.VIDEO_BITRATE_LIMITS[0] or bitrate > self.VIDEO_BITRATE_LIMITS[1]:
			return False
		return self._setProperty(self.PROP_VIDEO_BITRATE, bitrate)

	videoBitrate = property(getVideoBitrate, setVideoBitrate)

	def getFramerate(self):
		rate = self._getProperty(self.PROP_FRAMERATE, self.FRAME_RATE_25)
		return rate

	def setFramerate(self, rate):
		self._setProperty(self.PROP_FRAMERATE, rate)

	framerate = property(getFramerate, setFramerate)

	def getResolution(self):
		x = int( self._getProperty(self.PROP_XRES, 0) )
		y = int( self._getProperty(self.PROP_YRES, 0) )
		if x > 0 and y > 0:
			return (x, y)
		return self.RES_720

	def setResolution(self, res): #res = [w, h]
		try:
			self._interface.setResolution(res[0], res[1])
			return True
		except:
			return False

	resolution = property(getResolution, setResolution)

	def _getProperty(self, prop, default=None):
		try:
			return self._proxy.Get(self.INTERFACE, prop, dbus_interface=dbus.PROPERTIES_IFACE)
		except:
			return default

	def _setProperty(self, prop, val):
		try:
			self._proxy.Set(self.INTERFACE, prop, val, dbus_interface=dbus.PROPERTIES_IFACE)
			return True
		except:
			return False
