from enigma import eNetworkManager
from Screens.WizardLanguage import WizardLanguage
from NetworkConfig import NetworkConfigGeneral, ServiceIPConfiguration, ServiceNSConfiguration


class NetworkWizardNew(NetworkConfigGeneral):
	def __init__(self):
		NetworkConfigGeneral.__init__(self)

		self._services = self["list"]

		self.__updateStateText()
		self.showState(False)

		self.addLanguageUpdateCallback(self.__updateNetworkLanguageTexts)

		self._ipconfig = None
		self._nsconfig = None

	def __updateNetworkLanguageTexts(self):
		self.__updateStateText()
		self.checkButtons()

	def __updateStateText(self):
		self["state_label"].setText(_("Connection State:"))
		self["state"].setText(NetworkConfigGeneral.translateState(self._nm.state()))

	def _buildListEntry(self, *args, **kwargs):
		return (args[1], args[0])

	def green(self):
		service = self["list"].getCurrent()
		if service:
			service = service[1]
			state = service.state()
			if state in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
				service.requestDisconnect()
				service.requestConnect()
				service.setAutoConnect(True)
			else:
				service.requestDisconnect()

	def yellow(self):
		if self.isCurrentStepID("services"):
			self._rescan()

	def checkButtons(self):
		if self.isCurrentStepID("services"):
			self["button_yellow_text"].setText(_("Rescan"))
			service = self._currentService
			if service:
				if not service.state() in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
					self["button_green_text"].setText(_("Disconnect"))
				else:
					self["button_green_text"].setText(_("Connect"))

	def selChanged(self):
		WizardLanguage.selChanged(self)
		self.checkButtons()

	def _technologiesChanged(self):
		if self.isCurrentStepID("technologies"):
			self["config"].list = self.getTechnologyConfig()

	def _techPoweredChanged(self, powered):
		if self.isCurrentStepID("technologies"):
			self["config"].list = self.getTechnologyConfig()

	def technologiesSet(self):
		pass

	def _servicesChanged(self, *args):
		self["state"].setText( NetworkConfigGeneral.translateState( self._nm.state() ) )
		if self.isCurrentStepID("services"):
			self["list"].updateList( self.getServiceList() )
			self.checkButtons()

	def ipConfigurationRequired(self):
		return not self.isOnline()

	def isNetworkConnected(self):
		return self.isOnline()

	def getAddressConfig(self):
		self._ipconfig = ServiceIPConfiguration(self._nm.getServices()[0])
		self._ipconfig.reload()
		return self._ipconfig.getList()

	def _reloadAddressConfig(self):
		self["config"].list = self._ipconfig.getList()

	def saveAddressConfig(self):
		self._ipconfig.save()

	def isOnline(self):
		return self._nm.online()

	def getNameserverConfig(self):
		self._nsconfig = ServiceNSConfiguration( self._nm.getServices()[0] )

	def saveNameserverConfig(self):
		self._nsconfig.save()
