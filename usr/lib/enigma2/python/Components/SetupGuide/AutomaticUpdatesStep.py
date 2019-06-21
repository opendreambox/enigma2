from Components.SetupGuide.BaseStep import SetupConfigStep
from Components.config import config, ConfigDateTime, getConfigListEntry

class AutomaticUpdatesStep(SetupConfigStep):
	def __init__(self, parent):
		SetupConfigStep.__init__(self, parent)
		try: #SoftwareManager may not be installed
			config.plugins.updatechecker.interval.addNotifier(self._onChange, initial_call=False)
		except:
			pass

	def prepare(self):
		#check for SotwareManager
		try:
			from Plugins.SystemPlugins.SoftwareManager.UpdateCheck import UPDATE_CHECK_NEVER
		except:
			return False
		self.title = _("Automatic Updates")
		self.text = _("Your dreambox can automatically search for available updates. Set the options you prefer here.")
		return True

	def onOk(self):
		config.plugins.updatechecker.save()
		config.plugins.updatechecker.interval.removeNotifier(self._onChange)
		return True

	def _onChange(self, *args):
		from twisted.internet import reactor
		reactor.callLater(0, self._recreate)

	def _recreate(self):
		self.parent.configList.list = self.configContent

	@property
	def configContent(self):
		from Plugins.SystemPlugins.SoftwareManager.UpdateCheck import updateCheck, UPDATE_CHECK_NEVER
		configNextCheck = ConfigDateTime(updateCheck.nextCheck, "%Y-%m-%d %H:%M:%S")
		configNextCheck.enabled = False
		config.plugins.updatechecker.lastcheck.enabled = False
		l = [
				getConfigListEntry(_("Check on every boot"), config.plugins.updatechecker.checkonboot),
				getConfigListEntry(_("Automatically check for new updates"), config.plugins.updatechecker.interval),
			]
		if config.plugins.updatechecker.interval.value != UPDATE_CHECK_NEVER:
			l.extend([
				getConfigListEntry(_("Last check"), config.plugins.updatechecker.lastcheck),
				getConfigListEntry(_("Next check"), configNextCheck),
			])
		return l
