from Screens.Screen import Screen
from Screens.LocationBox import MovieLocationBox, TimeshiftLocationBox
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.config import config, ConfigSelection, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists
from Components.UsageConfig import preferredPath, defaultStorageDevice
from Components.Harddisk import harddiskmanager

class RecordPathsSettings(Screen,ConfigListScreen):

	def __init__(self, session):
		from Components.Sources.StaticText import StaticText
		Screen.__init__(self, session)
		self.skinName = "RecordPathsSettings"
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["introduction"] = StaticText()

		ConfigListScreen.__init__(self, [])
		self.initConfigList()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
		    "green": self.save,
		    "red": self.cancel,
		    "cancel": self.cancel,
		    "ok": self.ok,
		}, -2)

	def checkReadWriteDir(self, configele):
		print "checkReadWrite: ", configele.value
		if configele.value in [x[0] for x in self.styles] or configele.value in [x[0] for x in self.storage_styles] or fileExists(configele.value, "w"):
			configele.last_value = configele.value
			return True
		else:
			dir = configele.value
			configele.value = configele.last_value
			self.session.open(
				MessageBox,
				_("The directory %s is not writable.\nMake sure you select a writable directory instead.")%dir,
				type = MessageBox.TYPE_ERROR
				)
			return False

	def initConfigList(self):
		self.styles = [ ("<default>", _("<Default movie location>")), ("<current>", _("<Current movielist location>")), ("<timer>", _("<Last timer location>")) ]
		styles_keys = [x[0] for x in self.styles]

		mountpoints = [ (p.mountpoint, p.description) for p in harddiskmanager.getConfiguredStorageDevices() if p.isInitialized]
		mountpoints.sort(reverse = True)
		self.storage_styles = [ ("<undefined>", _("<No default storage device selected.>"))]
		self.storage_styles += mountpoints
		storage_styles_keys = [x[0] for x in self.storage_styles]
		default = defaultStorageDevice()
		if default not in storage_styles_keys:
			p = harddiskmanager.getDefaultStorageDevicebyUUID(default)
			if p is not None:
				default = p.mountpoint
				if p.mountpoint not in storage_styles_keys:
					self.storage_styles.append((p.mountpoint, p.description))
			else:
				cfg_uuid = config.storage.get(default, None)
				if cfg_uuid is not None:
					if cfg_uuid["enabled"].value:
						default = cfg_uuid["mountpoint"].value
						if default not in storage_styles_keys:
							description = cfg_uuid["device_description"].value.split()[0] or ""
							description += " ( " + _("Offline") + " )"
							self.storage_styles.append((default, description ))
					else:
						default = "<undefined>"
				else:
					default = "<undefined>"
		print "DefaultDevice: ", default, self.storage_styles
		self.default_device = ConfigSelection(default = default, choices = self.storage_styles)
		tmp = config.movielist.videodirs.value
		default = config.usage.default_path.value
		if default not in tmp:
			tmp = tmp[:]
			tmp.append(default)
		print "DefaultPath: ", default, tmp
		self.default_dirname = ConfigSelection(default = default, choices = tmp)
		tmp = config.movielist.videodirs.value
		default = config.usage.timer_path.value
		if default not in tmp and default not in styles_keys:
			tmp = tmp[:]
			tmp.append(default)
		print "TimerPath: ", default, tmp
		self.timer_dirname = ConfigSelection(default = default, choices = self.styles+tmp)
		tmp = config.movielist.videodirs.value
		default = config.usage.instantrec_path.value
		if default not in tmp and default not in styles_keys:
			tmp = tmp[:]
			tmp.append(default)
		print "InstantrecPath: ", default, tmp
		self.instantrec_dirname = ConfigSelection(default = default, choices = self.styles+tmp)
		default = config.usage.timeshift_path.value
		tmp = config.usage.allowed_timeshift_paths.value
		if default not in tmp:
			tmp = tmp[:]
			tmp.append(default)
		print "TimeshiftPath: ", default, tmp
		self.timeshift_dirname = ConfigSelection(default = default, choices = tmp)
		self.timeshift_dirname.last_value = self.timeshift_dirname.value
		self.default_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
		self.default_dirname.last_value = self.default_dirname.value
		self.timer_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
		self.timer_dirname.last_value = self.timer_dirname.value
		self.instantrec_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
		self.instantrec_dirname.last_value = self.instantrec_dirname.value
		self.timeshift_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
		self.timeshift_dirname.last_value = self.timeshift_dirname.value

		self.list = []
		self.device_entry = getConfigListEntry(_("Default storage device"), self.default_device)
		self.list.append(self.device_entry)
		if config.usage.setup_level.index >= 2:
			self.default_entry = getConfigListEntry(_("Default movie location"), self.default_dirname)
			self.list.append(self.default_entry)
			self.timer_entry = getConfigListEntry(_("Timer record location"), self.timer_dirname)
			self.list.append(self.timer_entry)
			self.instantrec_entry = getConfigListEntry(_("Instant record location"), self.instantrec_dirname)
			self.list.append(self.instantrec_entry)
		else:
			self.default_entry = getConfigListEntry(_("Movie location"), self.default_dirname)
			self.list.append(self.default_entry)
		self.timeshift_entry = getConfigListEntry(_("Timeshift location"), self.timeshift_dirname)
		self.list.append(self.timeshift_entry)
		self["config"].setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

	def selectionChanged(self):
		currentry = self["config"].getCurrent()
		if currentry == self.device_entry:
			self["introduction"].setText(_("Please select the default storage device you want to use for recordings. This device gets mounted to /media/hdd."))
		elif currentry == self.default_entry:
			self["introduction"].setText(_("Please select the default movielist location which is used for recordings."))
		elif currentry == self.timeshift_entry:
			self["introduction"].setText(_("Please select the timeshift location which is used for storing timeshift recordings."))
		if config.usage.setup_level.index >= 2:
			if currentry == self.timer_entry:
				self["introduction"].setText(_("Please select the default timer record location which is used for timer based recordings."))
			elif currentry == self.instantrec_entry:
				self["introduction"].setText(_("Please select the default instant record location which is used for instant recordings."))

	def ok(self):
		currentry = self["config"].getCurrent()
		self.lastvideodirs = config.movielist.videodirs.value
		self.lasttimeshiftdirs = config.usage.allowed_timeshift_paths.value
		if config.usage.setup_level.index >= 2:
			txt = _("Default movie location")
		else:
			txt = _("Movie location")
		if currentry == self.default_entry:
			self.entrydirname = self.default_dirname
			self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, txt, preferredPath(self.default_dirname.value))
		elif currentry == self.timeshift_entry:
			self.entrydirname = self.timeshift_dirname
			config.usage.timeshift_path.value = self.timeshift_dirname.value
			self.session.openWithCallback(self.dirnameSelected,	TimeshiftLocationBox)
		if config.usage.setup_level.index >= 2:
			if currentry == self.timer_entry:
				self.entrydirname = self.timer_dirname
				self.session.openWithCallback(self.dirnameSelected,	MovieLocationBox,_("Initial location in new timers"), preferredPath(self.timer_dirname.value))
			elif currentry == self.instantrec_entry:
				self.entrydirname = self.instantrec_dirname
				self.session.openWithCallback(self.dirnameSelected,	MovieLocationBox, _("Location for instant recordings"), preferredPath(self.instantrec_dirname.value))

	def dirnameSelected(self, res):
		if res is not None:
			self.entrydirname.value = res
			if config.movielist.videodirs.value != self.lastvideodirs:
				styles_keys = [x[0] for x in self.styles]
				tmp = config.movielist.videodirs.value
				default = self.default_dirname.value
				if default not in tmp:
					tmp = tmp[:]
					tmp.append(default)
				self.default_dirname.setChoices(tmp, default=default)
				tmp = config.movielist.videodirs.value
				default = self.timer_dirname.value
				if default not in tmp and default not in styles_keys:
					tmp = tmp[:]
					tmp.append(default)
				self.timer_dirname.setChoices(self.styles+tmp, default=default)
				tmp = config.movielist.videodirs.value
				default = self.instantrec_dirname.value
				if default not in tmp and default not in styles_keys:
					tmp = tmp[:]
					tmp.append(default)
				self.instantrec_dirname.setChoices(self.styles+tmp, default=default)
				self.entrydirname.value = res
			if config.usage.allowed_timeshift_paths.value != self.lasttimeshiftdirs:
				tmp = config.usage.allowed_timeshift_paths.value
				default = self.instantrec_dirname.value
				if default not in tmp:
					tmp = tmp[:]
					tmp.append(default)
				self.timeshift_dirname.setChoices(tmp, default=default)
				self.entrydirname.value = res
			if self.entrydirname.last_value != res:
				self.checkReadWriteDir(self.entrydirname)

	def save(self):
		currentry = self["config"].getCurrent()
		defaultChanged = None
		if self.checkReadWriteDir(currentry[1]):
			config.usage.default_path.value = self.default_dirname.value
			config.usage.timer_path.value = self.timer_dirname.value
			config.usage.instantrec_path.value = self.instantrec_dirname.value
			config.usage.timeshift_path.value = self.timeshift_dirname.value
			config.usage.default_path.save()
			config.usage.timer_path.save()
			config.usage.instantrec_path.save()
			config.usage.timeshift_path.save()
			if self.default_device.value != defaultStorageDevice():
				if self.default_device.value != "<undefined>": #changing default ?
					tmp = harddiskmanager.getPartitionbyMountpoint(self.default_device.value)
					if tmp is not None:
						defaultChanged = harddiskmanager.changeStorageDevice(tmp.uuid, "mount_default", None)
				else: #disabling default ?
					p = harddiskmanager.getDefaultStorageDevicebyUUID(defaultStorageDevice())
					if p is not None:
						defaultChanged = harddiskmanager.changeStorageDevice(defaultStorageDevice(), "unmount", None)
			if defaultChanged is None:
				self.close()
			elif defaultChanged is False:
				self.session.open(MessageBox, _("There was en error while configuring your storage device."), MessageBox.TYPE_ERROR)
			else:
				self.close()

	def cancel(self):
		self.close()
