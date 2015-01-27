from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.StreamServerControl import StreamServerControl
from Components.config import config, ConfigSubsection, ConfigOnOff, ConfigSelection, ConfigInteger, getConfigListEntry

from Screens.Screen import Screen

config.streamserver = ConfigSubsection()
config.streamserver.enabled = ConfigOnOff(default=False)
config.streamserver.audioBitrate = ConfigInteger(128, StreamServerControl.AUDIO_BITRATE_LIMITS)
config.streamserver.videoBitrate = ConfigInteger(2048, StreamServerControl.VIDEO_BITRATE_LIMITS)
config.streamserver.resolution = ConfigSelection(StreamServerControl.RESOLUTIONS.keys(), default="720p")
config.streamserver.framerate = ConfigSelection(StreamServerControl.FRAME_RATES, default=StreamServerControl.FRAME_RATE_25)

def applyConfig(streamServerControl):
		streamServerControl.reconnect()
		if not streamServerControl.isConnected():
			return

		enabled = config.streamserver.enabled.value
		if enabled != streamServerControl.enabled:
			streamServerControl.enabled = config.streamserver.enabled.value
		if not enabled:
			return

		audioBitrate = config.streamserver.audioBitrate.value
		if audioBitrate != streamServerControl.audioBitrate:
			streamServerControl.audioBitrate = config.streamserver.audioBitrate.value

		videoBitrate = config.streamserver.videoBitrate.value
		if videoBitrate != streamServerControl.videoBitrate:
			streamServerControl.videoBitrate = config.streamserver.videoBitrate.value

		resolution = StreamServerControl.RESOLUTIONS[config.streamserver.resolution.value]
		if resolution != streamServerControl.resolution:
			streamServerControl.resolution = StreamServerControl.RESOLUTIONS[config.streamserver.resolution.value]

		framerate = config.streamserver.framerate.value
		if framerate != streamServerControl.framerate:
			streamServerControl.framerate = framerate

class StreamServerConfig(Screen, ConfigListScreen):
	skin = """
		<screen name="StreamServerConfig" position="center,center" size="560,400" title="Stream Server configuration">
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
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		self._streamServerControl = StreamServerControl()

		self["key_blue"] = StaticText(_("Apply"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"blue": self.apply,
			"save": self.close,
			"cancel": self.close,
			"ok" : self.close,
		}, -2)

		config.streamserver.enabled.addNotifier(self._onEnabled, initial_call=False)
		self._createSetup()

	def apply(self):
		applyConfig(self._streamServerControl)

	def close(self):
		self.apply()
		config.streamserver.enabled.removeNotifier(self._onEnabled)
		config.streamserver.save()
		Screen.close(self)

	def _onEnabled(self, element):
		self._streamServerControl.reconnect()
		if not self._streamServerControl.isConnected():
			return
		self.apply()
		config.streamserver.save()
		self._createSetup()

	def _createSetup(self):
		self._streamServerControl.reconnect()
		if not self._streamServerControl.isConnected():
			return

		config.streamserver.resolution.enabled = config.streamserver.framerate.enabled = not self._streamServerControl.enabled
		entries = [ getConfigListEntry(_("Enable Streaming Server"), config.streamserver.enabled),
					getConfigListEntry(_("Audio Bitrate"), config.streamserver.audioBitrate),
					getConfigListEntry(_("Video Bitrate"), config.streamserver.videoBitrate),
					getConfigListEntry(_("Resolution"), config.streamserver.resolution),
					getConfigListEntry(_("Framerate"), config.streamserver.framerate),
				]
		self["config"].list = entries
