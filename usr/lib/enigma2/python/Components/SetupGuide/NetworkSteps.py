from Components.SetupGuide.BaseStep import SetupConfigStep, SetupListStep
from Plugins.SystemPlugins.NetworkManager.NetworkConfig import NetworkConfigGeneral
from enigma import eNetworkManager
from Components.Sources.List import List
from Tools.Log import Log

class NetworkTechnologyStep(SetupConfigStep, NetworkConfigGeneral):
	def __init__(self, parent):
		SetupConfigStep.__init__(self, parent)
		NetworkConfigGeneral.__init__(self)
		self._nm_conn = []
		self._tech_conn = []
		self._services = List([])

	def prepare(self):
		self._nm = eNetworkManager.getInstance()
		if self._nm.online():
			Log.w("Network is already online! Skipping!")
			return False
		self.title = _("Network technologies")
		self.text = _("Please select one or more network technologies that should be used to connect your Dreambox to a Network and/or the Internet.\n\nYou may want to plug in USB Networking devices now (if you want to use any).")
		self._nm_conn = [
				self._nm.technologiesChanged.connect(self._technologiesChanged),
				self._nm.stateChanged.connect(self._servicesChanged),
				self._nm.servicesChanged.connect(self._servicesChanged),
			]
		self._tech_conn = []
		self._services = self.parent.list
		return True

	@property
	def configContent(self):
		return self.getTechnologyConfig()

	def onOk(self):
		self._nm_conn = []
		self._tech_conn = []
		self._services = List([])
		return True

	def _technologiesChanged(self):
		self.parent.configList.list = self.configContent

class NetworkServicesStep(SetupListStep, NetworkConfigGeneral):
	def __init__(self, parent):
		SetupListStep.__init__(self, parent, listStyle="networkservice")
		NetworkConfigGeneral.__init__(self)
		self._nm_conn = []
		self._tech_conn = []
		self._services = List([])

	def prepare(self):
		self._nm = eNetworkManager.getInstance()
		if self._nm.online():
			return False
		self.title = _("Network services")
		self.text = _("Please select the network service(s) you want to connect your Dreambox to.\nIt may take a few moments before wireless networks show up in the list below!")
		self._nm_conn = [
				self._nm.technologiesChanged.connect(self._technologiesChanged),
				self._nm.stateChanged.connect(self._servicesChanged),
				self._nm.servicesChanged.connect(self._servicesChanged),
			]
		self._tech_conn = []
		self._services = self.parent.list
		return True

	@property
	def listContent(self):
		return self.getServiceList()

	def buttons(self):
		service = self._currentService
		green = ""
		if service:
			if not service.state() in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
				green = _("Disconnect")
			else:
				green = _("Connect")
		return [None, green, _("Rescan"), None]

	def _servicesChanged(self, *args):
		self.parent.list.list = self.listContent

	def buildfunc(self, path, *args):
		instance = args[0]
		return self._buildListEntry(path, instance)

	def onSelectionChanged(self):
		self.parent.checkButtons()

	def green(self):
		service = self._currentService
		if service:
			state = service.state()
			if state in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
				service.requestDisconnect()
				service.requestConnect()
				service.setAutoConnect(True)
			else:
				service.requestDisconnect()

	def yellow(self):
		self._rescan()

	def onOk(self):
		self._nm_conn = []
		self._tech_conn = []
		self._services = List([])

		return True
