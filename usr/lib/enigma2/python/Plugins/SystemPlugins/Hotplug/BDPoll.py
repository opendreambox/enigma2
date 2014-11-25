from Components.Harddisk import harddiskmanager
from enigma import ePythonMessagePump, eTimer
from threading import Thread, Semaphore, Lock
import os
os.O_CLOEXEC = 02000000
import errno
import fcntl

class ThreadQueue(object):
	def __init__(self):
		self.__list = [ ]
		self.__lock = Lock()

	def push(self, val):
		list = self.__list
		lock = self.__lock
		lock.acquire()
		list.append(val)
		lock.release()

	def pop(self):
		list = self.__list
		lock = self.__lock
		lock.acquire()
		ret = list[0]
		del list[0]
		lock.release()
		return ret

class BDPoll(Thread):
	CHECK_INTERVAL = 2000
	MSG_MEDIUM_REMOVED = 1
	MSG_MEDIUM_INSERTED = 2
	MSG_POLL_FINISHED = 4

	CDROM_DRIVE_STATUS = 0x5326
	CDSL_CURRENT = ((int)(~0>>1))
	CDS_NO_INFO = 0
	CDS_NO_DISC = 1
	CDS_TRAY_OPEN = 2
	CDS_DRIVE_NOT_READY = 3
	CDS_DISC_OK = 4
	ENOMEDIUM = 159
	IOC_NRBITS = 8
	IOC_NRSHIFT = 0
	IOC_TYPESHIFT = (IOC_NRSHIFT+IOC_NRBITS)
	BLKRRPART = ((0x12<<IOC_TYPESHIFT) | (95<<IOC_NRSHIFT))

	def __init__(self):
		Thread.__init__(self)
		self.__sema = Semaphore(0)
		self.__lock = Lock()
		self.running = False
		self.devices_to_poll = { }
		self.messages = ThreadQueue()
		self.checkTimer = eTimer()
		self.checkTimer_conn = self.checkTimer.timeout.connect(self.timeout)
		self.checkTimer.start(BDPoll.CHECK_INTERVAL, True)
		self.mp = ePythonMessagePump()
		self.mp_recv_msg_conn = self.mp.recv_msg.connect(self.gotThreadMsg)
		self.start()

	def gotThreadMsg(self, msg):
		msg = self.messages.pop()
		if msg[0] == BDPoll.MSG_MEDIUM_REMOVED:
			print "MSG_MEDIUM_REMOVED"
			harddiskmanager.removeHotplugPartition(msg[1])
		elif msg[0] == BDPoll.MSG_MEDIUM_INSERTED:
			print "MSG_MEDIUM_INSERTED"
			harddiskmanager.addHotplugPartition(msg[1])
		elif msg[0] == BDPoll.MSG_POLL_FINISHED:
			self.checkTimer.start(BDPoll.CHECK_INTERVAL, True)

	def timeout(self):
		self.__sema.release() # start bdpoll loop in thread

	def is_mounted(self, dev):
		mounts = file('/proc/mounts').read()
		return mounts.find(dev) != -1

	def run(self):
		sema = self.__sema
		lock = self.__lock
		messages = self.messages
		mp = self.mp
		self.running = True
		while self.running:
			sema.acquire()
			self.__lock.acquire()
			devices_to_poll = self.devices_to_poll.items()
			self.__lock.release()
			devices_to_poll_processed = [ ]
			for device, state in devices_to_poll:
				got_media = False
				is_cdrom, prev_media_state = state
				if is_cdrom:
					try:
						fd = os.open("/dev/" + device, os.O_RDONLY | os.O_NONBLOCK | os.O_EXCL | os.O_CLOEXEC)
					except OSError, err:
						if err.errno == errno.EBUSY:
							print "open cdrom exclusive failed:",
							if not self.is_mounted(device):
								print "not mounted"
								continue
							try:
								print "mounted... try non exclusive"
								fd = os.open("/dev/" + device, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
							except OSError, err:
								print "open cdrom not exclusive failed", os.strerror(err.errno)
								continue
					#here the fs must be valid!
					try:
						ret = fcntl.ioctl(fd, BDPoll.CDROM_DRIVE_STATUS, BDPoll.CDSL_CURRENT)
					except IOError, err:
						print "ioctl CDROM_DRIVE_STATUS failed", os.strerror(err.errno)
					else:
						if ret in (BDPoll.CDS_NO_INFO, BDPoll.CDS_NO_DISC, BDPoll.CDS_TRAY_OPEN, BDPoll.CDS_DRIVE_NOT_READY):
							pass
						elif ret == BDPoll.CDS_DISC_OK:
							#todo new kernels support events to userspace event on media change
							#but not 2.6.18.... see hotplug-ng bdpoll.c
							got_media = True
					#catch exception if the cdrom was removed and we dont have a valid fs anymore
					try:
						os.close(fd)
					except (IOError, OSError), err:
						print "close cdrom failed", os.strerror(err.errno)
				else:
					try:
						fd = os.open("/dev/" + device, os.O_RDONLY | os.O_CLOEXEC)
					except OSError, err:
						if err.errno == BDPoll.ENOMEDIUM:
							pass
						else:
							print "open non cdrom failed", os.strerror(err.errno)
							continue
					else:
						got_media = True
						os.close(fd)
				if prev_media_state:
					if not got_media:
						print "media removal detected on", device
						try:
							fd = os.open("/dev/" + device, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
						except OSError, err:
							print "open device for blkrrpart ioctl failed", os.strerror(err.errno)
						else:
							try:
								fcntl.ioctl(fd, BDPoll.BLKRRPART)
							except IOError, err:
								print "ioctl BLKRRPART failed", os.strerror(err.errno)
							os.close(fd)
				else:
					if got_media:
						print "media insertion detected on", device
				devices_to_poll_processed.append((device, is_cdrom, got_media))
			self.__lock.acquire()
			for device, is_cdrom, state in devices_to_poll_processed:
				old_state = self.devices_to_poll.get(device)
				if old_state is not None and old_state[1] != state:
					msg = state and BDPoll.MSG_MEDIUM_INSERTED or BDPoll.MSG_MEDIUM_REMOVED
					self.devices_to_poll[device] = (is_cdrom, state)
					messages.push((msg, device))
					mp.send(0)

			self.__lock.release()
			messages.push((self.MSG_POLL_FINISHED,))
			mp.send(0)

	def addDevice(self, device, is_cdrom, inserted):
		self.__lock.acquire()
		if device in self.devices_to_poll:
			print "device", device, "already in bdpoll"
		else:
			print "add device", device, "to bdpoll current state:",
			if inserted:
				print "medium inserted"
			else:
				print "medium removed"
			self.devices_to_poll[device] = (is_cdrom, inserted)
		self.__lock.release()

	def removeDevice(self, device):
		self.__lock.acquire()
		if device in self.devices_to_poll:
			print "device", device, "removed from bdpoll"
			del self.devices_to_poll[device]
		else:
			print "try to del not exist device", device, "from bdpoll"
		self.__lock.release()
