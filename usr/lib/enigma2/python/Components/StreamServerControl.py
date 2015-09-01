from enigma import eStreamServer, eServiceReference, eServiceCenter, getBestPlayableServiceReference, iServiceInformation
from Components.config import config, ConfigInteger, ConfigOnOff, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText

from Tools.Log import Log
from urlparse import parse_qs

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

	UPSTREAM_STATE_DISABLED = eStreamServer.UPSTREAM_STATE_DISABLED
	UPSTREAM_STATE_CONNECTING = eStreamServer.UPSTREAM_STATE_CONNECTING
	UPSTREAM_STATE_WAITING = eStreamServer.UPSTREAM_STATE_WAITING
	UPSTREAM_STATE_TRANSMITTING = eStreamServer.UPSTREAM_STATE_TRANSMITTING
	UPSTREAM_STATE_OVERLOAD = eStreamServer.UPSTREAM_STATE_OVERLOAD
	UPSTREAM_STATE_ADJUSTING = eStreamServer.UPSTREAM_STATE_ADJUSTING

	READABLE_UPSTREAM_STATE = {
		UPSTREAM_STATE_DISABLED : _("Disabled"),
		UPSTREAM_STATE_CONNECTING : _("Connecting"),
		UPSTREAM_STATE_WAITING : _("Waiting for clients"),
		UPSTREAM_STATE_TRANSMITTING : _("Transmitting"),
		UPSTREAM_STATE_OVERLOAD : _("Overload"),
		UPSTREAM_STATE_ADJUSTING : _("Adjusting Bitrate")
	}

	URI_PARAM_REF = "ref"
	URI_PARAM_VIDEO_BITRATE = "video_bitrate"
	URI_PARAM_AUDIO_BITRATE = "audio_bitrate"

	def __init__(self):
		self._streamServer = eStreamServer.getInstance()
		self._encoderService = None
		self._currentService = None
		self._availabilityChanged_conn = self._streamServer.availabilityChanged.connect(self._onAvailabilityChanged)
		self._sourceStateChanged_conn = self._streamServer.sourceStateChanged.connect(self._onSourceStateChanged)
		self._upstreamStateChanged_conn = self._streamServer.upstreamStateChanged.connect(self._onUpstreamStateChanged)
		self._upstreamBitrateChanged_conn = self._streamServer.upstreamBitrateChanged.connect(self._onUpstreamBitrateChanged)
		self._rtspClientCountChanged_conn = self._streamServer.rtspClientCountChanged.connect(self._onRtspClientCountChanged)
		self._onUriParametersChanged_conn = self._streamServer.uriParametersChanged.connect(self._onUriParametersChanged)
		self.onAvailabilityChanged = []
		self.onSourceStateChanged = []
		self.onUpstreamStateChanged = []
		self.onUpstreamBitrateChanged = []
		self.onRtspClientCountChanged = []
		self.onUriParametersChanged = []

	def _onAvailabilityChanged(self, available):
		for fnc in self.onAvailabilityChanged:
			fnc(available)

	def _onSourceStateChanged(self, state):
		Log.i("state=%s" %state)
		if state > eStreamServer.SOURCE_STATE_READY and streamServerControl.inputMode == streamServerControl.INPUT_MODE_BACKGROUND:
			self.setEncoderService(eServiceReference(config.streamserver.lastservice.value))
		else:
			self.stopEncoderService()
		for fnc in self.onSourceStateChanged:
			fnc(state)

	def _onUpstreamStateChanged(self, state):
		if state > self._streamServer.UPSTREAM_STATE_WAITING and self._currentService and not self._encoderService:
			Log.i("Upstream required. Aquiring service")
			self.setEncoderService(self._currentService)
		if state <= self._streamServer.UPSTREAM_STATE_WAITING and self._encoderService:
			Log.i("Upstream superflous. Freeing service")
		for fnc in self.onUpstreamStateChanged:
			fnc(state)

	def _onUpstreamBitrateChanged(self, bitrate):
		for fnc in self.onUpstreamBitrateChanged:
			fnc(bitrate)

	def _onRtspClientCountChanged(self, count, client):
		Log.i("%s / %s" %(count, client))
		for fnc in self.onRtspClientCountChanged:
			fnc(count, client)

	def _onUriParametersChanged(self, parameters):
		Log.i("%s" %(parameters))
		params = parse_qs(parameters)
		self._applyUriParameters(params)
		for fnc in self.onUriParametersChanged:
			fnc(params)

	def _applyUriParameters(self, params):
		ref = str(params.get(self.URI_PARAM_REF, [""])[0])
		ref = eServiceReference(ref)
		if ref.valid():
			Log.i("setting encoder service to %s" %ref.toString())
			self.setEncoderService(ref)
		vb = params.get(self.URI_PARAM_VIDEO_BITRATE, [-1])[0]
		if vb > 0:
			try:
				Log.i("setting video bitrate to %s" %vb)
				self.videoBitrate = int(vb)
			except:
				pass
		ab = params.get(self.URI_PARAM_AUDIO_BITRATE, [-1])[0]
		if ab > 0:
			try:
				Log.i("setting audio bitrate to %s" %ab)
				self.audioBitrate = int(ab)
			except:
				pass

	def setEncoderService(self, service):
		self._currentService = service
		ref = self._getRef(service)
		if ref:
			refstr = ref.toString()
			config.streamserver.lastservice.value = refstr
			config.streamserver.save()
			self._startEncoderService(service)

	def getEncoderService(self):
		if self._currentService:
			return self._getRef(self._currentService)
		return None

	encoderService = property(getEncoderService, setEncoderService)

	def _startEncoderService(self, service):
		if not config.streamserver.enabled.value \
			or int(config.streamserver.source.value) != self.INPUT_MODE_BACKGROUND \
			or self.sourceState <= eStreamServer.SOURCE_STATE_READY:
			self.stopEncoderService()
			Log.i("Streamserver disabled, not in TV Service mode or no client connected, will not allocate service (%s, %s, %s)" % (config.streamserver.enabled.value, config.streamserver.source.value, self._streamServer.sourceState()))
			return
		ref = self._getRef(service)
		if ref:
			cur_ref = self._encoderService
			cur_ref = cur_ref and cur_ref.info()
			cur_ref = cur_ref and cur_ref.getInfoString(iServiceInformation.sServiceref)
			if cur_ref == ref.toString():
				Log.i("ignore request to play already running background streaming service (%s)" %cur_ref)
			else:
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
		if bitrate > self.AUDIO_BITRATE_LIMITS[0] and bitrate < self.AUDIO_BITRATE_LIMITS[1]:
			self._streamServer.setAudioBitrate(bitrate)
			config.streamserver.audioBitrate.value = bitrate
		else:
			Log.w("Desired audio bitrate is out of range! %s %s" %(bitrate, self.VIDEO_BITRATE_LIMITS))

	audioBitrate = property(getAudioBitrate, setAudioBitrate)

	def getVideoBitrate(self):
		return self._streamServer.videoBitrate()

	def setVideoBitrate(self, bitrate):
		if bitrate > self.VIDEO_BITRATE_LIMITS[0] and bitrate < self.VIDEO_BITRATE_LIMITS[1]:
			self._streamServer.setVideoBitrate(bitrate)
			config.streamserver.videoBitrate.value = bitrate
		else:
			Log.w("Desired video bitrate is out of range! %s %s" %(bitrate, self.VIDEO_BITRATE_LIMITS))

	videoBitrate = property(getVideoBitrate, setVideoBitrate)

	def getAutoBitrate(self):
		return self._streamServer.autoBitrate()

	def setAutoBitrate(self, auto):
		self._streamServer.setAutoBitrate(auto)
		config.streamserver.autoBitrate.value = auto

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

	def getSourceState(self):
		return self._streamServer.sourceState()

	sourceState = property(getSourceState)

	def getRtspClientcount(self):
		return self._streamServer.rtspClientCount()
	rtspClientCount = property(getRtspClientcount)

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

