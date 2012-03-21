from Screen import Screen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Harddisk import harddiskmanager	#global harddiskmanager
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.FileList import FileList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
from Components.config import config, configfile, ConfigYesNo, ConfigText, getConfigListEntry, ConfigNothing, NoSave
from Components.UsageConfig import defaultStorageDevice
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.Setup import Setup, getSetupTitle
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer
from os import path, makedirs, listdir, access, F_OK, R_OK

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
	config.save()
	configfile.save()
	print "updateVideoDirs:",config.movielist.videodirs.value

def doFstabUpgrade(uuid, path, mp, callConfirmApply, applyCallback = None, answer = None, selection = None):
	print "[doFstabUpgrade] - Removing hard mount entry from fstab.",path, mp
	partitionPath = path
	uuidpartitionPath = "/dev/disk/by-uuid/" + uuid
	mountpath = mp
	if harddiskmanager.isPartitionpathFsTabMount(uuid,mountpath):
		harddiskmanager.unmountPartitionbyMountpoint(mountpath)
		harddiskmanager.modifyFstabEntry(partitionPath, mountpath, mode = "add_deactivated")
	if harddiskmanager.isUUIDpathFsTabMount(uuid,mountpath):
		harddiskmanager.unmountPartitionbyMountpoint(mountpath)
		harddiskmanager.modifyFstabEntry(uuidpartitionPath, mountpath, mode = "add_deactivated")
	if mountpath != "/media/hdd":
		if harddiskmanager.isPartitionpathFsTabMount(uuid,"/media/hdd"):
			harddiskmanager.unmountPartitionbyMountpoint("/media/hdd")
			harddiskmanager.modifyFstabEntry(partitionPath, "/media/hdd", mode = "add_deactivated")
		if harddiskmanager.isUUIDpathFsTabMount(uuid,"/media/hdd"):
			harddiskmanager.unmountPartitionbyMountpoint("/media/hdd")
			harddiskmanager.modifyFstabEntry(uuidpartitionPath, "/media/hdd", mode = "add_deactivated")

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

class HarddiskWait(Screen):
	def doInit(self):
		self.timer.stop()
		result = self.hdd.initialize(self.isFstabMounted, self.numpart)
		harddiskmanager.trigger_udev()
		self.close(result)

	def doCheck(self):
		self.timer.stop()
		result = self.hdd.check( self.isFstabMounted, self.numpart )
		self.close(result)

	def __init__(self, session, hdd, stype, numpart = None):
		Screen.__init__(self, session)
		self.hdd = hdd
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
		if stype == HarddiskDriveSetup.HARDDISK_INITIALIZE:
			text = _("Initializing hard disk...")
			if self.hdd.isRemovable:
				text = _("Initializing storage device...")
			self.timer.callback.append(self.doInit)
		elif stype == HarddiskDriveSetup.HARDDISK_CHECK:
			text = _("Checking Filesystem...")
			self.timer.callback.append(self.doCheck)
		self["wait"] = Label(text)
		self.timer.start(100)


