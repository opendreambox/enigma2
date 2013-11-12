from Screen import Screen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Harddisk import harddiskmanager  #global harddiskmanager
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.FileList import FileList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Components.ConfigList import ConfigListScreen
from Components.config import config, configfile, getConfigListEntry
from Components.UsageConfig import defaultStorageDevice
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.Setup import Setup
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from enigma import eTimer
from os import path, makedirs, listdir, access, F_OK, R_OK

HARDDISK_INITIALIZE = 1
HARDDISK_CHECK = 2

harddisk_description = {'desc': _("hard disk"),'Desc': _("Hard disk")}
storagedevice_description = {'desc': _("storage device"),'Desc': _("Storage device")}

def updateVideoDirs(uuid = None):
	tmp = config.movielist.videodirs.value
	mountpath = moviedir = ""
	cfg = config.storage.get(uuid, None)
	if cfg is not None:
		p = harddiskmanager.getPartitionbyUUID(uuid)
		if p is not None:
			mountpath = cfg['mountpoint'].value
			if cfg["enabled"].value:
				if p.isInitialized and uuid == defaultStorageDevice():
					moviedir = "/hdd/movie/"
				elif p.isInitialized and uuid != defaultStorageDevice():
					moviedir = mountpath + "/movie/"
				else:
					moviedir = mountpath + "/"
				if moviedir not in ("/hdd/movie/", "/media/hdd/movie/") and moviedir not in tmp:
					tmp.append(moviedir)
			else:
				if p.isInitialized:
					moviedir = mountpath + "/movie/"
				else:
					moviedir = mountpath + "/"
				if moviedir not in ("/hdd/movie/", "/media/hdd/movie/") and moviedir in tmp:
					tmp.remove(moviedir)
		else:
			mountpath = cfg['mountpoint'].value
			moviedir = mountpath + "/"
			if moviedir not in ("/hdd/movie/", "/media/hdd/movie/") and moviedir in tmp:
				tmp.remove(moviedir)
			moviedir += "movie/"
			if moviedir not in ("/hdd/movie/", "/media/hdd/movie/") and moviedir in tmp:
				tmp.remove(moviedir)

	if "/hdd/movie/" not in tmp:
		tmp.append("/hdd/movie/")
	config.movielist.videodirs.value = tmp
	config.movielist.videodirs.save()
	config.movielist.save()
	configfile.save()
	print "updateVideoDirs:",config.movielist.videodirs.value

def doFstabUpgrade(uuid, path, mp, callConfirmApply, applyCallback = None, answer = None, selection = None):
	print "[doFstabUpgrade] - Removing hard mount entry from fstab.",path, mp, answer, selection
	partitionPath = path
	uuidpartitionPath = "/dev/disk/by-uuid/" + uuid
	mountpath = mp
	if harddiskmanager.isPartitionpathFsTabMount(uuid,mountpath):
		harddiskmanager.unmountPartitionbyMountpoint(mountpath)
		harddiskmanager.modifyFstabEntry(partitionPath, mountpath, mode = "remove")
	if harddiskmanager.isUUIDpathFsTabMount(uuid,mountpath):
		harddiskmanager.unmountPartitionbyMountpoint(mountpath)
		harddiskmanager.modifyFstabEntry(uuidpartitionPath, mountpath, mode = "remove")
	if mountpath != "/media/hdd":
		if harddiskmanager.isPartitionpathFsTabMount(uuid,"/media/hdd"):
			harddiskmanager.unmountPartitionbyMountpoint("/media/hdd")
			harddiskmanager.modifyFstabEntry(partitionPath, "/media/hdd", mode = "remove")
		if harddiskmanager.isUUIDpathFsTabMount(uuid,"/media/hdd"):
			harddiskmanager.unmountPartitionbyMountpoint("/media/hdd")
			harddiskmanager.modifyFstabEntry(uuidpartitionPath, "/media/hdd", mode = "remove")

	if applyCallback is not None:
		if harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto' or harddiskmanager.get_fstab_mountstate(uuidpartitionPath, mountpath) == 'auto' \
			or harddiskmanager.get_fstab_mountstate(partitionPath, "/media/hdd") == 'auto' or harddiskmanager.get_fstab_mountstate(uuidpartitionPath, "/media/hdd") == 'auto':
			if answer is not None and selection is not None:
				applyCallback(False, callConfirmApply, answer, selection)
			else:
				applyCallback(False, callConfirmApply)
		else:
			if answer is not None and selection is not None:
				applyCallback(True, callConfirmApply, answer, selection)
			else:
				applyCallback(True, callConfirmApply)
	else:
		print "error removing fstab entry!"

def hddConfirmed(confirmed, stype, hdd, partition = None, callback = None ):
	if not confirmed:
		return
	print "hddConfirmed: this will start either the initialize or the fsck now!"
	UUIDPartitionList = [ ]
	if stype == HARDDISK_INITIALIZE:
		print "hddConfirmed: start initialize for device:%s and partitions:%s" % (hdd.device, hdd.numPartitions())
		for p in harddiskmanager.partitions[:]:
			if p.device is not None:
				if p.device.startswith(hdd.device):
					if p.uuid is not None:
						UUIDPartitionList.append(p.uuid)
		if UUIDPartitionList:
			for uuid in UUIDPartitionList[:]:
				cfg = config.storage.get(uuid, None)
				if cfg is not None:
					harddiskmanager.unmountPartitionbyUUID(uuid)
					harddiskmanager.modifyFstabEntry("/dev/disk/by-uuid/" + uuid, cfg["mountpoint"].value, mode = "remove")
					cfg["enabled"].value = False
					updateVideoDirs(uuid)
					del config.storage[uuid]
					print "hddConfirmed: known device re-initialize, removed old uuid:",uuid
				else:
					harddiskmanager.unmountPartitionbyUUID(uuid)

				dev = harddiskmanager.getDeviceNamebyUUID(uuid)
				if dev is not None:
					harddiskmanager.unmountPartitionbyMountpoint("/autofs/" + dev)

		if defaultStorageDevice() in UUIDPartitionList: # we initialized the 'current' default storage device
			config.storage_options.default_device.value = "<undefined>"
		config.storage.save()
		configfile.save()
	elif stype == HARDDISK_CHECK:
		deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hdd,partition)
		harddiskmanager.unmountPartitionbyUUID(uuid)

	if callback is not None:
		callback(stype, hdd, partition)


class HarddiskWait(Screen):
	def doInit(self):
		self.timer.stop()
		result = self.hdd.initialize(self.isFstabMounted, self.numpart)
		if harddiskmanager.KernelVersion < "3.2":
			harddiskmanager.trigger_udev()
		self.close(result)

	def doCheck(self):
		self.timer.stop()
		result = self.hdd.check( self.isFstabMounted, self.numpart )
		self.close(result)

	def __init__(self, session, hdd, stype, numpart = None):
		Screen.__init__(self, session)
		self.hdd = hdd
		self.devicedescription = storagedevice_description
		if not self.hdd.isRemovable:
			self.devicedescription = harddisk_description
		self.isFstabMounted = False
		self.numpart = numpart
		uuid = partitionPath = None
		if not self.numpart:
			self.numpart = self.hdd.numPartitions()

		if self.numpart == 0:
			uuid = harddiskmanager.getPartitionUUID(hdd.device)
			partitionPath = hdd.dev_path
		if self.numpart >= 1:
			uuid = harddiskmanager.getPartitionUUID(hdd.device + str(self.numpart))
			partitionPath = hdd.partitionPath(str(self.numpart))

		if uuid is not None:
			mountpath = harddiskmanager.get_fstab_mountpoint(partitionPath)
			if harddiskmanager.isUUIDpathFsTabMount(uuid, mountpath) or harddiskmanager.isPartitionpathFsTabMount(uuid, mountpath):
				self.isFstabMounted = True

		self.timer = eTimer()
		if stype == HARDDISK_INITIALIZE:
			text = _("Initializing %(desc)s...") % self.devicedescription
			self.timer.callback.append(self.doInit)
		elif stype == HARDDISK_CHECK:
			text = _("Checking Filesystem...")
			self.timer.callback.append(self.doCheck)
		self["wait"] = Label(text)
		self.timer.start(100)


