from __future__ import absolute_import
from enigma import eInputDeviceManager
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Log import Log

from .InputDeviceAdapterFlasher import InputDeviceAdapterFlasher, InputDeviceUpdateChecker


class InputDeviceManagementBase(object):
	def __init__(self):
		try:
			self["pin"] = StaticText() #unused dummy
		except:
			pass
		self._devices = []
		self._list = List([], enableWrapAround=True, buildfunc=self._inputDeviceBuildFunc)

		self._dm = eInputDeviceManager.getInstance()

		self.__deviceListChanged_conn = self._dm.deviceListChanged.connect(self._devicesChanged)
		self.__deviceStateChanged_conn = self._dm.deviceStateChanged.connect(self._devicesChanged)
		self.__unboundRemoteKeyPressed_conn = self._dm.unboundRemoteKeyPressed.connect(self._onUnboundRemoteKeyPressed)
		self._dm.rescan()

	def responding(self):
		return self._dm.responding()

	def available(self):
		return self._dm.available()

	def _getCurrentInputDevice(self):
		return self._list.getCurrent() and self._list.getCurrent()[1]

	_currentInputDevice = property(_getCurrentInputDevice)

	def _reload(self):
		index = self._list.index
		if index < 0:
			index = 0
		self._devices = self._getInputDevices()
		self._list.list = self._devices
		if len(self._devices) > index:
			self._list.index = index

	def _getInputDevicesCount(self):
		return len(self._devices)

	def _getInputDevices(self):
		items = self._dm.getAvailableDevices()
		devices = []
		for d in items:
			devices.append((d.address(),d))
		return devices

	def _inputDeviceBuildFunc(self, title, device):
		bound = ""
		if device.bound():
			bound = _("bound")
		# A device may be connected but not yet bound right after binding has started!
		elif device.connected():
			bound = _("...")
		return (
			device.shortName() or _("DM RCU"),
			"%s dBm" %(int(device.rssi()),),
			device.address(),
			bound,
			_("connected") if device.connected() else _("disconnected")
		)

	def _devicesChanged(self, *args):
		pass

	def _connectDevice(self, device):
		if not device:
			return
		self.session.toastManager.showToast(_("Connecting to %s") %(device.address(),))
		self._dm.connectDevice(device)

	def _disconnectDevice(self, device):
		if device and device.connected():
			self._dm.disconnectDevice(device)

	def _onUnboundRemoteKeyPressed(self, address, key):
		pass

class InputDeviceManagement(Screen, InputDeviceManagementBase):
	skin = """
	<screen name="InputDeviceManagement" position="center,120" size="820,520" title="Input Devices">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" zPosition="1"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" zPosition="1"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" zPosition="1"/>
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" zPosition="1"/>
		<widget name="key_red" position="10,5" size="200,40" zPosition="2" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="key_green" position="210,5" size="200,40" zPosition="2" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="410,5" size="200,40" zPosition="2" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="610,5" size="200,40" zPosition="2" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="list" render="Listbox" position="10,60" size="800,340" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template":[
						MultiContentEntryText(pos = (5, 0), size = (590, 24), font=0, flags = RT_HALIGN_LEFT, text = 0), #device name
						MultiContentEntryText(pos = (600, 0), size = (200, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 4), #connection state
						MultiContentEntryText(pos = (300, 0), size = (190, 50), font=0, flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER, text = 3), #pairing state
						MultiContentEntryText(pos = (5, 30), size = (200, 18), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 2), #device address
						MultiContentEntryText(pos = (600, 30), size = (200, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_TOP, text = 1), #rssi
					],
				"itemHeight": 50,
				"fonts": [gFont("Regular", 22), gFont("Regular", 16)]
				}
			</convert>
		</widget>
		<widget source="description" render="Label" position="10,410" size="800,100" font="Regular;22" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session, windowTitle=_("Input devices"))
		InputDeviceManagementBase.__init__(self)
		self["description"] = StaticText("")
		self["list"] = self._list
		self["inputActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		actions={
			"ok" : self._onOk,
			"cancel" : self.close,
			"blue" : self._dm.rescan
		})

		self["key_red"] = Label()
		self["key_green"] = Label()
		self["key_yellow"] = Label()
		self["key_blue"] = Label(_("Rescan"))
		self._updateChecker = InputDeviceUpdateChecker()
		self._updateChecker.onUpdateAvailable.append(self._onUpdateAvailable)
		self._updateChecker.check()
		self._list.onSelectionChanged.append(self.__onSelectionChanged)
		self._devices = []
		self.__onSelectionChanged()
		self._reload()
		self.onFirstExecBegin.append(self._checkAdapter)

	def _onUpdateAvailable(self):
		self.session.openWithCallback(
			self._flashInputDeviceAdapterFirmware,
			MessageBox,
			_("There is a new firmware for your bluetooth remote reciver available. Update now?"),
			type=MessageBox.TYPE_YESNO,
			windowTitle=_("Update Bluetooth Receiver Firmware?"))


	def _checkAdapter(self):
		if self.available() and not self.responding():
			self.session.openWithCallback(
				self._flashInputDeviceAdapterFirmware,
				MessageBox,
				_("Your Dreambox bluetooth receiver has no firmware installed.\nInstall the latest firmware now?"),
				type=MessageBox.TYPE_YESNO,
				windowTitle=_("Flash Bluetooth Receiver Firmware?"))
			return

	def __onSelectionChanged(self):
		if not self.available():
			self["description"].text = _("No dreambox bluetooth receiver detected! Sorry!")
			return
		text = ""
		if self._currentInputDevice and self._currentInputDevice.connected():
			text = _("Press OK to disconnect")
		elif self._currentInputDevice:
			text = _("Press OK to connect the selected remote control.")
			if self._dm.hasFeature(eInputDeviceManager.FEATURE_UNCONNECTED_KEYPRESS) and len(self._devices) > 1:
				text = "%s\n%s" %(("Please pickup the remote control you want to connect and press any number key on it to select it in the list.\n"), text)
		if text != self["description"].text:
			self["description"].text = text

	def _devicesChanged(self, *args):
		self._reload()

	def _onOk(self):
		device = self._currentInputDevice
		if not device:
			return
		name = device.shortName() or "Dream RCU"
		if device.connected():
			self.session.openWithCallback(self._onDisconnectResult, MessageBox, _("Really disconnect %s (%s)?") %(name, device.address()), windowTitle=_("Disconnect paired remote?"))
		else:
			self.session.openWithCallback(self._onConnectResult, MessageBox, _("Do you really want to connect %s (%s) ") %(name, device.address()), windowTitle=_("Connect new remote?"))

	def _onDisconnectResult(self, result):
		if result:
			self._disconnectDevice(self._currentInputDevice)

	def _onConnectResult(self, result):
		if result:
			self._connectDevice(self._currentInputDevice)

	def _onUnboundRemoteKeyPressed(self, address, key):
		index = 0
		for d in self._devices:
			if d[1].address() == address:
				self._list.index = index
				break
			index += 1

	def _flashInputDeviceAdapterFirmware(self, answer):
		if answer:
			self.session.openWithCallback(self._onAdapterFlashFinished, InputDeviceAdapterFlasher)

	def _onAdapterFlashFinished(self, result):
		if not result:
			self["description"].setText(_("Flashing failed! Adapter has no firmware. Sorry!"))
		Log.w("%s" %(result))
