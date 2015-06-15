from enigma import eStreamServer, eServiceReference, eServiceCenter, getBestPlayableServiceReference
from Components.config import config

from Tools.Log import Log

class StreamServerControl(object):
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
	PORT_LIMITS = [1, 65535]

	INPUT_MODE_LIVE = 0
	INPUT_MODE_HDMI_IN = 1
	INPUT_MODE_BACKGROUND = 2

	INPUT_MODES = {
		str(INPUT_MODE_LIVE) : _("Follow Live"),
		str(INPUT_MODE_HDMI_IN) : _("HDMI Input"),
		str(INPUT_MODE_BACKGROUND) : _("TV Services")
	}

	ENCODER_TARGET = 2

	RTSP_STATE_DISABLED = 0
	RTSP_STATE_IDLE = 1
	RTSP_STATE_RUNNING = 2

	UPSTREAM_STATE_DISABLED = 0
	UPSTREAM_STATE_CONNECTING = 1
	UPSTREAM_STATE_WAITING = 2
	UPSTREAM_STATE_TRANSMITTING = 3
	UPSTREAM_STATE_OVERLOAD = 4
	UPSTREAM_STATE_ADJUSTING = 5

	READABLE_UPSTREAM_STATE = {
		UPSTREAM_STATE_DISABLED : _("Disabled"),
		UPSTREAM_STATE_CONNECTING : _("Connecting"),
		UPSTREAM_STATE_WAITING : _("Waiting for clients"),
		UPSTREAM_STATE_TRANSMITTING : _("Transmitting"),
		UPSTREAM_STATE_OVERLOAD : _("Overload"),
		UPSTREAM_STATE_ADJUSTING : _("Adjusting Bitrate")
	}

	def __init__(self):
		self._streamServer = eStreamServer.getInstance()
		self._encoderService = None
		self._currentService = None
		self._availabilityChanged_conn = self._streamServer.availabilityChanged.connect(self._onAvailabilityChanged)
		self._upstreamStateChanged_conn = self._streamServer.upstreamStateChanged.connect(self._onUpstreamStateChanged)
		self._upstreamBitrateChanged_conn = self._streamServer.upstreamBitrateChanged.connect(self._onUpstreamBitrateChanged)
		self.onAvailabilityChanged = []
		self.onUpstreamStateChanged = []
		self.onUpstreamBitrateChanged = []

	def _onAvailabilityChanged(self, available):
		for fnc in self.onAvailabilityChanged:
			fnc(available)

	def _onUpstreamStateChanged(self, state):
		if state > self._streamServer.UPSTREAM_STATE_WAITING and self._currentService and not self._encoderService:
			Log.w("Upstream required. Aquiring service")
			self._startEncoderService(self._currentService)
		if state <= self._streamServer.UPSTREAM_STATE_WAITING and self._encoderService:
			Log.w("Upstream superflous. Freeing service")
		for fnc in self.onUpstreamStateChanged:
			fnc(state)

	def _onUpstreamBitrateChanged(self, bitrate):
		for fnc in self.onUpstreamBitrateChanged:
			fnc(bitrate)

	def setEncoderService(self, service):
		self._currentService = service
		ref = self._getRef(service)
		if ref:
			refstr = ref.toString()
			config.streamserver.lastservice.value = refstr
			config.streamserver.save()
			Log.i("upstreamState=%s" % (self._streamServer.upstreamState()))
			#if self._streamServer.upstreamState() != self._streamServer.UPSTREAM_STATE_DISABLED:
			self._startEncoderService(service)

	def getEncoderService(self):
		if self._currentService:
			return self._getRef(self._currentService)
		return None

	encoderService = property(getEncoderService, setEncoderService)

	def _startEncoderService(self, service):
		ref = self._getRef(service)
		if ref:
			self.stopEncoderService()
			self._encoderService = eServiceCenter.getInstance().play(ref)
			if self._encoderService and not self._encoderService.setTarget(self.ENCODER_TARGET):
				Log.i("Starting encoder service [%s]!" % (service.toCompareString()))
				self._encoderService.start()

	def _getRef(self, service):
		if service and (service.flags & eServiceReference.isGroup):
			return getBestPlayableServiceReference(service, eServiceReference())
		else:
			return service

	def stopEncoderService(self):
		if self._encoderService:
			Log.i("Stopping encoder service (%s)" % (self._currentService.toCompareString()))
			self._encoderService.stop()
		self._encoderService = None

	def isConnected(self):
		return self._streamServer.isAvailable()

	def setEnabled(self, enabled, path, port, user, password):
		return self._streamServer.enableRTSP(enabled, path, port, user, password)

	def isEnabled(self):
		return self._streamServer.isRTSPEnabled()

	enabled = property(isEnabled)

	def getInputMode(self):
		return self._streamServer.inputMode()

	def setInputMode(self, mode):
		self._streamServer.setInputMode(mode)

	inputMode = property(getInputMode, setInputMode)

	def getAudioBitrate(self):
		return self._streamServer.audioBitrate()

	def setAudioBitrate(self, bitrate):
		self._streamServer.setAudioBitrate(bitrate)

	audioBitrate = property(getAudioBitrate, setAudioBitrate)

	def getVideoBitrate(self):
		return self._streamServer.videoBitrate()

	def setVideoBitrate(self, bitrate):
		self._streamServer.setVideoBitrate(bitrate)

	videoBitrate = property(getVideoBitrate, setVideoBitrate)

	def getAutoBitrate(self):
		return self._streamServer.autoBitrate()

	def setAutoBitrate(self, auto):
		self._streamServer.setAutoBitrate(auto)

	autoBitrate = property(getAutoBitrate, setAutoBitrate)

	def getFramerate(self):
		return self._streamServer.framerate()

	def setFramerate(self, rate):
		self._streamServer.setFramerate(rate)

	framerate = property(getFramerate, setFramerate)

	def getResolution(self):
		w = self._streamServer.width()
		h = self._streamServer.height()
		return w, h

	def setResolution(self, res): #res = [w, h]
		self._streamServer.setResolution(res[0], res[1])

	resolution = property(getResolution, setResolution)

	def setUpstream(self, state, host, port, token):
		return self._streamServer.enableUpstream(state, host, port, token)

	def getUpstreamState(self):
		return self._streamServer.upstreamState()
	upstreamState = property(getUpstreamState)

	def zapNext(self):
		Log.i()
		from Screens.InfoBar import InfoBar
		if not InfoBar.instance:
			Log.i("no infobar")
			return False
		input_mode = int(config.streamserver.source.value)
		if input_mode == self.INPUT_MODE_LIVE:
			Log.i("zapping to next live service")
			InfoBar.instance.zapDown()
			return True
		elif input_mode == self.INPUT_MODE_BACKGROUND:
			Log.i("zapping to next background service")
			oldservice = self.encoderService
			if not oldservice:
				return False
			service = InfoBar.instance.getNextService(oldservice)
			streamServerControl.setEncoderService(service)
			return True
		Log.i("nothing done")
		return False

	def zapPrev(self):
		from Screens.InfoBar import InfoBar
		if not InfoBar.instance:
			Log.i("no infobar")
			return False
		Log.i(config.streamserver.source.value)
		input_mode = int(config.streamserver.source.value)
		if input_mode == self.INPUT_MODE_LIVE:
			Log.i("zapping to previous live service")
			InfoBar.instance.zapUp()
			return True
		elif input_mode == self.INPUT_MODE_BACKGROUND:
			Log.i("zapping to previous background service")
			oldservice = self.encoderService
			if not oldservice:
				return False
			service = InfoBar.instance.getPrevService(oldservice)
			streamServerControl.setEncoderService(service)
			return True
		Log.i("nothing done")
		return False

streamServerControl = StreamServerControl()