class HarddiskDriveSetup(Screen, ConfigListScreen):

	def __init__(self, session, device = None, partition = False):
		Screen.__init__(self, session)
		self.skinName = "HarddiskDriveSetup"
		self.hdd = device
		self.devicedescription = storagedevice_description
		if not self.hdd.isRemovable:
			self.devicedescription = harddisk_description

		self.oldMountpath = None
		self.oldEnabledState = None
		self.UUIDPartitionList = [ ]

		self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.uuidPath, self.partitionPath = harddiskmanager.getPartitionVars(self.hdd,partition)
		print "[HarddiskDriveSetup] - deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s' - partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
		% (self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.partitionPath, self.uuidPath, self.hdd.device,self.hdd.dev_path)

		self.setup_title = _("Partition") + " " + self.deviceName
		if config.storage.get(self.UUID, None) is not None:
			self.oldMountpath = config.storage[self.UUID]["mountpoint"].value
			self.oldEnabledState = config.storage[self.UUID]["enabled"].value


		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["introduction"] = StaticText()
		self["model"] = StaticText(_("Model") + ": " + self.hdd.model())
		self["capacity"] = StaticText(_("Capacity") + ": "  + self.hdd.capacity())
		self["bus"] = StaticText(self.hdd.bus_description() + " " + "%(Desc)s" % self.devicedescription)
		self["icon"] = StaticText()
		self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-open.png"))
		if self.hdd.isRemovable:
			self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-big.png"))
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()

		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
			{
			"cancel": self.keyCancel,
			"ok": self.ok,
			}, -2)

		self["mountshortcuts"] = ActionMap(["ShortcutActions"],
			{
			"green": self.apply
			}, -2)

		self["mountshortcuts"].setEnabled(False)

		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.__onShown)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def __onShown(self):
		self.selectionChanged()

	def createSetup(self):
		self.list = [ ]
		if self.numPartitions >= 0:
			if self.UUID is not None and config.storage.get(self.UUID, None) is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = self.deviceName)
			uuid_cfg = config.storage.get(self.UUID, None)
			if uuid_cfg is not None:
				self["mountshortcuts"].setEnabled(True)
				self.list = [getConfigListEntry(_("Enable partition automount?"), uuid_cfg["enabled"])]
				if uuid_cfg["enabled"].value:
					if uuid_cfg["mountpoint"].value == "" or ( self.oldEnabledState is False and uuid_cfg["mountpoint"].value == "/media/hdd"):
						val = harddiskmanager.suggestDeviceMountpath(self.UUID)
						if self.UUID == defaultStorageDevice():
							val = "/media/hdd"
						uuid_cfg["mountpoint"].value = val
					self.list.append(getConfigListEntry(_("Mountpoint:"), uuid_cfg["mountpoint"]))

		self["config"].list = self.list
		self["config"].l.setSeperation(400)
		self["config"].l.setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

	def selectionChanged(self):
		if self.numPartitions >= 0:
			uuid_cfg = config.storage.get(self.UUID, None)
			if uuid_cfg is not None:
				if self["config"].isChanged():
					self["key_green"].setText(_("Save"))
				else:
					self["key_green"].setText("")
				if self["config"].getCurrent()[1] == uuid_cfg["enabled"]:
					self["introduction"].setText(_("Enable automatic partition mounting?"))
				elif self["config"].getCurrent()[1] == uuid_cfg["mountpoint"]:
					self["introduction"].setText(_("Please enter the directory to use as mountpoint or select a directory by pressing OK."))
				else:
					self["introduction"].setText("")

	def changedConfigList(self):
		if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
			if self["config"].getCurrent()[1] == config.storage[self.UUID]["enabled"]:
				self.createSetup()

	def keyLeft(self):
		if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
			ConfigListScreen.keyLeft(self)
			self.changedConfigList()

	def keyRight(self):
		if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
			ConfigListScreen.keyRight(self)
			self.changedConfigList()

	def ok(self):
		if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
			current = self["config"].getCurrent()
			if current is not None:
				if current[1] == config.storage[self.UUID]["mountpoint"]:
					self.hideHelpWindow()
					self.oldMountpath = config.storage[self.UUID]["mountpoint"].value
					self.session.openWithCallback(self.MountpointBrowserClosed, HarddiskMountpointBrowser, self.hdd, self.UUID)

	def hideHelpWindow(self):
		current = self["config"].getCurrent()
		if current and config.storage.get(self.UUID, None) is not None:
			if current[1] == config.storage[self.UUID]["mountpoint"]:
				if current[1].help_window.instance is not None:
					current[1].help_window.instance.hide()

	def MountpointBrowserClosed(self, retval = None):
		if retval and retval is not None:
			mountpath = retval.strip().replace(' ','')
			if retval.endswith("/"):
				mountpath = retval[:-1]
			print "MountpointBrowserClosed: with path: " + str(mountpath)
			try:
				if mountpath != self.oldMountpath:
					if not path.exists(mountpath):
						makedirs(mountpath)
			except OSError:
				print "mountpoint directory could not be created."

			if not path.exists(mountpath):
				self.session.open(MessageBox, _("Sorry, your directory is not writeable."), MessageBox.TYPE_INFO, timeout = 10)

			else:
				self.oldMountpath = config.storage[self.UUID]["mountpoint"].value
				config.storage[self.UUID]["mountpoint"].setValue(str(mountpath))
				self.selectionChanged()
				if (harddiskmanager.is_hard_mounted(self.partitionPath) or harddiskmanager.is_hard_mounted(self.uuidPath)):
					message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
					if harddiskmanager.isUUIDpathFsTabMount(self.UUID, mountpath) or harddiskmanager.isPartitionpathFsTabMount(self.UUID, mountpath) \
						or harddiskmanager.isUUIDpathFsTabMount(self.UUID, "/media/hdd") or harddiskmanager.isPartitionpathFsTabMount(self.UUID, "/media/hdd"):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, self.partitionPath, mountpath, False), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)

	def confirmFstabUpgrade(self, result, uuid, partitionPath, mountpath, callConfirmApply = False):
		print "[HarddiskSetup] - confirmFstabUpgrade:",result, uuid, partitionPath, mountpath, callConfirmApply
		if not result:
			return
		doFstabUpgrade(uuid, partitionPath, mountpath, callConfirmApply, self.confirmFstabUpgradeCB)

	def confirmFstabUpgradeCB(self, *val):
		answer, result = val
		if answer is not None:
			if answer:
				if result:
					self.session.openWithCallback(lambda x : self.confirmApply(True), MessageBox, _("Successfully, deactivated mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)
				else:
					self.session.open(MessageBox, _("Successfully, deactivated mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)
			else:
				self.session.open(MessageBox, _("Sorry, could not remove mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)

	def confirmApply(self, confirmed):
		if not confirmed:
			print "not confirmed"
			return
		else:
			for x in self["config"].list:
				x[1].save()
			print "confirmApply:",config.storage[self.UUID]['enabled'].value, config.storage[self.UUID]['mountpoint'].value
			successfully = False
			action = "mount_only"
			uuid_cfg = config.storage.get(self.UUID, None)
			if uuid_cfg is not None:
				if not uuid_cfg['enabled'].value and self.oldEnabledState:
					action = "unmount"
				if uuid_cfg['enabled'].value and uuid_cfg['mountpoint'].value == "/media/hdd":
					action = "mount_default"
				if action == "unmount":
					updateVideoDirs(self.UUID)
				mountpoint = uuid_cfg['mountpoint'].value
				newenable = uuid_cfg['enabled'].value
				if self.oldMountpath is None:
					self.oldMountpath = ""
				if self.oldEnabledState is None:
					self.oldEnabledState = False

				successfully = harddiskmanager.changeStorageDevice(self.UUID, action, [self.oldMountpath, self.oldEnabledState, mountpoint, newenable]) #mountDATA
				if successfully:
					uuid_cfg = config.storage.get(self.UUID, None)
					if uuid_cfg is not None:
						if action in ("mount_default", "mount_only"):
							if self.oldMountpath and self.oldMountpath != "":
								harddiskmanager.modifyFstabEntry(self.uuidPath, self.oldMountpath, mode = "remove")
							harddiskmanager.modifyFstabEntry(self.uuidPath, uuid_cfg['mountpoint'].value, mode = "add_activated")
						updateVideoDirs(self.UUID)
				else:
					self.session.open(MessageBox, _("There was en error while configuring your %(desc)s.") % self.devicedescription, MessageBox.TYPE_ERROR)
				self.close()

	def apply(self):
		self.hideHelpWindow()
		if self["config"].isChanged():
			if config.storage[self.UUID]['mountpoint'].value == '' :
					self.session.open(MessageBox, _("Please select a mountpoint for this partition."), MessageBox.TYPE_ERROR)
			else:
				mountpath = config.storage[self.UUID]['mountpoint'].value
				if (harddiskmanager.is_hard_mounted(self.partitionPath) or harddiskmanager.is_hard_mounted(self.uuidPath)):
					message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
					if harddiskmanager.isUUIDpathFsTabMount(self.UUID, mountpath) or harddiskmanager.isPartitionpathFsTabMount(self.UUID, mountpath) \
						or harddiskmanager.isUUIDpathFsTabMount(self.UUID, "/media/hdd") or harddiskmanager.isPartitionpathFsTabMount(self.UUID, "/media/hdd"):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, self.partitionPath, mountpath, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					else:
						self.session.openWithCallback(self.confirmApply, MessageBox, _("Use these settings?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)
				else:
					self.session.openWithCallback(self.confirmApply, MessageBox, _("Use these settings?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)

	def confirmCancel(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		self.hideHelpWindow()
		if self["config"].isChanged():
			self.session.openWithCallback(self.confirmCancel, MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)
		else:
			self.close()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
		self.selectionChanged()

	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].value)

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary


class HarddiskDriveSelection(Screen, HelpableScreen):
	VIEW_HARDDISK = 1
	VIEW_PARTITION = 2

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = "HarddiskDriveSelection"

		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["info"] = Boolean(True)
		self["introduction"] = StaticText()
		self.devicedescription = storagedevice_description


		self["CancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.keyCancel, _("Exit storage device selection.")),
			}, -2)

		self["OkActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"ok": (self.okbuttonClick, _("Select storage device.")),
			}, -2)

		self["RedColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"red": (self.keyRed, _("Initialize selected storage device or remove offline storage device.")),
			}, -2)

		self["GreenColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"green": (self.keyGreen, _("Check selected storage device.")),
			}, -2)

		self["YellowColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"yellow": (self.keyYellow,  _("Start storage device plugin...")),
			}, -2)

		self["BlueColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"blue": (self.keyBlue, _("Advanced settings.")),
			}, -2)

		self["StorageInfoActions"] = HelpableActionMap(self, "EPGSelectActions",
			{
			"info": (self.keyInfo, _("Display storage device informations.")),
			}, -2)

		self["OkActions"].setEnabled(False)
		self["RedColorActions"].setEnabled(False)
		self["GreenColorActions"].setEnabled(False)
		self["YellowColorActions"].setEnabled(False)
		self["BlueColorActions"].setEnabled(False)
		self["StorageInfoActions"].setEnabled(False)

		self.view = self.VIEW_HARDDISK
		self.selectedHDD = None
		self.currentIndex = 0
		self.currentlyUpdating = False
		self.verifyInitOrCheck = False
		self.list = []
		self["hddlist"] = List(self.list)

		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.__onClose)
		self.onHide.append(self.__onHide)
		self.onShown.append(self.__onShown)

	def layoutFinished(self):
		self.setTitle(_("Storage devices"))
		self.currentlyUpdating = True
		self.setButtons()
		self.updateList()

	def __onShown(self):
		self.currentlyUpdating = False
		if not self.hotplugCB in harddiskmanager.delayed_device_Notifier:
			harddiskmanager.delayed_device_Notifier.append(self.hotplugCB)
		self["hddlist"].setIndex(self.currentIndex)
		self.selectionChanged()

	def __onClose(self):
		self.currentIndex = 0
		self.currentlyUpdating = False
		if self.hotplugCB in harddiskmanager.delayed_device_Notifier:
			harddiskmanager.delayed_device_Notifier.remove(self.hotplugCB)

	def __onHide(self):
		self.currentlyUpdating = True
		if self.hotplugCB in harddiskmanager.delayed_device_Notifier:
			harddiskmanager.delayed_device_Notifier.remove(self.hotplugCB)

	def hotplugCB(self, dev, media_state):
		if media_state in ("add_delayed", "remove_delayed"):
			print "[HarddiskDriveSelection] - hotplugCB for dev:%s, media_state:%s" % (dev, media_state)
			if self.currentlyUpdating is False:
				self.currentlyUpdating = True
				self.setButtons()
				self.updateList()

	def buildHDDList(self, hd, isOfflineStorage = False, partNum = False):
		divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/div-h.png"))
		devicepng = onlinepng = None
		isOfflineStorageDevice = isOfflineStorage
		isMountedPartition = isReadable = False
		currentMountpoint = partitionType = selectedPart = partitionPath = deviceName = uuidPath =None
		hdd_description = device_info = capacity_info = ""
		numPartitions = 0
		partitionNum = False
		fstype = sys = size = sizeg = p = None
		devicedescription = storagedevice_description
		nomountpoint_msg = _("No mountpoint defined!")
		initialize_msg = _("Please initialize!")
		unsupportetpart_msg = _("Unsupported partition type!")
		multiplepartmsg = _("Multiple partitions found!")
		needsattention_msg = _("Needs attention!")
		systemountpoint_msg = _("Mounted by system!")

		if isOfflineStorageDevice:
			uuid = hd
			print "[HarddiskDriveSelection] - buildHDDList for offline uuid: ",uuid
			hdd_description = config.storage[uuid]["device_description"].value
			if config.storage[uuid]["enabled"].value == True:
				currentMountpoint = config.storage[uuid]["mountpoint"].value
			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-unavailable.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green_off.png"))
			if config.storage[uuid]["isRemovable"].value == True:
				devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-unavailable.png"))
				device_info += config.storage[uuid]["device_info"].value + " " + _("%(Desc)s") % devicedescription
			else:
				devicedescription = harddisk_description
				device_info += config.storage[uuid]["device_info"].value + " " + _("%(Desc)s") % devicedescription
			if currentMountpoint is not None:
				device_info += " - " + "( " + currentMountpoint + " )"
		else:
			hdd_description = hd.model()
			deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)
			print "[HarddiskDriveSelection] - buildHDDList for online device:",deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath
			if uuid is None and numPartitions == 2:
				part2Type = harddiskmanager.getBlkidPartitionType(hd.partitionPath("2"))
				if part2Type == "swap":
					uid = harddiskmanager.getPartitionUUID(hd.device + "1")
					if uid is not None:
						p = harddiskmanager.getPartitionbyUUID(uid)
						if p is not None and p.isInitialized: # Found HDD was initialized by Enigma2 with swap partition
							deviceName = hd.device + "1"
							uuid = uid
							numPartitions = 1
							uuidPath = "/dev/disk/by-uuid/" + uuid
							partitionPath = hd.partitionPath("1")
							print "[HarddiskDriveSelection] - RE-buildHDDList for online device:",deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath
			if partitionNum is False:
				cap = hd.capacity()
				if cap != "":
					capacity_info = " (" + cap + ")"
			if uuid is not None:
				p = harddiskmanager.getPartitionbyUUID(uuid)
				if p is not None:
					if capacity_info == "":
						if p.total() is not None:
							tmp = p.total()/1000/1000
							cap = "%d.%03d GB" % (tmp/1000, tmp%1000)
							if cap != "":
								capacity_info = " (" + cap + ")"
					selectedPart = p
					if selectedPart is not None and selectedPart.fsType == None:
						partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)
			if capacity_info == "":
				fstype, sys, size, sizeg, sectors = harddiskmanager.getFdiskInfo(hd.device + str(partitionNum))
				if sizeg is not None:
					capacity_info = " (" + sizeg + " GB)"
				else:
					if size is not None:
						tmp = int(size)/1000/1000
						cap = "%d.%03d GB" % (tmp/1000, tmp%1000)
						if cap != "":
							capacity_info = " (" + cap + ")"
			hdd_description += capacity_info

			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green.png"))
			hddname = hd.device
			if self.view != self.VIEW_HARDDISK:
				hddname = deviceName
			if hd.isRemovable:
				devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable.png"))
				device_info += hd.bus_description() + " " + _("%(Desc)s") % devicedescription + " (" + hddname + ")"
			else:
				devicedescription = harddisk_description
				device_info += hd.bus_description() + " " + _("%(Desc)s") % devicedescription + " (" + hddname + ")"

			if uuid is not None:
				cfg_uuid = config.storage.get(uuid, None)
				if cfg_uuid is not None:
					if cfg_uuid["mountpoint"].value != "":
						currentMountpoint = cfg_uuid["mountpoint"].value
					if cfg_uuid["enabled"].value:
						p = harddiskmanager.getPartitionbyMountpoint(currentMountpoint)
						if p is not None:
							if p.mounted():
								isMountedPartition = True
				if not isMountedPartition:
					if currentMountpoint is None:
						currentMountpoint = harddiskmanager.get_fstab_mountpoint(partitionPath) or harddiskmanager.get_fstab_mountpoint(uuidPath)
					if currentMountpoint is not None:
						if harddiskmanager.is_hard_mounted(partitionPath) or harddiskmanager.is_hard_mounted(uuidPath):
							if harddiskmanager.isPartitionpathFsTabMount(uuid,currentMountpoint) or harddiskmanager.isUUIDpathFsTabMount(uuid,currentMountpoint):
								devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-attention.png"))
								if hd.isRemovable:
									devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-attention.png"))
								device_info += " - " + currentMountpoint
								device_info += " - " + needsattention_msg
							else:
								device_info += " - " + nomountpoint_msg
						else:
							if not isMountedPartition:
								if selectedPart is not None and selectedPart.isMountable:
									if selectedPart.isReadable:
										isReadable = True
										device_info += " - " + nomountpoint_msg
									else:
										device_info += " - " + unsupportetpart_msg
								elif selectedPart is not None and not selectedPart.isMountable:
									if self.view == self.VIEW_HARDDISK:
										device_info += " - " + initialize_msg
									else:
										device_info += " - " + unsupportetpart_msg
								else:
									if access("/autofs/" + deviceName, F_OK|R_OK):
										isReadable = True
										try:
											listdir("/autofs/" + deviceName)
										except OSError:
											isReadable = False
										if isReadable:
											device_info += " - " + nomountpoint_msg
										else:
											device_info += " - " + unsupportetpart_msg
									else:
										if self.view == self.VIEW_HARDDISK:
											device_info += " - " + initialize_msg
										else:
											device_info += " - " + unsupportetpart_msg
					if currentMountpoint is None and cfg_uuid is not None:
						currentMountpoint = cfg_uuid["mountpoint"].value
						if currentMountpoint == "":
							if selectedPart is not None and selectedPart.isMountable:
								if selectedPart.isReadable:
									isReadable = True
									device_info += " - " + nomountpoint_msg
								else:
									device_info += " - " + unsupportetpart_msg
							elif selectedPart is not None and not selectedPart.isMountable:
								if self.view == self.VIEW_HARDDISK:
									if selectedPart.fsType is not None:
										if selectedPart.isReadable or selectedPart.fsType == "swap":
											device_info += " - " + selectedPart.fsType
										else:
											device_info += " - " + unsupportetpart_msg
									else:
										device_info += " - " + initialize_msg
								else:
									if selectedPart.fsType is not None and selectedPart.fsType == "swap":
										device_info += " - " + selectedPart.fsType
									else:
										device_info += " - " + unsupportetpart_msg
							else:
								if access("/autofs/" + deviceName, F_OK|R_OK):
									isReadable = True
									try:
										listdir("/autofs/" + deviceName)
									except OSError:
										isReadable = False
									if isReadable:
										device_info += " - " + nomountpoint_msg
									else:
										device_info += " - " + unsupportetpart_msg
								else:
									if self.view == self.VIEW_HARDDISK:
										device_info += " - " + initialize_msg
									else:
										device_info += " - " + unsupportetpart_msg
					if currentMountpoint is None and cfg_uuid is None:
						device_info += " - " + nomountpoint_msg
				if isMountedPartition:
					isReadable = True
					devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-configured.png"))
					if hd.isRemovable:
						devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-configured.png"))
					device_info += " - " + currentMountpoint
			else:
				if numPartitions <=1:
					device_info += " - " + initialize_msg
				else:
					if self.view == self.VIEW_HARDDISK:
						device_info += " - " + multiplepartmsg
					else:
						device_info += " - " + unsupportetpart_msg

		return((hdd_description, hd, device_info, numPartitions, isOfflineStorageDevice, isMountedPartition, currentMountpoint, devicepng, onlinepng, divpng, partitionNum, isReadable, partitionPath, partitionType, deviceName))

	def updateList(self):
		self.view = self.VIEW_HARDDISK
		self.selectedHDD = None
		self.list = []

		for hd in harddiskmanager.hdd:
			if not hd.isRemovable:
				self.list.append(self.buildHDDList(hd, isOfflineStorage = False)) #online hard disk devices discovered
		for hd in harddiskmanager.hdd:
			if hd.isRemovable:
				self.list.append(self.buildHDDList(hd, isOfflineStorage = False)) #online removable devices discovered
		if self.list:
			self.list.sort(key=lambda x: x[14][:3])

		for uuid in config.storage:
			dev = harddiskmanager.getDeviceNamebyUUID(uuid)
			if dev is None:
				self.list.append(self.buildHDDList(uuid, isOfflineStorage = True)) #offline devices
		if not self.list:
			self["key_blue"].setText("")
			self["BlueColorActions"].setEnabled(False)
			self.list.append((_("no storage devices found"), 0, None, None, None, None, None, None, None, None, False, None, None, None, None))
			self["introduction"].setText(_("No installed or configured storage devices found!"))

		self["hddlist"].setList(self.list)
		if not self.selectionChanged in self["hddlist"].onSelectionChanged:
			self["hddlist"].onSelectionChanged.append(self.selectionChanged)
		self["hddlist"].setIndex(self.currentIndex)
		self.currentlyUpdating = False

	def updatePartitionList(self, hdd):
		self.view = self.VIEW_PARTITION
		self.selectedHDD = hdd
		self.list = []
		for p in harddiskmanager.partitions[:]:
			if p.device is not None:
				if p.device.startswith(hdd.device) and p.device[3:].isdigit():
					self.list.append(self.buildHDDList(hdd, isOfflineStorage = False, partNum = p.device[3:])) #online devices partition discovered
		if self.list:
			self.list.sort(key=lambda x: x[14][3:])

		self["hddlist"].setList(self.list)
		self["hddlist"].setIndex(0)
		self.currentlyUpdating = False
		self.selectionChanged()

	def setButtons(self):
		self["key_red"].setText("")
		self["key_green"].setText("")
		self["key_yellow"].setText("")
		self["key_blue"].setText("")
		self["OkActions"].setEnabled(False)
		self["RedColorActions"].setEnabled(False)
		self["GreenColorActions"].setEnabled(False)
		self["YellowColorActions"].setEnabled(False)
		self["BlueColorActions"].setEnabled(False)
		self["StorageInfoActions"].setEnabled(False)
		self["info"].boolean = False

	def selectionChanged(self):
		#[HarddiskDriveSelection] - current: (0: hdd_description, 1:hd/uuid, 2;device_info, 3:numpart, 4:isOfflineStorageDevice, 5:isMountedPartition, 6:currentMountpoint, devicepng, onlinepng, divpng)
		initialize_btntxt = _("Initialize")
		check_btntxt = _("Check")
		remove_btntxt = _("Remove")
		settings_btntxt = _("Settings")
		plugins_btntxt  = _("Storage plugins")
		self.setButtons()
		current = self["hddlist"].getCurrent()
		introduction = ""
		selectedPart = None
		isInitializing = False
		isVerifying = False
		if current:
			self.currentIndex = self["hddlist"].getIndex()
			numpart = current[3]
			offline = current[4]
			if numpart >= 0 and not offline:
				storage_plugins = plugins.getPlugins(PluginDescriptor.WHERE_STORAGEMANAGER)
				if len(storage_plugins):
					self["YellowColorActions"].setEnabled(True)
					self["key_yellow"].setText(plugins_btntxt)
				if config.usage.setup_level.index >= 1:
					self["key_blue"].setText(settings_btntxt)
					self["BlueColorActions"].setEnabled(True)
				self["StorageInfoActions"].setEnabled(True)
				self["info"].boolean = True
				hd = current[1]
				partNum = current[10]
				isReadable = current[11]
				selectedPart = None
				partitionType = None
				isInitializing = hd.isInitializing
				isVerifying = hd.isVerifying
				if not isInitializing and not isVerifying and not self.verifyInitOrCheck:
					self["OkActions"].setEnabled(True)
				self.devicedescription = storagedevice_description
				if not hd.isRemovable:
					self.devicedescription = harddisk_description
				showpartitions_msg = _("Please press OK to see available partitions!")
				mountpartition_msg = _("Please press OK to set up a mountpoint for this partition!")
				unknownpartition_msg = _("Unknown or unsupported partition type found!")
				mount_msg = _("Please press OK to set up a mountpoint for this %(desc)s!") % self.devicedescription
				init_msg = _("Please initialize this %(desc)s!") % self.devicedescription
				redinit_msg = _("Please press red to initialize this %(desc)s!") % self.devicedescription
				introduction = mount_msg

				deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)
				print "[HarddiskDriveSelection] - selectionChanged: deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s' - partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
				% (deviceName, uuid, numPartitions, partitionNum, partitionPath, uuidPath, hd.device, hd.dev_path)

				if numPartitions >= 2:
					introduction = showpartitions_msg

				if uuid is not None:
					p = harddiskmanager.getPartitionbyUUID(uuid)
					if p is not None:
						selectedPart = p
						if selectedPart is not None:
							print "[HarddiskDriveSelection] - selectionChanged: SelectedPart device:'%s'-uuid:'%s' isMountable:'%s'-isReadable:'%s'-isWriteable:'%s'-isInitialized:'%s'-fsType:'%s'" \
							% (selectedPart.device ,selectedPart.uuid ,selectedPart.isMountable, selectedPart.isReadable,selectedPart.isWriteable,selectedPart.isInitialized,selectedPart.fsType)
							isReadable = selectedPart.isReadable
							partitionType = selectedPart.fsType
				if partitionType is None:
					partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)



				if self.view == self.VIEW_HARDDISK:
					self["key_red"].setText(initialize_btntxt)
					if not isInitializing and not isVerifying and not self.verifyInitOrCheck:
						self["RedColorActions"].setEnabled(True)
					if uuid is not None:
						if numPartitions <= 1:
							introduction = mountpartition_msg
							if not isInitializing and not isVerifying and not self.verifyInitOrCheck:
								if partitionType is not None and partitionType in ( "ext2", "ext3" ):
									self["key_green"].setText(check_btntxt)
									self["GreenColorActions"].setEnabled(True)
							if not isReadable and partitionType is None:
								introduction = redinit_msg
							if not isReadable and partitionType is not None:
								introduction = unknownpartition_msg
					else:
						if numPartitions <= 1:
							introduction = redinit_msg
				if self.view == self.VIEW_PARTITION:
					self["key_red"].setText("")
					self["RedColorActions"].setEnabled(False)
					if uuid is not None:
						if partitionType is not None and partitionType in ( "ext2", "ext3" ):
							self["key_green"].setText(check_btntxt)
							self["GreenColorActions"].setEnabled(True)
						introduction = mountpartition_msg
						if not isReadable:
							self["OkActions"].setEnabled(False)
							introduction = unknownpartition_msg
					else:
						self["OkActions"].setEnabled(False)
						introduction = init_msg
						if not isReadable:
							introduction = unknownpartition_msg
			if offline:
				self["key_red"].setText(remove_btntxt)
				self["RedColorActions"].setEnabled(True)
				self["OkActions"].setEnabled(True)
				if isinstance(current[1], (basestring, str)):
					self.devicedescription = storagedevice_description
					if not config.storage[current[1]]["isRemovable"].value:
						self.devicedescription = harddisk_description
					introduction = _("Please press red to remove this %(desc)s configuration!") % self.devicedescription
			if not isInitializing and not self.verifyInitOrCheck:
				self["introduction"].setText(introduction)

	def keyCancel(self):
		if self.view == self.VIEW_PARTITION:
			self.view = self.VIEW_HARDDISK
			self.mainMenuClosed()
		else:
			self.close()

	def handleAnswer(self, answer, selection):
		self.devicedescription = storagedevice_description
		answer = answer and answer[1]
		print "[HarddiskDriveSelection] - handleAnswer:",answer
		if answer == "mount_default":
			self.applyAnswer(answer, selection)
		elif answer == "mount_only":
			self.applyAnswer(answer, selection)
		elif answer == "adopt_mount":
			self.applyAnswer(answer, selection)
		elif answer == "mount_manually":
			hd = selection[1]
			numpart = selection[3]
			partNum = selection[10]
			if numpart >= 2 and partNum is not False:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, device = hd, partition = partNum)
			else:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, device = hd)
		elif answer == "unmount":
			self.confirmApplyAnswer(True, answer, selection)
		elif answer == "remove":
			if isinstance(selection[1], (basestring, str)):
				if not config.storage[selection[1]]["isRemovable"].value:
					self.devicedescription = harddisk_description
				message = _("Really remove this %(desc)s entry?") % self.devicedescription
				self.session.openWithCallback(lambda x : self.keyRedConfirm(x, selection[1]), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
		elif answer == "init":
			if not selection[1].isRemovable:
				self.devicedescription = harddisk_description
			message = _("Do you really want to initialize this %(desc)s?\nAll data on this %(desc)s will be lost!") % self.devicedescription
			self.session.openWithCallback(lambda x : hddConfirmed(x, HARDDISK_INITIALIZE, selection[1], None, self.starthddInitCheck), MessageBox, message)
		elif answer in ( None, "nothing"):
			print "nothing to do"

	def applyAnswer(self, answer, selection):
		print "[HarddiskDriveSelection] - applyAnswer:",answer,selection
		hd = selection[1]
		partNum = selection[10]
		deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)

		uuid_cfg = config.storage.get(uuid, None)
		if uuid_cfg is not None:
			mountpath = ""
			checkFstabUpgrade = True
			if answer == "adopt_mount":
				checkFstabUpgrade = False
			if answer == "mount_default":
				mountpath = "/media/hdd"
			else:
				if defaultStorageDevice() == "<undefined>" and answer != "adopt_mount":
					mountpath = "/media/hdd"
					answer = "mount_default"
				else:
					mountpath = harddiskmanager.suggestDeviceMountpath(uuid)
			if checkFstabUpgrade:
				if harddiskmanager.isUUIDpathFsTabMount(uuid, mountpath) or harddiskmanager.isPartitionpathFsTabMount(uuid, mountpath) \
				or harddiskmanager.isUUIDpathFsTabMount(uuid, "/media/hdd") or harddiskmanager.isPartitionpathFsTabMount(uuid, "/media/hdd"):
					message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
					self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, uuid, partitionPath, mountpath, answer, selection, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
				else:
					self.confirmApplyAnswer(True, answer, selection)
			else:
				self.confirmApplyAnswer(True, answer, selection)
		else:
			print "[applyAnswer] - could not determine uuid"

	def confirmFstabUpgrade(self, result, uuid, partitionPath, mountpath, answer, selection, callConfirmApply = False):
		if not result:
			self.confirmApplyAnswer(True, answer, selection)
		else:
			doFstabUpgrade(uuid, partitionPath, mountpath, callConfirmApply, self.confirmFstabUpgradeCB, answer, selection)

	def confirmFstabUpgradeCB(self, *val):
		result, callConfirmApply, answer, selection, = val
		if result is not None:
			if result:
				if callConfirmApply:
					self.session.openWithCallback(lambda x : self.confirmApplyAnswer(True, answer, selection), MessageBox, _("Successfully, deactivated mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)
			else:
				self.session.open(MessageBox, _("Sorry, could not remove mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)

	def confirmApplyAnswer(self, confirmed, answer, selection):
		if not confirmed:
			print "not confirmed"
			return
		else:
			self.devicedescription = storagedevice_description
			hd = selection[1]
			if not hd.isRemovable:
				self.devicedescription = harddisk_description
			partNum = selection[10]
			deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)

			successfully = False
			old_mountpoint = ""
			uuid_cfg = config.storage.get(uuid, None)
			if uuid_cfg is not None:
				mountpoint = ""
				if answer == "unmount":
					uuid_cfg['enabled'].value = False
					old_mountpoint = uuid_cfg['mountpoint'].value
					updateVideoDirs(uuid)
					uuid_cfg['enabled'].value = True
				if answer == "adopt_mount":
					mountpoint = selection[6]
					if mountpoint == "/media/hdd":
						answer = "mount_default"
				if answer == "adopt_mount":
					uuid_cfg['mountpoint'].value = mountpoint
					uuid_cfg['enabled'].value = True
					successfully = harddiskmanager.changeStorageDevice(uuid, "mount_only", ["", False, mountpoint, True]) #mountDATA
				else:
					successfully = harddiskmanager.changeStorageDevice(uuid, answer, None)
				print "confirmApplyAnswer:",answer, uuid_cfg['enabled'].value, uuid_cfg['mountpoint'].value
			if successfully:
				uuid_cfg = config.storage.get(uuid, None)
				if uuid_cfg is not None:
					if answer in ("mount_default", "mount_only"):
						harddiskmanager.modifyFstabEntry(uuidPath, uuid_cfg['mountpoint'].value, mode = "add_activated")
					updateVideoDirs(uuid)
					if answer == "unmount":
						harddiskmanager.modifyFstabEntry(uuidPath, old_mountpoint, mode = "remove")
			else:
				self.session.open(MessageBox, _("There was en error while configuring your %(desc)s.") % self.devicedescription, MessageBox.TYPE_ERROR)
			self.mainMenuClosed()

	def okbuttonClick(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - okbuttonClick:",selection[0], selection[2], selection[3],selection[10]
			hd = selection[1]
			offline = selection[4]
			partNum = selection[10]
			isRemovable = False
			selectedPart = None
			if not offline:
				deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)
				print "[HarddiskDriveSelection] - okbuttonClick: deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
				% (deviceName, uuid, numPartitions, partitionNum, partitionPath, uuidPath, hd.device, hd.dev_path)
				isRemovable = hd.isRemovable
			else: #offline drive ?
				uuid = hd
				numPartitions = 1
				partNum = False

			if uuid is not None:
				p = harddiskmanager.getPartitionbyUUID(uuid)
				if p is not None:
					selectedPart = p

			uuid_cfg = config.storage.get(uuid, None)
			if uuid is not None and uuid_cfg is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = deviceName)
			if uuid_cfg is not None and offline:
				isRemovable = uuid_cfg['isRemovable'].value

			self.devicedescription = storagedevice_description
			if not isRemovable:
				self.devicedescription = harddisk_description

			mountmsg = (_("Automatically set up a mountpoint."), "mount_only")
			manualmsg = (_("Manually select a mountpoint."), "mount_manually")
			adoptmsg = (_("Adopt current configuration."), "adopt_mount")
			defaultmsg = (_("Set up as default %(desc)s.") % self.devicedescription, "mount_default")
			unmountmsg = (_("Unmount this %(desc)s.") % self.devicedescription, "unmount")
			removemsg = (_("Remove this %(desc)s configuration.") % self.devicedescription, "remove")
			initmsg = (_("Initialize this %(desc)s.") % self.devicedescription, "init")

			choices = [ ]
			if uuid_cfg is None: # uninitialized drive
				choices.extend([initmsg])
			elif uuid_cfg is not None and not uuid_cfg['enabled'].value: # unconfigured drive
				if selectedPart is not None and selectedPart.isInitialized:
					isManualMounted = False
					currentMountpoint = harddiskmanager.get_fstab_mountpoint(partitionPath) or harddiskmanager.get_fstab_mountpoint(uuidPath)
					if currentMountpoint is not None:
						if harddiskmanager.is_hard_mounted(partitionPath) or harddiskmanager.is_hard_mounted(uuidPath):
							if harddiskmanager.isPartitionpathFsTabMount(uuid,currentMountpoint) or harddiskmanager.isUUIDpathFsTabMount(uuid,currentMountpoint):
								isManualMounted = True
					if defaultStorageDevice() == "<undefined>":
						if not isManualMounted:
							choices.extend([defaultmsg, mountmsg, manualmsg])
						else:
							choices.extend([defaultmsg, adoptmsg, mountmsg, manualmsg])
					else:
						if not isManualMounted:
							choices.extend([mountmsg, manualmsg, defaultmsg])
						else:
							choices.extend([adoptmsg, defaultmsg, mountmsg, manualmsg])
				else:
					if selectedPart is not None and selectedPart.isWriteable and selectedPart.isMountable: #writeable device, but not initialized by Enigma2
						choices.extend([defaultmsg, mountmsg, manualmsg])
					else:
						choices.extend([mountmsg, manualmsg])
					choices.extend([mountmsg, manualmsg])
			elif uuid_cfg is not None and uuid_cfg['enabled'].value: # configured drive
				if selectedPart is not None and selectedPart.isInitialized:
					if defaultStorageDevice() != uuid:
						choices.extend([unmountmsg, defaultmsg, manualmsg])
					elif defaultStorageDevice() == uuid:
						choices.extend([unmountmsg, mountmsg, manualmsg])
				else:
					if offline:
						choices.extend([removemsg])
					else:
						choices.extend([unmountmsg, manualmsg])
			choices.append((_("Do nothing."), "nothing"))

			if uuid_cfg is not None and not uuid_cfg['enabled'].value:
				titletext = _("Unconfigured %(desc)s found!") % self.devicedescription
			elif uuid_cfg is not None and uuid_cfg['enabled'].value:
				titletext = _("%(Desc)s already configured!") % self.devicedescription
			else:
				titletext = _("Uninitialized %(desc)s found!") % self.devicedescription

			if numPartitions >= 2 and partNum is False:
				self.updatePartitionList(hd)
			else:
				self.session.openWithCallback(lambda x : self.handleAnswer(x, selection), ChoiceBox, title = titletext + "\n" , list = choices)

	def mainMenuClosed(self, *val):
		if self.currentlyUpdating is False:
			self.currentlyUpdating = True
			self.setButtons()
			if self.view == self.VIEW_PARTITION:
				self.updatePartitionList(self.selectedHDD)
			else:
				self.updateList()

	def starthddInitCheck(self, stype, hdd, partition ):
		if stype == HARDDISK_INITIALIZE:
			print "[HarddiskDriveSelection]- starthddInit Initialize: ",stype, hdd
			hdd.isInitializing = True
			self.session.openWithCallback(lambda x : self.hddReady(x, stype, hdd), HarddiskWait, hdd, stype)
		else:
			print "[HarddiskDriveSelection]- starthddInit Check: ",stype, hdd, partition
			hdd.isVerifying = True
			self.session.openWithCallback(lambda x : self.hddReady(x, stype, hdd, partition), HarddiskWait, hdd, stype, partition)

	def hddReady(self, result, stype, hdd, partition = None ):
		if (result != 0):
			self.devicedescription = storagedevice_description
			if not hdd.isRemovable:
				self.devicedescription = harddisk_description
			if stype == HARDDISK_INITIALIZE:
				hdd.isInitializing = False
				message = _("Unable to initialize %(desc)s.\nError: ") % self.devicedescription
			else:
				hdd.isVerifying = False
				message = _("Unable to complete filesystem check.\nError: ")
			self.session.open(MessageBox, message + str(hdd.errorList[0 - result]), MessageBox.TYPE_ERROR)
		else:
			if stype == HARDDISK_INITIALIZE:
				#we need to wait until udev has set up all new system links
				self.timer = eTimer()
				self.timer.callback.append(boundFunction(self.verifyInitialize, hdd))
				self["introduction"].setText(_("Verifying initialization. Please wait!"))
				self.timer.start(3000,True)
			elif stype == HARDDISK_CHECK:
				deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hdd,partition)
				harddiskmanager.mountPartitionbyUUID(uuid)
				hdd.isVerifying = False
				self["introduction"].setText(_("Filesystem check completed without errors."))

	def verifyInitialize(self, hdd):
		self.timer.stop()
		self.devicedescription = storagedevice_description
		if not hdd.isRemovable:
			self.devicedescription = harddisk_description
		successfully = False
		action = "mount_only"
		deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hdd, "1")
		#print "[HarddiskDriveSelection]-> deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'\n- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
		#% (deviceName, uuid, numPartitions, partitionNum, partitionPath, uuidPath, hdd.device, hdd.dev_path)
		if uuid is not None:
			print "[HarddiskDriveSelection]- verifyInitialize - got new uuid: ",uuid
			uuid_cfg = config.storage.get(uuid, None)
			if uuid_cfg is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = deviceName)
			print "[HarddiskDriveSelection]- verifyInitialize -defaultStorageDevice()",defaultStorageDevice()
			print "[HarddiskDriveSelection]- verifyInitialize -HDDEnabledCount()",harddiskmanager.HDDEnabledCount()
			if uuid_cfg is not None:
				if defaultStorageDevice() == "<undefined>" or not harddiskmanager.HDDEnabledCount(): # no configured default storage device found
					action = "mount_default"
				print "[HarddiskDriveSelection]- verifyInitialize -ACTION",action
				successfully = harddiskmanager.changeStorageDevice(uuid, action, None)
			if successfully:
				uuid_cfg = config.storage.get(uuid, None)
				if uuid_cfg is not None:
					if action in ("mount_default", "mount_only"):
						harddiskmanager.modifyFstabEntry(uuidPath, uuid_cfg['mountpoint'].value, mode = "add_activated")
					updateVideoDirs(uuid)
			else:
				self.session.open(MessageBox, _("There was en error while configuring your %(desc)s.") % self.devicedescription, MessageBox.TYPE_ERROR)
		else:
			self["introduction"].setText(_("Unable to verify partition information. Please restart!"))
		hdd.isInitializing = False
		self.verifyInitOrCheck = True
		self.timer = eTimer()
		self.timer.callback.append(self.verifyInitializeOrCheck)
		self.timer.start(3000,True)

	def verifyInitializeOrCheck(self):
		self.timer.stop()
		self.verifyInitOrCheck = False
		self.mainMenuClosed()

	def keyRed(self):
		selection = self["hddlist"].getCurrent()
		print "[HarddiskDriveSelection] - keyRed:",selection[0], selection[1], selection[2], selection[3], selection[4], selection[10],selection[11]
		if selection[1] != 0:
			self.devicedescription = storagedevice_description
			if isinstance(selection[1], (basestring, str)):
				if not config.storage[selection[1]]["isRemovable"].value:
					self.devicedescription = harddisk_description
				message = _("Really delete this %(desc)s entry?") % self.devicedescription
				self.session.openWithCallback(lambda x : self.keyRedConfirm(x, selection[1]), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
			else:
				hd = selection[1]
				if not hd.isRemovable:
					self.devicedescription = harddisk_description
				message = _("Do you really want to initialize this %(desc)s?\nAll data on this %(desc)s will be lost!") % self.devicedescription
				self.session.openWithCallback(lambda x : hddConfirmed(x, HARDDISK_INITIALIZE, hd, None, self.starthddInitCheck), MessageBox, message)

	def keyRedConfirm(self, result, uuid):
		if not result:
			return
		uuid_cfg = config.storage.get(uuid, None)
		if uuid_cfg is not None:
			harddiskmanager.modifyFstabEntry("/dev/disk/by-uuid/" + uuid, uuid_cfg["mountpoint"].value, mode = "remove")
			uuid_cfg["enabled"].value = False
			updateVideoDirs(uuid)
			del config.storage[uuid]
			if uuid == defaultStorageDevice():
				config.storage_options.default_device.value = "<undefined>"
				config.storage_options.default_device.save()
				config.storage_options.save()
			config.storage.save()
			configfile.save()
			self.setButtons()
			self.updateList()

	def keyGreen(self):
		#[HarddiskDriveSelection] - current: (0: hdd_description, 1:hd/uuid, 2;device_info, 3:numpart, 4:isOfflineStorageDevice, 5:isMountedPartition, 6:currentMountpoint, 10:partNum, devicepng, onlinepng, divpng)
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - keyGreen:",selection[0], selection[1], selection[2], selection[3], selection[10]
			hd = selection[1]
			message = _("Do you really want to check the filesystem?\nThis could take lots of time!")
			if selection[3] >= 2 and selection[10] is not False:
				self.session.openWithCallback(lambda x : hddConfirmed(x, HARDDISK_CHECK, hd, selection[10], self.starthddInitCheck), MessageBox, message)
			else:
				self.session.openWithCallback(lambda x : hddConfirmed(x, HARDDISK_CHECK, hd, selection[3], self.starthddInitCheck), MessageBox, message)

	def keyYellow(self):
		selection = self["hddlist"].getCurrent()
		print "[HarddiskDriveSelection] - keyYellow:",selection[0], selection[1], selection[2], selection[3], selection[4], selection[10],selection[11]
		if selection[1] != 0:
			if not isinstance(selection[1], (basestring, str)):
				storage_plugins = plugins.getPlugins(PluginDescriptor.WHERE_STORAGEMANAGER)
				l = len(storage_plugins)
				if l == 1:
					storage_plugins[0](session=self.session, current=selection)
				elif l > 1:
					pluginlist = []
					for p in storage_plugins:
						pluginlist.append( (p.name, p) )
					self.session.openWithCallback(lambda x : self.onStoragePluginSelected(x, selection),  ChoiceBox, title=_("Please select a storage device plugin"), list = pluginlist)

	def onStoragePluginSelected(self, p, selection):
		p = p and p[1]
		if p is not None:
			p(session=self.session, current=selection)

	def keyBlue(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			self.session.openWithCallback(self.mainMenuClosed, Setup, "harddisk")

	def keyInfo(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			#print "[HarddiskDriveSelection] - keyInfo:",selection[0], selection[1], selection[2], selection[3], selection[10]
			hd = selection[1]
			numpart = selection[3]
			partNum = selection[10]
			if numpart >= 2 and partNum is not False:
				self.session.openWithCallback(self.mainMenuClosed, StorageInformation, hdd = hd, partition = partNum)
			else:
				self.session.openWithCallback(self.mainMenuClosed, StorageInformation, hdd = hd)


class HarddiskMountpointBrowser(Screen, HelpableScreen):

	def __init__(self, session, hdd, uuid):
		Screen.__init__(self, session)
		self.skinName = "HarddiskMountpointBrowser"
		self.hdd = hdd
		self.UUID = uuid
		HelpableScreen.__init__(self)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Use"))
		self["key_yellow"] = StaticText(_("Create directory"))
		self["key_blue"] = StaticText()

		currdir = "/media/"
		inhibitDirs = ["/autofs", "/mnt", "/hdd", "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/proc", "/sbin", "/share", "/sys", "/tmp", "/usr", "/var", "/media/realroot", "/media/union"]
		self.filelist = FileList(currdir, matchingPattern="", inhibitDirs = inhibitDirs)
		self["filelist"] = self.filelist

		self["shortcuts"] = ActionMap(["ColorActions"],
			{
			"red": self.exit,
			"green": self.use,
			"yellow": self.createMountdir,
			}, -2)

		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
			{
			"cancel": self.exit,
			"ok": self.ok,
			}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Select mountpoint"))

	def ok(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def use(self):
		if self["filelist"].getCurrentDirectory() is not None:
			if self.filelist.canDescent() and self["filelist"].getFilename() and len(self["filelist"].getFilename()) > len(self["filelist"].getCurrentDirectory()):
				self.filelist.descent()
				self.close(self["filelist"].getCurrentDirectory())
		else:
			self.close(self["filelist"].getFilename())

	def createMountdir(self):
		cfg = config.storage.get(self.UUID, None)
		if cfg is not None:
			self.session.openWithCallback(self.createMountdirCB, VirtualKeyBoard, title = (_("Enter mountpoint path.")), text = cfg["mountpoint"].value)

	def createMountdirCB(self, retval = None):
		if retval is not None:
			self.close(retval)

	def exit(self):
		self.close(False)


class StorageInformation(Screen):

	def __init__(self, session, hdd = None, partition = False):
		Screen.__init__(self, session)
		self.skinName = "StorageInformation"

		self.hdd = hdd
		self.partition = partition

		self.devicedescription = storagedevice_description
		if not self.hdd.isRemovable:
			self.devicedescription = harddisk_description
		self.setup_title = _("Storage device information")

		self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.uuidPath, self.partitionPath = harddiskmanager.getPartitionVars(self.hdd,self.partition)
		print "[StorageInformation] - deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'\n- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
		% (self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.partitionPath, self.uuidPath, self.hdd.device,self.hdd.dev_path)

		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["introduction"] = StaticText()
		self["icon"] = StaticText()
		self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-open.png"))
		if self.hdd.isRemovable:
			self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-big.png"))
		self["model"] = StaticText(_("Model") + ": " + self.hdd.model())
		self["device_capacity"] = StaticText(_("Capacity") + ": "  + self.hdd.capacity())
		self["device_free"] = StaticText(_("Free") + ": %d MB"  % self.hdd.free())
		self["bus"] = StaticText(_("Description") + ": "  + self.hdd.bus_description() + " " + _("%(Desc)s") % self.devicedescription + " (" + self.hdd.device + ")" )
		self["num_partitions"] = StaticText(_("Partitions") + ": " + str(self.numPartitions))
		self["partition"] = StaticText()
		self["partition_capacity"] = StaticText()
		self["filesystem"] = StaticText()

		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
		{
			"back": self.close,
			"cancel": self.close,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)
		self.updateInfo()

	def updateInfo(self):
		init_msg = _("Please initialize this %(desc)s!") % self.devicedescription
		unknownpartition_msg = _("Unknown or unsupported partition type.")
		selectedPart = None
		partitionType = None
		capacity_info = ""

		if self.UUID is not None:
			p = harddiskmanager.getPartitionbyUUID(self.UUID)
			if p is not None:
				selectedPart = p
				if selectedPart is not None:
					partitionType = selectedPart.fsType
		if partitionType is None:
			partitionType = harddiskmanager.getBlkidPartitionType(self.partitionPath)

		if self.UUID is None and self.numPartitions == 0:
			self["introduction"].setText(init_msg)

		if self.UUID is not None:
			self["partition"].setText(_("Partition") + ": " + self.deviceName)
			if partitionType is None:
				self["filesystem"].setText(_("Filesystem") + ": " + unknownpartition_msg)
			else:
				self["filesystem"].setText(_("Filesystem") + ": " + partitionType)
			if self.partitionNum is False:
				cap = self.hdd.capacity()
				if cap != "":
					capacity_info = str(cap)
			else:
				if selectedPart is not None:
					if capacity_info == "":
						if selectedPart.total() is not None:
							tmp = selectedPart.total()/1000/1000
							cap = "%d.%03d GB" % (tmp/1000, tmp%1000)
							if cap != "":
								capacity_info = str(cap)
				if capacity_info == "":
					fstype, sys, size, sizeg, sectors = harddiskmanager.getFdiskInfo(self.hdd.device + str(self.partitionNum))
					if sizeg is not None:
						capacity_info = " " + sizeg + " GB"
					else:
						if size is not None:
							tmp = int(size)/1000/1000
							cap = "%d.%03d GB" % (tmp/1000, tmp%1000)
							capacity_info = str(cap)
			self["partition_capacity"].setText(_("Partition capacity") + ": "  + capacity_info)
