from Components.Harddisk import harddiskmanager
from config import ConfigSubsection, ConfigYesNo, config, ConfigSelection, ConfigText, ConfigNumber, ConfigSet, ConfigLocations, ConfigInteger, ConfigSlider
from Tools.Directories import resolveFilename, SCOPE_HDD
from enigma import setTunerTypePriorityOrder, eEnv

def BaseInitUsageConfig():
	config.usage = ConfigSubsection();

	config.usage.keymap = ConfigText(default = eEnv.resolve("${datadir}/enigma2/keymap.xml"))

	config.usage.setup_level = ConfigSelection(default = "intermediate", choices = [
		("simple", _("Simple")),
		("intermediate", _("Intermediate")),
		("expert", _("Expert")) ])

	config.seek = ConfigSubsection()
	config.seek.selfdefined_13 = ConfigNumber(default=15)
	config.seek.selfdefined_46 = ConfigNumber(default=60)
	config.seek.selfdefined_79 = ConfigNumber(default=300)

	config.seek.speeds_forward = ConfigSet(default=[2, 4, 8, 16, 32, 64, 128], choices=[2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.speeds_backward = ConfigSet(default=[2, 4, 8, 16, 32, 64, 128], choices=[1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.speeds_slowmotion = ConfigSet(default=[2, 4, 8], choices=[2, 4, 6, 8, 12, 16, 25])

	config.seek.enter_forward = ConfigSelection(default = "2", choices = ["2", "4", "6", "8", "12", "16", "24", "32", "48", "64", "96", "128"])
	config.seek.enter_backward = ConfigSelection(default = "1", choices = ["1", "2", "4", "6", "8", "12", "16", "24", "32", "48", "64", "96", "128"])

	def updateEnterForward(configElement):
		if not configElement.value:
			configElement.value = [2]
		updateChoices(config.seek.enter_forward, configElement.value)
	config.seek.speeds_forward.addNotifier(updateEnterForward, immediate_feedback = False)

	def updateEnterBackward(configElement):
		if not configElement.value:
			configElement.value = [2]
		updateChoices(config.seek.enter_backward, configElement.value)
	config.seek.speeds_backward.addNotifier(updateEnterBackward, immediate_feedback = False)

def FinalInitUsageConfig():
	try:
		usage_old = config.usage.dict().copy()
	except KeyError:
		usage_old = { }

	try:
		seek_old = config.seek.dict().copy()
	except KeyError:
		seek_old = { }

	#We have do it again to ensure tranlsations are applied after language load has finished
	config.usage.setup_level = ConfigSelection(default = "intermediate", choices = [
		("simple", _("Simple")),
		("intermediate", _("Intermediate")),
		("expert", _("Expert")) ])

	config.seek.on_pause = ConfigSelection(default = "play", choices = [
		("play", _("Play")),
		("step", _("Singlestep (GOP)")),
		("last", _("Last speed")) ])

	inactivity_shutdown_choices = [ ("never", _("disabled")) ]
	for i in range(1,6):
		inactivity_shutdown_choices.extend([("%d" % i, ngettext("%(num)d hour", "%(num)d hours",i) % {"num" : i})])
	config.usage.inactivity_shutdown = ConfigSelection(default = "3", choices = inactivity_shutdown_choices)
	config.usage.inactivity_shutdown_initialized = ConfigYesNo(default = False)
	config.usage.showdish = ConfigYesNo(default = True)
	config.usage.multibouquet = ConfigYesNo(default = False)
	config.usage.multiepg_ask_bouquet = ConfigYesNo(default = False)

	config.usage.quickzap_bouquet_change = ConfigYesNo(default = False)
	config.usage.e1like_radio_mode = ConfigYesNo(default = False)
	config.usage.infobar_timeout = ConfigSelection(default = "5", choices = [
		("0", _("no timeout")), ("1", "1 " + _("second")), ("2", "2 " + _("seconds")), ("3", "3 " + _("seconds")),
		("4", "4 " + _("seconds")), ("5", "5 " + _("seconds")), ("6", "6 " + _("seconds")), ("7", "7 " + _("seconds")),
		("8", "8 " + _("seconds")), ("9", "9 " + _("seconds")), ("10", "10 " + _("seconds"))])
	config.usage.show_infobar_on_zap = ConfigYesNo(default = True)
	config.usage.show_infobar_on_skip = ConfigYesNo(default = True)
	config.usage.show_infobar_on_event_change = ConfigYesNo(default = True)
	config.usage.hdd_standby = ConfigSelection(default = "600", choices = [
		("0", _("no standby")), ("10", "10 " + _("seconds")), ("30", "30 " + _("seconds")),
		("60", "1 " + _("minute")), ("120", "2 " + _("minutes")),
		("300", "5 " + _("minutes")), ("600", "10 " + _("minutes")), ("1200", "20 " + _("minutes")),
		("1800", "30 " + _("minutes")), ("3600", "1 " + _("hour")), ("7200", "2 " + _("hours")),
		("14400", "4 " + _("hours")) ])

	config.usage.pip_zero_button = ConfigSelection(default = "standard", choices = [
		("standard", _("standard")), ("swap", _("swap PiP and main picture")),
		("swapstop", _("move PiP to main picture")), ("stop", _("stop PiP")) ])

	config.usage.default_path = ConfigText(default = resolveFilename(SCOPE_HDD))
	config.usage.timer_path = ConfigText(default = "<default>")
	config.usage.instantrec_path = ConfigText(default = "<default>")
	config.usage.timeshift_path = ConfigText(default = "/media/hdd/")
	config.usage.allowed_timeshift_paths = ConfigLocations(default = ["/media/hdd/"])

	config.usage.on_movie_start = ConfigSelection(default = "ask", choices = [
		("ask", _("Ask user")), ("resume", _("Resume from last position")), ("beginning", _("Start from the beginning")) ])
	config.usage.on_movie_stop = ConfigSelection(default = "ask", choices = [
		("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service")) ])
	config.usage.on_movie_eof = ConfigSelection(default = "ask", choices = [
		("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service")), ("pause", _("Pause movie at end")) ])

	config.usage.resume_treshold = ConfigInteger(default=30, limits=[0,300])

	config.usage.on_long_powerpress = ConfigSelection(default = "show_menu", choices = [
		("show_menu", _("show shutdown menu")),
		("shutdown", _("immediate shutdown")),
		("standby", _("Idle Mode")) ] )

	config.usage.on_short_powerpress = ConfigSelection(default = "standby", choices = [
		("show_menu", _("show shutdown menu")),
		("shutdown", _("immediate shutdown")),
		("standby", _("Idle Mode")) ] )

	config.usage.alternatives_priority = ConfigSelection(default = "0", choices = [
		("0", "DVB-S/-C/-T"),
		("1", "DVB-S/-T/-C"),
		("2", "DVB-C/-S/-T"),
		("3", "DVB-C/-T/-S"),
		("4", "DVB-T/-C/-S"),
		("5", "DVB-T/-S/-C") ])

	config.usage.show_event_progress_in_servicelist = ConfigYesNo(default = False)

	config.usage.blinking_display_clock_during_recording = ConfigYesNo(default = False)

	config.usage.show_message_when_recording_starts = ConfigYesNo(default = True)

	config.usage.load_length_of_movies_in_moviellist = ConfigYesNo(default = True)

	config.usage.timerlist_finished_timer_position = ConfigSelection(default = "beginning", choices = [("beginning", _("at beginning")), ("end", _("at end"))])

	config.usage.text_subtitle_presentation = ConfigSelection(default = "black box", choices = [("black box", _("black box")), ("drop-shadow", _("drop-shadow"))])
	config.usage.text_subtitle_black_box_transparency = ConfigSlider(default = 0x64, increment = 5, limits = (0, 0xff))
	config.usage.ttx_subtitle_prefer_pmt_language_code = ConfigYesNo(default=True)

	# Channelselection settings
	config.usage.configselection_showsettingsincontextmenu = ConfigYesNo(default=True)
	config.usage.configselection_showlistnumbers = ConfigYesNo(default=True)
	config.usage.configselection_showservicename = ConfigYesNo(default=True)
	config.usage.configselection_progressbarposition = ConfigSelection(default = "0", choices = [("0",_("After servicenumber")),("1",_("After servicename")), ("2",_("After servicedescription"))])
	config.usage.configselection_servicenamecolwidth = ConfigInteger(200, limits =(100,400))
	config.usage.configselection_columnstyle = ConfigYesNo(default=False)
	config.usage.configselection_additionaltimedisplayposition = ConfigSelection(default = "1", choices = [("0",_("ahead")),("1",_("behind"))])
	config.usage.configselection_showadditionaltimedisplay = ConfigSelection(default = "0",choices = [("0", _("Off")), ("1", _("Percent")), ("2", _("Remain")),("3", _("Remain / duration")), ("4", _("Elapsed")), ("5", _("Elapsed / duration")), ("6", _("Elapsed / remain / duration")),("7", _("Time"))])
	config.usage.configselection_showpicons = ConfigYesNo(default=False)
	config.usage.configselection_bigpicons = ConfigYesNo(default=False)
	config.usage.configselection_secondlineinfo =  ConfigSelection(default = "0", choices = [("0",_("nothing")),("1",_("short description")), ("2",_("upcoming event"))])

	config.usage.configselection_piconspath = ConfigSelection(default = eEnv.resolve('${datadir}/enigma2/picon_50x30/'), choices = [
				(eEnv.resolve('${datadir}/enigma2/picon_50x30/'), eEnv.resolve('${datadir}/enigma2/picon_50x30')),
				(eEnv.resolve('${datadir}/enigma2/picon/'), eEnv.resolve('${datadir}/enigma2/picon')),
				])

	config.usage.configselection_showrecordings = ConfigYesNo(default=False)
	config.usage.standby_zaptimer_wakeup = ConfigYesNo(default=True)

	seek = config.seek.dict()
	for (key, value) in seek_old.items():
		value_old = value.value
		configEntry = seek[key]
		value_new = configEntry.value
		if value_old != value_new:
			configEntry.value = value_old
		configEntry._ConfigElement__notifiers = value._ConfigElement__notifiers
		configEntry._ConfigElement__notifiers_final = value._ConfigElement__notifiers_final

	usage = config.usage.dict()
	for (key, value) in usage_old.items():
		value_old = value.value
		configEntry = usage[key]
		value_new = configEntry.value
		if value_old != value_new:
			configEntry.value = value_old
		configEntry._ConfigElement__notifiers = value._ConfigElement__notifiers
		configEntry._ConfigElement__notifiers_final = value._ConfigElement__notifiers_final

	if usage_old.get("alternatives_priority", None) == None:
		def TunerTypePriorityOrderChanged(configElement):
			setTunerTypePriorityOrder(int(configElement.value))
		config.usage.alternatives_priority.addNotifier(TunerTypePriorityOrderChanged, immediate_feedback=False)

	if usage_old.get("hdd_standby", None) == None:
		def setHDDStandby(configElement):
			for hdd in harddiskmanager.HDDList():
				hdd[1].setIdleTime(int(configElement.value))
		config.usage.hdd_standby.addNotifier(setHDDStandby, immediate_feedback=False)

	config.usage.record_mode = ConfigSelection(default = "direct_io", choices = [
		("direct_io", _("Direct IO (default)")),
		("cached_io", _("Cached IO")) ] )

def updateChoices(sel, choices):
	if choices:
		defval = None
		val = int(sel.value)
		if not val in choices:
			tmp = choices[:]
			tmp.reverse()
			for x in tmp:
				if x < val:
					defval = str(x)
					break
		sel.setChoices(map(str, choices), defval)

def preferredPath(path):
	if config.usage.setup_level.index < 2 or path == "<default>":
		return None  # config.usage.default_path.value, but delay lookup until usage
	elif path == "<current>":
		return config.movielist.last_videodir.value
	elif path == "<timer>":
		return config.movielist.last_timer_videodir.value
	else:
		return path

def preferredTimerPath():
	return preferredPath(config.usage.timer_path.value)

def preferredInstantRecordPath():
	return preferredPath(config.usage.instantrec_path.value)

def defaultMoviePath():
	return config.usage.default_path.value

def defaultStorageDevice():
	return config.storage_options.default_device.value
