from enigma import eStreamProcessor, cvar

from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigInteger, ConfigOnOff, ConfigPassword, ConfigSelection, Config, ConfigSubsection, ConfigText, ConfigYesNo, ConfigSubDict
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry
from Components.Network import iNetworkInfo

from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
import six


class StreamServicesConfig:
	ADAPTIVE_MODES = [
		("START_WORST", _("Start worst")),
		("START_MID", _("Start mid")),
		("START_BEST", _("Start best")),

		("WORST", _("Worst")),	# non-adaptive
		("MID", _("Mid")),		# non-adaptive
		("BEST", _("Best"))		# non-adaptive
	]

	DASH_MIN_BUFFER_MODES = [
		("SERVER", _("Server buffer time")),
		("SERVER_2", _("Half server buffer time")),
		("SERVER_4", _("Quarter server buffer time")),
		("CUSTOM", _("Custom buffer time"))
	]

	instance = None
	def __init__(self):
		assert(not StreamServicesConfig.instance)
		StreamServicesConfig.instance = self

		# there may be added new processors after this constructor.. keep track of them
		self._processorAddedConn = cvar.eStreamProcessor_processorAdded.connect(self._addProcessor)

		self._initStreamServicesConfig()

	def _initStreamServicesConfig(self):
		config.streamservices = ConfigSubsection()

		config.streamservices.dash = ConfigSubsection()
		config.streamservices.dash.adaptive = ConfigSubsection()
		config.streamservices.dash.adaptive.mode = ConfigSelection(StreamServicesConfig.ADAPTIVE_MODES, default="START_MID")
		config.streamservices.dash.min_buffer_mode = ConfigSelection(StreamServicesConfig.DASH_MIN_BUFFER_MODES, default="SERVER")
		config.streamservices.dash.min_buffer = ConfigInteger(4, [0, 15])
		config.streamservices.dash.fallback_min_buffer = ConfigInteger(4, [0, 15])

		config.streamservices.hls = ConfigSubsection()
		config.streamservices.hls.min_buffer = ConfigInteger(4, [0, 15])

		config.streamservices.processors = ConfigSubDict()

		for processor in eStreamProcessor.getProcessors():
			self._addProcessor(processor)

	def _addProcessor(self, processor):
		procName = processor.getName()
		config.streamservices.processors[procName] = ConfigSubsection()
		config.streamservices.processors[procName].limitBandwidth = ConfigInteger(0, [0, 1000])
		config.streamservices.processors[procName].limitResolution = ConfigInteger(0, [0, 2160])


class StreamServicesConfigScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="StreamServicesConfig" position="center,120" size="590,520" title="Stream Services configuration">
			<ePixmap pixmap="skin_default/buttons/green.png" position="10,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="210,5" size="200,40" />
			<widget source="key_green" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="560,1" backgroundColor="grey" />
			<widget name="config" position="10,55" size="560,450" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)

		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Default"))

		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self._close,
			"green": self._close,
			"yellow": self.reset,
		}, -2)

		self.setTitle(_("Stream Client"))

		config.streamservices.dash.min_buffer_mode.addNotifier(self.dashMinBufferModeChanged)

		self._createSetup()

	def _createSetup(self):
		entries = [
		]

		entries.extend([ getConfigListEntry(_("DASH")) ])
		entries.extend([ getConfigListEntry(_("Adaptive Mode"), config.streamservices.dash.adaptive.mode) ])
		entries.extend([ getConfigListEntry(_("Minimum Buffer Mode"), config.streamservices.dash.min_buffer_mode)])
		if config.streamservices.dash.min_buffer_mode.value == "CUSTOM":
			entries.extend( [getConfigListEntry(_("Minimum buffer (s)"), config.streamservices.dash.min_buffer)])
		else:
			entries.extend( [getConfigListEntry(_("Minimum buffer (Fallback, s)"), config.streamservices.dash.fallback_min_buffer)])

		entries.extend([ getConfigListEntry(_("HLS")) ])
		entries.extend([ getConfigListEntry(_("Minimum buffer (s)"), config.streamservices.hls.min_buffer)])

		for procName, procConfig in config.streamservices.processors.iteritems():
			entries.extend( [ getConfigListEntry(_("Processor") + " " + procName) ])
			entries.extend( [ getConfigListEntry(_("Limit by bandwidth (MBit/s)"), procConfig.limitBandwidth) ])
			entries.extend( [ getConfigListEntry(_("Limit by resolution (Height in px)"), procConfig.limitResolution) ])

		self["config"].list = entries

	def _close(self):
		config.streamservices.save()
		configfile.save()
		self.close()

	def dashMinBufferModeChanged(self, cfgelement):
		self._createSetup()

	def reset(self):
		config.streamservices.dash.adaptive.mode.value = "START_MID"
		config.streamservices.dash.min_buffer_mode.value = "SERVER"
		config.streamservices.dash.min_buffer.value = 4
		config.streamservices.dash.fallback_min_buffer.value = 4
		config.streamservices.hls.min_buffer.value = 4

		for procName, procConfig in config.streamservices.processors.iteritems():
			config.streamservices.processors[procName].limitBandwidth.value = 0
			config.streamservices.processors[procName].limitResolution.value = 0

		self._createSetup()

StreamServicesConfig()
