from Components.SetupGuide.BaseStep import SetupConfigStep
from Components.config import config, getConfigListEntry
from Components.Timezones import Timezones, timezones

class TimezoneStep(SetupConfigStep):
	def __init__(self, parent):
		SetupConfigStep.__init__(self, parent)

	def prepare(self):
		self.title = _("Timezone")
		self.text = _("Please select your timezone!")
		return True

	@property
	def configContent(self):
		return [
			getConfigListEntry(_("Region"), config.timezone.region),
			getConfigListEntry(_("Zone"), config.timezone.zone)
		]

	@property
	def selectedIndex(self):
		return 0

	def onOk(self):
		config.timezone.version.value = Timezones.CONFIG_VERSION
		return SetupConfigStep.onOk(self)
