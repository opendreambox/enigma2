from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.StreamServerControl import StreamServerControl, streamServerControl
from Components.config import config, getConfigListEntry
from Components.Network import iNetworkInfo

from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from enigma import eStreamServer

def applyConfig(streamServerControl, initial=False, forceRestart=False):
		isMediatorEnabled = streamServerControl.config.streamserver.mediator.enabled.value
		if initial:
			streamServerControl.config.streamserver.mediator.enabled.value = False

		rtsp_enabled = streamServerControl.config.streamserver.rtsp.enabled.value
		rtsp_path = streamServerControl.config.streamserver.rtsp.path.value
		rtsp_user = streamServerControl.config.streamserver.rtsp.user.value
		rtsp_password = streamServerControl.config.streamserver.rtsp.password.value
		#rtsp_port = streamServerControl.config.streamserver.rtsp.port.value
		hls_enabled = streamServerControl.config.streamserver.hls.enabled.value
		hls_path = streamServerControl.config.streamserver.hls.path.value
		#hls_port = streamServerControl.config.streamserver.hls.port.value
		hls_user = streamServerControl.config.streamserver.hls.user.value
		hls_password = streamServerControl.config.streamserver.hls.password.value

		if forceRestart:
			streamServerControl.enableRTSP(False, rtsp_path, 554, rtsp_user, rtsp_password)
			streamServerControl.enableHLS(False, hls_path, 8080, hls_user, hls_password)
			streamServerControl.config.streamserver.mediator.enabled.value = False

		inputMode = int(streamServerControl.config.streamserver.source.value)
		streamServerControl.setInputMode(inputMode)

		audioBitrate = streamServerControl.config.streamserver.audioBitrate.value
		if audioBitrate != streamServerControl.audioBitrate:
			streamServerControl.audioBitrate = streamServerControl.config.streamserver.audioBitrate.value

		videoBitrate = streamServerControl.config.streamserver.videoBitrate.value
		if videoBitrate != streamServerControl.videoBitrate:
			streamServerControl.videoBitrate = streamServerControl.config.streamserver.videoBitrate.value

		autoBitrate = streamServerControl.config.streamserver.autoBitrate.value
		if autoBitrate != streamServerControl.autoBitrate:
			streamServerControl.autoBitrate = autoBitrate

		resolution = StreamServerControl.RESOLUTIONS[streamServerControl.config.streamserver.resolution.value]
		if resolution != streamServerControl.resolution:
			streamServerControl.resolution = StreamServerControl.RESOLUTIONS[streamServerControl.config.streamserver.resolution.value]

		gopLength = streamServerControl.config.streamserver.gopLength.value
		if gopLength != streamServerControl.gopLength:
			streamServerControl.gopLength = gopLength

		if StreamServerControl.FEATURE_SCENE_DETECTION:
			gopOnSceneChange = streamServerControl.config.streamserver.gopOnSceneChange.value
			if gopOnSceneChange != streamServerControl.gopOnSceneChange:
				streamServerControl.gopOnSceneChange = gopOnSceneChange

		openGop = streamServerControl.config.streamserver.openGop.value
		if openGop != streamServerControl.openGop:
			streamServerControl.openGop = openGop

		bFrames = streamServerControl.config.streamserver.bFrames.value
		if bFrames != streamServerControl.bFrames:
			streamServerControl.bFrames = bFrames

		pFrames = streamServerControl.config.streamserver.pFrames.value
		if pFrames != streamServerControl.pFrames:
			streamServerControl.pFrames = pFrames

		if StreamServerControl.FEATURE_SLICES:
			slices = streamServerControl.config.streamserver.slices.value
			if slices != streamServerControl.slices:
				streamServerControl.slices = slices

		level = int(streamServerControl.config.streamserver.level.value)
		if level != streamServerControl.level:
			streamServerControl.level = level

		profile = int(streamServerControl.config.streamserver.profile.value)
		if profile != streamServerControl.profile:
			streamServerControl.profile = profile

		framerate = streamServerControl.config.streamserver.framerate.value
		if framerate != streamServerControl.framerate:
			streamServerControl.framerate = framerate

		streamServerControl.enableRTSP(rtsp_enabled, rtsp_path, 554, rtsp_user, rtsp_password)
		streamServerControl.enableHLS(hls_enabled, hls_path, 8080, hls_user, hls_password)
		streamServerControl.config.streamserver.mediator.enabled.value = isMediatorEnabled

