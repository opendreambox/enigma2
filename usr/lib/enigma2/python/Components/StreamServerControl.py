from enigma import eStreamServer, eServiceReference, eServiceCenter, getBestPlayableServiceReference, iServiceInformation
from Components.config import config, ConfigInteger, ConfigOnOff, ConfigPassword, ConfigSelection, Config, ConfigSubsection, ConfigText, ConfigYesNo

from Tools.Log import Log
from six.moves.urllib.parse import parse_qs

from Tools import Notifications
from Screens.MessageBox import MessageBox
from Tools.HardwareInfo import HardwareInfo
import six

NOTIFICATION_DOMAIN_STREAMSERVER = "StreamServer"
Notifications.notificationQueue.registerDomain(NOTIFICATION_DOMAIN_STREAMSERVER, _("Streaming Server"))



class StreamServerControl(object):
	FEATURE_SCENE_DETECTION = HardwareInfo().get_device_name() in ["dm900", "dm920"]
	FEATURE_SLICES = HardwareInfo().get_device_name() in ["dm900", "dm920"]

	FRAME_RATE_25 = "25"
	FRAME_RATE_30 = "30"
	FRAME_RATE_50 = "50"
	FRAME_RATE_60 = "60"
	FRAME_RATE_23_976 = "23.976"
	FRAME_RATE_24 = "24"
	FRAME_RATE_29_97 = "29.97"
	FRAME_RATE_59_94 = "59.94"

	FRAME_RATES = [
		FRAME_RATE_23_976,
		FRAME_RATE_24,
		FRAME_RATE_25,
		FRAME_RATE_29_97,
		FRAME_RATE_30,
		FRAME_RATE_50,
		FRAME_RATE_59_94,
		FRAME_RATE_60
	]

	FRAME_RATE_LUT = {
		FRAME_RATE_23_976 : "23",
		FRAME_RATE_24 : "24",
		FRAME_RATE_25 : "25",
		FRAME_RATE_29_97 : "29",
		FRAME_RATE_30 : "30",
		FRAME_RATE_50 : "50",
		FRAME_RATE_59_94 : "59",
		FRAME_RATE_60 : "60"
	}

	FRAME_RATE_LUT_REVERSE = {v: k for k, v in six.iteritems(FRAME_RATE_LUT)}

	LEVELS = [
		(str(eStreamServer.LEVEL1_1) , _("1.1")),
		(str(eStreamServer.LEVEL1_2) , _("1.2")),
		(str(eStreamServer.LEVEL1_3) , _("1.3")),
		(str(eStreamServer.LEVEL2_0) , _("2.0")),
		(str(eStreamServer.LEVEL2_1) , _("2.1")),
		(str(eStreamServer.LEVEL2_2) , _("2.2")),
		(str(eStreamServer.LEVEL3_0) , _("3.0")),
		(str(eStreamServer.LEVEL3_1) , _("3.1")), #default
		(str(eStreamServer.LEVEL3_2) , _("3.2")),
		(str(eStreamServer.LEVEL4_0) , _("4.0")),
		(str(eStreamServer.LEVEL4_1) , _("4.1")),
		(str(eStreamServer.LEVEL4_2) , _("4.2")),
	]

	PROFILES = [
		(str(eStreamServer.PROFILE_MAIN) , _("main")),
		(str(eStreamServer.PROFILE_HIGH) , _("high")),
	]

	RES_1080 = (1920, 1080)
	RES_720 = (1280, 720)
	RES_PAL = (720, 576)

	RES_KEY_1080P = "1080p"
	RES_KEY_720P = "720p"
	RES_KEY_PAL = "576p"

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

	AUDIO_BITRATE_LIMITS = [32, 448]
	VIDEO_BITRATE_LIMITS = [256, 20000]
	PORT_LIMITS = [1, 65535]

	INPUT_MODES = {
		str(eStreamServer.INPUT_MODE_LIVE) : _("Follow Live"),
		str(eStreamServer.INPUT_MODE_HDMI_IN) : _("HDMI Input"),
		str(eStreamServer.INPUT_MODE_BACKGROUND) : _("TV Services")
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

	ENCODER_SERVICE_SET = 0
	ENCODER_SERVICE_ALREADY_ACTIVE = 1
	ENCODER_SERVICE_INVALID_MODE = -1
	ENCODER_SERVICE_INVALID = -2
	ENCODER_SERVICE_INSUFFICIENT_RESOURCES = -3

	def __init__(self):
		self._streamServer = eStreamServer.getInstance()
		self.setupConfig()
		self._encoderService = None
		self._currentService = None
		self._availabilityChanged_conn = self._streamServer.availabilityChanged.connect(self._onAvailabilityChanged)
		self._sourceStateChanged_conn = self._streamServer.sourceStateChanged.connect(self._onSourceStateChanged)
		self._upstreamStateChanged_conn = self._streamServer.upstreamStateChanged.connect(self._onUpstreamStateChanged)
		self._upstreamBitrateChanged_conn = self._streamServer.upstreamBitrateChanged.connect(self._onUpstreamBitrateChanged)
		self._rtspClientCountChanged_conn = self._streamServer.rtspClientCountChanged.connect(self._onRtspClientCountChanged)
		self._onUriParametersChanged_conn = self._streamServer.uriParametersChanged.connect(self._onUriParametersChanged)
		self._dbusError_conn = self._streamServer.dbusError.connect(self._onDBusError)
		self._mediatorStateBeforeStandby = self.config.streamserver.mediator.enabled.value
		self.onAvailabilityChanged = []
		self.onSourceStateChanged = []
		self.onUpstreamStateChanged = []
		self.onUpstreamBitrateChanged = []
		self.onRtspClientCountChanged = []
		self.onUriParametersChanged = []
		self._isRunning = False

	def setupConfig(self):
		#Streamserver base config
		self.config = Config()
		self.config.streamserver = ConfigSubsection()
		self.config.streamserver.source = ConfigSelection(StreamServerControl.INPUT_MODES, default=str(eStreamServer.INPUT_MODE_LIVE))
		self.config.streamserver.audioBitrate = ConfigInteger(96, StreamServerControl.AUDIO_BITRATE_LIMITS)
		self.config.streamserver.videoBitrate = ConfigInteger(1500, StreamServerControl.VIDEO_BITRATE_LIMITS)
		self.config.streamserver.autoBitrate = ConfigOnOff(default=False)
		self.config.streamserver.resolution = ConfigSelection(list(StreamServerControl.RESOLUTIONS.keys()), default=StreamServerControl.RES_KEY_PAL)
		self.config.streamserver.framerate = ConfigSelection(StreamServerControl.FRAME_RATES, default=StreamServerControl.FRAME_RATE_23_976)
		# extended encoder settings
		self.config.streamserver.gopLength = ConfigInteger(default=eStreamServer.GOP_LENGTH_AUTO, limits=[eStreamServer.GOP_LENGTH_MIN, eStreamServer.GOP_LENGTH_MAX])
		self.config.streamserver.gopOnSceneChange = ConfigOnOff(default=False)
		self.config.streamserver.openGop = ConfigOnOff(default=False)
		self.config.streamserver.bFrames = ConfigInteger(default=eStreamServer.BFRAMES_DEFAULT, limits=[eStreamServer.BFRAMES_MIN, eStreamServer.BFRAMES_MAX])
		self.config.streamserver.pFrames = ConfigInteger(default=eStreamServer.PFRAMES_DEFAULT, limits=[eStreamServer.PFRAMES_MIN, eStreamServer.PFRAMES_MAX])
		self.config.streamserver.slices = ConfigInteger(default=eStreamServer.SLICES_DEFAULT, limits=[eStreamServer.SLICES_MIN, eStreamServer.SLICES_MAX])
		self.config.streamserver.level = ConfigSelection(StreamServerControl.LEVELS, default=str(eStreamServer.LEVEL_DEFAULT))
		self.config.streamserver.profile = ConfigSelection(StreamServerControl.PROFILES, default=str(eStreamServer.PROFILE_DEFAULT))
		#servers
		self.config.streamserver.rtsp = ConfigSubsection()
		self.config.streamserver.rtsp.enabled = ConfigOnOff(default=False)
		self.config.streamserver.rtsp.port = ConfigInteger(554, StreamServerControl.PORT_LIMITS)
		self.config.streamserver.rtsp.path = ConfigText(default="stream", fixed_size=False)
		self.config.streamserver.rtsp.user = ConfigText(default="", fixed_size=False)
		self.config.streamserver.rtsp.password = ConfigPassword(default="")
		self.config.streamserver.hls = ConfigSubsection()
		self.config.streamserver.hls.enabled = ConfigOnOff(default=False)
		self.config.streamserver.hls.path = ConfigText(default="stream", fixed_size=False)
		self.config.streamserver.hls.user = ConfigText(default="", fixed_size=False)
		self.config.streamserver.hls.password = ConfigPassword(default="")
		self.config.streamserver.hls.port = ConfigInteger(8080, StreamServerControl.PORT_LIMITS)
		self.config.streamserver.lastservice = ConfigText(default=config.tv.lastservice.value)
		self.config.streamserver.mediator = ConfigSubsection()
		self.config.streamserver.mediator.enabled = ConfigOnOff(default=False)
		self.config.streamserver.mediator.boxid = ConfigText()
		self.config.streamserver.mediator.boxkey = ConfigText()
		self.config.streamserver.mediator.streaminggroups = ConfigSubsection()
		self.config.streamserver.mediator.streaminggroups.member_alias = ConfigText(default="dreambox", fixed_size=False)
		self.config.streamserver.mediator.streaminggroups.stream_alias = ConfigText(default="", fixed_size=False)
		self.config.streamserver.mediator.streaminggroups.hide_empty = ConfigYesNo(default=False)
		self.config.streamserver.client = ConfigSubsection()
		self.config.streamserver.client.boxid = ConfigText(default="", fixed_size=False)
		self.config.streamserver.client.boxkey = ConfigText(default="", fixed_size=False)

		self.loadConfig()

	def loadConfig(self):
		#Streamserver base config
		self.config.streamserver.source.value = str(self._streamServer.inputMode())
		self.config.streamserver.audioBitrate.value = self._streamServer.audioBitrate()
		self.config.streamserver.videoBitrate.value = self._streamServer.videoBitrate()
		self.config.streamserver.autoBitrate.value = self._streamServer.autoBitrate()
		self.config.streamserver.resolution.value = str(self._streamServer.height()) + "p"
		self.config.streamserver.framerate.value = str(self._streamServer.framerate())

		# extended encoder settings
		self.config.streamserver.gopLength.value = self._streamServer.gopLength()
		self.config.streamserver.gopOnSceneChange.value = self._streamServer.gopOnSceneChange()
		self.config.streamserver.openGop.value = self._streamServer.openGop()
		self.config.streamserver.bFrames.value = self._streamServer.bFrames()
		self.config.streamserver.pFrames.value = self._streamServer.pFrames()
		self.config.streamserver.slices.value = self._streamServer.slices()
		self.config.streamserver.level.value = self._streamServer.level()
		self.config.streamserver.profile.value = self._streamServer.profile()

		#servers
		self.config.streamserver.rtsp.enabled.value = self._streamServer.isRTSPEnabled()
		self.config.streamserver.rtsp.path.value = self._streamServer.rtspPath()
		self.config.streamserver.rtsp.user.value = self._streamServer.rtspUsername()
		self.config.streamserver.rtsp.password.value = self._streamServer.rtspPassword()
		self.config.streamserver.hls.enabled.value = self._streamServer.isHLSEnabled()
		self.config.streamserver.hls.path.value = self._streamServer.hlsPath()
		self.config.streamserver.hls.user.value = self._streamServer.hlsUsername()
		self.config.streamserver.hls.password.value = self._streamServer.hlsPassword()

		#self.config.streamserver.lastservice = ConfigText(default=config.tv.lastservice.value)

		#TODO
		#self.config.streamserver.mediator = ConfigSubsection()
		#self.config.streamserver.mediator.enabled = ConfigOnOff(default=False)
		#self.config.streamserver.mediator.boxid = ConfigText()
		#self.config.streamserver.mediator.boxkey = ConfigText()
		#self.config.streamserver.mediator.streaminggroups = ConfigSubsection()
		#self.config.streamserver.mediator.streaminggroups.member_alias = ConfigText(default="dreambox", fixed_size=False)
		#self.config.streamserver.mediator.streaminggroups.stream_alias = ConfigText(default="", fixed_size=False)
		#self.config.streamserver.mediator.streaminggroups.hide_empty = ConfigYesNo(default=False)
		#self.config.streamserver.client = ConfigSubsection()
		#self.config.streamserver.client.boxid = ConfigText(default="", fixed_size=False)
		#self.config.streamserver.client.boxkey = ConfigText(default="", fixed_size=False)


	def start(self):
		if not self._isRunning:
			self.config.misc.standbyCounter.addNotifier(self._onStandby, initial_call = False)
			self._isRunning = True
		else:
			Log.w("start was called multiple times, self is not harmful but unneccessary!")

	def _onStandby(self, element):
		Log.d()
		from Screens.Standby import inStandby
		inStandby.onClose.append(self._onLeaveStandby)
		if self.config.streamserver.source.value == str(eStreamServer.INPUT_MODE_LIVE) and self.config.streamserver.mediator.enabled.value:
			Log.i("Going into Standby, mode is Follow Live, stopping proxy stream")
			self._mediatorStateBeforeStandby = self.config.streamserver.mediator.enabled.value
			self.config.streamserver.mediator.enabled.value = False

	def _onLeaveStandby(self):
		Log.d()
		if self.config.streamserver.source.value == str(eStreamServer.INPUT_MODE_LIVE) and self._mediatorStateBeforeStandby:
			Log.i("Leaving Standby, mode is Follow live, recovering upload state=%s" %(self._mediatorStateBeforeStandby,))
			self.config.streamserver.mediator.enabled.value = self._mediatorStateBeforeStandby

	def _onAvailabilityChanged(self, available):
		for fnc in self.onAvailabilityChanged:
			fnc(available)

	def _onSourceStateChanged(self, state):
		Log.i("state=%s" %state)
		if state == True and streamServerControl.inputMode == eStreamServer.INPUT_MODE_BACKGROUND:
			self.setEncoderService(eServiceReference(self.config.streamserver.lastservice.value))
		else:
			self.stopEncoderService()
		for fnc in self.onSourceStateChanged:
			fnc(state)

	def _onUpstreamStateChanged(self, state):
		if state > self._streamServer.UPSTREAM_STATE_WAITING and self._currentService and not self._encoderService:
			Log.i("Upstream running.")
		if state <= self._streamServer.UPSTREAM_STATE_WAITING and self._encoderService:
			Log.i("Upstream idle.")
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

	def _onDBusError(self, error):
		Log.w("DBUS ERROR! %s" %(error,))
		Notifications.AddPopup("%s" %(error,), MessageBox.TYPE_ERROR, -1, domain=NOTIFICATION_DOMAIN_STREAMSERVER)

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
			self.config.streamserver.lastservice.value = refstr
			self.config.streamserver.save()
			return self._startEncoderService(service)
		return self.ENCODER_SERVICE_INVALID

	def getEncoderService(self):
		if self._currentService:
			return self._getRef(self._currentService)
		return None

	encoderService = property(getEncoderService, setEncoderService)

	def isAnyEnabled(self):
		return self.config.streamserver.rtsp.enabled.value or self.config.streamserver.hls.enabled.value or self.config.streamserver.mediator.enabled.value

	def _startEncoderService(self, service):
		if not self.isAnyEnabled() \
			or int(self.config.streamserver.source.value) != eStreamServer.INPUT_MODE_BACKGROUND \
			or self.sourceState == False:
			self.stopEncoderService()
			Log.i("Streamserver disabled, not in TV Service mode or source not ready, will not allocate service: (isAnyEnabled, source!=TV_MODE, sourceState) (%s, %s, %s)"
				% (str(self.isAnyEnabled()), str(self.config.streamserver.source.value), str(self.sourceState)))
			return self.ENCODER_SERVICE_INVALID_MODE
		ref = self._getRef(service)
		if ref:
			cur_ref = self._encoderService
			cur_ref = cur_ref and cur_ref.info()
			cur_ref = cur_ref and cur_ref.getInfoString(iServiceInformation.sServiceref)
			if cur_ref == ref.toString():
				Log.i("ignore request to play already running background streaming service (%s)" %cur_ref)
				return self.ENCODER_SERVICE_ALREADY_ACTIVE
			else:
				self.stopEncoderService()
				self._encoderService = eServiceCenter.getInstance().play(ref)
				if self._encoderService and not self._encoderService.setTarget(self.ENCODER_TARGET):
					Log.i("Starting encoder service [%s]!" % (service.toCompareString()))
					self._encoderService.start()
					return self.ENCODER_SERVICE_SET
				else:
					return self.ENCODER_SERVICE_INSUFFICIENT_RESOURCES
		return self.ENCODER_SERVICE_INVALID

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

	def enableRTSP(self, enabled, path, port, user, password):
		return self._streamServer.enableRTSP(enabled, path, port, user, password)

	def enableHLS(self, enabled, path, port, user, password):
		#TODO streamserver has no user/password functionality for hls atm
		return self._streamServer.enableHLS(enabled, path, port, user, password)

	def isEnabled(self):
		return self.isAnyEnabled()

	enabled = property(isEnabled)

	def getInputMode(self):
		return self._streamServer.inputMode()

	def setInputMode(self, mode):
		self._streamServer.setInputMode(mode)

	inputMode = property(getInputMode, setInputMode)

	def getAudioBitrate(self):
		return self._streamServer.audioBitrate()

	def setAudioBitrate(self, bitrate):
		if bitrate >= self.AUDIO_BITRATE_LIMITS[0] and bitrate <= self.AUDIO_BITRATE_LIMITS[1]:
			self._streamServer.setAudioBitrate(bitrate)
			self.config.streamserver.audioBitrate.value = bitrate
		else:
			Log.w("Desired audio bitrate is out of range! %s %s" %(bitrate, self.VIDEO_BITRATE_LIMITS))

	audioBitrate = property(getAudioBitrate, setAudioBitrate)

	def getVideoBitrate(self):
		return self._streamServer.videoBitrate()

	def setVideoBitrate(self, bitrate):
		if bitrate >= self.VIDEO_BITRATE_LIMITS[0] and bitrate <= self.VIDEO_BITRATE_LIMITS[1]:
			self._streamServer.setVideoBitrate(bitrate)
			self.config.streamserver.videoBitrate.value = bitrate
		else:
			Log.w("Desired video bitrate is out of range! %s %s" %(bitrate, self.VIDEO_BITRATE_LIMITS))

	videoBitrate = property(getVideoBitrate, setVideoBitrate)

	def getAutoBitrate(self):
		return self._streamServer.autoBitrate()

	def setAutoBitrate(self, auto):
		self._streamServer.setAutoBitrate(auto)
		self.config.streamserver.autoBitrate.value = auto

	autoBitrate = property(getAutoBitrate, setAutoBitrate)

	def getGopLength(self):
		return self._streamServer.gopLength()

	def setGopLength(self, length):
		self._streamServer.setGopLength(length)

	gopLength = property(getGopLength, setGopLength)

	def getGopOnSceneChange(self):
		return self._streamServer.gopOnSceneChange()

	def setGopOnSceneChange(self, enabled):
		if self.FEATURE_SCENE_DETECTION:
			self._streamServer.setGopOnSceneChange(enabled)
		else:
			Log.w("This device's encoder has no support for scene detection!")

	gopOnSceneChange = property(getGopOnSceneChange, setGopOnSceneChange)

	def getOpenGop(self):
		return self._streamServer.openGop()

	def setOpenGop(self, enabled):
		self._streamServer.setOpenGop(enabled)

	openGop = property(getOpenGop, setOpenGop)

	def getBFrames(self):
		return self._streamServer.bFrames()

	def setBFrames(self, bFrames):
		self._streamServer.setBFrames(bFrames)

	bFrames = property(getBFrames, setBFrames)

	def getPFrames(self):
		return self._streamServer.pFrames()

	def setPFrames(self, pFrames):
		self._streamServer.setPFrames(pFrames)

	pFrames = property(getPFrames, setPFrames)

	def getSlices(self):
		return self._streamServer.slices()

	def setSlices(self, slices):
		if self.FEATURE_SLICES:
			self._streamServer.setSlices(slices)
		else:
			Log.w("This device's encoder has no support for setting slices")

	slices = property(getSlices, setSlices)

	def getLevel(self):
		return self._streamServer.level()

	def setLevel(self, level):
		self._streamServer.setLevel(level)

	level = property(getLevel, setLevel)

	def getProfile(self):
		return self._streamServer.profile()

	def setProfile(self, profile):
		self._streamServer.setProfile(profile)

	profile = property(getProfile, setProfile)

	def getFramerate(self):
		return self.FRAME_RATE_LUT_REVERSE.get(str(self._streamServer.framerate()))

	def setFramerate(self, rate):
		Log.w(rate)
		self._streamServer.setFramerate(int(self.FRAME_RATE_LUT.get(str(rate))))

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
		input_mode = int(self.config.streamserver.source.value)
		if input_mode == eStreamServer.INPUT_MODE_LIVE:
			Log.i("zapping to next live service")
			InfoBar.instance.zapDown()
			return True
		elif input_mode == eStreamServer.INPUT_MODE_BACKGROUND:
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
		Log.i(self.config.streamserver.source.value)
		input_mode = int(self.config.streamserver.source.value)
		if input_mode == eStreamServer.INPUT_MODE_LIVE:
			Log.i("zapping to previous live service")
			InfoBar.instance.zapUp()
			return True
		elif input_mode == eStreamServer.INPUT_MODE_BACKGROUND:
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
