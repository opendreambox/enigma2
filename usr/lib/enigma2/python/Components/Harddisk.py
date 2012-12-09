from os import system, listdir, statvfs, popen, makedirs, stat, major, minor, path, access, readlink, unlink, getcwd, chdir, W_OK
from Tools.Directories import SCOPE_HDD, resolveFilename
from Tools.CList import CList
from SystemInfo import SystemInfo
import time
import re
from Components.Console import Console
from config import config, configfile, ConfigYesNo, ConfigText, ConfigSubDict, ConfigSubsection, ConfigBoolean

def MajorMinor(path):
	rdev = stat(path).st_rdev
	return (major(rdev),minor(rdev))

def readFile(filename):
	file = open(filename)
	data = file.read().strip()
	file.close()
	return data

DEVTYPE_UDEV = 0
DEVTYPE_DEVFS = 1

def forceAutofsUmount(dev):
	try:
		mounts = open("/proc/mounts")
	except IOError:
		return -1

	lines = mounts.readlines()
	mounts.close()

	res = -1
	for line in lines:
		parts = line.strip().split(" ")
		real_path = path.realpath(parts[0])
		if not real_path[-1].isdigit():
			continue
		try:
			if parts[1] == '/autofs/' + dev:
				print "forced", parts[1], "umount!!"
				cmd = "umount /autofs/" + dev + " || /bin/true"
				res = system(cmd)
				break
		except OSError:
			pass
	return (res >> 8)

