from os import system, listdir, statvfs, makedirs, stat, major, minor, path, access, readlink, unlink, getcwd, chdir, W_OK
from re import search
from time import time

from Tools.Directories import SCOPE_HDD, resolveFilename
from Tools.CList import CList
from Tools.IO import runPipe, saveFile
from SystemInfo import SystemInfo
from Components.Console import Console
from config import config, configfile, ConfigYesNo, ConfigText, ConfigSubDict, ConfigSubsection, ConfigBoolean

class Util:
	@staticmethod
	def compareDeviceId(pathnameA, pathnameB):
		try:
			rdevA = stat(pathnameA).st_rdev
		except:
			print "Harddisk.py: stat failed on %s" % pathnameA
			raise
		try:
			rdevB = stat(pathnameB).st_rdev
		except:
			print "Harddisk.py: stat failed on %s" % pathnameB
			raise
		return rdevA == rdevB

	@staticmethod
	def readFile(filename):
		try:
			return file(filename).read().strip()
		except:
			print "Harddisk.py: failed to read %s" % filename
			raise

	@staticmethod
	def __readLines(filename):
		try:
			return file(filename).read().splitlines()
		except:
			print "Harddisk.py: failed to read %s" % filename
			return []

	@staticmethod
	def fstab():
		if not hasattr(Util.fstab, 'cache'):
			Util.fstab.cache = []
			Util.fstab.mtime = -1
		try:
			mtime = stat('/etc/fstab').st_mtime
		except:
			print "Harddisk.py: stat failed on %s" % '/etc/fstab'
			return Util.fstab.cache

		if mtime != Util.fstab.mtime:
			Util.fstab.cache = Util.__readLines('/etc/fstab')
			Util.fstab.mtime = mtime

		return Util.fstab.cache

	@staticmethod
	def mtab(phys=True, virt=True):
		mounts = Util.__readLines('/proc/mounts')
		if phys and virt:
			return mounts
		elif phys:
			return [m for m in mounts if m.startswith('/')]
		elif virt:
			return [m for m in mounts if not m.startswith('/')]
		else:
			return []

	@staticmethod
	def parseFstabLine(line):
		if line.startswith('#'):
			return None
		fields = line.split()
		nfields = len(fields)
		if not 4 <= nfields <= 6:
			return None
		# freq defaults to 0
		if nfields < 5:
			fields.append('0')
		# passno defaults to 0
		if nfields < 6:
			fields.append('0')
		return fields

	@staticmethod
	def __findInTab(tab, src, dst):
		if src or dst:
			for line in tab:
				fields = Util.parseFstabLine(line)
				if not fields:
					continue
				if src is not None and src != fields[0]:
					continue
				if dst is not None and dst != fields[1]:
					continue
				return dict(src = fields[0],
					dst = fields[1],
					vfstype = fields[2],
					options = set(fields[3].split(',')),
					freq = int(fields[4]),
					passno = int(fields[5]))
		return None

	@staticmethod
	def findInFstab(src=None, dst=None):
		return Util.__findInTab(Util.fstab(), src, dst)

	@staticmethod
	def findInMtab(src=None, dst=None):
		return Util.__findInTab(Util.mtab(), src, dst)

	@staticmethod
	def __mountUmount(cmd, dir_or_device):
		if dir_or_device:
			rc, _ = runPipe([cmd, dir_or_device])
			return rc
		else:
			return -1

	@staticmethod
	def mount(dir_or_device):
		return Util.__mountUmount('mount', dir_or_device)

	@staticmethod
	def umount(dir_or_device):
		return Util.__mountUmount('umount', dir_or_device)

	# We must unmount autofs before mounting manually, because autofs uses the
	# "sync" option, which the manual mount would inherit. This would be bad
	# for performance.
	@staticmethod
	def forceAutofsUmount(dev):
		autofsPath = '/autofs/%s' % dev
		if Util.findInMtab(dst=autofsPath):
			Util.umount(autofsPath)

