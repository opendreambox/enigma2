from enigma import eInputDeviceManager
from Plugins.Plugin import PluginDescriptor
from Tools.Notifications import AddNotificationWithCallback
from Screens.MessageBox import MessageBox
from Components.config import config
from InputDeviceManagement import InputDeviceManagement
from Tools.Log import Log

global inputDeviceWatcher
inputDeviceWatcher = None
class InputDeviceWatcher(object):
	def __init__(self, session):
		self.session = session
		self._dm = eInputDeviceManager.getInstance()
		self.__deviceListChanged_conn = self._dm.deviceListChanged.connect(self._onDeviceListChanged)
		self._onDeviceListChanged()

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
			AddNotificationWithCallback(self._onDiscoveryAnswered, MessageBox, _("A new bluetooth remote has been discovered. Connect now?"), type=MessageBox.TYPE_YESNO, windowTitle=_("New Bluetooth Remote"))

	def _onDiscoveryAnswered(self, answer):
		if answer:
			self.session.open(InputDeviceManagement)

def sessionStart(reason, session, *args, **kwargs):
	global inputDeviceWatcher
	inputDeviceWatcher = InputDeviceWatcher(session)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Input Device Autosetup"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionStart)]
