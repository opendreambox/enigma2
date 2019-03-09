from enigma import eInputDeviceManager
from Plugins.Plugin import PluginDescriptor
from Tools.Notifications import AddNotificationWithCallback
from Screens.MessageBox import MessageBox
from Components.config import config
from Tools.Directories import createDir
from Tools.Log import Log
import time

from InputDeviceManagement import InputDeviceManagement
from InputDeviceAdapterFlasher import InputDeviceUpdateChecker, InputDeviceAdapterFlasher

global inputDeviceWatcher
inputDeviceWatcher = None

class InputDeviceWatcher(object):
	BATTERY_LOG_DIR = "/var/lib/enigma2"

	def __init__(self, session):
		self.session = session
		self._updateChecker = InputDeviceUpdateChecker()
		self._updateChecker.onUpdateAvailable.append(self._onUpdateAvailable)
		self._updateChecker.check()
		self._dm = eInputDeviceManager.getInstance()
		self.__deviceListChanged_conn = self._dm.deviceListChanged.connect(self._onDeviceListChanged)
		self.__deviceStateChanged_conn = self._dm.deviceStateChanged.connect(self._onDeviceStateChanged)
		self._batteryStates = {}
		logdir = "/tmp"
		if createDir(self.BATTERY_LOG_DIR):
			logdir = self.BATTERY_LOG_DIR
		self._batteryLogFile = "%s/battery.dat" %(logdir,)
		self._onDeviceListChanged()

	def _onDeviceStateChanged(self, address, state):
		old = self._batteryStates.get(address, 0)
		device = self._dm.getDevice(address)
		if device.ready():
			new = device.batteryLevel()
			if old != device.batteryLevel():
				if config.inputDevices.settings.logBattery.value:
					Log.i("%s\t%s%% Battery" %(address, device.batteryLevel()))
					try:
						with open(self._batteryLogFile, "a") as f:
							f.write("%s %s %s\n" %(address, int(time.time()), new ))
					except Exception as e:
						Log.w(e)
				self._batteryStates[address] = device.batteryLevel()

	def _onDeviceListChanged(self):
		if config.misc.firstrun.value: #Wizard will run!
			return
		if not config.inputDevices.settings.firstDevice.value:
			return
		devices = self._dm.getAvailableDevices();
		if devices:
			config.inputDevices.settings.firstDevice.value = False
			config.inputDevices.settings.save()

			for device in devices:
				if device.ready():
					return
			AddNotificationWithCallback(self._onDiscoveryAnswer, MessageBox, _("A new bluetooth remote has been discovered. Connect now?"), type=MessageBox.TYPE_YESNO, windowTitle=_("New Bluetooth Remote"))

	def _onDiscoveryAnswer(self, answer):
		if answer:
			self.session.open(InputDeviceManagement)

	def _onUpdateAvailable(self):
		AddNotificationWithCallback(self._onUpdateAnswer, MessageBox, _("There is a new firmware for your bluetooth remote reciver available. Update now?"), type=MessageBox.TYPE_YESNO, windowTitle=_("New Bluetooth Remote"))

	def _onUpdateAnswer(self, answer):
		if answer:
			self.session.open(InputDeviceAdapterFlasher)

def sessionStart(reason, session, *args, **kwargs):
	global inputDeviceWatcher
	inputDeviceWatcher = InputDeviceWatcher(session)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Input Device Autosetup"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionStart)]