class Harddisk:
	def __init__(self, device, removable = False):
		self.device = device
		self.isRemovable = removable

		if access("/dev/.udev", 0):
			self.type = DEVTYPE_UDEV
		elif access("/dev/.devfsd", 0):
			self.type = DEVTYPE_DEVFS
		else:
			print "Unable to determine structure of /dev fallback to udev"
			self.type = DEVTYPE_UDEV

		self.is_sleeping = False
		self.max_idle_time = 0
		self.idle_running = False
		self.timer = None

		self.isInitializing = False
		self.isVerifying = False

		self.dev_path = ''
		self.disk_path = ''
		self.phys_path = path.realpath(self.sysfsPath('device'))

		if self.type == DEVTYPE_UDEV:
			self.dev_path = '/dev/' + self.device
			self.disk_path = self.dev_path

		elif self.type == DEVTYPE_DEVFS:
			tmp = readFile(self.sysfsPath('dev')).split(':')
			s_major = int(tmp[0])
			s_minor = int(tmp[1])
			for disc in listdir("/dev/discs"):
				dev_path = path.realpath('/dev/discs/' + disc)
				disk_path = dev_path + '/disc'
				try:
					rdev = stat(disk_path).st_rdev
				except OSError:
					continue
				if s_major == major(rdev) and s_minor == minor(rdev):
					self.dev_path = dev_path
					self.disk_path = disk_path
					break

		print "new Harddisk", self.device, '->', self.dev_path, '->', self.disk_path
		if not self.isRemovable:
			self.startIdle()

	def __lt__(self, ob):
		return self.device < ob.device

	def partitionPath(self, n):
		if self.type == DEVTYPE_UDEV:
			return self.dev_path + n
		elif self.type == DEVTYPE_DEVFS:
			return self.dev_path + '/part' + n

	def sysfsPath(self, filename):
		return path.realpath('/sys/block/' + self.device + '/' + filename)

	def stop(self):
		if self.timer:
			self.timer.stop()
			self.timer.callback.remove(self.runIdle)

	def bus(self):
		# CF (7025 specific)
		if self.type == DEVTYPE_UDEV:
			ide_cf = False	# FIXME
		elif self.type == DEVTYPE_DEVFS:
			ide_cf = self.device[:2] == "hd" and "host0" not in self.dev_path

		internal = "pci" in self.phys_path

		if ide_cf:
			ret = "External (CF)"
		elif internal:
			ret = "Internal"
		else:
			ret = "External"
		return ret

	def bus_type(self):
		# CF (7025 specific)
		if self.type == DEVTYPE_UDEV:
			ide_cf = False	# FIXME
		elif self.type == DEVTYPE_DEVFS:
			ide_cf = self.device[:2] == "hd" and "host0" not in self.dev_path

		sata = "pci" in self.phys_path
		sata_desc = self.bus_description()

		if ide_cf:
			ret = "IDE"
		elif sata:
			if sata_desc is not None:
				ret = sata_desc
			else:
				ret = "SATA"
		else:
			ret = "USB"
		return ret

	def bus_description(self):
		phys = self.phys_path[4:]
		from Tools.HardwareInfo import HardwareInfo
		if self.device.find('sr') == 0 and self.device[2].isdigit():
			devicedb = DEVICEDB_SR
		else:
			devicedb = DEVICEDB

		for physdevprefix, pdescription in devicedb.get(HardwareInfo().device_name,{}).items():
			#print "bus_description:",phys, physdevprefix, pdescription
			if phys.startswith(physdevprefix):
				return pdescription
		if phys.find('pci') != -1:
			return "SATA"
		elif phys.find('usb') != -1:
			return "USB"
		return "External Storage"

	def diskSize(self, sectors = False):
		try:
			line = readFile(self.sysfsPath('size'))
			cap = int(line)
		except:
			return 0;
		if sectors:
			return cap
		return cap / 1000 * 512 / 1000

	def capacity(self):
		cap = self.diskSize()
		if cap == 0:
			return ""
		return "%d.%03d GB" % (cap/1000, cap%1000)

	def model(self, model_only = False, vendor_only = False):
		if self.device[:2] == "hd":
			return readFile('/proc/ide/' + self.device + '/model')
		elif self.device[:2] == "sd":
			try:
				vendor = readFile(self.sysfsPath('device/vendor'))
				model = readFile(self.sysfsPath('device/model'))
			except:
				vendor = ""
				model = ""

			if vendor_only:
				return vendor
			if model_only:
				return model
			return vendor + '-' + model
		else:
			assert False, "no hdX or sdX"

	def free(self):
		try:
			mounts = open("/proc/mounts")
		except IOError:
			return -1

		lines = mounts.readlines()
		mounts.close()

		for line in lines:
			parts = line.strip().split(" ")
			real_path = path.realpath(parts[0])
			if not real_path[-1].isdigit():
				continue
			try:
				if MajorMinor(real_path) == MajorMinor(self.partitionPath(real_path[-1])):
					stat = statvfs(parts[1])
					return stat.f_bfree/1000 * stat.f_bsize/1000
			except OSError:
				pass
		return -1

	def numPartitions(self):
		numPart = -1
		if self.type == DEVTYPE_UDEV:
			try:
				devdir = listdir('/dev')
			except OSError:
				return -1
			for filename in devdir:
				if filename.startswith(self.device):
					numPart += 1

		elif self.type == DEVTYPE_DEVFS:
			try:
				idedir = listdir(self.dev_path)
			except OSError:
				return -1
			for filename in idedir:
				if filename.startswith("disc"):
					numPart += 1
				if filename.startswith("part"):
					numPart += 1
		return numPart

	def unmount(self, numpart = None):
		try:
			mounts = open("/proc/mounts")
		except IOError:
			return -1

		lines = mounts.readlines()
		mounts.close()

		cmd = "umount"
		for line in lines:
			parts = line.strip().split(" ")
			real_path = path.realpath(parts[0])
			if not real_path[-1].isdigit():
				if numpart is not None and numpart == 0:
					if real_path.startswith("/dev/sd"):
						uuid = harddiskmanager.getPartitionUUID(self.device)
						if uuid is not None:
							try:
								if MajorMinor(real_path) == MajorMinor(self.dev_path):
									cmd = ' ' . join([cmd, parts[1]])
									break
							except OSError:
								pass
			try:
				if MajorMinor(real_path) == MajorMinor(self.partitionPath(real_path[-1])):
					cmd = ' ' . join([cmd, parts[1]])
					break
			except OSError:
				pass
		res = system(cmd)
		if cmd == "umount": # nothing found to unmount
			res = 0
		return (res >> 8)

	def createPartition(self):
		cmd = 'printf "8,\n;0,0\n;0,0\n;0,0\ny\n" | sfdisk -f -uS -q ' + self.disk_path
		if harddiskmanager.KernelVersion >= "3.2":
			maxSectorsMBR = int(4294967295) #2TB
			swapPartSize = int(2097152) #1GB
			fstype, sys, size, sizeg, sectors = harddiskmanager.getFdiskInfo(self.device[:3])
			if sectors is None:
				sectors = self.diskSize(sectors = True)
			cmd = 'parted --script --align=min ' + self.disk_path + ' -- mklabel msdos mkpart primary ext3 40s 100%'
			if sectors and not self.isRemovable:
				part1end = int(sectors-swapPartSize) #leaving 1GB for swap
				cmd = 'parted --script --align=min ' + self.disk_path + ' -- mklabel msdos mkpart primary ext3 40s ' + str(part1end) + 's'
				cmd+=  ' mkpart primary linux-swap ' + str(int(part1end+1)) + 's -1s'
				if sectors > maxSectorsMBR:
					cmd = 'parted --script --align=opt -- ' + self.disk_path + ' mklabel gpt mkpart primary ext3 2048s ' + str(part1end) + 's'
					cmd+=  ' mkpart primary linux-swap ' + str(int(part1end+1)) + 's -1'

		res = system(cmd)
		print  "[createPartition]:",res,cmd
		return (res >> 8)

	def mkfs(self, fstype = "ext3", partitionNum = "1"):
		cmd = "mkfs." + fstype + " "
		if self.diskSize() > 4 * 1024:
			cmd += "-T largefile "
		cmd += "-m0 -O dir_index " + self.partitionPath(partitionNum)
		res = system(cmd)
		print "[mkfs]:",res,cmd
		return (res >> 8)

	def mkswap(self, partitionNum = "2"):
		cmd = "mkswap " + self.partitionPath(partitionNum)
		res = system(cmd)
		print "[mkswap]:",cmd,res
		return (res >> 8)

	def activateswap(self, partitionNum = "2"):
		partitionType = harddiskmanager.getBlkidPartitionType(self.partitionPath(partitionNum))
		if partitionType is not None and partitionType == "swap":
			cmd = "swapon " + self.partitionPath(partitionNum)
			system(cmd)

	def deactivateswap(self, partitionNum = "2"):
		partitionType = harddiskmanager.getBlkidPartitionType(self.partitionPath(partitionNum))
		if partitionType is not None and partitionType == "swap":
			cmd = "swapoff " + self.partitionPath(partitionNum)
			print "[deactivate swap]:",cmd
			system(cmd)

	def mount(self):
		try:
			fstab = open("/etc/fstab")
		except IOError:
			return -1

		lines = fstab.readlines()
		fstab.close()

		res = -1
		for line in lines:
			parts = line.strip().split(" ")
			real_path = path.realpath(parts[0])
			if not real_path[-1].isdigit():
				continue
			try:
				if MajorMinor(real_path) == MajorMinor(self.partitionPath(real_path[-1])):

					forceAutofsUmount(self.device+real_path[-1])
					# we must umount autofs first because autofs mounts with "sync" option
					# and the real mount than also mounts with this option
					# this is realy bad for the performance!

					cmd = "mount -t auto " + parts[0]
					res = system(cmd)
					break
			except OSError:
				pass

		return (res >> 8)

	def createMovieFolder(self, isFstabMounted = False):
		if isFstabMounted:
			try:
				makedirs(resolveFilename(SCOPE_HDD))
			except OSError:
				return -1
		else:
			try:
				makedirs("/autofs/" + self.device[:3] + "1/movie")
			except OSError:
				return -1
		return 0

	def fsck(self, numpart):
		# We autocorrect any failures and check if the fs is actually one we can check (currently ext2/ext3)
		partitionPath = self.partitionPath("1")

		# Lets activate the swap partition if exists
		self.activateswap()

		if numpart is not None:
			if numpart == 0:
				partitionPath = self.dev_path
			if numpart >= 1:
				partitionPath = self.partitionPath(str(numpart))

		partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)

		res = -1
		if access(partitionPath, 0):
			if partitionType is not None and partitionType in ("ext2", "ext3"):
				cmd = "fsck." + partitionType + " -f -p -C 0 " + partitionPath
				res = system(cmd)

		# Lets deactivate the swap partition
		self.deactivateswap()

		return (res >> 8)

	def killPartition(self):
		part = self.disk_path
		cmd = 'dd bs=4k count=3 if=/dev/zero of=' + part
		if harddiskmanager.KernelVersion >= "3.2":
			cmd = 'parted --script --align=min -- ' + part + ' mklabel msdos'
		if access(part, 0):
			res = system(cmd)
		else:
			res = 0
		print "[killPartition]",res,cmd
		return (res >> 8)

	errorList = [ _("Everything is fine"), _("Creating partition failed"), _("Mkfs failed"), _("Mount failed"), _("Create movie folder failed"), _("Fsck failed"), _("Please Reboot"), _("Filesystem contains uncorrectable errors"), _("Unmount failed")]

	def initialize(self, isFstabMounted = False, numpart = None):
		if self.unmount(numpart) != 0:
			return -8
		# Udev tries to mount the partition immediately if there is an
		# old filesystem on it when fdisk reloads the partition table.
		# To prevent that, we overwrite the first sectors of the
		# partitions, if the partition existed before. This should work
		# for ext2/ext3 and also for GPT/EFI partitions.
		self.killPartition()

		if self.createPartition() != 0:
			return -1

		if self.mkfs() != 0:
			return -2

		# init the swap partition
		if harddiskmanager.KernelVersion >= "3.2":
			if not self.isRemovable:
				if self.mkswap() != 0:
					return -2
			# Call partprobe to inform the system about the partition table change.
			Console().ePopen(("partprobe", "partprobe", "-s"))

		if isFstabMounted:
			if self.mount() != 0:
				return -3

		if self.createMovieFolder(isFstabMounted) != 0:
			return -4

		return 0

	def check(self, isFstabMounted = False, numpart = None):

		if self.unmount(numpart) != 0:
			return -8

		res = self.fsck(numpart)
		if res & 2 == 2:
			return -6

		if res & 4 == 4:
			return -7

		if res != 0 and res != 1:
			# A sum containing 1 will also include a failure
			return -5

		if isFstabMounted:
			if self.mount() != 0:
				return -3

		return 0

	def getDeviceDir(self):
		return self.dev_path

	def getDeviceName(self):
		return self.disk_path

	# the HDD idle poll daemon.
	# as some harddrives have a buggy standby timer, we are doing this by hand here.
	# first, we disable the hardware timer. then, we check every now and then if
	# any access has been made to the disc. If there has been no access over a specifed time,
	# we set the hdd into standby.
	def readStats(self):
		try:
			l = open("/sys/block/%s/stat" % self.device).read()
		except IOError:
			return -1,-1
		(nr_read, _, _, _, nr_write) = l.split()[:5]
		return int(nr_read), int(nr_write)

	def startIdle(self):
		self.last_access = time.time()
		self.last_stat = 0
		from enigma import eTimer

		# disable HDD standby timer
		if self.bus() == "External":
			Console().ePopen(("sdparm", "sdparm", "--set=SCT=0", self.disk_path))
		else:
			Console().ePopen(("hdparm", "hdparm", "-S0", self.disk_path))
		self.timer = eTimer()
		self.timer.callback.append(self.runIdle)
		self.idle_running = True
		self.setIdleTime(self.max_idle_time) # kick the idle polling loop

	def runIdle(self):
		if not self.max_idle_time:
			return
		t = time.time()

		idle_time = t - self.last_access

		stats = self.readStats()
		print "nr_read", stats[0], "nr_write", stats[1]
		l = sum(stats)
		print "sum", l, "prev_sum", self.last_stat

		if l != self.last_stat and l >= 0: # access
			print "hdd was accessed since previous check!"
			self.last_stat = l
			self.last_access = t
			idle_time = 0
			self.is_sleeping = False
		else:
			print "hdd IDLE!"

		print "[IDLE]", idle_time, self.max_idle_time, self.is_sleeping
		if idle_time >= self.max_idle_time and not self.is_sleeping:
			self.setSleep()

	def setSleep(self):
		if self.bus() == "External":
			Console().ePopen(("sdparm", "sdparm", "--command=stop", self.disk_path))
		else:
			Console().ePopen(("hdparm", "hdparm", "-y", self.disk_path))
		self.is_sleeping = True

	def setIdleTime(self, idle):
		self.max_idle_time = idle
		if self.idle_running:
			if not idle:
				self.timer.stop()
			else:
				self.timer.start(idle * 100, False)  # poll 10 times per period.

	def isSleeping(self):
		return self.is_sleeping

	def isIdle(self):
		return self.idle_running

class Partition:
	def __init__(self, mountpoint, device = None, description = "", force_mounted = False):
		self.mountpoint = mountpoint
		self.description = description
		self.force_mounted = force_mounted
		self.is_hotplug = force_mounted # so far; this might change.
		self.device = device
		self.disc_path = None
		self.uuid = None
		self.isMountable = False
		self.isReadable = False
		self.isWriteable = False
		self.isInitialized = False
		self.fsType = None
		if self.device is not None:
			self.updatePartitionInfo()

	def updatePartitionInfo(self, dstpath = "", dev = None ):
		curdir = getcwd()
		testpath = ""
		if dstpath != "" and dev is not None:
			self.device = dev
			testpath = dstpath + self.device

		if self.device is not None:
			if testpath == "":
				testpath = "/autofs/" + self.device
			self.uuid = harddiskmanager.getPartitionUUID(self.device)
			try:
				chdir(testpath)
				self.isMountable = True
			except OSError:
				pass
			if self.isMountable:
				try:
					listdir(testpath)
					self.isReadable = True
				except OSError:
					pass
			if self.uuid is not None:
				if self.fsType is None:
					self.fsType = harddiskmanager.getBlkidPartitionType("/dev/" + self.device)
			if self.isReadable:
				mountpoint, fsType, mountopt = harddiskmanager.getMountInfo("/dev/" + self.device)
				if self.fsType is None and fsType is not None:
					self.fsType = fsType
				if mountopt is not None and mountopt == 'rw':
					self.isWriteable = True
					if not access(testpath, W_OK):
						self.isWriteable = False
			if self.isWriteable:
				if access(testpath + "/movie", W_OK):
					self.isInitialized = True
		else:
			self.uuid = None
			self.isMountable = False
			self.isReadable = False
			self.isWriteable = False
			self.isInitialized = False
			self.fsType = None
		chdir(curdir)

	def stat(self):
		return statvfs(self.mountpoint)

	def free(self):
		try:
			s = self.stat()
			return s.f_bavail * s.f_bsize
		except OSError:
			return None

	def total(self):
		try:
			s = self.stat()
			return s.f_blocks * s.f_bsize
		except OSError:
			return None

	def mounted(self):
		# THANK YOU PYTHON FOR STRIPPING AWAY f_fsid.
		# TODO: can os.path.ismount be used?
		if self.force_mounted:
			return True
		try:
			mounts = open("/proc/mounts")
		except IOError:
			return False

		lines = mounts.readlines()
		mounts.close()

		for line in lines:
			if line.split(' ')[1] == self.mountpoint:
				return True
		return False