#Streamserver base config
config.streamserver = ConfigSubsection()
config.streamserver.enabled = ConfigOnOff(default=False)
config.streamserver.source = ConfigSelection(StreamServerControl.INPUT_MODES, default=str(StreamServerControl.INPUT_MODE_LIVE))
config.streamserver.audioBitrate = ConfigInteger(128, StreamServerControl.AUDIO_BITRATE_LIMITS)
config.streamserver.videoBitrate = ConfigInteger(2048, StreamServerControl.VIDEO_BITRATE_LIMITS)
config.streamserver.autoBitrate = ConfigOnOff(default=False)
config.streamserver.resolution = ConfigSelection(StreamServerControl.RESOLUTIONS.keys(), default="720p")
config.streamserver.framerate = ConfigSelection(StreamServerControl.FRAME_RATES, default=StreamServerControl.FRAME_RATE_25)
config.streamserver.rtspport = ConfigInteger(554, StreamServerControl.PORT_LIMITS)
config.streamserver.rtsppath = ConfigText(default="stream", fixed_size=False)
config.streamserver.user = ConfigText(default="", fixed_size=False)
config.streamserver.password = ConfigPassword(default="")
config.streamserver.lastservice = ConfigText(default=config.tv.lastservice.value)

streamServerControl = StreamServerControl()
