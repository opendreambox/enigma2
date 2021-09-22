from enigma import eInputDeviceManager, eInputDeviceDfuFlasher as Dfu, eTimer
from Tools.Log import Log

import json

from twisted.internet import reactor

from Tools.Directories import createDir, fileExists, pathExists

class DfuFileset(object):
	TYPE_SYSTEM 	= 1
	TYPE_APP 		= 1 << 1
	SECTION_INIT	= 1 << 4
	SECTION_DATA	= 1 << 5

	def __init__(self, type, dat, bin):
		self._type = type
		self._dat = dat
		self._bin = bin

	@property
	def type(self):
		return self._type

	@property
	def dat(self):
		return self._dat

	@property
	def bin(self):
		return self._bin


	def __str__(self):
		return "<{0} instance at{1}> :: {2} - bin: {3}, data: {4}".format(self.__class__.__name__, id(self), self.type, self.dat, self.bin)

class DfuFlash(object):
	EVT_DFU_LOWBAT		= 1 << 9
	EVT_DFU_NA			= 1 << 10
	EVT_DFU_TIMEOUT		= 1 << 11
	EVT_DFU_AVAILABLE	= 1 << 12
	EVT_DFU_CONNECTED 	= 1 << 13
	EVT_FLASH_BEGIN		= 1 << 14
	EVT_FLASH_REJECTED	= 1 << 15
	EVT_INIT_FAIL		= 1 << 16
	EVT_UPLOAD_BEGIN	= 1 << 17
	EVT_UPLOAD_PROGRESS = 1 << 18
	EVT_UPLOAD_RESULT	= 1 << 19
	EVT_BL_SKIPPED		= 1 << 20
	EVT_REBOOT_AWAIT	= 1 << 21
	EVT_FINISHED		= 1 << 31

	UPLOAD_RESULT_ERROR = 0
	UPLOAD_RESULT_SUCCESS = 1

	FILENAME_MANIFEST = "manifest.json"

	def __init__(self, eventCallback, progressCallback):
		self._dm = eInputDeviceManager.getInstance()
		self.__deviceStateChanged_conn = None
		self._address = None
		self._dfuAddress = None
		self._section = None
		self._isRebooting = False

		self._dfuTimer = eTimer()
		self.__dfuTimer_conn = self._dfuTimer.timeout.connect(self._dfuTimeout)
		self._sets = []
		self._currentSet = None
		self._onEvent = eventCallback
		self._onProgress = progressCallback

	@property
	def currentSetType(self):
		return self._currentSet and self._currentSet.type or None

	def event(self, event, value=None):
		self._onEvent(event, value)

	def load(self, targetdir):
		manifest = "{0}/{1}".format(targetdir, self.FILENAME_MANIFEST)
		if not pathExists(manifest):
			return False
		mf = None
		with open(manifest) as m:
			mf = json.load(m)
		if not "manifest" in mf:
			return False

		mf = mf["manifest"]
		types = 0
		if "softdevice_bootloader" in mf:
			sdBlDat = "{0}/{1}".format(targetdir, mf["softdevice_bootloader"]["dat_file"])
			sdBlBin = "{0}/{1}".format(targetdir, mf["softdevice_bootloader"]["bin_file"])
			if fileExists(sdBlDat) and fileExists(sdBlBin):
				fileset = DfuFileset(DfuFileset.TYPE_SYSTEM, sdBlDat, sdBlBin)
				self._sets.append(fileset)
				types |= fileset.type
				Log.w("{0}".format(fileset))
			else:
				Log.w("SD+BL files indicated by manifest but not found!")
				return -1

		if "application" in mf:
			appDat = "{0}/{1}".format(targetdir, mf["application"]["dat_file"])
			appBin = "{0}/{1}".format(targetdir, mf["application"]["bin_file"])
			if fileExists(appDat) and fileExists(appBin):
				fileset = DfuFileset(DfuFileset.TYPE_APP, appDat, appBin)
				self._sets.append(fileset)
				types |= fileset.type
				Log.w("{0}".format(fileset))
			else:
				Log.w("Application files indicated by manifest but not found!")
				return -2

		return types

	def _rebootAwait(self):
		Log.w()
		self.__deviceStateChanged_conn = self._dm.deviceStateChanged.connect(self._onDeviceStateChanged)
		self._isRebooting = True
		self.event(self.EVT_REBOOT_AWAIT)

	def update(self, device):
		if not len(self._sets):
			return False

		self.__deviceStateChanged_conn = self._dm.deviceStateChanged.connect(self._onDeviceStateChanged)
		if (device.isDfu()):
			self._dfuAddress = device.address()
			mac = self._dfuAddress.split(":")
			mac[-1] = "{0:02x}".format(int(mac[-1], 16) - 1)
			mac = ":".join(mac)
			self._address = mac
			self._onDeviceStateChanged(device.address(), device.state())
			return False

		self._address = device.address()
		mac = self._address.split(":")
		mac[-1] = "{0:02x}".format(int(mac[-1], 16) + 1)
		mac = ":".join(mac)
		self._dfuAddress = mac
		return self._dfuEnable(device)

	def _deviceDfu(self, device):
		self._dfuTimer.startLongTimer(20)
		return device.dfu()

	def _dfuEnable(self, device):
		Log.w("Enabling DFU. Expecting DFU mac: {0}".format(self._dfuAddress))
		res = self._deviceDfu(device)
		if res != Dfu.DFU_SUCCESS:
			Log.w("DFU enable failed with code '{0}'".format(res))
			evt = self.EVT_DFU_NA if res == Dfu.DFU_ERROR else self.EVT_DFU_LOWBAT
			self.event(evt)
			return False
		return True

	def _dfuTimeout(self):
		self.__deviceStateChanged_conn = None
		self.event(self.EVT_DFU_TIMEOUT)

	def _onDeviceRebootFinished(self):
		d = self._dm.getDevice(self._address)
		if not d.connected():
			Log.w("Connecting!")
			d.connect()
		else:
			Log.w("Waiting for DFU mac: {0}".format(self._dfuAddress))
			self._isRebooting = False
			reactor.callLater(4, self._onDeviceRebootDfu)

	def _onDeviceRebootDfu(self):
		Log.w()
		device = self._dm.getDevice(self._address)
		self._deviceDfu(device)

	def _onDeviceStateChanged(self, address, state):
		Log.w("{0} # {1}".format(address, self._dfuAddress))
		if self._isRebooting and address.lower() == self._address.lower():
			self._onDeviceRebootFinished()
			return
		if address.lower() != self._dfuAddress.lower():
			return
		Log.w("Device appeared with DFU MAC! ({0})".format(address))
		self._dfuTimer.stop()
		device = self._dm.getDevice(address)
		if not device.connected():
			self.event(self.EVT_DFU_AVAILABLE)
			Log.w("Connecting device...")
			device.connect()
			return
		Log.w("Device connected with DFU MAC! ({0})".format(address))
		self.event(self.EVT_DFU_CONNECTED)
		self.__dfuEvent_conn = self._dm.dfuEvent.connect(self._onDfuEvent)
		self.__dfuProgress_conn = self._dm.dfuProgress.connect(self._onDfuProgress)
		self.__deviceStateChanged_conn = None
		self._flashNextSet(device)

	def _flashNextSet(self, device):
		self._section = None
		if not device:
			self.event(self.EVT_UPLOAD_RESULT, False)
			return
		self._currentSet = self._sets.pop(0)
		if device.dfuFlash(self._currentSet.dat, self._currentSet.bin) == Dfu.DFU_SUCCESS:
			self.event(self.EVT_FLASH_BEGIN, self._currentSet.type)
		else:
			self.event(self.EVT_FLASH_REJECTED, self._currentSet.type)

	def _onDfuExecuteError(self):
		if self.currentSetType == DfuFileset.TYPE_SYSTEM and self._section == Dfu.DFU_FIRMWARE_TYPE_DAT:
			device = self._dm.getDevice(self._dfuAddress)
			self.event(self.EVT_BL_SKIPPED)
			self._flashNextSet(device)
			return
		self.event(self.EVT_UPLOAD_RESULT, self.UPLOAD_RESULT_ERROR)

	def _onDfuEvent(self, event, value):
		Log.d("{0} :: {1}".format(event, value))
		if event in (
					Dfu.DFU_EVT_FILE_INVALID,
					Dfu.DFU_EVT_FILE_READ_ERROR
				):
			self.event(self.EVT_FLASH_REJECTED)
		if event in (
				Dfu.DFU_EVT_ENABLE_NOTIFY_ERROR,
				Dfu.DFU_EVT_OBJECT_CREATE_ERROR,
				Dfu.DFU_EVT_OBJECT_READ_ERROR):
			self.event(self.EVT_INIT_FAIL, event)

		elif event == Dfu.DFU_EVT_OBJECT_CREATE_SUCCESS:
			self.event(self.EVT_UPLOAD_BEGIN, value) # value is the section (data or bin)
			self._section = value

		elif event == Dfu.DFU_EVT_COMMAND_ERROR:
			if value == Dfu.DFU_CMD_EXECUTE:
				self._onDfuExecuteError()

		elif event == Dfu.DFU_EVT_EXECUTE_SUCCESS:
			self.event(self.EVT_UPLOAD_RESULT, self.UPLOAD_RESULT_SUCCESS)
			if value == Dfu.DFU_FIRMWARE_TYPE_BIN:
				if not len(self._sets):
					self.event(self.EVT_FINISHED)
				else:
					self._rebootAwait()
		elif event == Dfu.DFU_EVT_UPLOAD_ERROR:
			self.event(self.EVT_UPLOAD_RESULT, self.UPLOAD_RESULT_ERROR)

	def _onDfuProgress(self, currentBytes, totalBytes):
		self._onProgress(currentBytes, totalBytes)
