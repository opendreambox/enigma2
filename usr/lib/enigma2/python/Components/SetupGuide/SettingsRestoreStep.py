from Components.SetupGuide.BaseStep import SetupListStep
from Plugins.SystemPlugins.SoftwareManager.ImageWizard import checkConfigBackup
from Plugins.SystemPlugins.SoftwareManager.BackupRestore import RestoreScreen

class SettingsRestoreStep(SetupListStep):
	def __init__(self, parent):
		SetupListStep.__init__(self, parent)
		self._backupPath = None
		self._options = []

	def prepare(self):
		self._backupPath = checkConfigBackup()
		self.title = _("Restore")
		self.text = _("A settings backup has been found.\nDo you want to restore your settings now?\nNOTE: Enigma2 will restart automatically after restoring your settings.")
		self._options = [
			(True, _("Yes, restore the settings now")),
			(False,_("No, continue without restoring")),
		]
		return self._backupPath is not None

	@property
	def listContent(self):
		return self._options

	def buildfunc(self, enabled, entry):
		return [entry,enabled]

	def onOk(self):
		lst = self.parent.list
		if not lst.current or not lst.current[0]:
			return True
		self.parent.session.openWithCallback(self._onRestoreFinished, RestoreScreen, runRestore=True)
		return False

	def _onRestoreFinished(self, success):
		if not success:
			self.parent.nextStep()
