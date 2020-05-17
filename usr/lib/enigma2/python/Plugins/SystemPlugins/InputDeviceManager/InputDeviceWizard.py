from __future__ import absolute_import
from .InputDeviceManagement import InputDeviceManagementBase
from enigma import eManagedInputDevicePtr, eInputDeviceManager

from .InputDeviceAdapterFlasher import InputDeviceAdapterFlasher
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
		if self.__isCurrentStep():
			self._reload()

	def yellow(self):
		if self.__isCurrentStep():
			device = self._currentInputDevice
			if not device:
				return
			if device.connected():
				self._disconnectDevice(device)
			else:
				self._connectDevice(device)

	def __selChanged(self):
		self.__updateStates()

	def __updateStates(self):
		if not self.__isCurrentStep():
			return
		self["state_label"].setText("")
		device = self._currentInputDevice
		if isinstance(device, eManagedInputDevicePtr) and device.connected():
			self["button_yellow_text"].setText(_("Disconnect"))
			text = _("Press Yellow to disconnect the selected remote control.")
			if self._dm.hasFeature(eInputDeviceManager.FEATURE_UNCONNECTED_KEYPRESS) and len(self._devices) > 1:
				text = "%s\n%s" %(_("Please pickup the remote control you want to connect and press any number key on it to select it in the list.\n"), text)
			self["text"].setText(text)
		else:
			self["button_yellow_text"].setText("")
			if isinstance(device, eManagedInputDevicePtr):
				self["button_yellow_text"].setText(_("Connect"))
				text = _("Press Yellow to connect the selected remote control.")
				if self._dm.hasFeature(eInputDeviceManager.FEATURE_UNCONNECTED_KEYPRESS) and len(self._devices) > 1:
					text = "%s\n%s" %(_("Please pickup the remote control you want to connect and press any number key on it to select it in the list.\n"), text)
				self["text"].setText(text)


	def _onUnboundRemoteKeyPressed(self, address, key):
		if self.__isCurrentStep():
			return InputDeviceManagementBase._onUnboundRemoteKeyPressed(self, address, key)

	def flashInputDeviceAdapterFirmware(self):
		self._foreignScreenInstancePrepare()
		self.session.openWithCallback(self._onAdapterFlashFinished, InputDeviceAdapterFlasher)

	def _onAdapterFlashFinished(self, result):
		Log.w("%s" %(result))
		self._foreignScreenInstanceFinished()

