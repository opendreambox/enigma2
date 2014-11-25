from enigma import eNetworkManager, eNetworkService

class NetworkData(object):
	def __init__(self, data):
		self._data = dict(data)

	def getData(self):
		return self._data
	data = property(getData)

class IpData(NetworkData):
	def __init__(self, data):
		NetworkData.__init__(self, data)

	def getMethod(self):
		return self._data.get(eNetworkService.KEY_METHOD, _("N/A"))
	method = property(getMethod)

	def getAddress(self):
		return self._data.get(eNetworkService.KEY_ADDRESS, _("N/A"))
	address = property(getAddress)

	def getNetmask(self):
		return self._data.get(eNetworkService.KEY_NETMASK, _("N/A"))
	netmask = property(getNetmask)

	def getGateway(self):
		return self._data.get(eNetworkService.KEY_GATEWAY, _("N/A"))
	gateway = property(getGateway)

class EthernetData(NetworkData):
	def __init__(self, data):
		NetworkData.__init__(self, data)

	def getInterface(self):
		return self._data.get(eNetworkService.KEY_INTERFACE, _("N/A"))
	interface = property(getInterface)

	def getMacAddress(self):
		return self._data.get(eNetworkService.KEY_ADDRESS, _("N/A"))
	mac = property(getMacAddress)

class NetworkInterface(object):
	def __init__(self, service):
		self._ethernet = EthernetData(service.ethernet())
		self._ipv4 = IpData(service.ipv4())
		self._ipv6 = IpData(service.ipv6())

	def getEthernet(self):
		return self._ethernet
	ethernet = property(getEthernet)

	def getIpv4(self):
		return self._ipv4
	ipv4 = property(getIpv4)

	def getIpv6(self):
		return self._ipv6
	ipv6 = property(getIpv6)

class NetworkInfo(object):
	def __init__(self):
		self._manager = eNetworkManager.getInstance()
		self._stateChangeConn = self._manager.stateChanged.connect(self._onStateChanged)
		self.onStateChanged = []

	def _onStateChanged(self, newstate):
		for fnc in self.onStateChanged:
			fnc(newstate)

	def getState(self):
		return self._manager.state()

	def isConnected(self):
		state = self._manager.state()
		return state == eNetworkManager.STATE_READY or state == eNetworkManager.STATE_ONLINE

	def isOnline(self):
		return self._manager.state() == eNetworkManager.STATE_ONLINE

	def getConfiguredInterfaces(self):
		services = self._manager.getServices()
		adapters = {}
		for service in services:
			if service:
				iface = NetworkInterface(service)
				key = iface.ethernet.interface
				if not key in adapters.keys() or not service.state() in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
					adapters[key] = iface
		return adapters

iNetworkInfo = NetworkInfo()