class HarddiskDriveSetup(Screen, ConfigListScreen):
	HARDDISK_INITIALIZE = 1
	HARDDISK_CHECK = 2
	HARDDISK_SETUP = 3

	def __init__(self, session, stype = None, device = None, partition = False):
		Screen.__init__(self, session)
		self.skinName = "HarddiskDriveSetup"
		self.hdd = device
		self.setup_title = _("Hard disk")
		if self.hdd.isRemovable:
			self.setup_title = _("Storage device")
		self.oldMountpath = None
		self.oldEnabledState = None
		self.UUIDPartitionList = [ ]

		if stype not in (self.HARDDISK_INITIALIZE, self.HARDDISK_CHECK, self.HARDDISK_SETUP):
			self.type = self.HARDDISK_INITIALIZE
		else:
			self.type = stype

		self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.uuidPath, self.partitionPath = harddiskmanager.getPartitionVars(self.hdd,partition)
		if config.storage.get(self.UUID, None) is not None:
			self.oldMountpath = config.storage[self.UUID]["mountpoint"].value
			self.oldEnabledState = config.storage[self.UUID]["enabled"].value

		print "[HarddiskDriveSetup]-> deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'\n- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
		% (self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.partitionPath, self.uuidPath, self.hdd.device,self.hdd.dev_path)

		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self["introduction"] = StaticText()
		self["model"] = StaticText(_("Model: ") + self.hdd.model())
		self["capacity"] = StaticText(_("Capacity: ") + self.hdd.capacity())
		self["bus"] = StaticText()
		self["icon"] = StaticText()
		self["bus"].setText(self.hdd.bus_description() + " " + _("Hard disk"))
		self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-open.png"))
		if self.hdd.isRemovable:
			self["bus"].setText(self.hdd.bus_description() + " " + _("Storage device"))
			self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-big.png"))
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()

		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
			{
			"cancel": self.keyCancel,
			"ok": self.ok,
			}, -2)

		self["shortcuts"] = ActionMap(["ColorActions"],
			{
			"red": self.hddQuestion
			}, -2)

		self["mountshortcuts"] = ActionMap(["ShortcutActions"],
			{
			"green": self.apply
			}, -2)

		self["mountshortcuts"].setEnabled(False)
		if self.type == self.HARDDISK_SETUP:
			self["shortcuts"].setEnabled(False)

		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.__onShown)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def __onShown(self):
		self.selectionChanged()

	def createSetup(self):
		self.list = [ ]
		if self.type == self.HARDDISK_SETUP:
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
							uuid_cfg["mountpoint"].value = val
						self.list.append(getConfigListEntry(_("Mountpoint:"), uuid_cfg["mountpoint"]))

		self["config"].list = self.list
		self["config"].l.setSeperation(400)
		self["config"].l.setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

	def selectionChanged(self):
		self["key_red"].setText(_("Initialize"))
		if self.type == self.HARDDISK_SETUP:
			self["shortcuts"].setEnabled(False)
			self["key_red"].setText("")
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
		elif self.type == self.HARDDISK_INITIALIZE:
			self["shortcuts"].setEnabled(True)
			self["key_red"].setText(_("Initialize"))
			if self.numPartitions >= 0:
				uuid_cfg = config.storage.get(self.UUID, None)
				if uuid_cfg is not None:
					self["introduction"].setText(_("Press Red to initialize this hard disk!"))
					if self.hdd.isRemovable:
						self["introduction"].setText(_("Press Red to initialize this storage device!"))
				partitionType = harddiskmanager.getBlkidPartitionType(self.partitionPath)
				if self.UUID is None and partitionType is None:
					self["introduction"].setText(_("New uninitialized hard disk found. Please initialize!"))
					if self.hdd.isRemovable:
						self["introduction"].setText(_("New uninitialized storage device found. Please initialize!"))
				if self.UUID is None and partitionType is not None:
					self["introduction"].setText(_("Unknown partition layout or new uninitialized hard disk found. Please initialize!"))
					if self.hdd.isRemovable:
						self["introduction"].setText(_("Unknown partition layout or new uninitialized storage device found. Please initialize!"))
				if self.UUID is not None and partitionType is None:
					self["introduction"].setText(_("Unknown partition layout or new uninitialized hard disk found. Please initialize!"))
					if self.hdd.isRemovable:
						self["introduction"].setText(_("Unknown partition layout or new uninitialized storage device found. Please initialize!"))
		elif self.type == self.HARDDISK_CHECK:
			self["shortcuts"].setEnabled(True)
			self["key_red"].setText(_("Check"))
			self["introduction"].setText(_("Press Red to start the filesystem check."))

	def hddReady(self, result):
		print "hddReady result: " + str(result)
		if (result != 0):
			if self.type == self.HARDDISK_INITIALIZE:
				message = _("Unable to initialize hard disk.\nError: ")
				if self.hdd.isRemovable:
					message = _("Unable to initialize storage device.\nError: ")
			else:
				message = _("Unable to complete filesystem check.\nError: ")
			self.session.open(MessageBox, message + str(self.hdd.errorList[0 - result]), MessageBox.TYPE_ERROR)
		else:
			if self.type == self.HARDDISK_INITIALIZE:
				#we need to wait until udev has set up all new system links
				self.timer = eTimer()
				self.timer.callback.append(self.verifyInitialize)
				self["introduction"].setText(_("Verifying initialization. Please wait!"))
				self.timer.start(3000,True)
			elif self.type == self.HARDDISK_CHECK:
				harddiskmanager.mountPartitionbyUUID(self.UUID)
				self["introduction"].setText(_("Filesystem check completed without errors."))

	def verifyInitialize(self):
		self.timer.stop()
		self.deviceName, tmpid, self.numPartitions, self.partitionNum, self.uuidPath, self.partitionPath = harddiskmanager.getPartitionVars(self.hdd)
		#print "[HarddiskDriveSetup]-> deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'\n- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
		#% (self.deviceName, tmpid, self.numPartitions, self.partitionNum, self.partitionPath, self.uuidPath, self.hdd.device,self.hdd.dev_path)

		if tmpid is not None and tmpid != self.UUID:
			if self.UUID == defaultStorageDevice() or (self.UUID is None and not harddiskmanager.HDDEnabledCount()): #we initialized the default storage device
				print "[HarddiskDriveSetup] - verifyInitialize - set up device %s as default." % tmpid
				config.storage_options.default_device.value = tmpid
				config.storage_options.default_device.save()
				config.storage_options.save()
			if config.storage.get(self.UUID, None) is not None:
				del config.storage[self.UUID] #delete old uuid reference entries
			self.UUID = harddiskmanager.getPartitionUUID(self.deviceName)
			print "[HarddiskDriveSetup] - verifyInitialize - got new uuid: ",self.UUID

		if self.UUID is not None:
			if config.storage.get(self.UUID, None) is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = self.deviceName)
			if config.storage.get(self.UUID, None) is not None:
				if self.UUID == defaultStorageDevice():
					config.storage[self.UUID]["enabled"].value = True
					config.storage[self.UUID]["mountpoint"].value = "/media/hdd"
				self.type = self.HARDDISK_SETUP
				self["shortcuts"].setEnabled(True)
				self.createSetup()
				self.selectionChanged()
			else:
				self["introduction"].setText(_("Unable to verify partition information. Please restart!"))

	def hddQuestion(self):
		if self.type == self.HARDDISK_INITIALIZE:
			message = _("Do you really want to initialize this hard disk?\nAll data on this disk will be lost!")
			if self.hdd.isRemovable:
				message = _("Do you really want to initialize this storage device?\nAll data on this device will be lost!")

		elif self.type == self.HARDDISK_CHECK:
			message = _("Do you really want to check the filesystem?\nThis could take lots of time!")
		self.session.openWithCallback(self.hddConfirmed, MessageBox, message)

	def hddConfirmed(self, confirmed):
		if not confirmed:
			return
		print "hddConfirmed: this will start either the initialize or the fsck now!"
		if self.type == self.HARDDISK_INITIALIZE:
			print "hddConfirmed: start initialize for uuid:%s and device:%s and partitions:%s" % (self.UUID, self.hdd.device, self.numPartitions)
			if self.hdd.numPartitions() >=2:
				for p in harddiskmanager.partitions[:]:
					if p.device is not None:
						if p.device.startswith(self.hdd.device) and p.device[3:].isdigit():
							if p.uuid is not None:
								self.UUIDPartitionList.append(p.uuid)
			if self.UUIDPartitionList:
				for uuid in self.UUIDPartitionList[:]:
					if config.storage.get(uuid, None) is not None:
						harddiskmanager.unmountPartitionbyUUID(uuid)
						del config.storage[uuid]
						print "hddConfirmed: known device re-initialize, removed old uuid:",uuid
						config.storage.save()
						config.save()
						configfile.save()

			if config.storage.get(self.UUID, None) is not None:
				harddiskmanager.unmountPartitionbyUUID(self.UUID)
				del config.storage[self.UUID]
				print "hddConfirmed: known device re-initialize"
				config.storage.save()
				config.save()
				configfile.save()
		self.session.openWithCallback(self.hddReady, HarddiskWait, self.hdd, self.type, self.numPartitions)

	def changedConfigList(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
				if self["config"].getCurrent()[1] == config.storage[self.UUID]["enabled"]:
					self.createSetup()

	def keyLeft(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
				ConfigListScreen.keyLeft(self)
				self.changedConfigList()

	def keyRight(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
				ConfigListScreen.keyRight(self)
				self.changedConfigList()

	def ok(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numPartitions >= 0 and config.storage.get(self.UUID, None) is not None:
				current = self["config"].getCurrent()
				if current is not None:
					if current[1] == config.storage[self.UUID]["mountpoint"]:
						self.hideHelpWindow()
						self.oldMountpath = config.storage[self.UUID]["mountpoint"].value
						self.session.openWithCallback(self.MountpointBrowserClosed, HarddiskMountpointBrowser, self.hdd, self.UUID)

	def hideHelpWindow(self):
		if self.type == self.HARDDISK_SETUP:
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
		print "[HarddiskSetup]confirmFstabUpgrade:",result, uuid, partitionPath, mountpath, callConfirmApply
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
							harddiskmanager.modifyFstabEntry(self.uuidPath, uuid_cfg['mountpoint'].value, mode = "add_deactivated")
						updateVideoDirs(self.UUID)
				else:
					self.session.open(MessageBox, _("There was en error while configuring your storage device."), MessageBox.TYPE_ERROR)

				#print "[HarddiskDriveSetup confirmApply]-> deviceName:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'\n- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
				#% (self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.partitionPath, self.uuidPath, self.hdd.device,self.hdd.dev_path)
				self.close()

	def apply(self):
		self.hideHelpWindow()
		if self["config"].isChanged():
			if config.storage[self.UUID]['mountpoint'].value == '' :
					self.session.open(MessageBox, _("Please select a mountpoint for this partition."), MessageBox.TYPE_ERROR)
			else:
				mountpath = config.storage[self.UUID]['mountpoint'].value
				#print "[HarddiskDriveSetup]-> Apply:'%s' - uuid:'%s' - numPart:'%s' - partNum:'%s'\n- partPath:'%s' - uuidPath:'%s' - hdd.device:'%s' - hdd.dev_path:'%s'" \
				#% (self.deviceName, self.UUID, self.numPartitions, self.partitionNum, self.partitionPath, self.uuidPath, self.hdd.device,self.hdd.dev_path)

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
		self["introduction"] = StaticText()

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
			"red": (self.keyRed, _("Remove offline storage device.")),
			}, -2)

		self["GreenColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"green": (self.keyGreen, _("Initialize selected storage device.")),
			}, -2)

		self["YellowColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"yellow": (self.keyYellow, _("Check selected storage device.")),
			}, -2)

		self["BlueColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"blue": (self.keyBlue, _("Advanced settings.")),
			}, -2)

		self["OkActions"].setEnabled(False)
		self["RedColorActions"].setEnabled(False)
		self["GreenColorActions"].setEnabled(False)
		self["YellowColorActions"].setEnabled(False)
		self["BlueColorActions"].setEnabled(False)

		self.view = self.VIEW_HARDDISK
		self.selectedHDD = None
		self.currentIndex = 0
		self.currentlyUpdating = False
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
			if self.currentlyUpdating is False and self.view == self.VIEW_HARDDISK:
				self.currentlyUpdating = True
				self.setButtons()
				self.updateList()

	def buildHDDList(self, hd, isOfflineStorage = False, partNum = False):
		divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/div-h.png"))
		devicepng = onlinepng = None
		isOfflineStorageDevice = isOfflineStorage
		isConfiguredStorageDevice = isMountedPartition = isReadable = False
		currentMountpoint = partitionType = selectedPart = partitionPath = deviceName = uuidPath =None
		hdd_description = device_info = ""
		numPartitions = 0
		partitionNum = False
		fstype = sys = size = sizeg = None

		if isOfflineStorageDevice:
			uuid = hd
			print "[HarddiskDriveSelection] - buildHDDList for offline uuid: ",uuid
			hdd_description = config.storage[uuid]["device_description"].value
			if config.storage[uuid]["enabled"].value == True:
				isConfiguredStorageDevice = True
				currentMountpoint = config.storage[uuid]["mountpoint"].value
			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-unavailable.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green_off.png"))
			if config.storage[uuid]["isRemovable"].value == True:
				devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-unavailable.png"))
				device_info += config.storage[uuid]["device_info"].value + " " + _("Storage device")
			else:
				device_info += config.storage[uuid]["device_info"].value + " " + _("Hard disk")
			if currentMountpoint is not None:
				device_info += " - " + "( " + currentMountpoint + " )"
		else:
			hdd_description = hd.model()
			deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)
			print "[HarddiskDriveSelection] - buildHDDList for online device:",deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath
			if partitionNum is False:
				cap = hd.capacity()
				if cap != "":
					hdd_description += " (" + cap + ")"
			else:
				fstype, sys, size, sizeg = harddiskmanager.getFdiskInfo(hd.device + str(partitionNum))
				if sizeg is not None:
					hdd_description += " (" + sizeg + " GB)"

			if uuid is not None:
				p = harddiskmanager.getPartitionbyUUID(uuid)
				if p is not None:
					selectedPart = p
					if selectedPart.fsType == None:
						partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)

			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green.png"))
			if hd.isRemovable:
				devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable.png"))
				device_info += hd.bus_description() + " " + _("Storage device")
			else:
				device_info += hd.bus_description() + " " + _("Hard disk")

			if uuid is not None:
				cfg_uuid = config.storage.get(uuid, None)
				if cfg_uuid is not None:
					if cfg_uuid["mountpoint"].value != "":
						currentMountpoint = cfg_uuid["mountpoint"].value
					if cfg_uuid["enabled"].value:
						isConfiguredStorageDevice = True
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
								device_info += " - " + _("Needs attention!")
							else:
								device_info += " - " + _("No mountpoint defined!")
						else:
							if not isMountedPartition:
								if selectedPart is not None and selectedPart.isMountable:
									if selectedPart.isReadable:
										isReadable = True
										device_info += " - " + _("No mountpoint defined!")
									else:
										device_info += " - " + _("Unsupported partition type!")
								elif selectedPart is not None and not selectedPart.isMountable:
									if self.view == self.VIEW_HARDDISK:
										device_info += " - " + _("Please initialize!")
									else:
										device_info += " - " + _("Unsupported partition type!")
								else:
									if access("/autofs/" + deviceName, F_OK|R_OK):
										isReadable = True
										try:
											listdir("/autofs/" + deviceName)
										except OSError:
											isReadable = False
										if isReadable:
											device_info += " - " + _("No mountpoint defined!")
										else:
											device_info += " - " + _("Unsupported partition type!")
									else:
										if self.view == self.VIEW_HARDDISK:
											device_info += " - " + _("Please initialize!")
										else:
											device_info += " - " + _("Unsupported partition type!")
					if currentMountpoint is None and cfg_uuid is not None:
						currentMountpoint = cfg_uuid["mountpoint"].value
						if currentMountpoint == "":
							if selectedPart is not None and selectedPart.isMountable:
								if selectedPart.isReadable:
									isReadable = True
									device_info += " - " + _("No mountpoint defined!")
								else:
									device_info += " - " + _("Unsupported partition type!")
							elif selectedPart is not None and not selectedPart.isMountable:
								if self.view == self.VIEW_HARDDISK:
									device_info += " - " + _("Please initialize!")
								else:
									device_info += " - " + _("Unsupported partition type!")
							else:
								if access("/autofs/" + deviceName, F_OK|R_OK):
									isReadable = True
									try:
										listdir("/autofs/" + deviceName)
									except OSError:
										isReadable = False
									if isReadable:
										device_info += " - " + _("No mountpoint defined!")
									else:
										device_info += " - " + _("Unsupported partition type!")
								else:
									if self.view == self.VIEW_HARDDISK:
										device_info += " - " + _("Please initialize!")
									else:
										device_info += " - " + _("Unsupported partition type!")
					if (currentMountpoint is None and cfg_uuid is None):
						device_info += " - " + _("No mountpoint defined!")
				if isMountedPartition:
					isReadable = True
					devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-configured.png"))
					if hd.isRemovable:
						devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-configured.png"))
					device_info += " - " + currentMountpoint
			else:
				if numPartitions <=1:
					device_info += " - " + _("Please initialize!")
				else:
					if self.view == self.VIEW_HARDDISK:
						device_info += " - " + _("Multiple partitions found!")
					else:
						device_info += " - " + _("Unsupported partition type!")

		#print "BuildHDDLIST",hdd_description, device_info, numPartitions, isOfflineStorageDevice, isMountedPartition, currentMountpoint, partitionPath, partitionType, partitionNum, isReadable
		return((hdd_description, hd, device_info, numPartitions, isOfflineStorageDevice, isMountedPartition, currentMountpoint, devicepng, onlinepng, divpng, partitionNum, isReadable, partitionPath, partitionType, deviceName))

	def updateList(self):
		self.view = self.VIEW_HARDDISK
		self.selectedHDD = None
		self.list = []

		for hd in harddiskmanager.hdd:
			if not hd.isRemovable:
				numPart = hd.numPartitions()
				self.list.append(self.buildHDDList(hd, isOfflineStorage = False)) #online hard disk devices discovered
		for hd in harddiskmanager.hdd:
			if hd.isRemovable:
				numPart = hd.numPartitions()
				self.list.append(self.buildHDDList(hd, isOfflineStorage = False)) #online removable devices discovered
		if self.list:
			self.list.sort(key=lambda x: x[14][:3])
		for uuid in config.storage:
			dev = harddiskmanager.getDeviceNamebyUUID(uuid)
			if dev is None:
				self.list.append(self.buildHDDList(uuid, isOfflineStorage = True)) #offline devices
		if not self.list:
			self.list.append((_("no storage devices found"), 0, None, None, None, None, None, None, None, None, False))
			self["introduction"].setText(_("No installed or configured storage devices found!"))

		self["hddlist"].setList(self.list)
		if not self.selectionChanged in self["hddlist"].onSelectionChanged:
			self["hddlist"].onSelectionChanged.append(self.selectionChanged)
		self["hddlist"].setIndex(self.currentIndex)
		self.currentlyUpdating = False

	def updatePartitionList(self, hdd):
		self.view = self.VIEW_PARTITION
		self.selectedHDD = hdd
		numpart = hdd.numPartitions()
		self.list = []
		for p in harddiskmanager.partitions[:]:
			if p.device is not None:
				if p.device.startswith(hdd.device) and p.device[3:].isdigit():
					#print "add partition",p.device[3:],p.device
					self.list.append(self.buildHDDList(hdd, isOfflineStorage = False, partNum = p.device[3:])) #online devices partition discovered
		if self.list:
			self.list.sort(key=lambda x: x[14][3:])
		self["hddlist"].setList(self.list)
		if not self.selectionChanged in self["hddlist"].onSelectionChanged:
			self["hddlist"].onSelectionChanged.append(self.selectionChanged)
		self["hddlist"].setIndex(0)
		self.currentlyUpdating = False

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
		if config.usage.setup_level.index >= 1:
			if self.list:
				self["key_blue"].setText(_("Settings"))
				self["BlueColorActions"].setEnabled(True)

	def selectionChanged(self):
		#[HarddiskDriveSelection] - current: (0: hdd_description, 1:hd/uuid, 2;device_info, 3:numpart, 4:isOfflineStorageDevice, 5:isMountedPartition, 6:currentMountpoint, devicepng, onlinepng, divpng)
		self.setButtons()
		current = self["hddlist"].getCurrent()
		introduction = ""
		selectedPart = None
		if current:
			self.currentIndex = self["hddlist"].getIndex()
			numpart = current[3]
			offline = current[4]
			partNum = current[10]
			if numpart >= 0 and not offline:
				self["key_green"].setText(_("Initialize"))
				self["GreenColorActions"].setEnabled(True)
				self["OkActions"].setEnabled(True)
				introduction = _("Please press OK to set up a mountpoint for this hard disk!")
				hd = current[1]
				isReadable = current[11]
				selectedPart = None
				partitionType = None
				if hd.isRemovable:
					introduction = _("Please press OK to set up a mountpoint for this storage device!")
				deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)
				if partitionNum is False and numPartitions >= 2:
						self["key_green"].setText("")
						self["GreenColorActions"].setEnabled(False)
						introduction = _("Please press OK to see available partitions!")
				if partitionNum is not False and numPartitions >= 2:
					self["key_green"].setText("")
					self["GreenColorActions"].setEnabled(False)

				if uuid is not None:
					p = harddiskmanager.getPartitionbyUUID(uuid)
					if p is not None:
						selectedPart = p
						partitionType = selectedPart.fsType
						if partitionType is None:
							partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)
				if self.view == self.VIEW_HARDDISK:
					if uuid is not None:
						if numPartitions <= 1:
							if partitionType is not None and partitionType in ( "ext2", "ext3" ):
								self["key_yellow"].setText(_("Check"))
								self["YellowColorActions"].setEnabled(True)
							else:
								if not isReadable:
									self["OkActions"].setEnabled(False)
									introduction = _("Please press green to initialize this hard disk!")
									if hd.isRemovable:
										introduction = _("Please press green to initialize this storage device!")
					else:
						if numPartitions <= 1:
							self["OkActions"].setEnabled(False)
							introduction = _("Please press green to initialize this hard disk!")
							if hd.isRemovable:
								introduction = _("Please press green to initialize this storage device!")
				if self.view == self.VIEW_PARTITION:
					if uuid is not None:
						if partitionType is not None and partitionType in ( "ext2", "ext3" ):
							self["key_yellow"].setText(_("Check"))
							self["YellowColorActions"].setEnabled(True)
						else:
							introduction = _("Please press OK to set up a mountpoint for this partition!")
							if not isReadable:
								self["OkActions"].setEnabled(False)
								introduction = _("Unknown or unsupported partition type found!")
					else:
						self["OkActions"].setEnabled(False)
						introduction = _("Please initialize this hard disk!")
						if hd.isRemovable:
							introduction = _("Please initialize this storage device!")
						if not isReadable:
								introduction = _("Unknown or unsupported partition type found!")
			if offline:
				self["key_red"].setText(_("Remove"))
				self["RedColorActions"].setEnabled(True)
				introduction = _("Please press red to remove this hard disk configuration!")
				if isinstance(current[1], (basestring, str)):
					if config.storage[current[1]]["isRemovable"].value == True:
						introduction = _("Please press red to remove this storage device configuration!")

			self["introduction"].setText(introduction)

	def keyCancel(self):
		if self.view == self.VIEW_PARTITION:
			self.view = self.VIEW_HARDDISK
			self.mainMenuClosed()
		else:
			self.close()

	def handleAnswer(self, answer, selection):
		answer = answer and answer[1]
		if answer == "mount_default":
			self.applyAnswer(answer, selection)
		elif answer == "mount_only":
			self.applyAnswer(answer, selection)
		elif answer == "mount_manually":
			hd = selection[1]
			numpart = selection[3]
			partNum = selection[10]
			if numpart >= 2 and partNum is not False:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_SETUP, device = hd, partition = partNum)
			else:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_SETUP, device = hd)
		elif answer == "unmount":
			self.confirmApplyAnswer(True, answer, selection)
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
			if answer == "mount_default":
				mountpath = "/media/hdd"
			else:
				mountpath = harddiskmanager.suggestDeviceMountpath(uuid)

			if harddiskmanager.isUUIDpathFsTabMount(uuid, mountpath) or harddiskmanager.isPartitionpathFsTabMount(uuid, mountpath) \
				or harddiskmanager.isUUIDpathFsTabMount(uuid, "/media/hdd") or harddiskmanager.isPartitionpathFsTabMount(uuid, "/media/hdd"):
				message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
				self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, uuid, partitionPath, mountpath, answer, selection, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
			else:
				self.confirmApplyAnswer(True, answer, selection)
		else:
			print "[applyAnswer] - could not determine uuid"

	def confirmFstabUpgrade(self, result, uuid, partitionPath, mountpath, answer, selection, callConfirmApply = False):
		if not result:
			return
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
			hd = selection[1]
			partNum = selection[10]
			deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)

			successfully = False
			uuid_cfg = config.storage.get(uuid, None)
			if uuid_cfg is not None:
				if answer == "unmount":
					updateVideoDirs(uuid)
				successfully = harddiskmanager.changeStorageDevice(uuid, answer, None)
				print "confirmApplyAnswer:",uuid_cfg['enabled'].value, uuid_cfg['mountpoint'].value
			if successfully:
				uuid_cfg = config.storage.get(uuid, None)
				if uuid_cfg is not None:
					if answer in ("mount_default", "mount_only"):
						harddiskmanager.modifyFstabEntry(uuidPath, uuid_cfg['mountpoint'].value, mode = "add_deactivated")
					updateVideoDirs(uuid)
			else:
				self.session.open(MessageBox, _("There was en error while configuring your storage device."), MessageBox.TYPE_ERROR)
			self.mainMenuClosed()

	def okbuttonClick(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - okbuttonClick:",selection[0], selection[2], selection[3],selection[10]
			hd = selection[1]
			partNum = selection[10]
			isReadable = selection[11]
			selectedPart = None
			deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath = harddiskmanager.getPartitionVars(hd,partNum)

			if uuid is not None:
				p = harddiskmanager.getPartitionbyUUID(uuid)
				if p is not None:
					selectedPart = p

			uuid_cfg = config.storage.get(uuid, None)
			if uuid is not None and uuid_cfg is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = deviceName)

			defaultmsg = (_("Set up as default storage device now."), "mount_default")
			mountmsg = (_("Automatically set up a mountpoint now."), "mount_only")
			manualmsg = (_("Manually select a mountpoint now."), "mount_manually")
			unmountmsg = (_("Unmount now."), "unmount")

			choices = [ ]
			if uuid_cfg is not None and not uuid_cfg['enabled'].value: # unconfigured drive
				if selectedPart is not None and selectedPart.isInitialized:
					choices.extend([defaultmsg, mountmsg, manualmsg])
				else:
					choices.extend([mountmsg, manualmsg])
			elif uuid_cfg is not None and uuid_cfg['enabled'].value: # configured drive
				if selectedPart is not None and selectedPart.isInitialized:
					if defaultStorageDevice() != uuid:
						choices.extend([unmountmsg, defaultmsg, manualmsg])
					elif defaultStorageDevice() == uuid:
						choices.extend([unmountmsg, mountmsg, manualmsg])
				else:
					choices.extend([unmountmsg, manualmsg])
			choices.append((_("Do nothing."), "nothing"))

			titletext = _("Unconfigured hard disk found!")
			if hd.isRemovable:
				titletext = _("Unconfigured storage device found!")

			if uuid_cfg is not None and uuid_cfg['enabled'].value:
				titletext = _("Hard disk already configured!")
				if hd.isRemovable:
					titletext = _("Storage device already configured!")

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

	def keyRed(self):
		selection = self["hddlist"].getCurrent()
		if isinstance(selection[1], (basestring, str)):
			print "[HarddiskDriveSelection] - keyRed:",selection[0], selection[1]
			message = _("Really delete this hard disk entry?")
			if config.storage[selection[1]]["isRemovable"].value:
				message = _("Really delete this storage device entry?")
			self.session.openWithCallback(lambda x : self.keyRedConfirm(x, selection[1]), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)

	def keyRedConfirm(self, result, uuid):
		if not result:
			return
		if config.storage.get(uuid, None) is not None:
			updateVideoDirs(uuid)
			del config.storage[uuid]
			config.storage.save()
			config.save()
			configfile.save()
			if self.currentlyUpdating is False:
				self.currentlyUpdating = True
				self.setButtons()
				self.updateList()

	def keyGreen(self):
		#[HarddiskDriveSelection] - current: (0: hdd_description, 1:hd/uuid, 2;device_info, 3:numpart, 4:isOfflineStorageDevice, 5:isMountedPartition, 6:currentMountpoint, devicepng, onlinepng, divpng)
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - keyGreen:",selection[0], selection[2], selection[3]
			self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_INITIALIZE, device = selection[1])

	def keyYellow(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - keyYellow:",selection[0], selection[2], selection[3], selection[10]
			if selection[3] >= 2 and selection[10] is not False:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_CHECK, device = selection[1], partition = selection[10])
			else:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_CHECK, device = selection[1], partition = selection[3])

	def keyBlue(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			self.session.openWithCallback(self.mainMenuClosed, Setup, "harddisk")


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
