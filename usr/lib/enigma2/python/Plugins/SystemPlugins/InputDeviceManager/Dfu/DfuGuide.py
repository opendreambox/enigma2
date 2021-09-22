from __future__ import absolute_import
from Tools.Directories import SCOPE_RCU_FIRMWARE, fileExists, resolveFilename

from enigma import eManagedInputDevicePtr

from Components.config import config
from Components.SetupGuide.BaseStep import SetupTextStep, SetupListStep
from Components.Sources.List import List
from Screens.MessageBox import MessageBox

from ..InputDeviceManagement import InputDeviceManagementBase

from .DfuFlashGuard import DfuFlashGuard

class DfuWelcomeStep(SetupTextStep):
	def __init__(self, parent):
		SetupTextStep.__init__(self, parent)

	def prepare(self):
		self.title = _("Welcome...")
		self.text = _("to the Remote Control Firmware Update Assistant.\nWe will now guide you through the remote control firmware update procedure!\n\nLet's begin!\n\n[Press OK]")
		return True

class DfuUpdateStep(SetupListStep, InputDeviceManagementBase):
	VERSION_MAP = {
		5 	: (1,0),
		6 	: (1,3),
		7 	: (1,4),
		8 	: (1,5),
		9 	: (1,6),
		10	: (1,7),
	}

	def mapAppVersion(self, code):
		if code < 6:
			code = 5
		return self.VERSION_MAP.get(code, (100+code,0))

	def _getFwVersion(self, dat):
		if not fileExists(dat):
			return False
		with open(dat, 'rb') as f:
			f.seek(0x0a)
			return ord(f.read(1))

	def getAppVersion(self):
		appdat = "{0}/nrf52832_xxaa.dat".format(resolveFilename(SCOPE_RCU_FIRMWARE))
		return self.mapAppVersion(self._getFwVersion(appdat))

	def getBootloaderVersion(self):
		sdbldat = "{0}/sd_bl.dat".format(resolveFilename(SCOPE_RCU_FIRMWARE))
		return self._getFwVersion(sdbldat)

	def __init__(self, parent):
		InputDeviceManagementBase.__init__(self)
		SetupListStep.__init__(self, parent, listStyle="inputdevice")

		self._suspended = True
		self._list = List([])
		self.session = self.parent.session
		self._flashGuard = None

	def prepare(self):
		if not self._dm.available():
			return False
		self._list = self.parent.list
		self.title = _("Available Remotes")
		self.text = _("Press OK to finish the Remote Control Firmware Update Assistant.")
		self._suspended = False
		self._disableListFeedback()
		return True

	@property
	def listContent(self):
		self._refresh()
		return self._getInputDevices()

	def buildfunc(self, title, device):
		bound = ""
		if device.bound():
			bound = _("bound")
		# A device may be connected but not yet bound right after binding has started!
		elif device.connected():
			bound = _("...")
		name = device.name() or device.shortName()
		name = _(name) if name else _("DM Remote")
		if device.isDfu():
			name = _("DFU - DM Remote")
		return (
			name,
			"{0}".format(device.version()),
			device.address(),
			bound,
			_("connected") if device.connected() else _("disconnected")
		)

	def buttons(self):
		device = self._currentInputDevice
		yellow = None
		blue = None

		text = ""
		if isinstance(device, eManagedInputDevicePtr) and (device.connected() or device.isDfu()):
			if self._updateAvailable():
				blue = _("Update")
			else:
				blue = _("Force Update")
			version = self.getAppVersion()
			text = _("Press Blue to update the firmware of the selected remote control to application version {0} and bootloader version {1}").format(".".join([str(x) for x in version]), self.getBootloaderVersion())
		else:
			if isinstance(device, eManagedInputDevicePtr):
				yellow = _("Connect")
				text = _("Firmware updates can only be applied to connected remotes!\nPress Yellow to connect the selected remote control.")

		self.parent.text = "{0}\n\n{1}".format(text, _("Press OK to finish the Remote Control Firmware Update Assistant."))
		return [None, None, yellow, blue]

	def onSelectionChanged(self):
		self.parent.checkButtons()
		if not self._flashGuard:
			self._highlight()

	def yellow(self):
		if self._currentInputDevice and not self._currentInputDevice.connected():
			self._connectDevice(self._currentInputDevice)

	def _updateAvailable(self):
		return self._currentInputDevice.checkVersion(*self.getAppVersion()) < 0

	def blue(self):
		if self._currentInputDevice and (self._currentInputDevice.connected() or self._currentInputDevice.isDfu()):
			if self._currentInputDevice.isDfu():
				 self._currentInputDevice.disconnect()
			if self._updateAvailable():
				self._startFlashing()
			else:
				self.session.openWithCallback(
						self._onNoUpgradeWarning,
						MessageBox,
						_("The selected remote is already running the latest firmware!\nUpdate anyways?"),
						type=MessageBox.TYPE_YESNO,
						windowTitle=_("Force Update"),
						default=False
					)

	def _startFlashing(self):
		self._suspended = True
		self._flashGuard = self.session.openWithCallback(self._onGuardClosed, DfuFlashGuard, self._currentInputDevice)

	def _onGuardClosed(self, result):
		self._suspended = False
		self._flashGuard = None
		self._refresh()
		if result:
			self.parent.nextStep()

	def _onNoUpgradeWarning(self, response):
		if response and self._currentInputDevice and self._currentInputDevice.connected():
			self._startFlashing()

	def onOk(self):
		self._suspended = True
		self._restoreListFeedback()
		self._list = List([])
		return True

	def cancel(self):
		self.onOk()

	def _devicesChanged(self, *args):
		if self._suspended:
			return
		self._reload()
		self.parent.updateSummary()

class DfuFinishStep(SetupTextStep):
	def __init__(self, parent):
		SetupTextStep.__init__(self, parent)

	def prepare(self):
		self.title = _("Thank you...")
		self.text = _("for using the Remote Control Firmware Update Assistant.\n\n[Press OK to close]")
		return True
