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

def doFstabUpgrade(uuid, path, mp, callConfirmApply, applyCallback = None, answer = None, selection = None):
	partitionPath = path
	mountpath = mp
	if (harddiskmanager.is_fstab_mountpoint(partitionPath, mountpath) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto'):
		harddiskmanager.unmountPartitionbyMountpoint(mountpath)
		harddiskmanager.modifyFstabEntry(partitionPath, mountpath, mode = "add_deactivated")
	if (harddiskmanager.is_fstab_mountpoint(partitionPath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(partitionPath, "/media/hdd") == 'auto'):
		harddiskmanager.unmountPartitionbyMountpoint("/media/hdd")
		harddiskmanager.modifyFstabEntry(partitionPath, "/media/hdd", mode = "add_deactivated")
	if applyCallback is not None:
		if harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto':
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

	def __init__(self, session, hdd, type, numpart = None):
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

		mountpath = harddiskmanager.get_fstab_mountpoint(partitionPath)
		if mountpath is not None:
			if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.is_fstab_mountpoint(partitionPath, mountpath)):
				self.isFstabMounted = True

		if uuid is not None:
			uuidpartitionPath = "/dev/disk/by-uuid/" + uuid
			if (harddiskmanager.is_hard_mounted(uuidpartitionPath) and harddiskmanager.is_fstab_mountpoint(uuidpartitionPath, mountpath)):
				if harddiskmanager.get_fstab_mountstate(uuidpartitionPath, mountpath) == 'auto':
					self.isFstabMounted = True
				else:
					self.isFstabMounted = False
		self.timer = eTimer()
		if type == HarddiskDriveSetup.HARDDISK_INITIALIZE:
			text = _("Initializing hard disk...")
			if self.hdd.isRemovable:
				text = _("Initializing storage device...")
			self.timer.callback.append(self.doInit)
		elif type == HarddiskDriveSetup.HARDDISK_CHECK:
			text = _("Checking Filesystem...")
			self.timer.callback.append(self.doCheck)
		self["wait"] = Label(text)
		self.timer.start(100)


class HarddiskDriveSetup(Screen, ConfigListScreen):
	HARDDISK_INITIALIZE = 1
	HARDDISK_CHECK = 2
	HARDDISK_SETUP = 3

	def __init__(self, session, type = None, device = None, partition = None):
		Screen.__init__(self, session)
		self.skinName = "HarddiskDriveSetup"
		self.hdd = device
		self.setup_title = _("Hard disk")
		if self.hdd.isRemovable:
			self.setup_title = _("Storage device")
		self.oldMountpath = None
		self.oldEnabledState = None
		self.UUIDPartitionList = [ ]
		
		if type not in (self.HARDDISK_INITIALIZE, self.HARDDISK_CHECK, self.HARDDISK_SETUP):
			self.type = self.HARDDISK_INITIALIZE
		else:
			self.type = type
		if partition is not None:
			self.numpart = partition
		else:
			self.numpart = self.hdd.numPartitions()

		if self.numpart == 0:
			self.devicename = self.hdd.device
			self.UUID = harddiskmanager.getPartitionUUID(self.devicename)
			self.partitionPath = self.hdd.dev_path
		if self.numpart >= 1:
			self.devicename = self.hdd.device + str(self.numpart)
			self.UUID = harddiskmanager.getPartitionUUID(self.devicename)
			self.partitionPath = self.hdd.partitionPath(str(self.numpart))
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
			if self.numpart >= 0:
				if self.UUID is not None and config.storage.get(self.UUID, None) is None:
					harddiskmanager.setupConfigEntries(initial_call = False, dev = self.devicename)
				uuid_cfg = config.storage.get(self.UUID, None)
				if uuid_cfg is not None:
					self["mountshortcuts"].setEnabled(True)
					self.list = [getConfigListEntry(_("Enable partition automount?"), uuid_cfg["enabled"])]
					if uuid_cfg["enabled"].value:
						if uuid_cfg["mountpoint"].value == "" or ( self.oldEnabledState is False and uuid_cfg["mountpoint"].value == "/media/hdd"):
							val = "/media/" + str(self.hdd.model(model_only = True)).strip().replace(' ','').replace('-','')
							if self.hdd.numPartitions() >= 2:
								val += "Part" + str(self.numpart)
							uuid_cfg["mountpoint"].value = val
						self.list.append(getConfigListEntry(_("Mountpoint:"), uuid_cfg["mountpoint"]))
		self["config"].list = self.list
		self["config"].l.setSeperation(400)
		self["config"].l.setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

	def selectionChanged(self):
		if self.type == self.HARDDISK_INITIALIZE:
			text = _("Initialize")
		elif self.type == self.HARDDISK_CHECK:
			text = _("Check")
		else:
			text = ""
		self["key_red"].setText(_("Initialize"))
		if self.type == self.HARDDISK_SETUP:
			self["shortcuts"].setEnabled(False)
			self["key_red"].setText("")
			if self.numpart >= 0:
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
			if self.numpart >= 0:
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
		self.numpart = self.hdd.numPartitions()
		self.partitionPath = self.hdd.partitionPath(str(self.numpart))
		self.devicename = self.hdd.device + str(self.numpart)
		tmpid = harddiskmanager.getPartitionUUID(self.devicename)
		if tmpid is not None and tmpid != self.UUID:
			if config.storage.get(self.UUID, None) is not None:
				del config.storage[self.UUID] #delete old uuid reference entries
			self.UUID = harddiskmanager.getPartitionUUID(self.devicename)

		if self.UUID is not None:
			if config.storage.get(self.UUID, None) is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = self.devicename)
			if config.storage.get(self.UUID, None) is not None:
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
		self.session.openWithCallback(self.hddReady, HarddiskWait, self.hdd, self.type, self.numpart)
	
	def changedConfigList(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numpart >= 0 and config.storage.get(self.UUID, None) is not None:
				print "changedConfigList",self["config"].getCurrent()
				if self["config"].getCurrent()[1] == config.storage[self.UUID]["enabled"]:
					self.createSetup()

	def keyLeft(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numpart >= 0 and  config.storage.get(self.UUID, None) is not None:
				ConfigListScreen.keyLeft(self)
				self.changedConfigList()

	def keyRight(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numpart >= 0 and config.storage.get(self.UUID, None) is not None:
				ConfigListScreen.keyRight(self)
				self.changedConfigList()

	def ok(self):
		if self.type == self.HARDDISK_SETUP:
			if self.numpart >= 0 and config.storage.get(self.UUID, None) is not None:
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
				uuidpath = "/dev/disk/by-uuid/" + self.UUID
				if (harddiskmanager.is_hard_mounted(self.partitionPath) or harddiskmanager.is_hard_mounted(uuidpath)):
					message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
					if (harddiskmanager.is_fstab_mountpoint(self.partitionPath, mountpath) and harddiskmanager.get_fstab_mountstate(self.partitionPath, mountpath) == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, self.partitionPath, mountpath, False), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					elif (harddiskmanager.is_fstab_mountpoint(self.partitionPath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(self.partitionPath, "/media/hdd") == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, self.partitionPath, "/media/hdd", False), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					elif (harddiskmanager.is_fstab_mountpoint(uuidpath, mountpath) and harddiskmanager.get_fstab_mountstate(uuidpath, mountpath) == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, uuidpath, mountpath, False), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					elif (harddiskmanager.is_fstab_mountpoint(uuidpath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(uuidpath, "/media/hdd") == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, uuidpath, "/media/hdd", False), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)

	def confirmFstabUpgrade(self, result, uuid, partitionPath, mountpath, callConfirmApply = False):
		if not result:
			return
		print "confirmFstabUpgrade - Removing hard mount entry from fstab."
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

			mountpath = config.storage[self.UUID]['mountpoint'].value
			partitionPath = self.partitionPath
			uuidpath = "/dev/disk/by-uuid/" + self.UUID

			if mountpath != self.oldMountpath:
				if harddiskmanager.is_uuidpath_mounted(uuidpath, self.oldMountpath):
					harddiskmanager.unmountPartitionbyMountpoint(self.oldMountpath)

			if config.storage[self.UUID]['enabled'].value:
				if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'noauto'):
					harddiskmanager.unmountPartitionbyMountpoint(config.storage[self.UUID]['mountpoint'].value, self.devicename) #self.hdd.device

			harddiskmanager.modifyFstabEntry(uuidpath, mountpath, mode = "add_deactivated")
			harddiskmanager.storageDeviceChanged(self.UUID)

			if config.storage[self.UUID]['enabled'].value:
				partitionType = harddiskmanager.getBlkidPartitionType(self.partitionPath)
				if partitionType is not None and partitionType in ( "ext2", "ext3" ):
					moviedir = mountpath + "/movie"
					if not path.exists(moviedir):
						self.session.open(MessageBox, _("Create movie folder failed. Please verify your mountpoint!"), MessageBox.TYPE_ERROR)
					else:
						tmp = config.movielist.videodirs.value
						movietmp = moviedir + "/"
						if movietmp not in tmp:
							tmp.append(movietmp)
						config.movielist.videodirs.value = tmp
			config.storage.save()
			config.save()
			configfile.save()

			if (mountpath != self.oldMountpath and config.storage[self.UUID]['enabled'].value and defaultStorageDevice() == self.UUID):
				harddiskmanager.verifyDefaultStorageDevice()
				tmp = config.movielist.videodirs.value
				movietmp = self.oldMountpath + "/movie/"
				if movietmp in tmp:
					tmp.remove(movietmp)
					config.movielist.videodirs.value = tmp

			if (not config.storage[self.UUID]['enabled'].value and defaultStorageDevice() == self.UUID):
				harddiskmanager.defaultStorageDeviceChanged(mountpath)

			if (harddiskmanager.HDDEnabledCount() and defaultStorageDevice() == "<undefined>"):
				self.session.openWithCallback(self.noDefaultDeviceConfigured, MessageBox, _("No default storage device defined!")  + "\n" \
					+ _("Please make sure to set up your default storage device in menu -> setup -> system -> recording paths.") + "\n\n" \
					+ _("Set up this storage device as default now?"), type = MessageBox.TYPE_YESNO, timeout = 20, default = True)
			else:
				self.close()

	def noDefaultDeviceConfigured(self, answer):
		if answer is not None:
			if answer:
				config.storage_options.default_device.value = self.UUID
				config.storage_options.default_device.save()
				config.storage_options.save()
				harddiskmanager.verifyDefaultStorageDevice()
				self.close()
			else:
				self.close()

	def apply(self):
		self.hideHelpWindow()
		if self["config"].isChanged():
			if config.storage[self.UUID]['mountpoint'].value == '' :
					self.session.open(MessageBox, _("Please select a mountpoint for this partition."), MessageBox.TYPE_ERROR)
			else:
				mountpath = config.storage[self.UUID]['mountpoint'].value
				uuidpath = "/dev/disk/by-uuid/" + self.UUID
				if (harddiskmanager.is_hard_mounted(self.partitionPath) or harddiskmanager.is_hard_mounted(uuidpath)):
					message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
					if (harddiskmanager.is_fstab_mountpoint(self.partitionPath, mountpath) and harddiskmanager.get_fstab_mountstate(self.partitionPath, mountpath) == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, self.partitionPath, mountpath, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					elif (harddiskmanager.is_fstab_mountpoint(uuidpath, mountpath) and harddiskmanager.get_fstab_mountstate(uuidpath, mountpath) == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, uuidpath, mountpath, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					else:
						if (harddiskmanager.is_fstab_mountpoint(self.partitionPath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(self.partitionPath, "/media/hdd") == 'auto'):
							self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, self.partitionPath, "/media/hdd", True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
						elif (harddiskmanager.is_fstab_mountpoint(uuidpath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(uuidpath, "/media/hdd") == 'auto'):
							self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, self.UUID, uuidpath, "/media/hdd", True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
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
		print "changedEntry",self["config"].getCurrent()
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

	def buildHDDList(self, hd, isOfflineStorage = False, partitionNum = False ):
		divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/div-h.png"))
		devicepng = onlinepng = None
		isOfflineStorageDevice = isOfflineStorage
		isConfiguredStorageDevice = isMountedPartition = isReadable = False
		uuid = currentMountpoint = partitionPath = partitionType = devicename = None
		hdd_description = device_info = ""
		numpart = 0		

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
				device_info +=  config.storage[uuid]["device_info"].value + " " + _("Storage device")
			else:
				device_info +=  config.storage[uuid]["device_info"].value + " " + _("Hard disk")

			if currentMountpoint is not None:
				device_info += " - " + "( " + currentMountpoint + " )"
		else:
			hdd_description = hd.model()
			numpart = hd.numPartitions()
			if partitionNum is False:
				cap = hd.capacity()
				if cap != "":
					hdd_description += " (" + cap + ")"
				if numpart == 0:
					devicename = hd.device
					uuid = harddiskmanager.getPartitionUUID(devicename)
					partitionPath = hd.dev_path
				if numpart == 1:
					devicename = hd.device + str(numpart)
					uuid = harddiskmanager.getPartitionUUID(devicename)
					partitionPath = hd.partitionPath(str(numpart))
			else:
				type, sys, size, sizeg = harddiskmanager.getFdiskInfo(hd.device + str(partitionNum))
				if sizeg is not None:
					hdd_description += " (" + sizeg + " GB)"
				devicename = hd.device + str(partitionNum)
				uuid = harddiskmanager.getPartitionUUID(devicename)
				partitionPath = hd.partitionPath(str(partitionNum))
			partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)
			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green.png"))
			if hd.isRemovable:
				devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable.png"))
				device_info +=  hd.bus_description() + " " + _("Storage device")
			else:
				device_info +=  hd.bus_description() + " " + _("Hard disk")				

			print "[HarddiskDriveSelection] - found online device %s, '%s', '%s', '%s','%s'" % (devicename, device_info, partitionPath, partitionType, partitionNum)

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
					uuidpath = "/dev/disk/by-uuid/" + uuid
					if currentMountpoint is None:
						currentMountpoint = harddiskmanager.get_fstab_mountpoint(partitionPath) or harddiskmanager.get_fstab_mountpoint(uuidpath)
					if currentMountpoint is not None:
						if (harddiskmanager.is_hard_mounted(partitionPath) or harddiskmanager.is_hard_mounted(uuidpath)):
							if (harddiskmanager.is_fstab_mountpoint(partitionPath, currentMountpoint) and harddiskmanager.get_fstab_mountstate(partitionPath, currentMountpoint) == 'auto'):
								devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-attention.png"))
								if hd.isRemovable:
									devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-attention.png"))
								device_info += " - " + _("Needs attention!")
							elif (harddiskmanager.is_fstab_mountpoint(uuidpath, currentMountpoint) and harddiskmanager.get_fstab_mountstate(uuidpath, currentMountpoint) == 'auto'):
								devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-attention.png"))
								if hd.isRemovable:
									devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_removable-attention.png"))
								device_info += " - " + _("Needs attention!")
							elif (harddiskmanager.is_fstab_mountpoint(uuidpath, currentMountpoint) and harddiskmanager.get_fstab_mountstate(uuidpath, currentMountpoint) == 'noauto'):
								device_info += " - " + _("No mountpoint defined!")
							elif (harddiskmanager.is_fstab_mountpoint(partitionPath, currentMountpoint) and harddiskmanager.get_fstab_mountstate(partitionPath, currentMountpoint) == 'noauto'):
								device_info += " - " + _("No mountpoint defined!")
						else:
							if not isMountedPartition:
								if access("/autofs/" + devicename, F_OK|R_OK):
									isReadable = True
									try:
										listdir("/autofs/" + devicename)
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
					if (currentMountpoint is None and cfg_uuid is not None):
						currentMountpoint = cfg_uuid["mountpoint"].value
						if currentMountpoint == "":
							if access("/autofs/" + devicename, F_OK|R_OK):
								isReadable = True
								try:
									listdir("/autofs/" + devicename)
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
				if numpart <=1:
					device_info += " - " + _("Please initialize!")
				else:
					if self.view == self.VIEW_HARDDISK:
						device_info += " - " + _("Multiple partitions found!")
					else:
						device_info += " - " + _("Unsupported partition type!")
		#print "FINAL ENTRY",hdd_description, device_info, numpart, isOfflineStorageDevice, isMountedPartition, currentMountpoint, partitionPath, partitionType, partitionNum, isReadable
		return((hdd_description, hd, device_info, numpart, isOfflineStorageDevice, isMountedPartition, currentMountpoint, devicepng, onlinepng, divpng, partitionNum, isReadable))

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
					self.list.append(self.buildHDDList(hdd, isOfflineStorage = False, partitionNum = p.device[3:])) #online device partition discovered
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
		self.setButtons()
		current = self["hddlist"].getCurrent()
		introduction = ""
		if current:
			self.currentIndex = self["hddlist"].getIndex()
			numpart = current[3]
			offline = current[4]
			partitionNum = current[10]
			if numpart >= 0 and not offline:
				self["key_green"].setText(_("Initialize"))
				self["GreenColorActions"].setEnabled(True)
				self["OkActions"].setEnabled(True)
				introduction = _("Please press OK to set up a mountpoint for this hard disk!")
				hd = current[1]
				if hd.isRemovable:
					introduction = _("Please press OK to set up a mountpoint for this storage device!")
				uuid = None
				devicename = hd.device
				partitionPath = hd.partitionPath(str(numpart))
				isReadable = current[11]
				if partitionNum is False:
					if numpart == 0:
						uuid = harddiskmanager.getPartitionUUID(hd.device)
						partitionPath = hd.dev_path
					if numpart == 1:
						uuid = harddiskmanager.getPartitionUUID(hd.device + str(numpart))
						devicename = hd.device + str(numpart)
					if numpart >= 2:
						print "[HarddiskDriveSelection] - 2 or more partitions found!"
						introduction = _("Please press OK to see available partitions!")
				else:
					self["key_green"].setText("")
					self["GreenColorActions"].setEnabled(False)
					uuid = harddiskmanager.getPartitionUUID(hd.device + str(partitionNum))
					partitionPath = hd.partitionPath(str(partitionNum))
					devicename = hd.device + str(partitionNum)
				partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)
				if self.view == self.VIEW_HARDDISK:
					if uuid is not None:
						if numpart <= 1:
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
						if numpart <= 1:
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
			self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_SETUP, device = hd, partition = numpart)
		elif answer == "unmount":
			self.confirmApplyAnswer(True, answer, selection)
		elif answer in ( None, "nothing"):
			print "nothing to do"

	def applyAnswer(self, answer, selection):
		hd = selection[1]
		numpart = selection[3]
		partitionNum = selection[10]
		uuid = devicename = partitionPath = mountpath = uuidpath = None
		if numpart == 0:
			devicename = hd.device
			uuid = harddiskmanager.getPartitionUUID(devicename)
			partitionPath = hd.dev_path
		if numpart == 1:
			devicename = hd.device + str(numpart)
			uuid = harddiskmanager.getPartitionUUID(devicename)
			partitionPath = hd.partitionPath(str(numpart))

		if uuid is not None and config.storage.get(uuid, None) is None:
			harddiskmanager.setupConfigEntries(initial_call = False, dev = devicename)

		uuid_cfg = config.storage.get(uuid, None)
		if uuid_cfg is not None:
			oldenable = uuid_cfg["enabled"].value
			if oldenable is False:
				uuid_cfg["enabled"].value = True
				if uuid_cfg["mountpoint"].value == "" or ( oldenable is False and uuid_cfg["mountpoint"].value == "/media/hdd"):
					val = "/media/" + str(hd.model(model_only = True)).strip().replace(' ','').replace('-','')
					if hd.numPartitions() >= 2:
						val += "Part" + str(numpart)
					uuid_cfg["mountpoint"].value = val

			mountpath = uuid_cfg['mountpoint'].value
			uuidpath = "/dev/disk/by-uuid/" + uuid
			
			if (harddiskmanager.is_hard_mounted(partitionPath) or harddiskmanager.is_hard_mounted(uuidpath)):
				message = _("Device already hard mounted over filesystem table. Remove fstab entry?")
				if (harddiskmanager.is_fstab_mountpoint(partitionPath, mountpath) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto'):
					self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, uuid, partitionPath, mountpath, answer, selection, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
				elif (harddiskmanager.is_fstab_mountpoint(uuidpath, mountpath) and harddiskmanager.get_fstab_mountstate(uuidpath, mountpath) == 'auto'):
					self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, uuid, uuidpath, mountpath, answer, selection, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
				else:
					if (harddiskmanager.is_fstab_mountpoint(partitionPath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(partitionPath, "/media/hdd") == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, uuid, partitionPath, "/media/hdd", answer, selection, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					elif (harddiskmanager.is_fstab_mountpoint(uuidpath, "/media/hdd") and harddiskmanager.get_fstab_mountstate(uuidpath, "/media/hdd") == 'auto'):
						self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, uuid, uuidpath, "/media/hdd", answer, selection, True), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)
					else:
						self.confirmApplyAnswer(True, answer, selection)
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
			numpart = selection[3]
			partitionNum = selection[10]
			uuid = devicename = partitionPath = mountpath = uuidpath = None

			if partitionNum is False:
				if numpart == 0:
					devicename = hd.device
					uuid = harddiskmanager.getPartitionUUID(devicename)
					partitionPath = hd.dev_path
				if numpart == 1:
					devicename = hd.device + str(numpart)
					uuid = harddiskmanager.getPartitionUUID(devicename)
					partitionPath = hd.partitionPath(str(numpart))

			uuid_cfg = config.storage.get(uuid, None)
			if uuid_cfg is not None:
				if answer == "unmount":
					uuid_cfg["enabled"].value = False
				uuid_cfg.save()
				mountpath = uuid_cfg['mountpoint'].value
				uuidpath = "/dev/disk/by-uuid/" + uuid
				print "confirmApplyAnswer:",uuid_cfg['enabled'].value, uuid_cfg['mountpoint'].value

			if uuid_cfg is not None and uuid_cfg['enabled'].value:
				if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'noauto'):
					harddiskmanager.unmountPartitionbyMountpoint(mountpath, devicename)

			harddiskmanager.modifyFstabEntry(uuidpath, mountpath, mode = "add_deactivated")
			harddiskmanager.storageDeviceChanged(uuid)

			if uuid_cfg is not None and uuid_cfg['enabled'].value:
				if answer == "mount_default":
					config.storage_options.default_device.value = uuid
					config.storage_options.default_device.save()
					config.storage_options.save()
					harddiskmanager.verifyDefaultStorageDevice()

				partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)
				if partitionType is not None and partitionType in ( "ext2", "ext3" ):
					moviedir = mountpath + "/movie"
					if not path.exists(moviedir):
						self.session.open(MessageBox, _("Create movie folder failed. Please verify your mountpoint!"), MessageBox.TYPE_ERROR)
					else:
						tmp = config.movielist.videodirs.value
						if defaultStorageDevice != uuid:
							movietmp = moviedir + "/"
							if movietmp not in tmp:
								tmp.append(movietmp)
								config.movielist.videodirs.value = tmp

			if uuid_cfg is not None and not uuid_cfg['enabled'].value:
				tmp = config.movielist.videodirs.value
				movietmp = mountpath + "/movie/"
				if movietmp in tmp:
					tmp.remove(movietmp)
					config.movielist.videodirs.value = tmp
				if defaultStorageDevice() == uuid:
					config.storage_options.default_device.value = "<undefined>"
					config.storage_options.default_device.save()
					config.storage_options.save()
					harddiskmanager.verifyDefaultStorageDevice()

			config.storage.save()
			config.save()
			configfile.save()
			self.mainMenuClosed()

	def okbuttonClick(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - okbuttonClick:",selection[0], selection[2], selection[3],selection[10]
			hd = selection[1]
			numpart = selection[3]
			partitionNum = selection[10]
			isReadable = selection[11]
			uuid = devicename = partitionPath = mountpath = uuidpath = None

			if partitionNum is False:
				if numpart == 0:
					devicename = hd.device
					uuid = harddiskmanager.getPartitionUUID(devicename)
					partitionPath = hd.dev_path
				if numpart == 1:
					devicename = hd.device + str(numpart)
					uuid = harddiskmanager.getPartitionUUID(devicename)
					partitionPath = hd.partitionPath(str(numpart))

			uuid_cfg = config.storage.get(uuid, None)
			if uuid is not None and uuid_cfg is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = devicename)

			defaultmsg = ((_("Set up this hard disk as default storage device now."), "mount_default"),)
			mountmsg = ((_("Automatically set up a mountpoint for this hard disk now."), "mount_only"),)
			manualmsg = ((_("Manually select a mountpoint for this hard disk now."), "mount_manually"),)
			unmountmsg = ((_("Unmount this hard disk now."), "unmount"),)
			titletext = _("Unconfigured hard disk found!")
			if hd.isRemovable:
				defaultmsg = ((_("Set up this storage device as default storage device now."), "mount_default"),)
				mountmsg = ((_("Automatically set up a mountpoint for this storage device now."), "mount_only"),)
				manualmsg = ((_("Manually select a mountpoint for this storage device now."), "mount_manually"),)
				unmountmsg = ((_("Unmount this storage device now."), "unmount"),)
				titletext = _("Unconfigured storage device found!")

			if uuid_cfg is not None and uuid_cfg['enabled'].value:
				titletext = _("Hard disk already configured!")
				if hd.isRemovable:
					titletext = _("Storage device already configured!")

			if harddiskmanager.HDDCount() and not harddiskmanager.HDDEnabledCount():
				choices = defaultmsg + mountmsg + manualmsg
			elif harddiskmanager.HDDEnabledCount() and defaultStorageDevice() == "<undefined>":
				choices = defaultmsg + unmountmsg + manualmsg
			elif uuid_cfg is not None and uuid_cfg['enabled'].value and defaultStorageDevice() == "<undefined>":
				choices = defaultmsg + unmountmsg + manualmsg
			elif uuid_cfg is not None and uuid_cfg['enabled'].value and defaultStorageDevice() == uuid:
				choices = unmountmsg + manualmsg
			elif uuid_cfg is not None and not uuid_cfg['enabled'].value and defaultStorageDevice() == uuid:
				choices = mountmsg + manualmsg
			elif uuid_cfg is not None and not uuid_cfg['enabled'].value and defaultStorageDevice() == "<undefined>":
				choices = defaultmsg + unmountmsg + manualmsg
			elif uuid_cfg is not None and uuid_cfg['enabled'].value and defaultStorageDevice() != uuid:
				choices = unmountmsg + manualmsg + defaultmsg
			elif uuid_cfg is not None and not uuid_cfg['enabled'].value and defaultStorageDevice() != uuid:
				choices = mountmsg + manualmsg + defaultmsg
			else:
				choices = ()
			choices += ( (_("Do nothing."), "nothing"),)

			if numpart >= 2 and partitionNum is False:
				self.updatePartitionList(selection[1])
			elif numpart >= 2 and partitionNum is not False:
				self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_SETUP, device = hd, partition = partitionNum)
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
			if config.storage[selection[1]]["isRemovable"].value == True:
				message = _("Really delete this storage device entry?")
			self.session.openWithCallback(lambda x : self.keyRedConfirm(x, selection[1]), MessageBox, message, MessageBox.TYPE_YESNO, timeout = 20, default = True)

	def keyRedConfirm(self, result, uuid):
		if not result:
			return
		if config.storage.get(uuid, None) is not None:
			del config.storage[uuid]
			config.storage.save()
			config.save()
			configfile.save()
			if self.currentlyUpdating is False:
				self.currentlyUpdating = True
				self.setButtons()
				self.updateList()

	def keyGreen(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - keyGreen:",selection[0], selection[2], selection[3]
			self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_INITIALIZE, device = selection[1])

	def keyYellow(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - keyYellow:",selection[0], selection[2], selection[3],selection[10]
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
