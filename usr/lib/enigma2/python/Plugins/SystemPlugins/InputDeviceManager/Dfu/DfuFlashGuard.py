from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.Progress import Progress
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.Directories import SCOPE_RCU_FIRMWARE, resolveFilename

from enigma import eInputDeviceDfuFlasher, DFU_BATTERY_MIN

from .DfuFlash import DfuFileset, DfuFlash

from os.path import dirname

class DfuLog(Screen):
	IS_DIALOG = True

	skin = """<screen name="DfuLog" position="center,120" size="820,520">
			<widget name="log" position="10,10" size="800,500" halign="left" valign="top" font="Regular;22"/>
		</screen>"""

	def __init__(self, session, text):
		Screen.__init__(self, session, windowTitle=_("DFU Log"))
		self._log = Label(text)
		self["log"] = self._log

		self["actions"] = ActionMap(["OkCancelActions"],
			actions={
				"ok" : self.close,
				"cancel" : self.close,
			})

	def _getText(self):
		return self._log.text

	def _setText(self, text):
		self._log.text = text

	text = property(_getText, _setText)

class DfuFlashGuard(Screen):
	IS_DIALOG = True

	skin = """<screen name="DfuFlashGuard" position="center,center" size="620,340" title="DFU Firmware Upgrade">
		<widget name="log" position="10,5" size="540,30" halign="right" valign="center" font="Regular;18"/>
		<ePixmap pixmap="skin_default/icons/info.png" position="555,5" size="60,30"/>
		<widget name="text" position="10,30" size="600,220" font="Regular;24" halign="center" valign="center"/>
		<widget name="bytes" position="10,260" size="600,30" font="Regular;22" halign="left" />
		<widget source="progress" render="Progress" position="0,300" size="620,40" zPosition="1" borderWidth="1"/>
	</screen>"""

	def __init__(self, session, device):
		Screen.__init__(self, session, windowTitle=_("DFU Firmware Upgrade"))
		self._device = device
		self._flasher = DfuFlash(self._onEvent, self._onUploadProgress)

		self._label = Label()
		self["text"] = self._label
		self._bytes = Label()
		self["bytes"] = self._bytes
		self._progress = Progress(range=1000)
		self["progress"] = self._progress
		self["log"] = Label(_("Show Full Log"))

		self._actionMap = ActionMap(["OkCancelActions"],
		actions={
			"ok" : self._close,
			"cancel" : self._close,
		})
		self["actions"] = self._actionMap
		self["logAction"] = ActionMap(["TimerEditActions"],
			actions={
				"log" : self._showLog,
			}
		)
		self._actionMap.setEnabled(False)
		self._section = None
		self._initialProgress = True

		self._log = ""
		self._logScreen = None
		self.onFirstExecBegin.append(self.load)

	def _close(self):
		self.close(True)

	def _enableActions(self):
		self._actionMap.setEnabled(True)

	def _onEvent(self, event, value):
		if event == DfuFlash.EVT_DFU_NA:
			self._onDfuNotAvailable()
		elif event == DfuFlash.EVT_DFU_TIMEOUT:
			self._onDfuTimeout()
		elif event == DfuFlash.EVT_DFU_LOWBAT:
			self._onDfuBatteryLow()
		elif event == DfuFlash.EVT_DFU_AVAILABLE:
			self._onDfuAvailable()
		elif event == DfuFlash.EVT_DFU_CONNECTED:
			self._onDfuConnected()
		elif event == DfuFlash.EVT_FLASH_BEGIN:
			self._onFlashBegin(value)
		elif event == DfuFlash.EVT_FLASH_REJECTED:
			self._onFlashRejected(event)
		elif event == DfuFlash.EVT_INIT_FAIL:
			self._onInitError(event)
		elif event == DfuFlash.EVT_DFU_CONTROL_ERROR:
			self._onWriteControlError(event)
		elif event == DfuFlash.EVT_UPLOAD_BEGIN:
			self._onUploadBegin(value)
		elif event == DfuFlash.EVT_UPLOAD_RESULT:
			self._onUploadResult(value)
		elif event == DfuFlash.EVT_BL_SKIPPED:
			self._onBlSkipped()
		elif event == DfuFlash.EVT_REBOOT_AWAIT:
			self._onRebootAwait()
		elif event == DfuFlash.EVT_FINISHED:
			self._onFinished()

	def _appendText(self, text, newline=True):
		if newline:
			self._label.text = text
			self._log = "{0}\n{1}".format(self._log, text)
		else:
			self._label.text = "{0} {1}".format(self._label.text, text)
			self._log = "{0} {1}".format(self._log, text)
		if self._logScreen:
			self._logScreen.text = self._log

	def _showLog(self):
		self._logScreen = self.session.openWithCallback(self._onLogClosed, DfuLog, self._log)

	def _onLogClosed(self):
		self._logScreen = None

	def load(self):
		types = self._flasher.load(resolveFilename(SCOPE_RCU_FIRMWARE))
		self._onLoadFinished(types)
		if self._device.checkVersion(1,5) < 0 and types & DfuFileset.TYPE_SYSTEM:
			self._warnBootloaderNoControl()
			return
		self._flash()

	def _flash(self):
		if self._flasher.update(self._device):
			self._appendText(_("Initializing DFU Mode..."))
		else:
			self._enableActions()

	def _warnBootloaderNoControl(self):
		txt = _("Your remote is likely to become unresponsive during the first half of the update Process.\nAfter the Bootloader/System has been updated you will regain control for the rest of this and all future updates.")
		self.session.openWithCallback(self._onBootloaderNoControlAck, MessageBox, txt, type=MessageBox.TYPE_INFO, windowTitle=_("Please read carefully!"))

	def _onBootloaderNoControlAck(self, response):
		self._flash()

	def _onDfuNotAvailable(self):
		self._appendText(_("DFU is not available on this device. A firmware update may be required upfront!"))
		self._enableActions()

	def _onDfuTimeout(self):
		self._flasher = None
		self._appendText(_("DFU device did not show up. Cancelling!\nYou may want to try this again!"))
		self._enableActions()

	def _onDfuBatteryLow(self):
		text = _("Device battery level of {0}% is too low.\nIt's required to be at least {1}%!".format(self._device.batteryLevel(), DFU_BATTERY_MIN))
		self.session.openWithCallback(self._onErrorAck, MessageBox,text, type=MessageBox.TYPE_ERROR, windowTitle=_("Upload rejected!"))

	def _onLoadFinished(self, types):
		t = []
		if types & DfuFileset.TYPE_SYSTEM:
			t.append(_("SYSTEM"))
		if types & DfuFileset.TYPE_APP:
			t.append(_("APPLICATION"))
		self._appendText(_("Package Content: {0}").format(",".join(t)))

	def _typeDescription(self, setType=None):
		if setType == None:
			setType = self._flasher.currentSetType
		return _("System") if setType == DfuFileset.TYPE_SYSTEM else _("Application")

	def _sectionDescription(self, section=None):
		section = section or self._section
		if not section:
			return "UNKNOWN"
		return _("BIN") if section == eInputDeviceDfuFlasher.DFU_FIRMWARE_TYPE_BIN else _("DAT")

	def _onDfuAvailable(self):
		self._appendText(_("DFU device ready!"))

	def _onDfuConnected(self):
		self._appendText(_("DFU device connected!"))

	def _onFlashBegin(self, type):
		typeDesc = self._typeDescription().upper()
		self._appendText(_("Starting DFU Upload of {0}").format(typeDesc))

	def _addBatteryRebootHintText(self, text):
		return "{0}\n\n{1}".format(text, _("You can remove the batteries of your remote for a short moment to reboot it!"))

	def _onFlashRejected(self, event):
		self._enableActions()
		text = self._addBatteryRebootHintText(_("The firmware files are invalid or corrupted!\nThe upload was rejected by the device!"))
		self._appendText(text)
		self.session.openWithCallback(self._onErrorAck, MessageBox,text, type=MessageBox.TYPE_ERROR, windowTitle=_("Upload rejected!"))

	def _onInitError(self, event):
		self._enableActions()
		text = self._addBatteryRebootHintText(_("Update initialization failed!\n"))
		self._appendText(text)
		self.session.openWithCallback(self._onErrorAck, MessageBox,text, type=MessageBox.TYPE_ERROR, windowTitle=_("Init failed!"))

	def _onWriteControlError(self, event):
		self._enableActions()
		text = self._addBatteryRebootHintText(_("Control write failed! Code %i\n") %(event,))
		self._appendText(text)
		self.session.openWithCallback(self._onErrorAck, MessageBox, text, type=MessageBox.TYPE_ERROR, windowTitle=_("Control write failed!"))

	def _onErrorAck(self, result=None):
		self.close(False)

	def _onUploadBegin(self, section):
		if section == self._section:
			return
		self._section = section
		self._initialProgress = True
		s = self._sectionDescription(section)
		setType = self._typeDescription()
		self._appendText("Uploading {0} {1}...".format(setType,s))

	def _onUploadProgress(self, currentBytes, totalBytes):
		self._initialProgress = False
		self._progress.value = int( float(currentBytes * 100.0 / totalBytes * 1.0) * 10 )
		self._bytes.text = _("Uploaded {0} of {1} bytes").format(currentBytes, totalBytes)

	def _onUploadResult(self, success):
		text = _("OK") if success else _("ERROR")
		self._appendText(text.format(self._sectionDescription()), newline=False)
		self._section = None
		self._initialProgress = True
		if not success:
			self._enableActions()

	def _onRebootAwait(self):
		self._appendText(_("Waiting for device reboot..."))

	def _onBlSkipped(self):
		self._appendText(_("System rejected! (Already the latest version?!). Skipping!"))

	def _onFinished(self):
		self._enableActions()
		self._appendText(_("\nYour remote control will restart in a few seconds (up to 40)!\n\nPress [OK] or [EXIT] to close this window once it finished booting!"))
