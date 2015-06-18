from enigma import eServiceReference

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.StreamServerControl import StreamServerControl, streamServerControl
from Components.config import config, ConfigSubsection, ConfigOnOff, ConfigSelection, ConfigInteger, ConfigText, ConfigPassword, getConfigListEntry
from Components.Network import iNetworkInfo
from Screens.Screen import Screen

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

def applyConfig(streamServerControl, initial=False):
		if not streamServerControl.isConnected():
			return

		enabled = config.streamserver.enabled.value
		path = config.streamserver.rtsppath.value
		port = config.streamserver.rtspport.value
		user = config.streamserver.user.value
		password = config.streamserver.password.value

		inputMode = int(config.streamserver.source.value)
		if inputMode == StreamServerControl.INPUT_MODE_BACKGROUND and enabled:
			streamServerControl.setEncoderService(eServiceReference(config.streamserver.lastservice.value))
		else:
			streamServerControl.stopEncoderService()

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

		framerate = config.streamserver.framerate.value
		if framerate != streamServerControl.framerate:
			streamServerControl.framerate = framerate

		streamServerControl.setEnabled(enabled, path, port, user, password)

class StreamServerConfig(Screen, ConfigListScreen):
	skin = """
		<screen name="StreamServerConfig" position="center,center" size="900,500" title="Stream Server configuration">
			<!--
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			-->
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<!--
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			-->
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,380" scrollbarMode="showOnDemand" zPosition="1"/>
			<widget name="info" position="5,440" size="550,50" font="Regular;16" halign="center" valign="bottom" backgroundColor="background" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="565,5" size="330,490" zPosition="0" backgroundColor="#0E3B62" />
			<widget name="details_hint" position="570,center" zPosition="2" size="330,50" font="Regular;16" backgroundColor="#0E3B62" halign="center" transparent="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		self._streamServerControl = streamServerControl
		self._upstreamBitrate = 0

		self["key_blue"] = StaticText(_("Apply"))
		self._info = Label("")
		self["info"] = self._info

		self._detailsHint = Label("Press PVR in channel selection to change the service in background mode")
		self["details_hint"] = self._detailsHint

		if not self._setInfoText in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self._setInfoText)

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"blue": self.apply,
			"save": self.close,
			"cancel": self.close,
			"ok" : self.close,
		}, -2)

		config.streamserver.enabled.addNotifier(self._onEnabled, initial_call=False)
		self._createSetup()

	def _onLoginCreated(self, *args):
		self._createSetup()

	def apply(self):
		applyConfig(self._streamServerControl)

	def close(self):
		config.streamserver.enabled.removeNotifier(self._onEnabled)
		config.streamserver.save()

		self.apply()
		Screen.close(self)

	def _onEnabled(self, element):
		if not self._streamServerControl.isConnected():
			return
		self.apply()
		config.streamserver.save()
		self._createSetup()

	def _createSetup(self):
		self._setInfoText()
		if not self._streamServerControl.isConnected():
			return

		en = not config.streamserver.enabled.value
		config.streamserver.resolution.enabled = en
		config.streamserver.framerate.enabled = en
		config.streamserver.source.enabled = en

		entries = [ getConfigListEntry(_("Enable Streaming Server"), config.streamserver.enabled),
					getConfigListEntry(_("Data Source"), config.streamserver.source),
					getConfigListEntry(_("Audio Bitrate"), config.streamserver.audioBitrate),
					getConfigListEntry(_("Video Bitrate"), config.streamserver.videoBitrate),
					getConfigListEntry(_("Adaptive Bitrate"), config.streamserver.autoBitrate),
					getConfigListEntry(_("Resolution"), config.streamserver.resolution),
					getConfigListEntry(_("Framerate"), config.streamserver.framerate),
					getConfigListEntry(_("RTSP Port"), config.streamserver.rtspport),
					getConfigListEntry(_("RTSP Path"), config.streamserver.rtsppath),
					getConfigListEntry(_("User"), config.streamserver.user),
					getConfigListEntry(_("Password"), config.streamserver.password),
				]
		self["config"].list = entries

	def _setInfoText(self):
		if not self._streamServerControl.isConnected():
			self._info.setText(_("ERROR: Streaming Server not available!"))
			return

		infotext = ""
		if config.streamserver.enabled.value:
			ifaces = iNetworkInfo.getConfiguredInterfaces()
			for iface in ifaces.itervalues():
				ip = iface.getIpv4()
				if not ip:
					ip = iface.getIpv6()
				if ip:
					infotext = "rtsp://%s:%s/%s" %(ip.getAddress(), config.streamserver.rtspport.value, config.streamserver.rtsppath.value)
					break
		self._info.setText(infotext)