DEVICEDB_SR = \
	{"dm8000":
		{
			"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("DVD Drive"),
			"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("DVD Drive"),
			"/devices/platform/brcm-ehci-1.1/usb2/2-1/2-1:1.0/host3/target3:0:0/3:0:0:0": _("DVD Drive"),
		},
	"dm800":
	{
	},
	"dm7025":
	{
	}
	}

DEVICEDB = \
	{"dm8000":
		{
			"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("SATA"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.1/1-1.1:1.0": _("Front USB"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.1/1-1.1.": _("Front USB"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.2/1-1.2:1.0": _("Back, upper USB"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.2/1-1.2.": _("Back, upper USB"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.3/1-1.3:1.0": _("Back, lower USB"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.3/1-1.3.": _("Back, lower USB"),
			"/devices/platform/brcm-ehci-1.1/usb2/2-1/2-1:1.0/": _("Internal USB"),
			"/devices/platform/brcm-ohci-1.1/usb4/4-1/4-1:1.0/": _("Internal USB"),
			"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.4/1-1.4.": _("Internal USB"),
		},
	"dm7020hd":
	{
		"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("SATA"),
		"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("eSATA"),
		"/devices/platform/brcm-ehci-1.1/usb2/2-1/2-1:1.0": _("Front USB"),
		"/devices/platform/brcm-ehci-1.1/usb2/2-1/2-1.": _("Front USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-2/1-2:1.0": _("Back, upper USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-2/1-2.": _("Back, upper USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-1/1-1:1.0": _("Back, lower USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-1/1-1.": _("Back, lower USB"),
	},
	"dm800":
	{
		"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("SATA"),
		"/devices/platform/brcm-ehci.0/usb1/1-2/1-2:1.0": _("Upper USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-1/1-1:1.0": _("Lower USB"),
	},
	"dm800se":
	{
		"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("SATA"),
		"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("eSATA"),
		"/devices/platform/brcm-ehci.0/usb1/1-2/1-2:1.0": _("Upper USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-1/1-1:1.0": _("Lower USB"),
	},
	"dm500hd":
	{
		"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("eSATA"),
		"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("eSATA"),
	},
	"dm800sev2":
	{
		"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("SATA"),
		"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("eSATA"),
		"/devices/platform/brcm-ehci.0/usb1/1-2/1-2:1.0": _("Upper USB"),
		"/devices/platform/brcm-ehci.0/usb1/1-1/1-1:1.0": _("Lower USB"),
	},
	"dm500hdv2":
	{
		"/devices/pci0000:01/0000:01:00.0/host1/target1:0:0/1:0:0:0": _("eSATA"),
		"/devices/pci0000:01/0000:01:00.0/host0/target0:0:0/0:0:0:0": _("eSATA"),
	},
	"dm7025":
	{
		"/devices/pci0000:00/0000:00:14.1/ide1/1.0": "Compact Flash", #hdc
		"/devices/pci0000:00/0000:00:14.1/ide0/0.0": "Internal Harddisk"
	}
	}


class HarddiskManager:
	EVENT_MOUNT = "mount"
	EVENT_UNMOUNT = "unmount"

	def __init__(self):

		config.storage_options = ConfigSubsection()
		config.storage_options.default_device = ConfigText(default = "<undefined>")
		config.storage = ConfigSubDict()
		self.hdd = [ ]
		self.cd = ""
		self.partitions = [ ]
		self.devices_scanned_on_init = [ ]
		self.delayed_device_Notifier = [ ]
		self.onUnMount_Notifier = [ ]

		self.on_partition_list_change = CList()
		self.KernelVersion = self.getKernelVersion()

		# currently, this is just an enumeration of what's possible,
		# this probably has to be changed to support automount stuff.
		# still, if stuff is mounted into the correct mountpoints by
		# external tools, everything is fine (until somebody inserts
		# a second usb stick.)
		p = [
					("/media/hdd", _("Hard disk")),
					("/media/card", _("Card")),
					("/media/cf", _("Compact Flash")),
					("/media/mmc1", _("SD/MMC")),
					("/media/net", _("Network Mount")),
					("/media/ram", _("Ram Disk")),
					("/media/usb", _("USB Stick")),
					("/", _("Internal Flash"))
				]
		self.partitions.extend([ Partition(mountpoint = x[0], description = x[1]) for x in p ])

	def getKernelVersion(self):
		version = "3.2"
		try:
			cmd = "uname -sr"
			for line in popen(cmd).read().split('\n'):
				if line.find("Linux 3.2") == 0:
					version = "3.2"
				if line.find("Linux 2.6.18") == 0:
					version = "2.6.18"
				if line.find("Linux 2.6.12") == 0:
					version = "2.6.12"
		except:
			print "error getting kernel version"
		return version

	def getBlockDevInfo(self, blockdev):
		devpath = "/sys/block/" + blockdev
		error = False
		removable = False
		blacklisted = False
		is_cdrom = False
		partitions = []
		try:
			removable = bool(int(readFile(devpath + "/removable")))
			dev = int(readFile(devpath + "/dev").split(':')[0])
			if dev in (1, 7, 31): # ram, loop, mtdblock
				blacklisted = True
			if blockdev[0:2] == 'sr':
				is_cdrom = True
			if blockdev[0:2] == 'hd':
				try:
					media = readFile("/proc/ide/%s/media" % blockdev)
					if "cdrom" in media:
						is_cdrom = True
				except IOError:
					error = True
			# check for partitions
			if not is_cdrom:
				for partition in listdir(devpath):
					if partition[0:len(blockdev)] != blockdev:
						continue
					partitions.append(partition)
			else:
				self.cd = blockdev
		except IOError:
			error = True
		# check for medium
		medium_found = True
		try:
			open("/dev/" + blockdev).close()
		except IOError, err:
			if err.errno == 159: # no medium present
				medium_found = False
		return error, blacklisted, removable, is_cdrom, partitions, medium_found

	def enumerateBlockDevices(self):
		self.setupConfigEntries(initial_call = True)
		print "enumerating block devices..."
		for blockdev in listdir("/sys/block"):
			error, blacklisted, removable, is_cdrom, partitions, medium_found = self.addHotplugPartition(blockdev)
			if not error and not blacklisted:
				if medium_found:
					for part in partitions:
						self.addHotplugPartition(part)
				self.devices_scanned_on_init.append((blockdev, removable, is_cdrom, medium_found))
				print "[enumerateBlockDevices] devices_scanned_on_init:",self.devices_scanned_on_init

	def getAutofsMountpoint(self, device):
		return "/autofs/%s/" % (device)

	def is_hard_mounted(self, device):
		mounts = file('/proc/mounts').read().split('\n')
		for x in mounts:
			if x.find('/autofs') == -1 and x.find(device) != -1:
				#print "is_hard_mounted:",device
				return True
		return False

	def get_mountdevice(self, mountpoint):
		mounts = file('/proc/mounts').read().split('\n')
		for x in mounts:
			if not x.startswith('/'):
				continue
			device, mp = x.split()[0:2]
			if mp == mountpoint:
				#print "get_mountdevice for '%s' -> %s " % (device, mp)
				return device
		return None

	def get_mountpoint(self, mountpath):
		mounts = file('/proc/mounts').read().split('\n')
		for x in mounts:
			if not x.startswith('/'):
				continue
			path, mp = x.split()[0:2]
			if path == mountpath:
				#print "get_mountpoint for '%s' -> %s " % (path, mp)
				return mp
		return None

	def is_uuidpath_mounted(self, uuidpath, mountpoint):
		mounts = file('/proc/mounts').read().split('\n')
		for x in mounts:
			if not x.startswith('/'):
				continue
			path, mp = x.split()[0:2]
			if (path == uuidpath and mp == mountpoint):
				#print "is_uuid_mounted:'%s' for: %s " % (path, mp)
				return True
		return False

	def is_fstab_mountpoint(self, device, mountpoint):
		mounts = file('/etc/fstab').read().split('\n')
		for x in mounts:
			if not x.startswith('/'):
				continue
			dev, mp = x.split()[0:2]
			if (dev == device and mp == mountpoint):
				#print "is_fstab_mountpoint:'%s' for: %s " % (mp, dev)
				return True
		return False

	def get_fstab_mountstate(self, device, mountpoint):
		mounts = file('/etc/fstab').read().split('\n')
		for x in mounts:
			if not x.startswith('/'):
				continue
			dev, mp, ms = x.split()[0:3]
			if (dev == device and mp == mountpoint):
				#print "got_fstab_mountstate:'%s' for: %s - %s" % (ms, dev, mp)
				return ms
		return False

	def get_fstab_mountpoint(self, device):
		mounts = file('/etc/fstab').read().split('\n')
		for x in mounts:
			if not x.startswith('/'):
				continue
			dev, mp = x.split()[0:2]
			if device == dev:
				#print "got_fstab_mountpoint:'%s' for: %s" % (mp, dev)
				return mp
		return None

	def modifyFstabEntry(self, partitionPath, mountpoint, mode = "add_deactivated"):
		try:
			alreadyAdded = self.is_fstab_mountpoint(partitionPath, mountpoint)
			oldLine = None
			mounts = file('/etc/fstab').read().split('\n')
			fp = file("/etc/fstab", 'w')
			fp.write("#automatically edited by enigma2, " + str(time.strftime( "%a" + ", " + "%d " + "%b" + " %Y %H:%M:%S", time.localtime(time.time() ))) + "\n")
			for x in mounts:
				if (x.startswith(partitionPath) and mountpoint in x):
					oldLine = x
					continue
				if len(x):
					if x.startswith('#automatically'):
						continue
					fp.write(x + "\n")
			if not alreadyAdded:
				if mode == "add_deactivated":
					print "modifyFstabEntry - add_deactivated:", partitionPath, mountpoint
					fp.write(partitionPath + "\t" + mountpoint + "\tnoauto\tdefaults\t0 0\n")
				elif mode == "add_activated":
					print "modifyFstabEntry - add_activated:", partitionPath, mountpoint
					fp.write(partitionPath + "\t" + mountpoint + "\tauto\tdefaults\t0 0\n")
			else:
				if mode == "add_deactivated":
					if oldLine is not None:
						if "noauto" in oldLine:
							fp.write(oldLine + "\n")
						else:
							fp.write(oldLine.replace("auto","noauto") + "\n")
				elif mode == "add_activated":
					if oldLine is not None:
						if "noauto" in oldLine:
							fp.write(oldLine.replace("noauto","auto") + "\n")
						else:
							fp.write(oldLine + "\n")
				elif mode == "remove":
					if oldLine is not None:
						pass
			fp.close()
		except:
			print "error adding fstab entry for: %s" % (partitionPath)

	def addHotplugPartition(self, device, physdev = None):
		if not physdev:
			dev, part = self.splitDeviceName(device)
			try:
				physdev = path.realpath('/sys/block/' + dev + '/device')[4:]
			except OSError:
				physdev = dev
				print "couldn't determine blockdev physdev for device", device

		error, blacklisted, removable, is_cdrom, partitions, medium_found = self.getBlockDevInfo(device)
		print "found block device '%s':" % device,

		if blacklisted:
			print "blacklisted"
		else:
			if error:
				print "error querying properties"
			elif not medium_found:
				print "no medium"
			else:
				print "ok, removable=%s, cdrom=%s, partitions=%s" % (removable, is_cdrom, partitions)

			l = len(device)
			if l:
				# see if this is a harddrive or removable drive (usb stick/cf/sd)
				if not device[l-1].isdigit() and not is_cdrom:
					if self.getHDD(device) is None and medium_found:
						if removable:
							self.hdd.append(Harddisk(device, True))
						else:
							self.hdd.append(Harddisk(device, False))
					self.hdd.sort()
					SystemInfo["Harddisk"] = len(self.hdd) > 0
				if (not removable or medium_found):
					self.addDevicePartition(device, physdev)

		return error, blacklisted, removable, is_cdrom, partitions, medium_found

	def removeHotplugPartition(self, device):
		mountpoint = self.getAutofsMountpoint(device)
		uuid = self.getPartitionUUID(device)
		print "[removeHotplugPartition] for device:'%s' uuid:'%s' and mountpoint:'%s'" % (device, uuid, mountpoint)

		# we must umount autofs first because autofs mounts with "sync" option
		# and the real mount than also mounts with this option
		# this is realy bad for the performance!
		forceAutofsUmount(device)

		p = self.getPartitionbyDevice(device)
		if p is None:
			p = self.getPartitionbyMountpoint(mountpoint)
		if p is not None:
			if uuid is None and p.uuid is not None:
				print "[removeHotplugPartition] we got uuid:'%s' but have:'%s'" % (uuid,p.uuid)
				uuid = p.uuid
				self.unmountPartitionbyMountpoint(p.mountpoint)
			if uuid is not None and config.storage.get(uuid, None) is not None:
				self.unmountPartitionbyUUID(uuid)
				if not config.storage[uuid]['enabled'].value:
					del config.storage[uuid]
					config.storage.save()
					config.save()
					print "[removeHotplugPartition] - remove uuid %s from temporary drive add" % (uuid)
			if p.mountpoint != "/media/hdd":
				self.partitions.remove(p)
				self.on_partition_list_change("remove", p)

		l = len(device)
		if l and not device[l-1].isdigit():
			for hdd in self.hdd:
				if hdd.device == device:
					hdd.stop()
					self.hdd.remove(hdd)
					break
			SystemInfo["Harddisk"] = len(self.hdd) > 0

			#call the notifier only after we have fully removed the disconnected drive
			for callback in self.delayed_device_Notifier:
				try:
					callback(device, "remove_delayed" )
				except AttributeError:
					self.delayed_device_Notifier.remove(callback)

	def addDevicePartition(self, device, physdev):
		# device is the device name, without /dev
		# physdev is the physical device path, which we (might) use to determine the userfriendly name
		description = self.getUserfriendlyDeviceName(device, physdev)
		device_mountpoint = self.getAutofsMountpoint(device)
		uuid = self.getPartitionUUID(device)
		print "[addDevicePartition] device:'%s' with UUID:'%s'" % (device, uuid)
		if config.storage.get(uuid, None) is not None:
			if config.storage[uuid]['enabled'].value and config.storage[uuid]['mountpoint'].value != "":
				device_mountpoint = config.storage[uuid]['mountpoint'].value

		if uuid is not None:
			if config.storage.get(uuid, None) is None:
				tmp = self.getPartitionbyDevice(device)
				if tmp is not None:
					if uuid != tmp.uuid and tmp.uuid == config.storage_options.default_device.value and tmp.mountpoint == "/media/hdd": #default hdd re/initialize
						tmp.device = None
						tmp.updatePartitionInfo()
				self.setupConfigEntries(initial_call = False, dev = device)
			else:
				tmp = self.getPartitionbyMountpoint(device_mountpoint)
				if tmp is not None and (tmp.uuid != uuid or tmp.mountpoint != device_mountpoint):
					self.storageDeviceChanged(uuid)

		p = self.getPartitionbyMountpoint(device_mountpoint)
		if p is not None:
			if uuid is not None:
				if p.uuid is not None and p.uuid != uuid:
					if config.storage.get(p.uuid, None) is not None:
						del config.storage[p.uuid] #delete old uuid reference entries
						config.storage.save()
						config.save()
			p.updatePartitionInfo()
		else:
			forced = True
			if uuid is not None:
				cfg_uuid = config.storage.get(uuid, None)
				if cfg_uuid is not None:
					if cfg_uuid['enabled'].value:
						forced = False
					else:
						device_mountpoint = self.getAutofsMountpoint(device)
			x = self.getPartitionbyDevice(device)
			if x is None:
				p = Partition(mountpoint = device_mountpoint, description = description, force_mounted = forced, device = device)
				self.partitions.append(p)
				self.on_partition_list_change("add", p)
			else:	# found old partition entry
				if config.storage.get(x.uuid, None) is not None:
					del config.storage[x.uuid] #delete old uuid reference entries
					config.storage.save()
					config.save()
				x.mountpoint = device_mountpoint
				x.force_mounted = True
				x.updatePartitionInfo()

		for callback in self.delayed_device_Notifier:
			try:
				callback(device, "add_delayed" )
			except AttributeError:
				self.delayed_device_Notifier.remove(callback)

	def HDDCount(self):
		return len(self.hdd)

	def HDDList(self):
		list = [ ]
		for hd in self.hdd:
			hdd = hd.model() + " - " + hd.bus()
			cap = hd.capacity()
			if cap != "":
				hdd += " (" + cap + ")"
			list.append((hdd, hd))
		return list

	def HDDEnabledCount(self):
		cnt = 0
		for uuid, cfg in config.storage.items():
			#print "uuid", uuid, "cfg", cfg
			if cfg["enabled"].value:
				cnt += 1
		return cnt

	def getHDD(self, part):
		for hdd in self.hdd:
			if hdd.device == part[:3]:
				return hdd
		return None

	def getCD(self):
		return self.cd

	def getMountInfo(self, device):
		dev = mountpoint = fstype = mountopt = None
		try:
			mounts = file('/proc/mounts').read().split('\n')
			for x in mounts:
				if not x.startswith('/'):
					continue
				if x.startswith(device):
					data = x.split(',')
					dev, mountpoint, fstype, mountopt = data[0].split(None,4)
		except:
			print "error getting mount info"
		#print "getMountInfo:",mountpoint, fstype, mountopt
		return mountpoint, fstype, mountopt

	def getFdiskInfo(self, devname):
		size = sizeg = fstype = sys = sectors = None
		cmd = "fdisk -l /dev/" + devname
		try:
			for line in popen(cmd).read().split('\n'):
				if line.startswith("Found valid GPT"):
					sys = "GPT"
				if line.startswith("Disk"):
					sizeobj = re.search(r', ((?:[a-zA-Z0-9])*) bytes', line)
					if sizeobj:
						size = sizeobj.group(1)
					sizegobj = re.search(r': ((?:[0-9.0-9])*) GB', line)
					if sizegobj:
						sizeg = sizegobj.group(1)
					sectorsobj = re.search(r': ((?:[0-9.0-9])*) sectors', line)
					if sectorsobj:
						sectors = sectorsobj.group(1)
				if not line.startswith('/'):
					continue
				if line.startswith("/dev/" + devname):
					a,b,c,d, fstype, sys = line.split(None,5)
		except:
			print "error getting fdisk device info"
		#print "getFdiskInfo:",devname, fstype, sys, size, sizeg, sectors
		return fstype, sys, size, sizeg, sectors

	def getBlkidPartitionType(self, device):
		#print "getBlkidPartitionType",device
		fstype = None
		cmd = "blkid " + str(device)
		try:
			for line in popen(cmd).read().split('\n'):
				if not line.startswith(device):
					continue
				fstobj = re.search(r' TYPE="((?:[^"\\]|\\.)*)"', line)
				if fstobj:
					fstype = fstobj.group(1)
		except:
			print "error getting blkid partition type"

		#print "getBlkidPartitionType:",device, fstype
		return fstype

	def getLinkPath(self,link):
		if path.islink(link):
			p = path.normpath(readlink(link))
			if path.isabs(p):
				return p
			return path.join(path.dirname(link), p)

	def getRealPath(self, dstpath):
		p = self.getLinkPath(dstpath)
		if p:
			return p
		return path.realpath(dstpath)

	def isMount(self, mountdir):
		return path.ismount( self.getRealPath(mountdir) )

	def _inside_mountpoint(self, filename):
		#print "is mount? '%s'" % filename
		if filename == "":
			return False
		if filename == "/":
			return False
		if path.ismount(filename):
			return True
		return self._inside_mountpoint("/".join(filename.split("/")[:-1]))

	def inside_mountpoint(self,filename):
		return self._inside_mountpoint(path.realpath(filename))

	def isUUIDpathFsTabMount(self, uuid, mountpath):
		uuidpartitionPath = "/dev/disk/by-uuid/" + uuid
		if self.is_hard_mounted(uuidpartitionPath) and self.is_fstab_mountpoint(uuidpartitionPath, mountpath):
			if self.get_fstab_mountstate(uuidpartitionPath, mountpath) == 'auto':
				return True
		return False

	def isPartitionpathFsTabMount(self, uuid, mountpath):
		dev = self.getDeviceNamebyUUID(uuid)
		if dev is not None:
			partitionPath = "/dev/" + str(dev)
			if self.is_hard_mounted(partitionPath) and self.is_fstab_mountpoint(partitionPath, mountpath):
				if self.get_fstab_mountstate(partitionPath, mountpath) == 'auto':
					return True
		return False

	def getPartitionVars(self, hd, partitionNum = False):
		#print "getPartitionVars for hdd:'%s' and partitionNum:'%s'" % (hd.device, partitionNum)
		hdd = hd
		numPartitions = hdd.numPartitions()
		uuid = partitionPath = uuidPath = deviceName = None
		if partitionNum is False:
			if numPartitions == 0:
				deviceName = hdd.device
				uuid = self.getPartitionUUID(deviceName)
				partitionPath = hdd.dev_path
			if numPartitions == 1:
				deviceName = hdd.device + str(numPartitions)
				uuid = self.getPartitionUUID(deviceName)
				partitionPath = hdd.partitionPath(str(numPartitions))
			else: #just in case, we should never get here
				deviceName = hdd.device
				partitionPath = hdd.dev_path
		else:
			deviceName = hdd.device + str(partitionNum)
			uuid = self.getPartitionUUID(deviceName)
			partitionPath = hdd.partitionPath(str(partitionNum))
		if uuid is not None:
			uuidPath = "/dev/disk/by-uuid/" + uuid
		return deviceName, uuid, numPartitions, partitionNum, uuidPath, partitionPath

	def cleanupMountpath(self, devname):
		return devname.strip().replace(' ','').replace('-','').replace('_','').replace('.','')

	def suggestDeviceMountpath(self,uuid):
		p = self.getPartitionbyUUID(uuid)
		if p is not None:
			hdd = self.getHDD(p.device)
			if hdd is not None:
				val = self.cleanupMountpath(str(hdd.model(model_only = True)))
				cnt = 0
				for dev in self.hdd:
					tmpval = self.cleanupMountpath(str(dev.model(model_only = True)))
					if tmpval == val:
						cnt +=1
				if cnt <=1:
					cnt = 0
					for uid in config.storage.keys():
						if uid == uuid:
							cnt += 1
							continue
						data = config.storage[uid]["device_description"].value.split(None,1)
						tmpval = self.cleanupMountpath(data[0])
						if tmpval == val or tmpval.endswith(val):
							cnt += 1
				if cnt >= 2:
					val += "HDD" + str(cnt)
				partNum = p.device[3:]
				if hdd.numPartitions() == 2 and partNum == "1":
					part2Type = self.getBlkidPartitionType(hdd.partitionPath("2"))
					if part2Type is not None and part2Type != "swap":
						val += "Part" + str(partNum)
				else:
					if str(partNum).isdigit():
						val += "Part" + str(partNum)
				print "suggestDeviceMountpath for uuid: '%s' -> '%s'" %(uuid,val)
				return "/media/" + val
		else:
			mountpath = ""
			uuid_cfg = config.storage.get(uuid, None)
			if uuid_cfg is not None:
				if uuid_cfg["mountpoint"].value != "" and uuid_cfg["mountpoint"].value != "/media/hdd":
					mountpath = uuid_cfg["mountpoint"].value
				else:
					if uuid_cfg["device_description"].value != "":
						tmp = uuid_cfg["device_description"].value.split(None,1)
						mountpath = "/media/" + self.cleanupMountpath(tmp[0])
			if mountpath != "":
				cnt = 0
				for uid in config.storage.keys():
					if config.storage[uid]["mountpoint"].value != "" and config.storage[uid]["mountpoint"].value != "/media/hdd":
						tmp = config.storage[uid]["mountpoint"].value
					else:
						data = config.storage[uid]["device_description"].value.split(None,1)
						mountpath = "/media/" + self.cleanupMountpath(data[0])
					if tmp == mountpath:
						cnt += 1
				if cnt >= 2:
					mountpath += "HDD" + str(cnt)
				return mountpath
		return ""

	def changeStorageDevice(self, uuid = None, action = None , mountData = None ):
		# mountData should be [oldenable,oldmountpath, newenable,newmountpath]
		print "[changeStorageDevice] uuid:'%s' - action:'%s' - mountData:'%s'" %(uuid, action, mountData)
		currentDefaultStorageUUID = config.storage_options.default_device.value
		print "[changeStorageDevice]: currentDefaultStorageUUID:",currentDefaultStorageUUID
		successfully = False
		def_mp = "/media/hdd"
		cur_default_newmp = new_default_newmp = old_cur_default_mp = old_new_default_mp = ""
		cur_default = new_default = None
		cur_default_dev = new_default_dev = None
		cur_default_cfg = new_default_cfg = None
		old_cur_default_enabled = old_new_default_enabled = False

		if action == "mount_default":
			if currentDefaultStorageUUID != "<undefined>" and currentDefaultStorageUUID != uuid:
				cur_default = self.getDefaultStorageDevicebyUUID(currentDefaultStorageUUID)
			new_default = self.getPartitionbyUUID(uuid)
			if cur_default is not None:
				cur_default_cfg = config.storage.get(currentDefaultStorageUUID, None)
			new_default_cfg = config.storage.get(uuid, None)
			if new_default is not None:
				new_default_dev = new_default.device
				if currentDefaultStorageUUID != "<undefined>" and currentDefaultStorageUUID != uuid:
					cur_default_newmp = self.suggestDeviceMountpath(currentDefaultStorageUUID)
				if cur_default is not None:
					cur_default_dev = cur_default.device
				if new_default_cfg is not None:
					old_new_default_enabled = new_default_cfg["enabled"].value
					old_new_default_mp = new_default_cfg["mountpoint"].value
					#[oldmountpath, oldenable, newmountpath, newenable]
					if mountData is not None and isinstance(mountData, (list, tuple)):
						old_new_default_enabled = mountData[1]
						old_new_default_mp = mountData[0]
					if cur_default_cfg is not None and path.exists(def_mp) and self.isMount(def_mp) and cur_default_cfg["enabled"].value and cur_default_cfg["mountpoint"].value == def_mp:
						old_cur_default_enabled = cur_default_cfg["enabled"].value
						old_cur_default_mp = cur_default_cfg["mountpoint"].value
						self.unmountPartitionbyMountpoint(def_mp)
					if not path.exists(def_mp) or (path.exists(def_mp) and not self.isMount(def_mp)) or not self.isPartitionpathFsTabMount(uuid, def_mp):
						if cur_default_cfg is not None:
							cur_default_cfg["mountpoint"].value = cur_default_newmp
						if cur_default_dev is not None:
							self.setupConfigEntries(initial_call = False, dev = cur_default_dev)
						if cur_default_dev is None or (path.exists(cur_default_newmp) and self.isMount(cur_default_newmp)):
							if new_default_cfg["enabled"].value and path.exists(new_default_cfg["mountpoint"].value) and self.isMount(new_default_cfg["mountpoint"].value):
								self.unmountPartitionbyMountpoint(new_default_cfg["mountpoint"].value, new_default_dev )
							if not new_default_cfg["enabled"].value or not self.isMount(new_default_cfg["mountpoint"].value):
								new_default_cfg["mountpoint"].value = def_mp
								new_default_cfg["enabled"].value = True
								self.storageDeviceChanged(uuid)
								new_default = self.getPartitionbyMountpoint(def_mp)
								if cur_default_cfg is None and cur_default_newmp is not "": #currentdefault was offline
									cur_default_cfg = config.storage.get(currentDefaultStorageUUID, None)
								if cur_default_cfg is not None:
									old_cur_default_enabled = cur_default_cfg["enabled"].value
									old_cur_default_mp = cur_default_cfg["mountpoint"].value
									cur_default_cfg["mountpoint"].value = cur_default_newmp
								if new_default is not None and new_default_cfg["mountpoint"].value == def_mp and path.exists(def_mp) and self.isMount(def_mp) and new_default.mountpoint == def_mp:
									successfully = True
									config.storage_options.default_device.value = uuid
									if new_default_cfg is not None:
										new_default_cfg.save()
									if cur_default_cfg is not None:
										cur_default_cfg.save()
		if action == "mount_only":
			new_default = self.getPartitionbyUUID(uuid)
			new_default_cfg = config.storage.get(uuid, None)
			if new_default is not None:
				new_default_dev = new_default.device
				new_default_newmp = self.suggestDeviceMountpath(uuid)
				if new_default_cfg is not None:
					old_new_default_enabled = new_default_cfg["enabled"].value
					old_new_default_mp = new_default_cfg["mountpoint"].value
					#[oldmountpath, oldenable, newmountpath, newenable]
					if mountData is not None and isinstance(mountData, (list, tuple)):
						old_new_default_enabled = mountData[1]
						old_new_default_mp = mountData[0]
						new_default_newmp = mountData[2]
					if old_new_default_enabled and path.exists(def_mp) and self.isMount(def_mp) and old_new_default_mp == def_mp:
						if uuid == currentDefaultStorageUUID:
							self.unmountPartitionbyMountpoint(def_mp) #current partition is default, unmount!
					if old_new_default_enabled and old_new_default_mp != "" and old_new_default_mp != def_mp and path.exists(old_new_default_mp) and self.isMount(old_new_default_mp):
						self.unmountPartitionbyMountpoint(old_new_default_mp, new_default_dev) #current partition is already mounted atm. unmount!
					if not new_default_cfg["enabled"].value or old_new_default_mp == "" or (new_default_cfg["enabled"].value and path.exists(old_new_default_mp) and not self.isMount(old_new_default_mp)):
						new_default_cfg["enabled"].value = True
						new_default_cfg["mountpoint"].value = new_default_newmp
						if path.exists(new_default_newmp) and self.isMount(new_default_newmp):
							tmppath = self.get_mountdevice(new_default_newmp)
							if tmppath is not None and tmppath == "/dev/disk/by-uuid/" + uuid:
								self.unmountPartitionbyMountpoint(new_default_newmp)
						x = None
						if new_default_dev is not None:
							x = self.getPartitionbyDevice(new_default_dev)
						if x is None:
							self.setupConfigEntries(initial_call = False, dev = new_default_dev)
						else:
							self.storageDeviceChanged(uuid)
						new_default = self.getPartitionbyUUID(uuid)
						if new_default is not None and path.exists(new_default_newmp) and self.isMount(new_default_newmp):
							successfully = True
							if uuid == currentDefaultStorageUUID:
								config.storage_options.default_device.value = "<undefined>"
							new_default_cfg.save()
		if action == "unmount":
			new_default = self.getPartitionbyUUID(uuid)
			new_default_cfg = config.storage.get(uuid, None)
			if new_default is not None:
				new_default_dev = new_default.device
				if new_default_cfg is not None and new_default_cfg["mountpoint"].value == new_default.mountpoint:
					old_new_default_mp = new_default_cfg["mountpoint"].value
					old_new_default_enabled = new_default_cfg["enabled"].value
					#[oldmountpath, oldenable, newmountpath, newenable]
					if mountData is not None and isinstance(mountData, (list, tuple)):
						old_new_default_enabled = mountData[1]
						old_new_default_mp = mountData[0]
				if new_default_cfg is not None and path.exists(old_new_default_mp) and self.isMount(old_new_default_mp):
					if uuid == currentDefaultStorageUUID:
						self.unmountPartitionbyMountpoint(old_new_default_mp)
					else:
						self.unmountPartitionbyMountpoint(old_new_default_mp, new_default_dev)
				if path.exists(old_new_default_mp) and not self.isMount(old_new_default_mp):
					new_default_cfg["mountpoint"].value = ""
					new_default_cfg["enabled"].value = False
					self.setupConfigEntries(initial_call = False, dev = new_default_dev)
					if path.exists(old_new_default_mp) and not self.isMount(old_new_default_mp):
						successfully = True
						new_default_cfg.save()
						if uuid == currentDefaultStorageUUID:
							config.storage_options.default_device.value = "<undefined>"
		if not successfully:
			print "<< not successfully >>"
			if cur_default_cfg is not None:
				cur_default_cfg["mountpoint"].value = old_cur_default_mp
				cur_default_cfg["enabled"].value = old_cur_default_enabled
				cur_default_cfg.save()
				if currentDefaultStorageUUID != "<undefined>":
					self.storageDeviceChanged(currentDefaultStorageUUID)
			if new_default_cfg is not None:
				new_default_cfg["mountpoint"].value = old_new_default_mp
				new_default_cfg["enabled"].value = old_new_default_enabled
				new_default_cfg.save()
				self.storageDeviceChanged(uuid)
		config.storage_options.default_device.save()
		config.storage_options.save()
		config.storage.save()
		config.save()
		configfile.save()
		print "changeStorageDevice default is now:",config.storage_options.default_device.value
		return successfully

	def isConfiguredStorageDevice(self,uuid):
		cfg_uuid = config.storage.get(uuid, None)
		if cfg_uuid is not None and cfg_uuid["enabled"].value:
			#print "isConfiguredStorageDevice:",uuid
			return True
		return False

	def isDefaultStorageDeviceActivebyUUID(self, uuid):
		p = self.getDefaultStorageDevicebyUUID(uuid)
		if p is not None and p.uuid == uuid:
			#print "isDefaultStorageDeviceActivebyUUID--for UUID:->",uuid,p.description, p.device, p.mountpoint, p.uuid
			return True
		return False

	def getDefaultStorageDevicebyUUID(self, uuid):
		for p in self.getConfiguredStorageDevices():
			if p.uuid == uuid:
				#print "getDefaultStorageDevicebyUUID--p:",uuid, p.description, p.device, p.mountpoint, p.uuid
				return p
		return None

	def getConfiguredStorageDevices(self):
		parts = [x for x in self.partitions if (x.uuid is not None and x.mounted() and self.isConfiguredStorageDevice(x.uuid))]
		return [x for x in parts]

	def getMountedPartitions(self, onlyhotplug = False):
		parts = [x for x in self.partitions if (x.is_hotplug or not onlyhotplug) and x.mounted()]
		devs = set([x.device for x in parts])
		for devname in devs.copy():
			if not devname:
				continue
			dev, part = self.splitDeviceName(devname)
			if part and dev in devs: # if this is a partition and we still have the wholedisk, remove wholedisk
				devs.remove(dev)

		# return all devices which are not removed due to being a wholedisk when a partition exists
		return [x for x in parts if not x.device or x.device in devs]

	def splitDeviceName(self, devname):
		# this works for: sdaX, hdaX, sr0 (which is in fact dev="sr0", part=""). It doesn't work for other names like mtdblock3, but they are blacklisted anyway.
		dev = devname[:3]
		part = devname[3:]
		for p in part:
			if not p.isdigit():
				return devname, 0
		return dev, part and int(part) or 0

	def getUserfriendlyDeviceName(self, dev, phys):
		#print "getUserfriendlyDeviceName",dev, phys
		dev, part = self.splitDeviceName(dev)
		description = "External Storage %s" % dev
		have_model_descr = False
		try:
			description = readFile("/sys" + phys + "/model")
			have_model_descr = True
		except IOError, s:
			print "couldn't read model: ", s
		from Tools.HardwareInfo import HardwareInfo
		if dev.find('sr') == 0 and dev[2].isdigit():
			devicedb = DEVICEDB_SR
		else:
			devicedb = DEVICEDB
		for physdevprefix, pdescription in devicedb.get(HardwareInfo().device_name,{}).items():
			if phys.startswith(physdevprefix):
				if have_model_descr:
					description = pdescription + ' - ' + description
				else:
					description = pdescription
		# not wholedisk and not partition 1
		if part and part != 1:
			description += " (Partition %d)" % part
		return description

	def addMountedPartition(self, device, desc):
		already_mounted = False
		for x in self.partitions[:]:
			if x.mountpoint == device:
				already_mounted = True
		if not already_mounted:
			self.partitions.append(Partition(mountpoint = device, description = desc))

	def removeMountedPartition(self, mountpoint):
		for x in self.partitions[:]:
			if x.mountpoint == mountpoint:
				self.partitions.remove(x)
				self.on_partition_list_change("remove", x)

	def removeMountedPartitionbyDevice(self, device):
		p = self.getPartitionbyDevice(device)
		if p is not None:
			#print "[removeMountedPartitionbyDevice] '%s', '%s', '%s', '%s', '%s'" % (p.mountpoint,p.description,p.device,p.force_mounted,p.uuid)
			self.partitions.remove(p)
			self.on_partition_list_change("remove", p)

	def trigger_udev(self):
		# We have to trigger udev to rescan sysfs
		Console().ePopen(("udevadm", "udevadm", "trigger"))

	def getPartitionbyUUID(self, uuid):
		for x in self.partitions[:]:
			if x.uuid == uuid:
				#print "[getPartitionbyUUID] '%s', '%s', '%s', '%s', '%s'" % (x.mountpoint,x.description,x.device,x.force_mounted,x.uuid)
				return x
		return None

	def getPartitionbyDevice(self, dev):
		for x in self.partitions[:]:
			if x.device == dev:
				#print "[getPartitionbyDevice] '%s', '%s', '%s', '%s', '%s'" % (x.mountpoint,x.description,x.device,x.force_mounted,x.uuid)
				return x
		return None

	def getPartitionbyMountpoint(self, mountpoint):
		for x in self.partitions[:]:
			if x.mountpoint == mountpoint:
				#print "[getPartitionbyMountpoint] '%s', '%s', '%s', '%s', '%s'" % (x.mountpoint,x.description,x.device,x.force_mounted,x.uuid)
				return x
		return None

	def getDeviceNamebyUUID(self, uuid):
		if path.exists("/dev/disk/by-uuid/" + uuid):
			return path.basename(path.realpath("/dev/disk/by-uuid/" + uuid))
		return None

	def getPartitionUUID(self, part):
		if not path.exists("/dev/disk/by-uuid"):
			return None
		for uuid in listdir("/dev/disk/by-uuid/"):
			if not path.exists("/dev/disk/by-uuid/" + uuid):
				return None
			if path.basename(path.realpath("/dev/disk/by-uuid/" + uuid)) == part:
				#print "[getPartitionUUID] '%s' - '%s'" % (uuid, path.basename(path.realpath("/dev/disk/by-uuid/" + uuid)) )
				return uuid
		return None

	def getDeviceDescription(self, dev):
		physdev = path.realpath('/sys/block/' + dev[:3] + '/device')[4:]
		description = self.getUserfriendlyDeviceName(dev[:3], physdev)
		#print "[getDeviceDescription] -> device:'%s' - desc: '%s' phy:'%s'" % (dev, description, physdev)
		return description

	def reloadExports(self):
		if path.exists("/etc/exports"):
			Console().ePopen(("exportfs -r"))

	def unmountPartitionbyMountpoint(self, mountpoint, device = None):
		if (path.exists(mountpoint) and path.ismount(mountpoint)) or (not path.exists(mountpoint) and self.get_mountdevice(mountpoint) is not None):
			#call the mount/unmount event notifier to inform about an unmount
			for callback in self.onUnMount_Notifier:
				try:
					callback(self.EVENT_UNMOUNT, mountpoint)
				except AttributeError:
					self.onUnMount_Notifier.remove(callback)
			cmd = "umount" + " " + mountpoint
			print "[unmountPartitionbyMountpoint] %s:" % (cmd)
			system(cmd)
		if path.exists(mountpoint) and not path.ismount(mountpoint):
			part = self.getPartitionbyMountpoint(mountpoint)
			if part is not None:
				if part.uuid is not None and part.uuid == config.storage_options.default_device.value: #unmounting Default Mountpoint /media/hdd
					#call the notifier also here if we unmounted the default partition
					for callback in self.delayed_device_Notifier:
						try:
							callback(part.device, "remove_default" )
						except AttributeError:
							self.delayed_device_Notifier.remove(callback)
					part.device = None
					part.updatePartitionInfo()
			if device is not None and not path.ismount(mountpoint):
				self.removeMountedPartitionbyDevice(device)
			self.reloadExports()

	def unmountPartitionbyUUID(self, uuid):
		mountpoint = ""
		cfg = config.storage.get(uuid, None)
		if cfg is not None:
			mountpoint = config.storage[uuid]['mountpoint'].value
		if mountpoint != "":
			if path.exists(mountpoint) and path.ismount(mountpoint):
				#call the mount/unmount event notifier to inform about an unmount
				for callback in self.onUnMount_Notifier:
					try:
						callback(self.EVENT_UNMOUNT, mountpoint)
					except AttributeError:
						self.onUnMount_Notifier.remove(callback)
				cmd = "umount" + " " + mountpoint
				print "[unmountPartitionbyUUID] %s:" % (mountpoint)
				system(cmd)
				self.reloadExports()

	def mountPartitionbyUUID(self, uuid):
		if path.exists("/dev/disk/by-uuid/" + uuid):
			cfg_uuid = config.storage.get(uuid, None)
			partitionPath = "/dev/disk/by-uuid/" + uuid
			mountpoint = cfg_uuid['mountpoint'].value
			dev = self.getDeviceNamebyUUID(uuid)
			#print "[mountPartitionbyUUID] for UUID:'%s' - '%s'" % (uuid,mountpoint)

			# we must umount autofs first because autofs mounts with "sync" option
			# and the real mount than also mounts with this option
			# this is realy bad for the performance!
			forceAutofsUmount(dev)

			#verify if mountpoint is still mounted from elsewhere (e.g fstab)
			if path.exists(mountpoint) and path.ismount(mountpoint):
				tmppath = self.get_mountdevice(mountpoint)
				if tmppath is not None and tmppath.startswith("/dev/disk/by-uuid/") and tmppath != partitionPath: #probably different device mounted on our mountpoint
					tmpuuid = tmppath.rsplit("/",1)[1]
					if not self.isUUIDpathFsTabMount(tmpuuid, mountpoint) and not self.isPartitionpathFsTabMount(tmpuuid, mountpoint):
						self.unmountPartitionbyMountpoint(mountpoint)

			#verify if our device is still mounted to somewhere else
			tmpmount = self.get_mountpoint(partitionPath)
			if tmpmount is not None and tmpmount != mountpoint and path.exists(tmpmount) and path.ismount(tmpmount):
				if not self.isUUIDpathFsTabMount(uuid, tmpmount) and not self.isPartitionpathFsTabMount(uuid, tmpmount):
						self.unmountPartitionbyMountpoint(tmpmount)

			if cfg_uuid['enabled'].value:
				if mountpoint != "":
					if not path.exists(mountpoint):
						try:
							makedirs(mountpoint)
						except OSError:
							print "[mountPartitionbyUUID] could not create mountdir:",mountpoint

					if path.exists(mountpoint) and not path.ismount(mountpoint) and not path.islink(mountpoint):
						cmd = "mount -t auto /dev/disk/by-uuid/" + uuid + " " + mountpoint
						system(cmd)
						print "[mountPartitionbyUUID]:",cmd
						#call the mount/unmount event notifier to inform about an mount
						for callback in self.onUnMount_Notifier:
							try:
								callback(self.EVENT_MOUNT, mountpoint)
							except AttributeError:
								self.onUnMount_Notifier.remove(callback)

					if path.ismount(mountpoint):
						dev = self.getDeviceNamebyUUID(uuid)
						if dev is not None:
							p = self.getPartitionbyMountpoint(mountpoint)
							if p is not None:
								x = self.getPartitionbyDevice(dev)
								if x is not None and x.mountpoint.startswith('/autofs'):
									self.removeMountedPartitionbyDevice(dev) #remove now obsolete entry
								p.mountpoint = mountpoint
								p.uuid = uuid
								p.device = dev
								p.force_mounted = False
								p.updatePartitionInfo()
							else:
								p = self.getPartitionbyDevice(dev)
								if p is not None:
									p.mountpoint = mountpoint
									p.uuid = uuid
									p.device = dev
									p.force_mounted = False
									p.updatePartitionInfo()
					else:
						print "[mountPartitionbyUUID] could not mount mountdir:",mountpoint
		else:
			print "[mountPartitionbyUUID] failed for UUID:'%s'" % (uuid)

	def storageDeviceChanged(self, uuid):
		if config.storage[uuid]["enabled"].value:
			#print "[storageDeviceChanged] for enabled UUID:'%s'" % (uuid)
			self.mountPartitionbyUUID(uuid)
		else:
			#print "[storageDeviceChanged] for disabled UUID:'%s'" % (uuid)
			self.unmountPartitionbyUUID(uuid)

	def setupConfigEntries(self, initial_call = False, dev = None):
		if initial_call and not dev:
			for uuid in config.storage.stored_values:
				print "[setupConfigEntries] initial_call for stored uuid:",uuid,config.storage.stored_values[uuid]
				config.storage[uuid] = ConfigSubDict()
				config.storage[uuid]["enabled"] = ConfigYesNo(default = False)
				config.storage[uuid]["mountpoint"] = ConfigText(default = "", visible_width = 50, fixed_size = False)
				config.storage[uuid]["device_description"] = ConfigText(default = "", visible_width = 50, fixed_size = False)
				config.storage[uuid]["device_info"] = ConfigText(default = "", visible_width = 50, fixed_size = False)
				config.storage[uuid]["isRemovable"] = ConfigBoolean(default = False)
				if config.storage[uuid]['enabled'].value:
					dev = self.getDeviceNamebyUUID(uuid)
					if uuid == config.storage_options.default_device.value and config.storage[uuid]["mountpoint"].value != "/media/hdd":
						print "[setupConfigEntries] initial_call discovered a default storage device misconfiguration, reapplied default storage config for:",uuid
						if path.exists("/media/hdd") and path.islink("/media/hdd") and self.getLinkPath("/media/hdd") == config.storage[uuid]["mountpoint"].value:
							unlink("/media/hdd")
						if dev is not None:
							self.unmountPartitionbyMountpoint(config.storage[uuid]["mountpoint"].value, dev)
						config.storage[uuid]["mountpoint"].value = "/media/hdd"
					if dev is not None:
						p = self.getPartitionbyDevice(dev) or self.getPartitionbyMountpoint(config.storage[uuid]["mountpoint"].value)
						if p is None: # manually add partition entry
							description = self.getDeviceDescription(dev)
							device_mountpoint = self.getAutofsMountpoint(dev)
							if config.storage[uuid]['mountpoint'].value != "":
								device_mountpoint = config.storage[uuid]['mountpoint'].value
							p = Partition(mountpoint = device_mountpoint, description = description, force_mounted = False, device = dev)
							p.uuid = uuid
							p.updatePartitionInfo()
							self.partitions.append(p)
							self.on_partition_list_change("add", p)
					if path.exists("/dev/disk/by-uuid/" + uuid):
						self.storageDeviceChanged(uuid)
				else:
					del config.storage[uuid]
					config.storage.save()
					config.save()
		if dev is not None:
			uuid = self.getPartitionUUID(dev)
			if uuid is not None:
				if config.storage.get(uuid, None) is None: #new unconfigured device added
					print "[setupConfigEntries] new device add for '%s' with uuid:'%s'" % (dev, uuid)
					hdd = self.getHDD(dev)
					if hdd is not None:
						hdd_description = hdd.model()
						cap = hdd.capacity()
						if cap != "":
							hdd_description += " (" + cap + ")"
						device_info =  hdd.bus_description()
					else:
						device_info = dev
						hdd_description = self.getDeviceDescription(dev)
					config.storage[uuid] = ConfigSubDict()
					config.storage[uuid]["enabled"] = ConfigYesNo(default = False)
					config.storage[uuid]["mountpoint"] = ConfigText(default = "", visible_width = 50, fixed_size = False)
					config.storage[uuid]["device_description"] = ConfigText(default = "", visible_width = 50, fixed_size = False)
					config.storage[uuid]["device_info"] = ConfigText(default = "", visible_width = 50, fixed_size = False)
					config.storage[uuid]["isRemovable"] = ConfigBoolean(default = False)
					removable = False
					if hdd is not None:
						removable = hdd.isRemovable
					config.storage[uuid]["device_description"].setValue(hdd_description)
					config.storage[uuid]["device_info"].setValue(device_info)
					config.storage[uuid]["isRemovable"].setValue(removable)
					config.storage[uuid].save()
					self.verifyInstalledStorageDevices()
					p = self.getPartitionbyDevice(dev)
					if p is None: # manually add partition entry (e.g. on long spinup times)
						description = self.getDeviceDescription(dev)
						device_mountpoint = self.getAutofsMountpoint(dev)
						p = Partition(mountpoint = device_mountpoint, description = description, force_mounted = True, device = dev)
						p.uuid = uuid
						p.updatePartitionInfo()
						self.partitions.append(p)
						self.on_partition_list_change("add", p)
					self.storageDeviceChanged(uuid)
				else:
					p = self.getPartitionbyDevice(dev)
					device_mountpoint = self.getAutofsMountpoint(dev)
					if config.storage[uuid]['enabled'].value and config.storage[uuid]['mountpoint'].value != "":
						device_mountpoint = config.storage[uuid]['mountpoint'].value
					if p is None: # manually add partition entry (e.g. on default storage device change)
						description = self.getDeviceDescription(dev)
						p = Partition(mountpoint = device_mountpoint, description = description, force_mounted = True, device = dev)
						p.uuid = uuid
						p.updatePartitionInfo()
						self.partitions.append(p)
						self.on_partition_list_change("add", p)
						print "[setupConfigEntries] new/changed device add for '%s' with uuid:'%s'" % (dev, uuid)
						self.storageDeviceChanged(uuid)
					else:
						tmp = self.getPartitionbyMountpoint(device_mountpoint)
						if tmp is not None and (tmp.uuid != uuid or tmp.mountpoint != config.storage[uuid]['mountpoint'].value):
							print "[setupConfigEntries] new/changed device add for '%s' with uuid:'%s'" % (dev, uuid)
							self.storageDeviceChanged(uuid)
			else:
				print "[setupConfigEntries] device add for '%s' without uuid !!!" % (dev)

	def configureUuidAsDefault(self, uuid, device):
		#verify if our device is manually mounted from fstab to somewhere else
		isManualFstabMount = False
		uuidPath = "/dev/disk/by-uuid/" + uuid
		tmpmount = self.get_mountpoint(uuidPath)
		if tmpmount is not None and tmpmount != "/media/hdd":
			isManualFstabMount = True
		if not isManualFstabMount:
			if not self.inside_mountpoint("/media/hdd") and not path.islink("/media/hdd") and not self.isPartitionpathFsTabMount(uuid, "/media/hdd"):
				print "configureUuidAsDefault: using found %s as default storage device" % device
				config.storage_options.default_device.value = uuid
				config.storage_options.save()
				cfg_uuid = config.storage.get(uuid, None)
				if cfg_uuid is not None and not cfg_uuid["enabled"].value:
					cfg_uuid["enabled"].value = True
					cfg_uuid["mountpoint"].value = "/media/hdd"
					config.storage[uuid].save()
					config.storage.save()
					config.save()
					self.modifyFstabEntry("/dev/disk/by-uuid/" + uuid, "/media/hdd", mode = "add_activated")
					self.storageDeviceChanged(uuid)

	def isInitializedByEnigma2(self, hdd):
		isInitializedByEnigma2 = False
		uuid = device = None
		if hdd and hdd.numPartitions() <= 2:
			numPart = hdd.numPartitions()
			device = hdd.device
			if numPart == 1 or numPart == 2:
				device = hdd.device + "1"
			p = self.getPartitionbyDevice(device)
			if p is not None and p.uuid and p.isInitialized: #only one by e2 initialized partition
				isInitializedByEnigma2 = True
				uuid = p.uuid
			if numPart == 2:
				part2Type = self.getBlkidPartitionType(hdd.partitionPath("2"))
				if part2Type != "swap":
					isInitializedByEnigma2 = False
		return isInitializedByEnigma2,device,uuid

	def verifyInstalledStorageDevices(self):
		if config.storage_options.default_device.value == "<undefined>" and self.HDDCount() == 1 and not self.HDDEnabledCount(): #only one installed and unconfigured device
			hdd = self.hdd[0]
			isInitializedByEnigma2,device,uuid = self.isInitializedByEnigma2(hdd)
			if isInitializedByEnigma2:
				self.configureUuidAsDefault(uuid, device)


harddiskmanager = HarddiskManager()
harddiskmanager.enumerateBlockDevices()
harddiskmanager.verifyInstalledStorageDevices() #take sure enumerateBlockdev is finished so we don't miss any at startup installed storage devices
