from InputDeviceManagement import InputDeviceManagementBase
from enigma import eManagedInputDevicePtr

from InputDeviceAdapterFlasher import InputDeviceAdapterFlasher
from Tools.Log import Log

class InputDeviceWizardBase(InputDeviceManagementBase):
	firstRun = False
	checkConnectedDevice = False

	def __init__(self):
		InputDeviceManagementBase.__init__(self)
		self.addLanguageUpdateCallback(self.__updateStates)
		self._list = self["list"]
		self._list.onSelectionChanged.append(self.__selChanged)
		self._pendingPin = self["state"]

	def _reload(self):
		# TODO
		# Wizard calls showHideList with "hide" when list is empty on step start, maybe we should fix it there?
		# for now we work around that issue here!
		self.showHideList("list", show=True)
		InputDeviceManagementBase._reload(self)

	def __isCurrentStep(self):
		return self.isCurrentStepID("inputdevices")

	def _setList(self):
		self._reload()

	def _devicesChanged(self, *args):
		Log.w("%s" %(self.__isCurrentStep(),))
		if self.__isCurrentStep():
			self._reload()

	def yellow(self):
		if self.__isCurrentStep():
			device = self._currentInputDevice
			if device:
				self._dm.disconnectDevice(device)

	def __selChanged(self):
		self.__updateStates()

	def __updateStates(self):
		if not self.__isCurrentStep():
			return
		self["state_label"].setText(_("PIN:"))
		device = self._currentInputDevice
		if isinstance(device, eManagedInputDevicePtr) and device.connected():
			self["button_yellow_text"].setText(_("Disconnect"))
			self["text"].setText(_("Please pickup the device you want to connect and press any key on it to select it in the list.\nEnter the assigned PIN code to connect it."))
		else:
			self["button_yellow_text"].setText("")
			if isinstance(device, eManagedInputDevicePtr):
				pin = self._getPin(device)
				self["text"].setText(_("Please pickup the device you want to connect and press any key on it to select it in the list.\n\nEnter %s on the currently selected remote to connect it.") %(pin,))


	def _onUnboundRemoteKeyPressed(self, address, key):
		if self.__isCurrentStep():
			return InputDeviceManagementBase._onUnboundRemoteKeyPressed(self, address, key)

	def flashInputDeviceAdapterFirmware(self):
		self._foreignScreenInstancePrepare()
		self.session.openWithCallback(self._onAdapterFlashFinished, InputDeviceAdapterFlasher)

	def _onAdapterFlashFinished(self, result):
		Log.w("%s" %(result))
		self._foreignScreenInstanceFinished()

