from enigma import eConsoleAppContainer, eEnv, eInputDeviceManager
from Tools.Log import Log
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists
from Components.config import config

class InputDeviceAdapterFlasher(MessageBox):
	FLASHER_BINARY = eEnv.resolve("${sbindir}/flash-nrf52")

	def __init__(self, session):
		MessageBox.__init__(self, session, _("Please wait! We are about to start..."), title=_("Flashing Adapter Firmware"), type=MessageBox.TYPE_WARNING, windowTitle=_("Bluetooth Receiver Firmware"))
		self.skinName = "MessageBox"
		self._console = eConsoleAppContainer()
		self.__onDataConn = self._console.dataAvail.connect(self._onData)
		self.__onAppClosedConn = self._console.appClosed.connect(self._onAppClosed)
		self._dm = eInputDeviceManager.getInstance()
		self._success = False
		self._flasherMissing = False

		self.onFirstExecBegin.append(self._check)
		self.onClose.append(self.__onClose)

		self._flashFirmware()

	def _check(self):
		if self._flasherMissing:
			self.session.openWithCallback(self.close, MessageBox, _("Firmware flasher is missing or broken! Cancelled!"), type=MessageBox.TYPE_ERROR)
			self.close(False)

	def __onClose(self):
		self._dm.start()

	def _onData(self, data):
		Log.i(data)
		pre = _("Working...")
		if data.strip().startswith("flashing"):
			pre = _("Flashing firmware...")
		elif data.strip().startswith("verifying"):
			pre = _("Verifying firmware...")

		if pre and config.usage.setup_level.index >= 2:
			text = "%s\n\n%s" %(pre, data)
		else:
			text = pre
		self["Text"].setText(text)
		self["text"].setText(text)
		if data.find("success:") >= 0:
			self._success = True

	def _onAppClosed(self, data):
		self.close(self._success)

	def _flashFirmware(self):
		if not fileExists(self.FLASHER_BINARY):
			self._flasherMissing = True
			return
		self._dm.stop()
		res = self._console.execute("%s --program --force --verify --start" %(self.FLASHER_BINARY))
		Log.w("%s" %(res,))
