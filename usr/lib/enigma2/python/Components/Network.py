from enigma import eNetworkManager, eNetworkService
from Components.config import config, ConfigSubsection, ConfigBoolean
from Tools.Log import Log

config.network = ConfigSubsection()
config.network.wol_enabled = ConfigBoolean(default=False)

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
		if eNetworkService.KEY_NETMASK in self._data:
			return self._data.get(eNetworkService.KEY_NETMASK, self.default)
		else:
			prefix = self._data.get(eNetworkService.KEY_PREFIX_LENGTH, chr(64)).strip()
			if len(prefix) == 1:
				prefix = ord(prefix)
			else:
				Log.w("INVALID PREFIX '%s' - defaulting to 64" %(prefix,))
				prefix = 64
			return prefix
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
				if key not in adapters or service.state() not in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
					adapters[key] = iface
		return adapters

iNetworkInfo = NetworkInfo()
