
from Plugins.SystemPlugins.InputDeviceManager.InputDeviceAdapterFlasher import InputDeviceAdapterFlasher
from Screens.MessageBox import MessageBox
from Tools.DreamboxHardware import getFPVersion
from enigma import quitMainloop


class InputDeviceUpdateHandlerBase(object):#
	def __init__(self):
		self._numTries = 0

	def _fpUpdateText(self):
		self._numTries = 0
		updateText = _("There is a new firmware for your frontprocessor available. Update now?")
		if getFPVersion() <= 1.12:
			updateText += _("\n\n!!! ATTENTION !!!\nDue to major firmware changes you can not downgrade to images dated before this one anymore!\nThis update is mandatory and should not be skipped!\n!!! ATTENTION !!!!")
		return updateText

	def _onUpdateAnswer(self, answer):
		if answer:
			self._numTries += 1
			self.session.openWithCallback(self._onUpdateFinished, InputDeviceAdapterFlasher)

	def _onUpdateFinished(self, result):
		if result:
			numTries = 0
			self.session.openWithCallback(self._onForcedReboot, MessageBox, _("The Frontprocessor was updated successfully!\nYour Dreambox will now be restarted!"), type=MessageBox.TYPE_INFO, timeout=10, title=_("Success"), windowTitle=_("Frontprocessor Update"))
		else:
			if self._numTries < 2:
				self.session.openWithCallback(self._onRetryFpUpdate, MessageBox, _("Frontprocessor update failed\nRetrying!"), type=MessageBox.TYPE_ERROR, timeout=10, title=_("RETRYING!"), windowTitle=_("ERROR! Frontprocessor Update"))
			else:
				self.session.open(MessageBox, _("Frontprocessor update failed multiple times!\nPlease contact the support!\nYou can try executing\n'flash-nrf52 --program --verify --start'\non a console manually"), type=MessageBox.TYPE_ERROR, title=_("ERROR!"), windowTitle=_("ERROR! Frontprocessor Update"))

	def _onRetryFpUpdate(self, *args):
		self._onUpdateAnswer(True)

	def _onForcedReboot(self, *args):
		quitMainloop(3)
