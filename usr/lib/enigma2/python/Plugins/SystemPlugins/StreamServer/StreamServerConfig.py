from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.StreamServerControl import StreamServerControl, streamServerControl
from Components.config import config, getConfigListEntry
from Components.Network import iNetworkInfo

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

def applyConfig(streamServerControl, initial=False, forceRestart=False):
		if not streamServerControl.isConnected():
			return

		isMediatorEnabled = config.streamserver.mediator.enabled.value
		if initial:
			config.streamserver.mediator.enabled.value = False

		rtsp_enabled = config.streamserver.rtsp.enabled.value
		rtsp_path = config.streamserver.rtsp.path.value
		rtsp_port = config.streamserver.rtsp.port.value
		hls_enabled = config.streamserver.hls.enabled.value
		hls_port = config.streamserver.hls.port.value
		user = config.streamserver.user.value
		password = config.streamserver.password.value

		if forceRestart:
			streamServerControl.enableRTSP(False, rtsp_path, rtsp_port, user, password)
			streamServerControl.enableHLS(False, hls_port, user, password)
			config.streamserver.mediator.enabled.value = False

		inputMode = int(config.streamserver.source.value)
		streamServerControl.setInputMode(inputMode)

		audioBitrate = config.streamserver.audioBitrate.value
		if audioBitrate != streamServerControl.audioBitrate:
			streamServerControl.audioBitrate = config.streamserver.audioBitrate.value

		videoBitrate = config.streamserver.videoBitrate.value
		if videoBitrate != streamServerControl.videoBitrate:
			streamServerControl.videoBitrate = config.streamserver.videoBitrate.value

		autoBitrate = config.streamserver.autoBitrate.value
		if autoBitrate != streamServerControl.autoBitrate:
			streamServerControl.autoBitrate = autoBitrate

		resolution = StreamServerControl.RESOLUTIONS[config.streamserver.resolution.value]
		if resolution != streamServerControl.resolution:
			streamServerControl.resolution = StreamServerControl.RESOLUTIONS[config.streamserver.resolution.value]

		framerate = int(config.streamserver.framerate.value)
		if framerate != streamServerControl.framerate:
			streamServerControl.framerate = framerate

		streamServerControl.enableRTSP(rtsp_enabled, rtsp_path, rtsp_port, user, password)
		streamServerControl.enableHLS(hls_enabled, hls_port, user, password)
		config.streamserver.mediator.enabled.value = isMediatorEnabled

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
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="210,5" size="200,40" alphatest="on" />
			<widget source="key_yellow" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="560,1" backgroundColor="grey" />
			<widget name="config" position="10,55" size="560,450" scrollbarMode="showOnDemand" zPosition="1"/>
			<ePixmap position="580,5" size="330,500" pixmap="skin_default/menu.png" zPosition="-1"/>
			<!-- details -->
			<widget name="details_label" position="590,20" zPosition="2" size="300,25" font="Regular;20" backgroundColor="background" halign="center" transparent="1" />
			<widget name="details" position="590,50" zPosition="2" size="300,320" font="Regular;18" backgroundColor="background" halign="center" transparent="1" />
			<widget name="details_hint" position="580,390" zPosition="2" size="330,45" font="Regular;17" backgroundColor="background" halign="center" transparent="1" />
			<!-- info -->
			<widget name="info" position="590,450" zPosition="2" size="310,45" font="Regular;17" halign="center" valign="bottom" backgroundColor="background" transparent="1" />
		</screen>"""

	BASIC_SETTINGS = [
		config.streamserver.user,
		config.streamserver.password,
		config.streamserver.source,
		config.streamserver.resolution,
		config.streamserver.framerate,
	]

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

		self.__encoderRestartRequired = False
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

		config.streamserver.rtsp.enabled.addNotifier(self._onEnabled, initial_call=False)
		config.streamserver.hls.enabled.addNotifier(self._onEnabled, initial_call=False)
		#Basic encoder setting change notifier
		for cfg in self.BASIC_SETTINGS:
			cfg.addNotifier(self._onBasicEncoderSettingChanged, initial_call=False)
		self._createSetup()

	def _getEncoderRestartRequired(self):
		return self.__encoderRestartRequired

	def _setEncoderRestartRequired(self, value):
		self.__encoderRestartRequired = value
		if self.__encoderRestartRequired:
			self._key_blue.setText(_("Apply"))
		else:
			self._key_blue.setText("")

	_encoderRestartRequired = property(_getEncoderRestartRequired, _setEncoderRestartRequired)

	def _onRtspClientCountChanged(self, count, client):
		self._clientCount = count
		self._setInfoText()

	def _onLoginCreated(self, *args):
		self._createSetup()

	def _onClientStreamUrlChanged(self, *args):
		self._setInfoText()

	def apply(self):
		if self._encoderRestartRequired:
			self.session.openWithCallback(
				self._onEncoderRestartResponse,
				MessageBox,
				text= _("You have changed basic encoder settings.\nTo apply these changes all streams have to be stopped.\nDo you want to stop and restart all streams now to apply these settings immediately?"),
				title=_("Stream restart required"))
			return
		else:
			applyConfig(self._streamServerControl)
			if self._closeAfterApply:
				self.close()

	def _onEncoderRestartResponse(self, response):
		self._encoderRestartRequired = False
		if response:
			applyConfig(self._streamServerControl, forceRestart=True)
		else:
			applyConfig(self._streamServerControl)
		if self._closeAfterApply:
			self.close()

	def _applyAndClose(self):
		self._closeAfterApply = True
		self.apply()

	def close(self):
		streamServerControl.onRtspClientCountChanged.remove(self._onRtspClientCountChanged)

		config.streamserver.rtsp.enabled.removeNotifier(self._onEnabled)
		config.streamserver.hls.enabled.removeNotifier(self._onEnabled)
		for cfg in self.BASIC_SETTINGS:
			cfg.removeNotifier(self._onBasicEncoderSettingChanged)
		config.streamserver.save()

		Screen.close(self)

	def _onEnabled(self, element):
		if not self._streamServerControl.isConnected():
			return
		self.apply()
		config.streamserver.save()
		self._createSetup()

	def _onMediatorEnabled(self, element):
		if not self._streamServerControl.isConnected():
			return
		self._createSetup()

	def _onBasicEncoderSettingChanged(self, element):
		self._encoderRestartRequired = True

	def _createSetup(self):
		self._setInfoText()
		if not self._streamServerControl.isConnected():
			return

		entries = [ getConfigListEntry(_("RTSP")),
					getConfigListEntry(_("RTSP Server"), config.streamserver.rtsp.enabled),]

		if config.streamserver.rtsp.enabled.value:
			entries.extend([
					getConfigListEntry(_("User"), config.streamserver.user),
					getConfigListEntry(_("Password"), config.streamserver.password),
				])
			if config.usage.setup_level.index > 0:
				entries.extend([
					getConfigListEntry(_("RTSP Port"), config.streamserver.rtsp.port),
					getConfigListEntry(_("RTSP Path"), config.streamserver.rtsp.path),
				])

		entries.extend([
			getConfigListEntry(_("HLS")),
			getConfigListEntry(_("HLS Server"), config.streamserver.hls.enabled)
		])
		if config.streamserver.hls.enabled.value and config.usage.setup_level.index > 0:
				entries.append(getConfigListEntry(_("HLS Port"), config.streamserver.hls.port))

		if config.streamserver.rtsp.enabled.value:
			entries.extend([
					getConfigListEntry(_("Authentication")),

			])

		if self._streamServerControl.isAnyEnabled():
			entries.extend([
					getConfigListEntry(_("Bitrates")),
					getConfigListEntry(_("Audio Bitrate"), config.streamserver.audioBitrate),
					getConfigListEntry(_("Video Bitrate"), config.streamserver.videoBitrate),
					getConfigListEntry(_("Basic Encoder Settings")),
					getConfigListEntry(_("Data Source"), config.streamserver.source),
					getConfigListEntry(_("Resolution"), config.streamserver.resolution),
					getConfigListEntry(_("Framerate"), config.streamserver.framerate),
				])

		self["config"].list = entries

	def _setInfoText(self):
		if not self._streamServerControl.isConnected():
			self._info.setText(_("ERROR: Streaming Server not available!"))
			return

		detailtext =_("Local client(s):\n    %s") %(self._clientCount)
		self._details.setText(detailtext)

		localstreams = []
		if config.streamserver.rtsp.enabled.value or config.streamserver.hls.enabled.value:
			ifaces = iNetworkInfo.getConfiguredInterfaces()
			for iface in ifaces.itervalues():
				ip = iface.getIpv4()
				if not ip:
					ip = iface.getIpv6()
				if ip:
					if config.streamserver.rtsp.enabled.value:
						localstreams.append("rtsp://%s:%s/%s" %(ip.getAddress(), config.streamserver.rtsp.port.value, config.streamserver.rtsp.path.value))
					if config.streamserver.hls.enabled.value:
						localstreams.append("http://%s:%s/dream.m3u8" %(ip.getAddress(), config.streamserver.hls.port.value))
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
			config.streamserver.videoBitrate.value = preset.videoBitrate
			config.streamserver.audioBitrate.value = preset.audioBitrate
			if preset.resolution != config.streamserver.resolution.value:
				config.streamserver.resolution.value = preset.resolution
			self._createSetup()
