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
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.Setup import Setup, getSetupTitle
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer
from os import path, makedirs
	
class HarddiskWait(Screen):
	def doInit(self):
		self.timer.stop()
		if self.isFstabMounted:
			result = self.hdd.initialize(self.isFstabMounted)
		else:
			result = self.hdd.initialize()
		harddiskmanager.trigger_udev()
		self.close(result)

	def doCheck(self):
		self.timer.stop()
		if self.isFstabMounted:
			result = self.hdd.check(isFstabMounted)
		else:
			result = self.hdd.check()
		self.close(result)

	def __init__(self, session, hdd, type):
		Screen.__init__(self, session)
		self.hdd = hdd
		self.isFstabMounted = False
		
		numpart = self.hdd.numPartitions()
		partitionPath = self.hdd.partitionPath(str(numpart))
		uuid = harddiskmanager.getPartitionUUID(self.hdd.device + str(numpart))
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
			text = _("Initializing Harddisk...")
			self.timer.callback.append(self.doInit)
		else:
			text = _("Checking Filesystem...")
			self.timer.callback.append(self.doCheck)
		self["wait"] = Label(text)
		self.timer.start(100)


class HarddiskDriveSetup(Screen, ConfigListScreen):
	HARDDISK_INITIALIZE = 1
	HARDDISK_CHECK = 2

	def __init__(self, session, type = None, device = None, partition = None):
		Screen.__init__(self, session)
		self.skinName = "HarddiskDriveSetup"
		self.setup_title = _("Harddisk")
		self.hdd = device
		
		if type not in (self.HARDDISK_INITIALIZE, self.HARDDISK_CHECK):
			self.type = self.HARDDISK_INITIALIZE
		else:
			self.type = type
		if partition is not None:
			self.numpart = partition
		else:
			self.numpart = self.hdd.numPartitions()
		
		self.UUID = harddiskmanager.getPartitionUUID(self.hdd.device + str(self.numpart))

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
		self["bus"] = StaticText(self.hdd.bus_description() + " " + _("Harddisk"))
		self["icon"] = StaticText()
		self["icon"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-open.png"))
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()

		if self.type == self.HARDDISK_INITIALIZE:
			text = _("Initialize")
		else:
			text = _("Check")
		
		self["key_red"].setText(text)

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

		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.list = [ ]
		if self.type == self.HARDDISK_INITIALIZE:
			if self.numpart:
				if self.UUID is not None and config.storage.get(self.UUID, None) is None:
					harddiskmanager.setupConfigEntries(initial_call = False, dev = self.hdd.device + str(self.numpart))
				uuid_cfg = config.storage.get(self.UUID, None)
				if uuid_cfg is not None:
					print "[HarddiskDriveSetup] createSetup for uuid:",self.UUID
					self["mountshortcuts"].setEnabled(True)
					self.list = [getConfigListEntry(_("Enable partition automount?"), uuid_cfg["enabled"])]
					if uuid_cfg["enabled"].value:
						if uuid_cfg["mountpoint"].value == "":
							if len(config.storage) <= 1:
								uuid_cfg["mountpoint"].value = "/media/hdd"
							else:
								uuid_cfg["mountpoint"].value = "/media/" + str(self.hdd.model(model_only = True))
						self.list.append(getConfigListEntry(_("Mountpoint:"), uuid_cfg["mountpoint"]))


		self["config"].list = self.list
		self["config"].l.setSeperation(400)
		self["config"].l.setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def selectionChanged(self):
		if self.type == self.HARDDISK_INITIALIZE:
			if self.numpart:
				if self["config"].isChanged():
					self["key_green"].setText(_("Save"))
				else:
					self["key_green"].setText("")
				if self["config"].getCurrent()[1] == config.storage[self.UUID]["enabled"]:
					self["introduction"].setText(_("Enable automatic partition mounting?"))
				elif self["config"].getCurrent()[1] == config.storage[self.UUID]["mountpoint"]:
					self["introduction"].setText(_("Please enter the directory to use as mountpoint or select a directory by pressing OK."))
				else:
					self["introduction"].setText("")
			else:
				self["introduction"].setText(_("New uninitialized harddisk found. Please initialize!"))
		else:
			self["introduction"].setText(_("Press Red to start the filesystem check."))	
	
	def hddReady(self, result):
		print "hddReady result: " + str(result)
		if (result != 0):
			if self.type == self.HARDDISK_INITIALIZE:
				message = _("Unable to initialize harddisk.\nError: ")
			else:
				message = _("Unable to complete filesystem check.\nError: ")
			self.session.open(MessageBox, message + str(self.hdd.errorList[0 - result]), MessageBox.TYPE_ERROR)
		else:
			if self.type == self.HARDDISK_INITIALIZE:
				#we need to wait until udev has set up all new system links
				self.timer = eTimer()
				self.timer.callback.append(self.verifyInitialize)
				self["introduction"].setText(_("Verifying harddisk initialization. Please wait!"))
				self.timer.start(2000,True)
			else:
				harddiskmanager.mountPartitionbyUUID(self.UUID)
				self["introduction"].setText(_("Filesystem check completed without errors."))

	def verifyInitialize(self):
		self.timer.stop()
		self.numpart = self.hdd.numPartitions()
		partitionPath = self.hdd.partitionPath(str(self.numpart))
		tmpid = harddiskmanager.getPartitionUUID(self.hdd.device + str(self.numpart))
		
		if tmpid is not None and tmpid != self.UUID:
			if config.storage.get(self.UUID, None) is not None:
				del config.storage[self.UUID] #delete old uuid reference entries
			self.UUID = harddiskmanager.getPartitionUUID(self.hdd.device + str(self.numpart))
			print "[HarddiskDriveSetup] - verifyInitialize - got new uuid: ",self.UUID
		
		if self.UUID is not None:
			if config.storage.get(self.UUID, None) is None:
				harddiskmanager.setupConfigEntries(initial_call = False, dev = self.hdd.device + str(self.numpart))
			if config.storage.get(self.UUID, None) is not None:
				self.createSetup()
			else:
				self["introduction"].setText(_("Unable to verifying partition information. Please restart!"))

	def hddQuestion(self):
		if self.type == self.HARDDISK_INITIALIZE:
			message = _("Do you really want to initialize the harddisk?\nAll data on the disk will be lost!")
		else:
			message = _("Do you really want to check the filesystem?\nThis could take lots of time!")
		self.session.openWithCallback(self.hddConfirmed, MessageBox, message)

	def hddConfirmed(self, confirmed):
		if not confirmed:
			return
		print "hddConfirmed: this will start either the initialize or the fsck now!"
		if self.type == self.HARDDISK_INITIALIZE:
			if config.storage.get(self.UUID, None) is not None:
				del config.storage[self.UUID]
				print "hddConfirmed: known device re-initialize"
				config.storage.save()
				config.save()
				configfile.save()
		self.session.openWithCallback(self.hddReady, HarddiskWait, self.hdd, self.type)
	
	def changedConfigList(self):
		if self.type == self.HARDDISK_INITIALIZE:
			if self.numpart:
				if self["config"].getCurrent()[1] == config.storage[self.UUID]["enabled"]:#self.autoMountEntry:
					self.createSetup()

	def keyLeft(self):
		if self.type == self.HARDDISK_INITIALIZE:
			if self.numpart:
				ConfigListScreen.keyLeft(self)
				self.changedConfigList()

	def keyRight(self):
		if self.type == self.HARDDISK_INITIALIZE:
			if self.numpart:
				ConfigListScreen.keyRight(self)
				self.changedConfigList()

	def ok(self):
		if self.type == self.HARDDISK_INITIALIZE:
			if self.numpart:
				current = self["config"].getCurrent()
				if current[1] == config.storage[self.UUID]["mountpoint"]:
					self.hideHelpWindow()
					self.session.openWithCallback(self.MountpointBrowserClosed, HarddiskMountpointBrowser, self.hdd, self.UUID)

	def hideHelpWindow(self):
		current = self["config"].getCurrent()
		if current is not None:
			if current[1] == config.storage[self.UUID]["mountpoint"]:
				if current[1].help_window.instance is not None:
					current[1].help_window.instance.hide()		

	def MountpointBrowserClosed(self, retval = None):
		if retval and retval is not None:
			mountpath = retval
			if retval.endswith("/"):
				mountpath = retval[:-1]
			print "MountpointBrowserClosed with path: " + str(mountpath)
			oldpath = config.storage[self.UUID]["mountpoint"].getValue()
			try:
				config.storage[self.UUID]["mountpoint"].setValue(str(mountpath))
				if mountpath != oldpath:
					if not path.exists(mountpath):
						makedirs(mountpath)
			except OSError:
				config.storage[self.UUID]["mountpoint"].setValue(oldpath)
				print "mountpoint directory could not be created."

			self["config"].invalidate(config.storage[self.UUID]["mountpoint"])
			if not path.exists(mountpath):
				self.session.open(MessageBox, _("Sorry, your directory is not writeable."), MessageBox.TYPE_INFO, timeout = 10)
			else:
				partitionPath = self.hdd.partitionPath(str(self.numpart))
				if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.is_fstab_mountpoint(partitionPath, mountpath)):
					if harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto':
						self.session.openWithCallback(self.confirmFstabUpgrade, MessageBox, _("Device already hard mounted over filesystem table. Remove fstab entry?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)
			
	def confirmFstabUpgrade(self, result, callConfirmApply = False):
		if not result:
			return
		print "confirmFstabUpgrade - Removing hard mount entry from fstab."
		partitionPath = self.hdd.partitionPath(str(self.numpart))
		mountpath = config.storage[self.UUID]['mountpoint'].value
		harddiskmanager.modifyFstabEntry(partitionPath, mountpath, mode = "add_deactivated")
		if harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto':
			self.session.open(MessageBox, _("Sorry, could not remove mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)
		else:
			self.session.open(MessageBox, _("Successfully, deactivated mount entry from fstab."), MessageBox.TYPE_INFO, timeout = 10)
			if callConfirmApply:
				self.confirmApply(True)
	
	def confirmApply(self, confirmed):
		if not confirmed:
			print "not confirmed"
			return
		else:
			for x in self["config"].list:
				x[1].save()
			print "confirmApply:",config.storage[self.UUID]['enabled'].value, config.storage[self.UUID]['mountpoint'].value
			mountpath = config.storage[self.UUID]['mountpoint'].value
			if config.storage[self.UUID]['enabled'].value:
				partitionPath = self.hdd.partitionPath(str(self.numpart))
				if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'noauto'):
					harddiskmanager.unmountPartitionbyMountpoint(config.storage[self.UUID]['mountpoint'].value, self.hdd.device)

			partitionPath = "/dev/disk/by-uuid/" + self.UUID
			harddiskmanager.modifyFstabEntry(partitionPath, mountpath, mode = "add_deactivated")
			harddiskmanager.storageDeviceChanged(self.UUID)
			
			if config.storage[self.UUID]['enabled'].value:
				moviedir = config.storage[self.UUID]['mountpoint'].value + "/movie"
				if not path.exists(moviedir):
					self.session.open(MessageBox, _("Create movie folder failed. Please verify your mountpoint!"), MessageBox.TYPE_ERROR)

			config.storage.save()
			config.save()
			configfile.save()
			self.close()

	def apply(self):
		self.hideHelpWindow()
		if config.storage[self.UUID]['mountpoint'].value == '' :
				self.session.open(MessageBox, _("Please select a mountpoint for this partition."), MessageBox.TYPE_ERROR)
		else:
			mountpath = config.storage[self.UUID]['mountpoint'].value					
			partitionPath = self.hdd.partitionPath(str(self.numpart))
			if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.is_fstab_mountpoint(partitionPath, mountpath) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpath) == 'auto'):
				self.session.openWithCallback(lambda x : self.confirmFstabUpgrade(x, True), MessageBox, _("Device already hard mounted over filesystem table. Remove fstab entry?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)
			else:
				self.session.openWithCallback(self.confirmApply, MessageBox, _("Use this settings?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)


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
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = "HarddiskDriveSelection"

		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()

		self["CancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.close, _("Exit harddisk selection.")),
			}, -2)

		self["OkActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"ok": (self.okbuttonClick, _("Select harddisk.")),
			}, -2)
		
		self["RedColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"red": (self.keyRed, _("Remove offline harddisk.")),
			}, -2)

		self["GreenColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"green": (self.keyGreen, _("Initialize selected harddisk.")),
			}, -2)

		self["YellowColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"yellow": (self.keyYellow, _("Check selected harddisk.")),
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
		
		harddiskmanager.delayed_device_Notifier.append(self.hotplugCB)

		self.currentIndex = 0
		self.currentlyUpdating = False
		self.list = []
		self["hddlist"] = List(self.list)

		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.__onClose)
		
	def layoutFinished(self):
		self.setTitle(_("Select HDD"))
		self.currentlyUpdating = True
		self.setButtons()
		self.updateList()
		
	def __onClose(self):
		self.currentlyUpdating = False
		self.currentIndex = 0
		harddiskmanager.delayed_device_Notifier.remove(self.hotplugCB)

	def hotplugCB(self, dev, media_state):
		if media_state in ("add_delayed", "remove_delayed"):
			print "[HarddiskDriveSelection] - hotplugCB for dev:%s, media_state:%s" % (dev, media_state)
			if self.currentlyUpdating is False:
				self.currentlyUpdating = True
				self.setButtons()
				self.updateList()

	def buildHDDList(self, hd, isOfflineStorage = False ):
		divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/div-h.png"))
		devicepng = None
		onlinepng = None
		isOfflineStorageDevice = isOfflineStorage
		isConfiguredStorageDevice = False
		isMountedPartition = False
		currentMountpoint = None
		numpart = 0
		uuid = None
		hdd_description = ""
		device_info = ""

		if isOfflineStorageDevice:
			uuid = hd
			print "[HarddiskDriveSelection] - buildHDDList for offline uuid: ",uuid
			hdd_description = config.storage[uuid]["device_description"].value
			if config.storage[uuid]["enabled"].value == True:
				isConfiguredStorageDevice = True
				currentMountpoint = config.storage[uuid]["mountpoint"].value
			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-unavailable.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green_off.png"))
			device_info +=  config.storage[uuid]["device_info"].value + " " + _("Harddisk")
			if currentMountpoint is not None:
				device_info += " - " + "( " + currentMountpoint + " )"
		else:
			#print "[HarddiskDriveSelection] - buildHDDList for online device: ",hd.device
			hdd_description = hd.model()
			cap = hd.capacity()
			if cap != "":
				hdd_description += " (" + cap + ")"
			numpart = hd.numPartitions()
			if numpart == 1:
				partitionPath = hd.partitionPath(str(numpart))
				uuid = harddiskmanager.getPartitionUUID(hd.device + str(numpart))
				if uuid is not None:
					if config.storage.get(uuid, None) is not None:
						if config.storage[uuid]["enabled"].value == True:
							isConfiguredStorageDevice = True
							p = harddiskmanager.getPartitionbyMountpoint(config.storage[uuid]["mountpoint"].value)
							if p is not None:
								if p.mounted():
									isMountedPartition = True
									currentMountpoint = config.storage[uuid]["mountpoint"].value
			
			devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk.png"))
			onlinepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/button_green.png"))
			device_info +=  hd.bus_description() + " " + _("Harddisk")
			if numpart == 0:
				device_info += " - " + _("Please initialize!")
			
			if numpart == 1 and not isMountedPartition:
				partitionPath = hd.partitionPath(str(numpart))
				if (harddiskmanager.is_hard_mounted(partitionPath)):
					print "[HarddiskDriveSelection] - buildHDDList found possible Fstab mounted device:",partitionPath
					mountpoint = harddiskmanager.get_fstab_mountpoint(partitionPath)
					if mountpoint is not None:
						if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.is_fstab_mountpoint(partitionPath, mountpoint)):
							devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-attention.png"))
							device_info += " - " + _("Needs attention!")
				else:
					partitionPath = "/dev/disk/by-uuid/" + uuid
					mountpoint = config.storage[uuid]["mountpoint"].value
					if mountpoint != "":
						if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.is_fstab_mountpoint(partitionPath, mountpoint) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpoint) == 'auto'):
							devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-attention.png"))
							device_info += " - " + _("Needs attention!")
						else:
							if (harddiskmanager.is_hard_mounted(partitionPath) and harddiskmanager.is_fstab_mountpoint(partitionPath, mountpoint) and harddiskmanager.get_fstab_mountstate(partitionPath, mountpoint) == 'noauto'):
								isMountedPartition = True
								currentMountpoint = config.storage[uuid]["mountpoint"].value	
							else:
								device_info += " - " + _("No mountpoint defined!")
					else:
						device_info += " - " + _("No mountpoint defined!")
			
			if isMountedPartition:
				devicepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/device_harddisk-configured.png"))
				device_info += " - " + currentMountpoint
		return((hdd_description, hd, device_info, numpart, isOfflineStorageDevice, isMountedPartition, currentMountpoint, devicepng, onlinepng, divpng))
		

	def updateList(self):
		self.list = []
		for hd in harddiskmanager.hdd:
			self.list.append(self.buildHDDList(hd, isOfflineStorage = False)) #online devices discovered
		for uuid in config.storage:
			dev = harddiskmanager.getDeviceNamebyUUID(uuid)
			if dev is None:
				self.list.append(self.buildHDDList(uuid, isOfflineStorage = True)) #offline devices
		if not self.list:
			self.list.append((_("no HDD found"), 0, None, None, None, None, None, None, None, None))
		
		self["hddlist"].setList(self.list)
		self["hddlist"].setIndex(self.currentIndex)
		self.currentlyUpdating = False
		if not self.selectionChanged in self["hddlist"].onSelectionChanged:
			self["hddlist"].onSelectionChanged.append(self.selectionChanged)
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
		if config.usage.setup_level.index >= 1:
			if self.list:
				self["key_blue"].setText(_("Settings"))
				self["BlueColorActions"].setEnabled(True)

	def selectionChanged(self):
		#[HarddiskDriveSelection] - current: (0: hdd_description, 1:hd/uuid, 2;device_info, 3:numpart, 4:isOfflineStorageDevice, 5:isMountedPartition, 6:currentMountpoint, devicepng, onlinepng, divpng)
		self.setButtons()
		current = self["hddlist"].getCurrent()
		if current:
			self.currentIndex = self["hddlist"].getIndex()
			if current[3] >= 0 and not current[4]:
				self["key_green"].setText(_("Initialize"))
				self["GreenColorActions"].setEnabled(True)
				self["OkActions"].setEnabled(True)
			if current[3] >= 1 and not current[4]:
				self["key_yellow"].setText(_("Check"))
				self["YellowColorActions"].setEnabled(True)				
			if current[4]:
				self["key_red"].setText(_("Remove"))
				self["RedColorActions"].setEnabled(True)
				
	def okbuttonClick(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - okbuttonClick:",selection[0], selection[2], selection[3]
			self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_INITIALIZE, device = selection[1], partition = selection[3])

	def mainMenuClosed(self, *val):
		if self.currentlyUpdating is False:
			self.currentlyUpdating = True
			self.setButtons()
			self.updateList()

	def keyRed(self):
		selection = self["hddlist"].getCurrent()
		if isinstance(selection[1], (basestring, str)):
			#print "[HarddiskDriveSelection] - keyRed:",selection[0], selection[1]
			self.session.openWithCallback(lambda x : self.keyRedConfirm(x, selection[1]), MessageBox, _("Really delete this harddisk entry?"), MessageBox.TYPE_YESNO, timeout = 20, default = True)

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
		#[HarddiskDriveSelection] - current: (0: hdd_description, 1:hd/uuid, 2;device_info, 3:numpart, 4:isOfflineStorageDevice, 5:isMountedPartition, 6:currentMountpoint, devicepng, onlinepng, divpng)
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			print "[HarddiskDriveSelection] - keyGreen:",selection[0], selection[2], selection[3]
			self.session.openWithCallback(self.mainMenuClosed, HarddiskDriveSetup, HarddiskDriveSetup.HARDDISK_INITIALIZE, device = selection[1], partition = selection[3])

	def keyYellow(self):
		selection = self["hddlist"].getCurrent()
		if selection[1] != 0:
			#print "[HarddiskDriveSelection] - keyYellow:",selection[0], selection[2], selection[3]
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
		x = config.storage.get(self.UUID, None)
		if x is not None and x["mountpoint"].value == "":
			mountpath = "/media/" + str(self.hdd.model(model_only = True))
			if len(config.storage) == 1:
				mountpath = "/media/hdd"
			self.session.openWithCallback(self.createMountdirCB, VirtualKeyBoard, title = (_("Enter mountpoint path.")), text = mountpath)

	def createMountdirCB(self, retval = None):
		if retval is not None:
			self.close(retval)
	def exit(self):
		self.close(False)

