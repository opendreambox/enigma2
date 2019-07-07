from Components.SetupGuide.BaseStep import SetupListStep
from Plugins.SystemPlugins.InputDeviceManager.InputDeviceAdapterFlasher import InputDeviceAdapterFlasher
from Plugins.SystemPlugins.InputDeviceManager.InputDeviceManagement import InputDeviceManagementBase
from Components.Sources.List import List
from enigma import eManagedInputDevicePtr, eInputDeviceManager

class InputDeviceCheckFirmwareStep(SetupListStep):
	def __init__(self, parent):
		SetupListStep.__init__(self, parent)
		self.session = self.parent.session
		self._options = []

	def prepare(self):
		self.title = _("Flash Bluetooth Receiver Firmware?")
		self.text = _("Your Dreambox bluetooth receiver has no firmware installed.\nInstall the latest firmware now?")
		self._options = [
				(True, _("Yes, install the latest bluetooth receiver firmware")),
				(False,_("No, skip update process")),
			]
		idm = eInputDeviceManager.getInstance()
		return idm.available() and not idm.responding()

	@property
	def listContent(self):
		return self._options

	def buildfunc(self, enabled, entry):
		return [entry,enabled]

	def onOk(self):
		lst = self.parent.list
		if not lst.current or not lst.current[0]:
			return True
		self.session.openWithCallback(self._onAdapterFlashFinished, InputDeviceAdapterFlasher)
		return False

	def _onAdapterFlashFinished(self, result):
		self.parent.nextStep()

class InputDeviceConnectStep(SetupListStep, InputDeviceManagementBase):
	def __init__(self, parent):

		SetupListStep.__init__(self, parent, listStyle="inputdevice")
		InputDeviceManagementBase.__init__(self)
		self._suspended = True
		self._list = List([])
		self.session = self.parent.session

	def prepare(self):
		if not self._dm.available():
			return False
		if (self._getInputDevicesCount() < 1):
			# Don't display this step if no input device is found yet:
			# infrared only devices don't need a pairing here
			# bluetooth rcus should've been seen by now since this isn't the first step of the SetupGuide. So if the list is empty, the user doesn't need to pair a device.
			# if we get another device in the future which could be discovered later or only on demand, we need to change this behavior.
			return False
		self._list = self.parent.list
		self.title = _("Input Devices")
		self.text = _("Press Yellow to connect the selected remote control.")
		self._suspended = False
		return True

	@property
	def listContent(self):
		return self._getInputDevices()

	def buildfunc(self, title, *args):
		return self._inputDeviceBuildFunc(title, *args)

	def buttons(self):
		device = self._currentInputDevice
		yellow = None
		blue = None

		if isinstance(device, eManagedInputDevicePtr) and device.connected():
			blue = _("Disconnect")
			text = _("Press Blue to disconnect the selected remote control.")
			if self._dm.hasFeature(eInputDeviceManager.FEATURE_UNCONNECTED_KEYPRESS) and len(self._devices) > 1:
				text = "%s\n%s" %(_("Please pickup the remote control you want to connect and press any number key on it to select it in the list.\n"), text)
			self.parent.text = text
		else:
			if isinstance(device, eManagedInputDevicePtr):
				yellow = _("Connect")
				text = _("Press Yellow to connect the selected remote control.")
				if self._dm.hasFeature(eInputDeviceManager.FEATURE_UNCONNECTED_KEYPRESS) and len(self._devices) > 1:
					text = "%s\n%s" %(_("Please pickup the remote control you want to connect and press any number key on it to select it in the list.\n"), text)
				self.parent.text = text
		return [None, None, yellow, blue]

	def onSelectionChanged(self):
		self.parent.checkButtons()

	def yellow(self):
		if self._currentInputDevice and not self._currentInputDevice.connected():
			self._connectDevice(self._currentInputDevice)

	def blue(self):
		if self._currentInputDevice and self._currentInputDevice.connected():
			self._disconnectDevice(self._currentInputDevice)

	def onOk(self):
		self._suspended = True
		self._list = List([])
		return True

	def cancel(self):
		self.onOk()

	def _devicesChanged(self, *args):
		if self._suspended:
			return
		self._list.list = self.listContent
		self.parent.updateSummary()
