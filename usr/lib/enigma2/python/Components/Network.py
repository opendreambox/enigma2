from enigma import eNetworkManager, eNetworkService

class NetworkData(object):
	def __init__(self, data):
		self._data = dict(data)

	def getData(self):
		return self._data
	data = property(getData)

class IpData(NetworkData):
	def __init__(self, data, default="0.0.0.0"):
		NetworkData.__init__(self, data)
		self.default = default

	def getMethod(self):
		return self._data.get(eNetworkService.KEY_METHOD, "off")
	method = property(getMethod)

	def getAddress(self):
		return self._data.get(eNetworkService.KEY_ADDRESS, self.default)
	address = property(getAddress)

	def getNetmask(self):
		if self._data.has_key(eNetworkService.KEY_NETMASK):
			return self._data.get(eNetworkService.KEY_NETMASK, self.default)
		else:
			return ord( self._data.get(eNetworkService.KEY_PREFIX_LENGTH, chr(1)) )
	netmask = property(getNetmask)

	def getGateway(self):
		return self._data.get(eNetworkService.KEY_GATEWAY, self.default)
	gateway = property(getGateway)

class EthernetData(NetworkData):
	def __init__(self, data):
		NetworkData.__init__(self, data)

	def getInterface(self):
		return self._data.get(eNetworkService.KEY_INTERFACE, _("n/a"))
	interface = property(getInterface)

	def getMacAddress(self):
		return self._data.get(eNetworkService.KEY_ADDRESS, "00:00:00:00:00:00")
	mac = property(getMacAddress)

class NetworkInterface(object):
	def __init__(self, service):
		self._ethernet = EthernetData(service.ethernet())
		self._ipv4 = IpData(service.ipv4())
		self._ipv6 = IpData(service.ipv6(), default="::")

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
		return self.isOnline()

	def isOnline(self):
		return self._manager.online()

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