class Harddisk:
	def __init__(self, device, removable = False):
		self.device = device
		self.isRemovable = removable

		self.is_sleeping = False
		self.max_idle_time = 0
		self.idle_running = False
		self.timer = None

		self.isInitializing = False
		self.isVerifying = False

		self.dev_path = ''
		self.disk_path = ''
		self.phys_path = path.realpath(self.sysfsPath('device'))

		self.dev_path = '/dev/' + self.device
		self.disk_path = self.dev_path

		print "new Harddisk", self.device, '->', self.dev_path, '->', self.disk_path
		if not self.isRemovable:
			self.startIdle()

	def __lt__(self, ob):
		return self.device < ob.device

	def partitionPath(self, n):
		return self.dev_path + n

	def sysfsPath(self, filename):
		return path.realpath('/sys/block/' + self.device + '/' + filename)

	def stop(self):
		if self.timer:
			self.timer.stop()
			self.timer_conn = None

	def bus(self):
		# FIXME: USB 3.0 is connected through pci, too
		internal = "pci" in self.phys_path

		if internal:
			ret = "Internal"
		else:
			ret = "External"
		return ret

	def bus_type(self):
		# FIXME: USB 3.0 is connected through pci, too
		sata = "pci" in self.phys_path
		sata_desc = self.bus_description()

		if sata:
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

	def __sectors(self):
		try:
			return int(Util.readFile(self.sysfsPath('size')))
		except:
			return 0

	def __diskSize(self):
		# Assume 512-bytes sectors, even for 4K drives. Return KB.
		return self.__sectors() * 512 / 1000

	def __capacityString(self, cap, divisor, unit):
		if cap < divisor:
			return ""
		value = cap * 10 / divisor
		remainder = value % 10
		value /= 10
		if remainder == 0:
			return "%d %s" % (value, unit)
		return "%d.%d %s" % (value, remainder, unit)

	def capacity(self):
		# Return at most one decimal place, but no leading zero.
		cap = self.__diskSize()
		return (self.__capacityString(cap, 1000000000000, 'PB') or
			self.__capacityString(cap, 1000000000, 'TB') or
			self.__capacityString(cap, 1000000, 'GB') or
			self.__capacityString(cap, 1000, 'MB') or
			self.__capacityString(cap, 1, 'KB'))

	def model(self, model_only = False, vendor_only = False):
		try:
			vendor = Util.readFile(self.sysfsPath('device/vendor'))
		except:
			vendor = ""
		try:
			model = Util.readFile(self.sysfsPath('device/model'))
		except:
			model = ""

		if vendor_only:
			return vendor
		if model_only:
			return model
		return vendor + '-' + model

	def free(self):
		for line in Util.mtab(virt=False):
			try:
				src, dst, _, _, _, _ = Util.parseFstabLine(line)
				real_path = path.realpath(src)
				if not real_path[-1].isdigit():
					continue
				if Util.compareDeviceId(real_path, self.partitionPath(real_path[-1])):
					stat = statvfs(dst)
					return stat.f_bfree/1000 * stat.f_bsize/1000
			except:
				pass
		return -1

	def numPartitions(self):
		numPart = -1
		try:
			devdir = listdir('/dev')
		except OSError:
			return -1
		for filename in devdir:
			if filename.startswith(self.device):
				numPart += 1
		return numPart

	def unmount(self, numpart = None):
		for line in Util.mtab(virt=False):
			try:
				src, _, _, _, _, _ = Util.parseFstabLine(line)
			except:
				continue
			real_path = path.realpath(src)
			if not real_path[-1].isdigit():
				if numpart == 0:
					if real_path.startswith("/dev/sd"):
						uuid = harddiskmanager.getPartitionUUID(self.device)
						if uuid is not None:
							try:
								if Util.compareDeviceId(real_path, self.dev_path):
									return Util.umount(src)
							except OSError:
								pass
			try:
				if Util.compareDeviceId(real_path, self.partitionPath(real_path[-1])):
					return Util.umount(src)
			except OSError:
				pass
		return 0

	def createPartition(self):
		maxSectorsMBR = int(4294967295) #2TB
		swapPartSize = int(2097152) #1GB
		fstype, sys, size, sizeg, sectors = harddiskmanager.getFdiskInfo(self.device[:3])
		if sectors is None:
			sectors = self.__sectors()
		cmd = 'parted --script --align=min ' + self.disk_path + ' -- mklabel msdos mkpart primary ext3 40s 100%'
		if sectors and not self.isRemovable:
			part1end = int(sectors)-swapPartSize #leaving 1GB for swap
			cmd = 'parted --script --align=min ' + self.disk_path + ' -- mklabel msdos mkpart primary ext3 40s ' + str(part1end) + 's'
			cmd+=  ' mkpart primary linux-swap ' + str(int(part1end+1)) + 's -1s'
			if sectors > maxSectorsMBR:
				cmd = 'parted --script --align=opt -- ' + self.disk_path + ' mklabel gpt mkpart primary ext3 2048s ' + str(part1end) + 's'
				cmd+=  ' mkpart primary linux-swap ' + str(int(part1end+1)) + 's -1'

		res = system(cmd)
		print  "[createPartition]:",res,cmd
		return (res >> 8)

	def mkfs(self, fstype = "ext4", partitionNum = "1"):
		cmd = "mkfs." + fstype + " "
		if self.__diskSize() >= 4000000:	# 4 GB
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
		if partitionType == "swap":
			cmd = "swapon " + self.partitionPath(partitionNum)
			system(cmd)

	def deactivateswap(self, partitionNum = "2"):
		partitionType = harddiskmanager.getBlkidPartitionType(self.partitionPath(partitionNum))
		if partitionType == "swap":
			cmd = "swapoff " + self.partitionPath(partitionNum)
			print "[deactivate swap]:",cmd
			system(cmd)

	def mount(self):
		for line in Util.fstab():
			try:
				src, dst, _, _, _, _ = Util.parseFstabLine(line)
			except:
				continue
			real_path = path.realpath(src)
			if not real_path[-1].isdigit():
				continue
			try:
				if Util.compareDeviceId(real_path, self.partitionPath(real_path[-1])):
					Util.forceAutofsUmount(self.device+real_path[-1])
					return Util.mount(src)
			except OSError:
				pass

		return -1

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
		# We autocorrect any failures and check if the fs is actually one we can check (currently ext2/ext3/ext4)
		partitionPath = self.partitionPath("1")

		# Lets activate the swap partition if exists
		self.activateswap()

		if numpart == 0:
			partitionPath = self.dev_path
		elif numpart >= 1:
			partitionPath = self.partitionPath(str(numpart))

		partitionType = harddiskmanager.getBlkidPartitionType(partitionPath)

		res = -1
		if access(partitionPath, 0):
			if partitionType in ("ext2", "ext3", "ext4"):
				cmd = "fsck." + partitionType + " -f -p -C 0 " + partitionPath
				res = system(cmd)

		# Lets deactivate the swap partition
		self.deactivateswap()

		return (res >> 8)

	def killPartition(self):
		part = self.disk_path
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
		# for ext2/ext3/ext4 and also for GPT/EFI partitions.
		self.killPartition()

		if self.createPartition() != 0:
			return -1

		if self.mkfs() != 0:
			return -2

		# init the swap partition
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
		self.last_access = time()
		self.last_stat = 0
		from enigma import eTimer

		# disable HDD standby timer
		if self.bus() == "External":
			Console().ePopen(("sdparm", "sdparm", "--set=SCT=0", self.disk_path))
		else:
			Console().ePopen(("hdparm", "hdparm", "-S0", self.disk_path))
		self.timer = eTimer()
		self.timer_conn = self.timer.timeout.connect(self.runIdle)
		self.idle_running = True
		try:
			self.setIdleTime(int(config.usage.hdd_standby.value))
		except KeyError:
			self.setIdleTime(self.max_idle_time) # kick the idle polling loop

	def runIdle(self):
		if not self.max_idle_time:
			return
		t = time()

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
	def __init__(self, hddmanager, mountpoint, device = None, description = "", force_mounted = False, uuid = None):
		self.__hddmanager = hddmanager
		self.mountpoint = mountpoint
		self.description = description
		self.force_mounted = force_mounted
		self.is_hotplug = force_mounted # so far; this might change.
		self.device = device
		self.disc_path = None
		self.uuid = uuid
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
			self.uuid = self.__hddmanager.getPartitionUUID(self.device)
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
					self.fsType = self.__hddmanager.getBlkidPartitionType("/dev/" + self.device)
			if self.isReadable:
				entry = Util.findInMtab(src='/dev/%s' % self.device)
				if entry:
					if self.fsType is None:
						self.fsType = entry['vfstype']
					self.isWriteable = 'rw' in entry['options'] and access(testpath, W_OK)
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
		return self.force_mounted or Util.findInMtab(dst=self.mountpoint) is not None


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
	"dm7080":
	{
		"/devices/pci0000:00/0000:00:00.0/usb9/9-1/": _("Back USB 3.0"),
		"/devices/pci0000:00/0000:00:00.0/usb9/9-2/": _("Front USB 3.0"),
		"/devices/platform/ehci-brcm.0/": _("Back, lower USB"),
		"/devices/platform/ehci-brcm.1/": _("Back, upper USB"),
		"/devices/platform/ehci-brcm.2/": _("Internal USB"),
		"/devices/platform/ehci-brcm.3/": _("Internal USB"),
		"/devices/platform/ohci-brcm.0/": _("Back, lower USB"),
		"/devices/platform/ohci-brcm.1/": _("Back, upper USB"),
		"/devices/platform/ohci-brcm.2/": _("Internal USB"),
		"/devices/platform/ohci-brcm.3/": _("Internal USB"),
		"/devices/platform/sdhci-brcmstb.0/": _("eMMC"),
		"/devices/platform/sdhci-brcmstb.1/": _("SD"),
		"/devices/platform/strict-ahci.0/ata1/": _("SATA"),	# front
		"/devices/platform/strict-ahci.0/ata2/": _("SATA"),	# back
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
		self.delayed_device_Notifier = [ ]
		self.onUnMount_Notifier = [ ]

		self.on_partition_list_change = CList()

		# currently, this is just an enumeration of what's possible,
		# this probably has to be changed to support automount stuff.
		# still, if stuff is mounted into the correct mountpoints by
		# external tools, everything is fine (until somebody inserts
		# a second usb stick.)
		p = [
					("/media/hdd", _("Hard disk")),
					("/media/net", _("Network Mount")),
					("/", _("Internal Flash"))
				]
		for x in p:
			self.__addPartition(mountpoint = x[0], description = x[1], notify = False)
		self.setupConfigEntries(initial_call = True)

	class BlockDevice:
		def __init__(self, name):
			self._name = name
			self._blockPath = path.join('/sys/block', self._name)
			self._classPath = path.realpath(path.join('/sys/class/block', self._name))
			self._deviceNode = path.join('/dev', self._name)

		def isBlacklisted(self):
			try:
				dev = int(Util.readFile(path.join(self._classPath, 'dev')).split(':')[0])
				return dev in (1, 7, 31, 179) # ram, loop, mtdblock, mmcblk
			except IOError:
				return True

		def isOpticalDiscDrive(self):
			return self._name.startswith('sr')

		def isPartition(self):
			# /sys/block lists only full block devices
			return not path.exists(self._blockPath)

		def isRemovable(self):
			# Partitions don't have a 'removable' property. Ask their parent.
			try:
				return bool(int(Util.readFile(self.sysfsPath('removable', physdev=True))))
			except IOError:
				return False

		def hasMedium(self):
			try:
				open(self._deviceNode, 'rb').close()
			except IOError, err:
				if err.errno == 159: # no medium present
					return False
			return True

		def partitions(self):
			partitions = []
			for partition in listdir(self._classPath):
				if partition.startswith(self._name):
					partitions.append(partition)
			return partitions

		def sysfsPath(self, filename, physdev=False):
			classPath = self._classPath
			if physdev and self.isPartition():
				classPath = path.dirname(classPath)
			return path.join(classPath, filename)

	def getAutofsMountpoint(self, device):
		return "/autofs/%s/" % (device)

	def is_hard_mounted(self, device):
		entry = Util.findInMtab(src=device)
		if entry:
			return not entry['dst'].startswith('/autofs/')
		return False

	def get_mountdevice(self, mountpoint):
		entry = Util.findInMtab(dst=mountpoint)
		if entry:
			return entry['src']
		return None

	def get_mountpoint(self, device):
		entry = Util.findInMtab(src=device)
		if entry:
			return entry['dst']
		return None

	def is_uuidpath_mounted(self, uuidpath, mountpoint):
		return Util.findInMtab(src=uuidpath, dst=mountpoint) is not None

	def is_fstab_mountpoint(self, device, mountpoint):
		return Util.findInFstab(src=device, dst=mountpoint) is not None

	def get_fstab_mountstate(self, device, mountpoint):
		entry = Util.findInFstab(src=device, dst=mountpoint)
		if entry:
			return ('noauto' if 'noauto' in entry['options'] else 'auto')
		return None

	def get_fstab_mountpoint(self, device):
		entry = Util.findInFstab(src=device)
		if entry:
			return entry['dst']
		return None

	def modifyFstabEntry(self, partitionPath, mountpoint, mode = "add_deactivated"):
		fstab = Util.fstab()
		if not fstab:
			print '[Harddisk.py] Refusing to modify empty fstab'
			return False

		newopt = {'noauto' if mode == 'add_deactivated' else 'auto'}
		newopt.add('nofail')
		output = []
		for x in fstab:
			try:
				src, dst, vfstype, mntops, freq, passno = Util.parseFstabLine(x)
			except:
				output.append(x)
			else:
				# remove or replace existing entry
				if src == partitionPath and dst == mountpoint:
					if mode == 'remove':
						continue
					opts = set(mntops.split(',')) - { 'auto', 'noauto', 'fail' }
					opts.update(newopt)
					mntops = ','.join(opts)
					output.append('\t'.join([src, dst, vfstype, mntops, freq, passno]))
					# remove possible duplicate entries
					mode = 'remove'
				else:
					output.append(x)

		# append new entry
		if mode != 'remove':
			mntops = ','.join(newopt)
			output.append('\t'.join([partitionPath, mountpoint, 'auto', mntops, '0', '0']))

		if not output:
			print '[Harddisk.py] Refusing to write empty fstab'
			return False

		return saveFile('/etc/fstab', '\n'.join(output) + '\n')

	def addHotplugPartition(self, device, data):
		print "found block device '%s':" % device
		if not device:
			return False, False, False

		blkdev = self.BlockDevice(device)
		physdev = blkdev.sysfsPath('device', physdev=True)[4:]

		removable = blkdev.isRemovable()
		is_cdrom = blkdev.isOpticalDiscDrive()
		medium_found = blkdev.hasMedium()

		# This sucks with two optical drives
		if is_cdrom:
			self.cd = device

		if blkdev.isBlacklisted():
			print "blacklisted"
		else:
			if not medium_found:
				print "no medium"
			else:
				print "ok, removable=%s, cdrom=%s" % (removable, is_cdrom)

			# see if this is a harddrive or removable drive (usb stick/cf/sd)
			devtype = data.get('DEVTYPE')	# "disk","partition"
			if devtype:
				if not is_cdrom and medium_found:
					if devtype == "disk":
						if self.getHDD(device) is None:
							self.hdd.append(Harddisk(device, removable))
							self.hdd.sort()
							SystemInfo["Harddisk"] = len(self.hdd) > 0
					if devtype == "partition":
						p = self.getPartitionbyDevice(device)
						if p is None:
							self.addDevicePartition(device, physdev)
				return removable, is_cdrom, medium_found

			if not blkdev.isPartition() and not is_cdrom and medium_found and self.getHDD(device) is None:
				self.hdd.append(Harddisk(device, removable))
				self.hdd.sort()
				SystemInfo["Harddisk"] = len(self.hdd) > 0
			if not removable or medium_found:
				self.addDevicePartition(device, physdev)

		return removable, is_cdrom, medium_found

	def removeHotplugPartition(self, device, data):
		blkdev = self.BlockDevice(device)
		if blkdev.isBlacklisted():
			print "blacklisted"
			return

		mountpoint = self.getAutofsMountpoint(device)
		uuid = self.getPartitionUUID(device)
		print "[removeHotplugPartition] for device:'%s' uuid:'%s' and mountpoint:'%s'" % (device, uuid, mountpoint)

		Util.forceAutofsUmount(device)

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
					print "[removeHotplugPartition] - remove uuid %s from temporary drive add" % (uuid)
			if p.mountpoint != "/media/hdd":
				self.__removePartition(p)

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
				self.__addPartition(mountpoint = device_mountpoint, description = description, force_mounted = forced, device = device)
				cfg_uuid = config.storage.get(uuid, None)
				if cfg_uuid is not None:
					self.storageDeviceChanged(uuid)
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

	def getFdiskInfo(self, devname):
		size = sizeg = fstype = sys = sectors = None
		try:
			_, output = runPipe(['fdisk', '-l', '/dev/%s' % devname])
			for line in output:
				if line.startswith("Found valid GPT"):
					sys = "GPT"
				if line.startswith("Disk"):
					sizeobj = search(r', ((?:[a-zA-Z0-9])*) bytes', line)
					if sizeobj:
						size = sizeobj.group(1)
					sizegobj = search(r': ((?:[0-9.0-9])*) GB', line)
					if sizegobj:
						sizeg = sizegobj.group(1)
					sectorsobj = search(r': ((?:[0-9.0-9])*) sectors', line)
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

	def __getBlkidAttributes(self, options):
		res = dict()
		try:
			rc, output = runPipe(['blkid', '-o', 'export' ] + options)
			if rc == 0:
				for line in output:
					key, value = line.split('=', 1)
					res[key] = value
		except:
			pass
		return res

	def __getBlkidAttribute(self, options, name):
		attrs = self.__getBlkidAttributes(options)
		if name in attrs:
			return attrs[name]
		return None

	def __getBlkidAttributeByDevice(self, device, name):
		return self.__getBlkidAttribute([device], name)

	def __getBlkidAttributeByUuid(self, uuid, name):
		return self.__getBlkidAttribute(['-t', 'UUID=%s' % uuid, '-l'], name)

	def getBlkidPartitionType(self, device):
		return self.__getBlkidAttributeByDevice(device, 'TYPE')

	def isMount(self, mountdir):
		return path.ismount(path.realpath(mountdir))

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
		oldcurrentDefaultStorageUUID = currentDefaultStorageUUID = config.storage_options.default_device.value
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
								config.storage_options.default_device.value = uuid  #temporary assign the default storage uuid
								self.storageDeviceChanged(uuid)
								config.storage_options.default_device.value = currentDefaultStorageUUID  #reassign the original default storage uuid
								new_default = self.getPartitionbyMountpoint(def_mp)
								if cur_default_cfg is None and cur_default_newmp is not "": #currentdefault was offline
									cur_default_cfg = config.storage.get(currentDefaultStorageUUID, None)
								if cur_default_cfg is not None:
									old_cur_default_enabled = cur_default_cfg["enabled"].value
									old_cur_default_mp = cur_default_cfg["mountpoint"].value
									cur_default_cfg["mountpoint"].value = cur_default_newmp
								if new_default is not None and new_default_cfg["mountpoint"].value == def_mp and path.exists(def_mp) and self.isMount(def_mp) and new_default.mountpoint == def_mp:
									# reverify if the movie folder was created correctly
									if not path.exists(resolveFilename(SCOPE_HDD)):
										print "default movie folder still missing...try again to create it."
										try:
											makedirs(resolveFilename(SCOPE_HDD))
										except OSError:
											pass
									if path.exists(resolveFilename(SCOPE_HDD)):
										successfully = True
										config.storage_options.default_device.value = uuid
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
					if not new_default_cfg["enabled"].value or old_new_default_mp == "" or not self.isMount(old_new_default_mp):
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
		if action in ("unmount", "eject"):
			new_default = self.getPartitionbyUUID(uuid)
			new_default_cfg = config.storage.get(uuid, None)
			if new_default is not None:
				new_default_dev = new_default.device
				if new_default_cfg is not None and new_default_cfg["mountpoint"].value == new_default.mountpoint:
					old_new_default_mp = new_default_cfg["mountpoint"].value
					old_new_default_enabled = new_default_cfg["enabled"].value
					#[oldmountpath, oldenable, newmountpath, newenable]
					if action == "unmount":
						if mountData is not None and isinstance(mountData, (list, tuple)):
							old_new_default_enabled = mountData[1]
							old_new_default_mp = mountData[0]
				if new_default_cfg is not None and path.exists(old_new_default_mp) and self.isMount(old_new_default_mp):
					if uuid == currentDefaultStorageUUID:
						self.unmountPartitionbyMountpoint(old_new_default_mp)
					else:
						self.unmountPartitionbyMountpoint(old_new_default_mp, new_default_dev)
				if path.exists(old_new_default_mp) and not self.isMount(old_new_default_mp):
					if action == "unmount":
						new_default_cfg["mountpoint"].value = ""
						new_default_cfg["enabled"].value = False
						self.setupConfigEntries(initial_call = False, dev = new_default_dev)
					if path.exists(old_new_default_mp) and not self.isMount(old_new_default_mp):
						successfully = True
						if action == "unmount":
							if uuid == currentDefaultStorageUUID:
								config.storage_options.default_device.value = "<undefined>"
		if not successfully:
			print "[changeStorageDevice]: << not successfully >>"
			if cur_default_cfg is not None:
				cur_default_cfg["mountpoint"].value = old_cur_default_mp
				cur_default_cfg["enabled"].value = old_cur_default_enabled
				if currentDefaultStorageUUID != "<undefined>":
					self.storageDeviceChanged(currentDefaultStorageUUID)
			if new_default_cfg is not None:
				new_default_cfg["mountpoint"].value = old_new_default_mp
				new_default_cfg["enabled"].value = old_new_default_enabled
				self.storageDeviceChanged(uuid)
		else:
			print "[changeStorageDevice]: successfully, verifying fstab entries"
			cur_defaultPart = new_defaultPart = None
			if action == "mount_default":
				if (cur_default_dev is not None and new_default_dev is not None):
					cur_defaultPart = self.getPartitionbyDevice(cur_default_dev)
					new_defaultPart = self.getPartitionbyDevice(new_default_dev)
					if cur_defaultPart is not None:
						devpath = "/dev/disk/by-uuid/" + cur_defaultPart.uuid
						if self.is_fstab_mountpoint(devpath, "/media/hdd"):
							self.modifyFstabEntry(devpath, "/media/hdd", mode = "remove")
						if not self.is_fstab_mountpoint(devpath, cur_default_newmp):
							self.modifyFstabEntry(devpath, cur_default_newmp, mode = "add_activated")
					if new_defaultPart is not None:
						if old_new_default_mp != "":
							devpath = "/dev/disk/by-uuid/" + new_defaultPart.uuid
							if self.is_fstab_mountpoint(devpath, old_new_default_mp):
								self.modifyFstabEntry(devpath, old_new_default_mp, mode = "remove")
				if (cur_default_dev is None and new_default_dev is not None):
					new_defaultPart = self.getPartitionbyDevice(new_default_dev)
					if (new_defaultPart is not None and cur_default is None):
						devpath = "/dev/disk/by-uuid/" + oldcurrentDefaultStorageUUID
						if self.is_fstab_mountpoint(devpath, old_cur_default_mp):
							self.modifyFstabEntry(devpath, old_cur_default_mp, mode = "remove")
						if old_new_default_mp != "":
							devpath = "/dev/disk/by-uuid/" + currentDefaultStorageUUID
							if self.is_fstab_mountpoint(devpath, old_new_default_mp):
								self.modifyFstabEntry(devpath, old_new_default_mp, mode = "remove")
							devpath = "/dev/disk/by-uuid/" + config.storage_options.default_device.value
							if self.is_fstab_mountpoint(devpath, old_new_default_mp):
								self.modifyFstabEntry(devpath, old_new_default_mp, mode = "remove")
						if cur_default_newmp != "":
							devpath = "/dev/disk/by-uuid/" + oldcurrentDefaultStorageUUID
							if not self.is_fstab_mountpoint(devpath, cur_default_newmp):
								self.modifyFstabEntry(devpath, cur_default_newmp, mode = "add_activated")
			if action == "mount_only":
				if (cur_default_dev is None and new_default_dev is not None):
					if (cur_default is None and new_default is not None):
						if old_new_default_mp != "":
							devpath = "/dev/disk/by-uuid/" + uuid
							if self.is_fstab_mountpoint(devpath, old_new_default_mp):
								self.modifyFstabEntry(devpath, old_new_default_mp, mode = "remove")
							if self.isMount(old_new_default_mp):
								self.unmountPartitionbyMountpoint(old_new_default_mp)
		config.storage_options.save()
		config.storage.save()
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
			description = Util.readFile("/sys" + phys + "/model")
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

	def __addPartition(self, mountpoint, device = None, description = "", force_mounted = False, uuid = None, notify = True):
		if device is not None:
			fsType = self.getBlkidPartitionType("/dev/" + device)
			if fsType is not None and fsType == 'swap':
				force_mounted = False
				notify = False
		p = Partition(self, mountpoint, device, description, force_mounted, uuid)
		self.partitions.append(p)
		if notify:
			self.on_partition_list_change("add", p)
		return p

	def __removePartition(self, p, notify = True):
		self.partitions.remove(p)
		if notify:
			self.on_partition_list_change("remove", p)

	def addMountedPartition(self, device, desc):
		already_mounted = False
		for x in self.partitions[:]:
			if x.mountpoint == device:
				already_mounted = True
		if not already_mounted:
			self.__addPartition(mountpoint = device, description = desc, notify = False)

	def removeMountedPartition(self, mountpoint):
		for x in self.partitions[:]:
			if x.mountpoint == mountpoint:
				self.__removePartition(x)

	def removeMountedPartitionbyDevice(self, device):
		p = self.getPartitionbyDevice(device)
		if p is not None:
			#print "[removeMountedPartitionbyDevice] '%s', '%s', '%s', '%s', '%s'" % (p.mountpoint,p.description,p.device,p.force_mounted,p.uuid)
			self.__removePartition(p)

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
		# try blkid first
		devname = self.__getBlkidAttributeByUuid(uuid, 'DEVNAME')
		if devname:
			return path.basename(devname)
		# fallback to udev symlinks
		if path.exists("/dev/disk/by-uuid/" + uuid):
			return path.basename(path.realpath("/dev/disk/by-uuid/" + uuid))
		return None

	def getPartitionUUID(self, part):
		absPart = '/dev/%s' % part
		# try blkid first
		uuid = self.__getBlkidAttributeByDevice(absPart, 'UUID')
		if uuid:
			return uuid
		# fallback to udev symlinks
		if path.exists("/dev/disk/by-uuid"):
			for uuid in listdir("/dev/disk/by-uuid/"):
				if path.realpath("/dev/disk/by-uuid/%s" % uuid) == absPart:
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
			devpath = path.realpath(partitionPath)
			mountpoint = cfg_uuid['mountpoint'].value
			dev = self.getDeviceNamebyUUID(uuid)
			#print "[mountPartitionbyUUID] for UUID:'%s' - '%s'" % (uuid,mountpoint)

			Util.forceAutofsUmount(dev)
			#remove now obsolete autofs entry
			for x in self.partitions[:]:
				if x is not None and x.mountpoint == self.getAutofsMountpoint(dev):
					self.removeMountedPartitionbyDevice(dev)

			#verify if mountpoint is still mounted from elsewhere (e.g fstab)
			if path.exists(mountpoint) and path.ismount(mountpoint):
				tmppath = self.get_mountdevice(mountpoint)
				if tmppath is not None and tmppath.startswith("/dev/disk/by-uuid/") and tmppath != partitionPath: #probably different device mounted on our mountpoint
					tmpuuid = tmppath.rsplit("/",1)[1]
					if not self.isUUIDpathFsTabMount(tmpuuid, mountpoint) and not self.isPartitionpathFsTabMount(tmpuuid, mountpoint):
						self.unmountPartitionbyMountpoint(mountpoint)

			#verify if our device is still mounted to somewhere else
			tmpmount = self.get_mountpoint(partitionPath) or self.get_mountpoint(devpath)
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
						cmd = "mount /dev/disk/by-uuid/" + uuid + " " + mountpoint
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
							# verify if the current storage device is our default storage and create the movie folder if it is missing
							if uuid == config.storage_options.default_device.value and not path.exists(resolveFilename(SCOPE_HDD)):
								print "default movie folder is missing...trying to create it."
								try:
									makedirs(resolveFilename(SCOPE_HDD))
								except OSError:
									pass
							p = self.getPartitionbyMountpoint(mountpoint)
							if p is not None:
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
						if path.exists("/media/hdd") and path.islink("/media/hdd") and path.realpath("/media/hdd") == config.storage[uuid]["mountpoint"].value:
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
							self.__addPartition(mountpoint = device_mountpoint, description = description, force_mounted = False, device = dev, uuid = uuid)
					if path.exists("/dev/disk/by-uuid/" + uuid):
						self.storageDeviceChanged(uuid)
				else:
					del config.storage[uuid]
					config.storage.save()
		if dev is not None:
			uuid = self.getPartitionUUID(dev)
			if uuid is not None:
				if config.storage.get(uuid, None) is None: #new unconfigured device added
					print "[setupConfigEntries] new device add for '%s' with uuid:'%s'" % (dev, uuid)
					hdd = self.getHDD(dev)
					if hdd is not None:
						hdd_description = hdd.model()
						cap = hdd.capacity()
						if cap:
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
					p = self.getPartitionbyDevice(dev)
					if p is None: # manually add partition entry (e.g. on long spinup times)
						description = self.getDeviceDescription(dev)
						device_mountpoint = self.getAutofsMountpoint(dev)
						self.__addPartition(mountpoint = device_mountpoint, description = description, force_mounted = True, device = dev, uuid = uuid)
					else:  # manually add partition entry (e.g. on default storage device change/initialize)
						if uuid != p.uuid:
							p.uuid = uuid
							p.updatePartitionInfo()
					p = self.getPartitionbyDevice(dev)
					if self.HDDCount() == 1 and not self.HDDEnabledCount(): #only one installed and unconfigured device
						if p is not None and p.fsType != 'swap':
							self.verifyInstalledStorageDevices()
					else:
						self.storageDeviceChanged(uuid)
				else:
					p = self.getPartitionbyDevice(dev)
					device_mountpoint = self.getAutofsMountpoint(dev)
					if config.storage[uuid]['enabled'].value and config.storage[uuid]['mountpoint'].value != "":
						device_mountpoint = config.storage[uuid]['mountpoint'].value
					if p is None: # manually add partition entry (e.g. on default storage device change)
						description = self.getDeviceDescription(dev)
						self.__addPartition(mountpoint = device_mountpoint, description = description, force_mounted = True, device = dev, uuid = uuid)
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
		devpath = path.realpath(uuidPath)
		tmpmount = self.get_mountpoint(uuidPath) or self.get_mountpoint(devpath)
		if tmpmount is not None and tmpmount != "/media/hdd":
			isManualFstabMount = True
		if not isManualFstabMount:
			if not path.islink("/media/hdd") and not self.isPartitionpathFsTabMount(uuid, "/media/hdd"):
				print "configureUuidAsDefault: using found %s as default storage device" % device
				config.storage_options.default_device.value = uuid
				config.storage_options.save()
				cfg_uuid = config.storage.get(uuid, None)
				if cfg_uuid is not None and not cfg_uuid["enabled"].value:
					cfg_uuid["enabled"].value = True
					cfg_uuid["mountpoint"].value = "/media/hdd"
					config.storage.save()
					self.modifyFstabEntry("/dev/disk/by-uuid/" + uuid, "/media/hdd", mode = "add_activated")
					self.storageDeviceChanged(uuid)
				configfile.save()

	def isInitializedByEnigma2(self, hdd):
		isInitializedByEnigma2 = False
		uuid = device = None
		if hdd and hdd.numPartitions() <= 2:
			numPart = hdd.numPartitions()
			device = hdd.device
			if numPart == 1 or numPart == 2:
				device = hdd.device + "1"
			p = self.getPartitionbyDevice(device)
			if p:
				isInitializedByEnigma2 = p.isInitialized
				uuid = p.uuid
			if numPart == 2:
				part2Type = self.getBlkidPartitionType(hdd.partitionPath("2"))
				if part2Type != "swap":
					isInitializedByEnigma2 = False
		return isInitializedByEnigma2,device,uuid

	def verifyInstalledStorageDevices(self):
		print "verifyInstalledStorageDevices"
		if self.HDDCount() == 1 and not self.HDDEnabledCount(): #only one installed and unconfigured device
			hdd = self.hdd[0]
			isInitializedByEnigma2,device,uuid = self.isInitializedByEnigma2(hdd)
			if config.storage_options.default_device.value == "<undefined>" or config.storage_options.default_device.value == uuid:
				if isInitializedByEnigma2:
					self.configureUuidAsDefault(uuid, device)

harddiskmanager = HarddiskManager()
