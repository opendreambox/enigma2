from enigma import eStreamProcessorFactory, cvar

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
		self._processorAddedConn = cvar.eStreamProcessorFactory_factoryAdded.connect(self._addFactory)

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

		for factory in eStreamProcessorFactory.getFactories():
			self._addFactory(factory)

	def _addFactory(self, factory):
		procName = factory.getName()
		config.streamservices.processors[procName] = ConfigSubsection()
		config.streamservices.processors[procName].limitBandwidth = ConfigInteger(0, [0, 1000])
		config.streamservices.processors[procName].limitResolution = ConfigInteger(0, [0, 2160])


class StreamServicesConfigScreen(Screen, ConfigListScreen):
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
		self.onClose.append(self._onClose)

		self._createSetup()

	def _onClose(self):
		config.streamservices.dash.min_buffer_mode.removeNotifier(self.dashMinBufferModeChanged)

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