class EncoderPreset(object):
	def __init__(self, name, videoBitrate, audioBitrate, resolution, fps=StreamServerControl.FRAME_RATE_25):
		self.name = name
		self.videoBitrate = videoBitrate
		self.audioBitrate = audioBitrate
		self.resolution = resolution
		self.fps = fps

class StreamServerConfig(Screen, ConfigListScreen):
	skin = """
		<screen name="StreamServerConfig" position="center,120" size="920,520" title="Stream Server configuration">
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="10,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="210,5" size="200,40" />
			<widget source="key_yellow" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="560,1" backgroundColor="grey" />
			<widget name="config" position="10,55" size="560,450" scrollbarMode="showOnDemand" zPosition="1"/>
			<ePixmap position="580,5" size="330,500" pixmap="skin_default/menu.png" zPosition="-1" scale="stretch"/>
			<!-- details -->
			<widget name="details_label" position="590,20" zPosition="2" size="300,25" font="Regular;20" backgroundColor="background" halign="center" transparent="1" />
			<widget name="details" position="590,50" zPosition="2" size="300,320" font="Regular;18" backgroundColor="background" halign="center" transparent="1" />
			<widget name="details_hint" position="580,390" zPosition="2" size="330,45" font="Regular;17" backgroundColor="background" halign="center" transparent="1" />
			<!-- info -->
			<widget name="info" position="590,450" zPosition="2" size="310,45" font="Regular;17" halign="center" valign="bottom" backgroundColor="background" transparent="1" />
		</screen>"""

	PRESETS = [
		EncoderPreset(_("Very Low"), 800, 64, StreamServerControl.RES_KEY_PAL),
		EncoderPreset(_("Low"), 1200, 96, StreamServerControl.RES_KEY_PAL),
		EncoderPreset(_("Medium"), 2000, 128, StreamServerControl.RES_KEY_720P),
		EncoderPreset(_("High"), 4000, 192, StreamServerControl.RES_KEY_720P),
		EncoderPreset(_("Higher"), 6000, 256, StreamServerControl.RES_KEY_1080P),
		EncoderPreset(_("Best"), 8000, 256, StreamServerControl.RES_KEY_1080P),
		EncoderPreset(_("Maximum"), 10000, 448, StreamServerControl.RES_KEY_1080P),
	]

	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		self._streamServerControl = streamServerControl
		self._upstreamBitrate = 0
		self._clientCount = streamServerControl.rtspClientCount

		self._key_blue = StaticText("")
		self["key_blue"] = self._key_blue
		self["key_yellow"] = StaticText(_("Presets"))
		self._info = Label("")
		self["info"] = self._info

		self["details_label"] = Label(_("Status Detail"))
		self._details = Label(_("No details available..."))
		self["details"] = self._details
		self._detailsHint = Label("Press PVR in channel selection to change the service in background mode")
		self["details_hint"] = self._detailsHint

		if not self._setInfoText in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self._setInfoText)

		self._closeAfterApply = False
		self._presetChoiceBox = None

		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"blue": self.apply,
			"yellow": self._showPresets,
			"cancel": self._applyAndClose,
			"ok" : self._applyAndClose,
		}, -2)

		self.setTitle(_("Streaming Server"))

		streamServerControl.onRtspClientCountChanged.append(self._onRtspClientCountChanged)

		self._streamServerControl.config.streamserver.rtsp.enabled.addNotifier(self._onEnabled, initial_call=False)
		self._streamServerControl.config.streamserver.hls.enabled.addNotifier(self._onEnabled, initial_call=False)
		self._streamServerControl.config.streamserver.gopLength.addNotifier(self._onGopLengthChanged, initial_call=False)
		self._streamServerControl.config.streamserver.bFrames.addNotifier(self._onBframesChanged, initial_call=False)
		self._createSetup()

	def _onBframesChanged(self, element):
		self._createSetup()

	def _onRtspClientCountChanged(self, count, client):
		self._clientCount = count
		self._setInfoText()

	def _onLoginCreated(self, *args):
		self._createSetup()

	def _onClientStreamUrlChanged(self, *args):
		self._setInfoText()

	def apply(self):
		applyConfig(self._streamServerControl)
		if self._closeAfterApply:
			self.close()

	def _applyAndClose(self):
		self._closeAfterApply = True
		self.apply()

	def close(self):
		streamServerControl.onRtspClientCountChanged.remove(self._onRtspClientCountChanged)

		self._streamServerControl.config.streamserver.rtsp.enabled.removeNotifier(self._onEnabled)
		self._streamServerControl.config.streamserver.hls.enabled.removeNotifier(self._onEnabled)
		self._streamServerControl.config.streamserver.gopLength.removeNotifier(self._onGopLengthChanged)
		self._streamServerControl.config.streamserver.bFrames.removeNotifier(self._onBframesChanged)
		self._streamServerControl.config.streamserver.save()

		Screen.close(self)

	def _onEnabled(self, element):
		self.apply()
		self._streamServerControl.config.streamserver.save()
		self._createSetup()

	def _onGopLengthChanged(self, element):
		self._createSetup()

	def _onMediatorEnabled(self, element):
		self._createSetup()

	def _createSetup(self):
		self._setInfoText()

		entries = [ getConfigListEntry(_("RTSP")),
					getConfigListEntry(_("RTSP Server"), self._streamServerControl.config.streamserver.rtsp.enabled),]

		if self._streamServerControl.config.streamserver.rtsp.enabled.value:
			entries.extend([
				getConfigListEntry(_("User"), self._streamServerControl.config.streamserver.rtsp.user),
				getConfigListEntry(_("Password"), self._streamServerControl.config.streamserver.rtsp.password),
			])
			if config.usage.setup_level.index > 0:
				entries.extend([
					#getConfigListEntry(_("RTSP Port"), self._streamServerControl.config.streamserver.rtsp.port),
					getConfigListEntry(_("RTSP Path"), self._streamServerControl.config.streamserver.rtsp.path),
				])

		entries.extend([
			getConfigListEntry(_("HLS")),
			getConfigListEntry(_("HLS Server"), self._streamServerControl.config.streamserver.hls.enabled)
		])
		if self._streamServerControl.config.streamserver.hls.enabled.value:
			entries.extend([
				getConfigListEntry(_("User"), self._streamServerControl.config.streamserver.hls.user),
				getConfigListEntry(_("Password"), self._streamServerControl.config.streamserver.hls.password)
			])
			if config.usage.setup_level.index > 0:
				entries.append(getConfigListEntry(_("Path"), self._streamServerControl.config.streamserver.hls.path))

		if self._streamServerControl.isAnyEnabled():
			entries.extend([
					getConfigListEntry(_("Bitrates")),
					getConfigListEntry(_("Audio Bitrate"),self. _streamServerControl.config.streamserver.audioBitrate),
					getConfigListEntry(_("Video Bitrate"), self._streamServerControl.config.streamserver.videoBitrate),
					getConfigListEntry(_("Basic Encoder Settings")),
					getConfigListEntry(_("Data Source"), self._streamServerControl.config.streamserver.source),
					getConfigListEntry(_("Resolution"), self._streamServerControl.config.streamserver.resolution),
					getConfigListEntry(_("Framerate"), self._streamServerControl.config.streamserver.framerate),
					getConfigListEntry(_("Expert Encoder Settings")),
					getConfigListEntry(_("GOP Length (ms, P-Frames auto calculated)"), self._streamServerControl.config.streamserver.gopLength)
				])

			if self._streamServerControl.config.streamserver.gopLength.value == eStreamServer.GOP_LENGTH_AUTO:
				entries.append( getConfigListEntry(_("Number of P-Frames"), self._streamServerControl.config.streamserver.pFrames) )

			entries.append( getConfigListEntry(_("Number of B-Frames"), self._streamServerControl.config.streamserver.bFrames) )

			if self._streamServerControl.config.streamserver.bFrames.value:
				entries.append( getConfigListEntry(_("Open GOP"), self._streamServerControl.config.streamserver.openGop) )

			if StreamServerControl.FEATURE_SCENE_DETECTION and not self._streamServerControl.config.streamserver.bFrames.value and not self._streamServerControl.config.streamserver.gopLength.value:
				entries.append( getConfigListEntry(_("New GOP On Scene Change"), self._streamServerControl.config.streamserver.gopOnSceneChange) )

			if StreamServerControl.FEATURE_SLICES:
				entries.append( getConfigListEntry(_("Number of slices"), self._streamServerControl.config.streamserver.slices) )

			entries.extend([
					getConfigListEntry(_("Level"), self._streamServerControl.config.streamserver.level),
					getConfigListEntry(_("Profile"), self._streamServerControl.config.streamserver.profile),
				])

		self["config"].list = entries

	def _setInfoText(self):
		detailtext =_("Local client(s):\n    %s") %(self._clientCount)
		self._details.setText(detailtext)

		localstreams = []
		if self._streamServerControl.config.streamserver.rtsp.enabled.value or self._streamServerControl.config.streamserver.hls.enabled.value:
			ifaces = iNetworkInfo.getConfiguredInterfaces()
			for iface in ifaces.itervalues():
				ip = iface.getIpv4()
				if not ip:
					ip = iface.getIpv6()
				if ip:
					if self._streamServerControl.config.streamserver.rtsp.enabled.value:
						localstreams.append("rtsp://%s:%s/%s" %(ip.getAddress(), self._streamServerControl.config.streamserver.rtsp.port.value, self._streamServerControl.config.streamserver.rtsp.path.value))
					if self._streamServerControl.config.streamserver.hls.enabled.value:
						localstreams.append("http://%s:%s/%s.m3u8" %(ip.getAddress(), self._streamServerControl.config.streamserver.hls.port.value, self._streamServerControl.config.streamserver.hls.path.value))
					break

		infotext = ""
		if not localstreams:
			infotext = _("no active streams...")
		else:
			infotext = "\n".join(localstreams)
		self._info.setText(infotext)

	def _showPresets(self):
		presets = []
		for preset in self.PRESETS:
			presets.append((preset.name, preset))
		current = self.PRESETS[0]
		title = _("Video Bitrate:\t%s\nAudio Bitrate:\t%s\nResolution:\t%s") %(current.videoBitrate, current.audioBitrate, current.resolution)
		self._presetChoiceBox = self.session.openWithCallback(self._onPresetSelected, ChoiceBox, title=title, titlebartext=_("Encoder Presets"), list=presets)
		self._presetChoiceBox["list"].onSelectionChanged.append(self._onSelectedPresetChanged)
		self._presetChoiceBox.onLayoutFinish.append(self._onSelectedPresetChanged)

	def _onSelectedPresetChanged(self, *args):
		if not self._presetChoiceBox:
			return
		current = self._presetChoiceBox["list"].getCurrent()
		if not current:
			return
		current = current[0][1]
		text = _("Video Bitrate:\t%s\nAudio Bitrate:\t%s\nResolution:\t%s") %(current.videoBitrate, current.audioBitrate, current.resolution)
		self._presetChoiceBox["text"].setText(text)

	def _onPresetSelected(self, choice):
		self._presetChoiceBox = None
		if choice:
			preset = choice[1]
			self._streamServerControl.config.streamserver.videoBitrate.value = preset.videoBitrate
			self._streamServerControl.config.streamserver.audioBitrate.value = preset.audioBitrate
			if preset.resolution != self._streamServerControl.config.streamserver.resolution.value:
				self._streamServerControl.config.streamserver.resolution.value = preset.resolution
			self._createSetup()
