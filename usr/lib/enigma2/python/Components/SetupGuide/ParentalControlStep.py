from Components.config import config
from Components.SetupGuide.BaseStep import SetupListStep
from Screens.ParentalControlSetup import ParentalControlChangePin
from Tools.Log import Log

class ParentalControlStep(SetupListStep):
	def __init__(self, parent):
		SetupListStep.__init__(self, parent)
		self._options = []

	def prepare(self):
		self.title = _("Parental Control")
		self.text = _("Do you want to enable the parental control feature on your dreambox?")
		self._options = [
			(False, _("Disable Parental Control")),
			(True, _("Enable Parental Control"))
		]
		return True

	@property
	def listContent(self):
		return self._options

	def buildfunc(self, enabled, entry):
		return [entry,enabled]

	def onOk(self):
		lst = self.parent.list
		if not lst.current or not lst.current[0]:
			return True

		config.ParentalControl.configured.value = True
		config.ParentalControl.configured.save()
		self.parent.session.openWithCallback(self._onPinSet, ParentalControlChangePin, config.ParentalControl.servicepin[0], _("parental control pin"))
		return False

	def _onPinSet(self, result=False):
		if config.ParentalControl.setuppin.value == -1:
			config.ParentalControl.setuppinactive.value = False
		else:
			config.ParentalControl.setuppinactive.value = True
		config.ParentalControl.setuppinactive.save()
		config.ParentalControl.servicepinactive.value = True
		config.ParentalControl.servicepinactive.save()
		config.ParentalControl.setuppin.value = config.ParentalControl.servicepin[0].value
		config.ParentalControl.setuppin.save()
		self.parent.nextStep()
