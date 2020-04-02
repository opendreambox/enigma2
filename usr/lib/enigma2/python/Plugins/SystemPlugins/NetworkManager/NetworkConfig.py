# -*- coding: utf-8 -*-
from enigma import eNetworkManager, eNetworkService, eNetworkServicePtr, StringList

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import getConfigListEntry, ConfigIP, ConfigOnOff, ConfigIP6, ConfigSelection, ConfigInteger,\
	ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Network import NetworkInterface
from Screens.Screen import Screen

from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.Log import Log
from Tools.LoadPixmap import LoadPixmap

from netaddr import IPAddress

def toIP4List(value):
	return [ int(v) for v in str(value).split(".") ]

def toIP4String(cfg):
	return cfg.tostring(cfg.value)

class NetworkConfigGeneral(object):
	@staticmethod
	def translateSecurity(security):
		security_map = {
			"none" : _("None"),
			"wep"  : "WEP",
			"psk"  : "WPA/WPA2",
			"wps"  : "WPS",
			"ieee8021x" : "ieee8021x",
		}
		return security_map.get(security, security.upper())

	@staticmethod
	def translateState(state):
		state_map = {
			"idle" : _("Idle"),
			"failure" : _("Failure"),
			"association" : _("Association"),
			"configuration" : _("Configuration"),
			"disconnect" : _("Disconnect"),
			"online" : _("Connected"),
		}
		return state_map.get(state, state)

	def __init__(self):
		self._nm = eNetworkManager.getInstance()
		self._nm_conn = [
				self._nm.technologiesChanged.connect(self._technologiesChanged),
				self._nm.stateChanged.connect(self._servicesChanged),
				self._nm.servicesChanged.connect(self._servicesChanged),
			]
		self._tech_conn = []
		self._services = List([], enableWrapAround = True)
		self._services.buildfunc = self._buildServiceListEntry

	def _getCurrentService(self):
		service = self._services.getCurrent()
		if service:
			return service[1]
		return None
	_currentService = property(_getCurrentService)

	def _technologiesChanged(self):
		pass

	def _techPoweredChanged(self, powered):
		if powered:
			self._rescan()

	def _setTechPowered(self, cfg):
		tech = cfg.tech
		powered = not tech.powered()
		tech.setPowered(powered)

	def _scanFinished(self, tech):
		pass

	def _rescan(self, tech=None):
		if tech is not None and tech.type() == eNetworkService.TYPE_WIFI and tech.powered():
			Log.i("Triggering rescan for '%s'" %tech.name())
			tech.scan()
			return True

		res = False
		for tech in self._nm.getTechnologies():
			if tech.type() == eNetworkService.TYPE_WIFI and tech.powered():
				Log.i("Triggering rescan for '%s'" %tech.name())
				tech.scan()
				res = True
		return res

	def _removeService(self):
		service = self._currentService
		if isinstance(service, eNetworkServicePtr):
			Log.i("Removing %s" %service.name())
			service.setAutoConnect(False)
			service.remove()

	def getTechnologyConfig(self):
		l = []
		techs = self._nm.getTechnologies()
		self._tech_conn = []
		for tech in techs:
			cfg = ConfigOnOff(default=tech.powered())
			cfg.tech = tech
			cfg.addNotifier(self._setTechPowered, initial_call=False)
			self._tech_conn.append(tech.poweredChanged.connect(self._techPoweredChanged))
			self._tech_conn.append(tech.scanFinished.connect(boundFunction(self._scanFinished, tech)))
			title = "%s (%s)" %(tech.name(), tech.type())
			l.append(getConfigListEntry(title, cfg))
		Log.w(l)
		return l

	def _servicesChanged(self, *args):
		pass

	def getServiceList(self, unified=False):
		l = []
		services = self._nm.getServices()
		techs = self._nm.getTechnologies()
		self._tech_conn = []
		if unified:
			for tech in techs:
				self._tech_conn.append(tech.poweredChanged.connect(self._techPoweredChanged))
				self._tech_conn.append(tech.scanFinished.connect(boundFunction(self._scanFinished, tech)))
				l.append( (tech.path(), tech,) )
				for service in services:
					if service.type() == tech.type():
						l.append( (service.path(), service,) )
		else:
			for service in services:
				l.append( (service.path(), service,) )
		return l

	def _buildListEntry(self, path, instance):
		if isinstance(instance, eNetworkServicePtr):
			return self._buildServiceListEntry(path, instance)
		else:
			return self._buildTechnologyListEntry(path, instance)

	def _buildTechnologyListEntry(self, techpath, tech):
		#Log.i("technology: %s/%s" %(tech.name(), tech.type()))
		enabled = _("on") if tech.powered() else _("off")
		name = tech.name()
		if tech.isScanning():
			name = _("%s - scanning...") %name
		return (tech.path(), None, enabled, None, None, None, name, "")

	def _buildServiceListEntry(self, svcpath, service):
		#Log.i("service: %s/%s/%s" %(service.name(), service.type(), service.strength()))
		strength = ""
		security = ""
		interfacepng = None
		if service.type() == eNetworkService.TYPE_ETHERNET:
			if service.connected():
				interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/network_wired-active.png"))
			else:
				if service.state() != eNetworkManager.STATE_IDLE:
					interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/network_wired.png"))
				else:
					interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/network_wired-inactive.png"))
		elif service.type() == eNetworkService.TYPE_WIFI:
			strength = "%s%s" %(service.strength(), "%")
			for sec in service.security():
				if not security:
					security = NetworkConfigGeneral.translateSecurity(sec)
				else:
					security = "%s, %s" %(security, NetworkConfigGeneral.translateSecurity(sec))
			if service.connected():
				interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/network_wireless-active.png"))
			else:
				if service.state() != eNetworkManager.STATE_IDLE:
					interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/network_wireless.png"))
				else:
					interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/network_wireless-inactive.png"))
		ip = ""
		if service.connected():
			ip = service.ipv4().get(eNetworkService.KEY_ADDRESS, "")
			if not ip:
				ip = service.ipv6().get(eNetworkService.KEY_ADDRESS, "")

		if service.type() == eNetworkService.TYPE_BLUETOOTH:
			if service.connected():
				interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/bluetooth-active.png"))
			else:
				if service.state() != eNetworkManager.STATE_IDLE:
					interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/bluetooth.png"))
				else:
					interfacepng = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/bluetooth-inactive.png"))


		return (service.path(), interfacepng, strength, service.name(), ip, NetworkConfigGeneral.translateState(service.state()), None, security)

class NetworkServiceConfig(Screen, NetworkConfigGeneral):
	def __init__(self, session):
		Screen.__init__(self, session)
		NetworkConfigGeneral.__init__(self)

		self["key_red"] = Label(_("Reset"))
		self["key_green"] = Label(_("Scan"))
		self["key_yellow"] = Label(_("IP"))
		self["key_blue"] = Label(_("DNS"))
		self["hint"] = Label(_("Press OK to connect"))
		self["details_label"] = Label(_("Active connection"))
		self["details"] = Label("")
		self["OkCancelActions"] = ActionMap(["OkCancelActions", "ColorActions", "MenuActions"],
		{
			"menu": self._menu,
			"cancel": self.close,
			"ok" : self._ok,
			"green": self._rescan,
			"red": self._removeService
		}, -3)
		self["ServiceActions"] = ActionMap(["ColorActions"],
		{
			"yellow": self._configIP,
			"blue": self._configDNS,
		}, -2)

		self["list"] = self._services
		self["summary_list"] = StaticText("")
		self._hasWireless = False

		self._services.buildfunc = self._buildListEntry
		self._services.onSelectionChanged.append(self._selectionChanged)

		self._addNotifiers()
		self._createSetup()

		self.onClose.append(self._onClose)
		self.onLayoutFinish.append(self.layoutFinished)

	def _menu(self):
		self.session.open(NetworkTimeserverConfig)

	def _rescan(self):
		if not self._currentService or isinstance(self._currentService, eNetworkServicePtr):
			return
		if self._currentService.type() != eNetworkService.TYPE_WIFI:
			return
		if NetworkConfigGeneral._rescan(self, self._currentService):
			self._createSetup()

	def _scanFinished(self, tech):
		Log.i("finished!")
		self._createSetup()

	def _removeService(self):
		NetworkConfigGeneral._removeService(self)
		self._createSetup()

	def _selectionChanged(self):
		self._checkButtons()
		self._updateSummary()

	def _updateSummary(self):
		text = ""
		service = self._currentService
		if not service:
			self["summary_list"].setText(text)
			return
		if isinstance(service, eNetworkServicePtr):
			text = service.name()
			if service.connected():
				ni = NetworkInterface(service)
				ip = ni.getIpv4()
				if not ip:
					ip = ni.getIpv6()
				if ip:
					ip = ip.address
				else:
					ip = self.translateState(service.state())
				text = "%s\n%s" %(text, ip)
			else:
				text = "%s\n%s" %(text, self.translateState(service.state()))
		else:
			powered = _("On") if service.powered() else _("Off")
			text = "%s - %s" %(service.name(), powered)
		self["summary_list"].setText(text)

	def _checkButtons(self):
		self["hint"].setText("")
		if isinstance(self._currentService, eNetworkServicePtr): #a service
			self["key_green"].hide()
			if self._currentService.connected():
				self["hint"].setText(_("Press OK to disconnect"))
			else:
				self["hint"].setText(_("Press OK to connect"))
			if self._currentService.favorite():
				self["key_red"].show()
			else:
				self["key_red"].hide()
			self["key_yellow"].show()
			self["key_blue"].show()
			self["ServiceActions"].setEnabled(True)
		else: #a technology
			if self._currentService and self._currentService.type() == eNetworkService.TYPE_WIFI:
				self["key_green"].show()
			else:
				self["key_green"].hide()
			self["key_red"].hide()
			if self._currentService:
				if self._currentService.powered():
					self["hint"].setText(_("Press OK to disable"))
				else:
					self["hint"].setText(_("Press OK to enable"))
			else:
				self["hint"].setText("")
			self["key_yellow"].hide()
			self["key_blue"].hide()
			self["ServiceActions"].setEnabled(False)

	def _configChanged(self, *args, **kwargs):
		self._createSetup()

	def _configIP(self):
		service = self._currentService
		if service:
			self.session.open(NetworkServiceIPConfig, service)

	def _configDNS(self):
		service = self._currentService
		if service:
			self.session.open(NetworkServiceNSConfig, service)

	def _technologiesChanged(self):
		self._createSetup()

	def _servicesChanged(self, *args):
		self._createSetup()

	def _addNotifiers(self):
		pass

	def _removeNotifiers(self):
		pass

	def _onClose(self):
		self._removeNotifiers()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def _ok(self):
		item = self._currentService
		if not item:
			return
		if isinstance(item, eNetworkServicePtr):
			state = item.state()
			Log.i(state)
			if state == eNetworkManager.STATE_IDLE or state == eNetworkManager.STATE_FAILURE:
				item.requestDisconnect()
				item.requestConnect()
				item.setAutoConnect(True)
			else:
				item.requestDisconnect()
		else:
			item.setPowered(not item.powered())

	def _createSetup(self):
		self._hasWireless = False
		for tech in self._nm.getTechnologies():
			if tech.type() == eNetworkService.TYPE_WIFI and tech.powered():
				self._hasWireless = True
		self._services.updateList(self.getServiceList(unified=True))
		self._checkButtons()
		self._setDetailText()

	def _setDetailText(self):
		text = ""
		for service in self._nm.getServices():
			if service.connected():
				if text:
					text = "\n\n%s" %(text)

				text = "%s\n\n" %(service.name())
				ni = NetworkInterface(service)

				ip4 = ni.getIpv4()
				ip6 = ni.getIpv6()
				iptext = _("%s IPv%s\n  Address: %s\n  %s: %s\n  Gateway: %s\n\n")
				#IPv4
				if ip4.method != eNetworkService.METHOD_OFF:
					addr = ip4.address
					mask = ip4.netmask
					gw = ip4.gateway
					text = iptext %(
							text,
							4,
							addr,
							_("Netmask"),
							mask,
							gw,
						)
				#IPv6
				if ip6.method != eNetworkService.METHOD_OFF:
					addr = ip6.address
					mask = ip6.netmask
					gw = ip6.gateway
					text = iptext %(
							text,
							6,
							addr,
							_("Prefix length"),
							mask,
							gw,
						)
				ns = self._textFormatIpList( service.nameservers() )
				text = _("%sName server\n%s\n") %(text, ns)
				ts = self._textFormatIpList( service.timeservers() )
				text = _("%s\nTime server\n%s\n") %(text, ts)

				mac = ni.ethernet.mac
				text = ("%s\n" + _("Hardware address") + "\n%s\n") %(text, mac)
				break
		self["details"].setText(text)

	def _textFormatIpList(self, iplist):
		if not iplist:
			return "  %s" %(_("n/a"))
		iplist = "  %s" %("\n  ".join(iplist))
		return iplist

	def _techPoweredChanged(self, powered):
		if powered:
			self._rescan()
		self._createSetup()

	def layoutFinished(self):
		self.setTitle(_("Network Config"))
		self._checkButtons()
		self._updateSummary()

class ServiceBoundConfiguration(object):
	def __init__(self, service):
		self._service = service
		nm = eNetworkManager.getInstance()
		self._svcRemovedConn = nm.serviceRemoved.connect(self.__onServiceRemoved)
		self._isServiceRemoved = False

	def __onServiceRemoved(self, svcpath):
		if svcpath == self._service.path():
			Log.i("Service '%s' removed. Closing..." %svcpath)
			self._isServiceRemoved = True
			#TODO show a messagebox! The user will be VERY confused otherwise!
			self.close()

class ServiceIPConfiguration(object):
	def __init__(self, service):
		self._service = service
		self.onChanged = []
		self.onMethodChanged = []
		method_choices_ip4 = {eNetworkService.METHOD_DHCP : "dhcp", eNetworkService.METHOD_MANUAL : _("manual"), eNetworkService.METHOD_OFF : _("off")}
		#IPv4
		self._config_ip4_method = ConfigSelection(method_choices_ip4, default=eNetworkService.METHOD_DHCP)
		self._config_ip4_address = ConfigIP(default=[0,0,0,0])
		self._config_ip4_mask = ConfigIP(default=[0,0,0,0])
		self._config_ip4_gw = ConfigIP(default=[0,0,0,0])
		#IPv6
		method_choices_ip6 = {eNetworkService.METHOD_AUTO : _("auto"), eNetworkService.METHOD_6TO4 : "6to4", eNetworkService.METHOD_MANUAL : _("manual"), eNetworkService.METHOD_OFF : _("off")}
		choices_privacy_ip6 = {eNetworkService.IPV6_PRIVACY_DISABLED : _("Disabled"), eNetworkService.IPV6_PRIVACY_ENABLED : _("Enabled"), eNetworkService.IPV6_PRIVACY_PREFERRED : _("Preferred")}
		self._config_ip6_method = ConfigSelection(method_choices_ip6, default=eNetworkService.METHOD_DHCP)
		self._config_ip6_address = ConfigIP6()
		self._config_ip6_prefix_length = ConfigInteger(0, limits=(1, 128))
		self._config_ip6_gw = ConfigIP6()
		self._config_ip6_privacy = ConfigSelection(choices_privacy_ip6, default="disabled")

		self._isReloading = False
		self._ipv4Changed = False
		self._ipv6Changed = False
		self._addNotifiers()
		self._service_conn = [
			self._service.ipv4Changed.connect(self._serviceChanged),
			self._service.ipv6Changed.connect(self._serviceChanged),
			self._service.ipv4ConfigChanged.connect(self._serviceChanged),
			self._service.ipv6ConfigChanged.connect(self._serviceChanged),
		]

	def _serviceChanged(self, *args):
		self.reload(force=False)

	def _addNotifiers(self):
		#Setup refresh
		self._config_ip4_method.addNotifier(self._methodChanged, initial_call=False)
		self._config_ip6_method.addNotifier(self._methodChanged, initial_call=False)

		#change tracking
		#ipv4
		self._config_ip4_method.addNotifier(self._changedIP4, initial_call=False)
		self._config_ip4_address.addNotifier(self._changedIP4, initial_call=False)
		self._config_ip4_mask.addNotifier(self._changedIP4, initial_call=False)
		self._config_ip4_gw.addNotifier(self._changedIP4, initial_call=False)
		#ipv6
		self._config_ip6_method.addNotifier(self._changedIP6, initial_call=False)
		self._config_ip6_address.addNotifier(self._changedIP6, initial_call=False)
		self._config_ip6_prefix_length.addNotifier(self._changedIP6, initial_call=False)
		self._config_ip6_gw.addNotifier(self._changedIP6, initial_call=False)
		self._config_ip6_privacy.addNotifier(self._changedIP6, initial_call=False)

	def _changedIP4(self, element):
		if not self._isReloading:
			self._ipv4Changed = True
		self._changed(element)

	def _changedIP6(self, element):
		if not self._isReloading:
			self._ipv6Changed = True
		self._changed(element)

	def _changed(self, element):
		if not self._isReloading:
			Log.i()
			for fnc in self.onChanged:
				fnc()

	def _methodChanged(self, element):
		if not self._isReloading:
			Log.i()
			for fnc in self.onMethodChanged:
				fnc()

	def reload(self, force=True):
		self._isReloading = True
		if force:
			self._ipv4Changed = False
			self._ipv6Changed = False
		if not self._ipv6Changed:
			ip4 = self._service.ipv4()
			if not dict(ip4):
				ip6 = self._service.ipv4Config()
			self._config_ip4_method.value = ip4.get(eNetworkService.KEY_METHOD, eNetworkService.METHOD_OFF)
			self._config_ip4_address.value = toIP4List( ip4.get("Address", "0.0.0.0") )
			self._config_ip4_mask.value = toIP4List( ip4.get(eNetworkService.KEY_NETMASK, "0.0.0.0") )
			self._config_ip4_gw.value = toIP4List( ip4.get(eNetworkService.KEY_GATEWAY, "0.0.0.0") )
		if not self._ipv6Changed:
			ip6 = self._service.ipv6()
			Log.i("%s / %s" %(dict(ip6), dict(self._service.ipv6Config())) )
			if not dict(ip6):
				ip6 = self._service.ipv6Config()
			self._config_ip6_method.value = ip6.get(eNetworkService.KEY_METHOD, eNetworkService.METHOD_OFF)
			self._config_ip6_address.value = ip6.get(eNetworkService.KEY_ADDRESS, "::")
			self._config_ip6_prefix_length.value = ord( ip6.get(eNetworkService.KEY_PREFIX_LENGTH, chr(1)) or chr(1) )
			self._config_ip6_gw.value = ip6.get(eNetworkService.KEY_GATEWAY, "::")
			self._config_ip6_privacy.value = ip6.get(eNetworkService.KEY_PRIVACY, eNetworkService.IPV6_PRIVACY_DISABLED)
		self._isReloading = False
		self._changed(None)

	def getList(self):
		if self._config_ip4_method.value == eNetworkService.METHOD_MANUAL:
			self._config_ip4_address.enabled = True
			self._config_ip4_mask.enabled = True
			self._config_ip4_gw.enabled = True
		else:
			self._config_ip4_address.enabled = False
			self._config_ip4_mask.enabled = False
			self._config_ip4_gw.enabled = False
		if self._config_ip6_method.value == eNetworkService.METHOD_MANUAL:
			self._config_ip6_address.enabled = True
			self._config_ip6_prefix_length.enabled = True
			self._config_ip6_gw.enabled = True
		else:
			self._config_ip6_address.enabled = False
			self._config_ip6_prefix_length.enabled = False
			self._config_ip6_gw.enabled = False

		l = [ getConfigListEntry(_("Method (IPv4)"), self._config_ip4_method), ]
		if self._config_ip4_method.value != eNetworkService.METHOD_OFF:
			l.extend([
				getConfigListEntry(_("Address (IPv4)"), self._config_ip4_address),
				getConfigListEntry(_("Mask (IPv4)"), self._config_ip4_mask),
				getConfigListEntry(_("Gateway (IPv4)"), self._config_ip4_gw),
			])
		l.append( getConfigListEntry(_("Method (IPv6)"), self._config_ip6_method))
		if self._config_ip6_method.value != eNetworkService.METHOD_OFF:
			l.extend([
				getConfigListEntry(_("Address (IPv6)"), self._config_ip6_address),
				getConfigListEntry(_("Prefix length (IPv6)"), self._config_ip6_prefix_length),
				getConfigListEntry(_("Gateway (IPv6)"), self._config_ip6_gw),
			])
		if self._config_ip6_method.value in (eNetworkService.METHOD_AUTO, eNetworkService.METHOD_6TO4):
			l.append( getConfigListEntry(_("Privacy (IPv6)"), self._config_ip6_privacy) )
		return l

	def save(self):
		if self._ipv4Changed:
			Log.i("IPv4 Changed, saving!")
			if self._config_ip4_method.value == eNetworkService.METHOD_MANUAL:
				ip4_config = {
						eNetworkService.KEY_METHOD : self._config_ip4_method.value,
						eNetworkService.KEY_ADDRESS : toIP4String(self._config_ip4_address),
						eNetworkService.KEY_NETMASK : toIP4String(self._config_ip4_mask),
						eNetworkService.KEY_GATEWAY : toIP4String(self._config_ip4_gw),
					}
			else:
				ip4_config = { eNetworkService.KEY_METHOD : self._config_ip4_method.value }
			Log.i(ip4_config)
			self._service.setIpv4Config(ip4_config)

		if self._ipv6Changed:
			Log.i("IPv6 Changed, saving!")
			if self._config_ip6_method.value == eNetworkService.METHOD_MANUAL:
				ip6_config = {
						eNetworkService.KEY_METHOD : self._config_ip6_method.value,
						eNetworkService.KEY_ADDRESS : self._config_ip6_address.value,
						eNetworkService.KEY_PREFIX_LENGTH : self._config_ip6_prefix_length.value,
						eNetworkService.KEY_GATEWAY : self._config_ip6_gw.value,
						eNetworkService.KEY_PRIVACY : self._config_ip6_privacy.value,
					}
			else:
				val = self._config_ip6_method.value #avoid config element overhead here
				#one can not configure 6to4, it will automatically be applied by connman if applicable -> change it to auto
				if val == eNetworkService.METHOD_6TO4:
					val = eNetworkService.METHOD_AUTO

				ip6_config = { eNetworkService.KEY_METHOD : val }
				if val != eNetworkService.METHOD_OFF:
					ip6_config[eNetworkService.KEY_PRIVACY] = self._config_ip6_privacy.value
			Log.i(ip6_config)
			self._service.setIpv6Config(ip6_config)

class NetworkServiceIPConfig(ConfigListScreen, Screen, ServiceBoundConfiguration):
	def __init__(self, session, service):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		ServiceBoundConfiguration.__init__(self, service)

		self["key_blue"] = StaticText(_("Reset"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"blue": self._reload,
			"save": self.close,
			"cancel": self.close,
			"ok" : self.close,
		}, -2)

		self._ipconfig = ServiceIPConfiguration(self._service)
		self._ipconfig.onMethodChanged.append(self._createSetup)
		self._noSave = False

		self._reload()
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self._ipconfig.onMethodChanged.remove(self._createSetup)
		self._apply()
		del self._ipconfig

	def _apply(self):
		if self._isServiceRemoved:
			return
		self._ipconfig.save()

	def _reload(self):
		self._ipconfig.reload()
		self._createSetup()

	def _createSetup(self):
		self["config"].list = self._ipconfig.getList()

class ServiceNSConfiguration(object):

	def __init__(self, service):
		self._service = service
		self.onChanged = []
		self._nameservers = []

	def reload(self):
		self._nameservers = []
		ns = self._service.nameserversConfig()
		for n in ns:
			ip = IPAddress(n)
			if ip.version == 4:
				cfg = ConfigIP( default=toIP4List(ip.format()))
				self._nameservers.append(cfg)
			elif ip.version == 6:
				cfg = ConfigIP6(default=ip.format())
				self._nameservers.append(cfg)

	def getList(self):
		return [ getConfigListEntry("Name server", ns) for ns in self._nameservers ]

	def add4(self):
		self._nameservers.append(ConfigIP([0,0,0,0]))

	def add6(self):
		self._nameservers.append(ConfigIP6())

	def remove(self, cfg):
		self._nameservers.remove(cfg)

	def save(self):
		servers = []
		for nscfg in self._nameservers:
			if isinstance(nscfg, ConfigIP):
				servers.append(toIP4String(nscfg))
			elif isinstance(nscfg, ConfigIP6):
				servers.append(nscfg.value)
		self._service.setNameserversConfig(StringList(servers))

class NetworkServiceNSConfig(ConfigListScreen, Screen, ServiceBoundConfiguration):

	def __init__(self, session, service):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		ServiceBoundConfiguration.__init__(self, service)

		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("New (IPv4)"))
		self["key_yellow"] = StaticText(_("New (IPv6)"))
		self["key_blue"] = StaticText(_("Reset"))
		self["activedns"] = StaticText(self.getActiveDnsText())
		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self._remove,
			"green": self._add4,
			"yellow": self._add6,
			"blue": self._reload,
			"save": self.close,
			"cancel": self.close,
			"ok" : self.close,
		}, -2)

		self._nsconfig = ServiceNSConfiguration(self._service)
		self._reload()
		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self._layoutFinished)

	def getActiveDnsText(self):
		nameservers = list(self._service.nameservers())
		text = ""
		if nameservers:
			text = _("Active name servers:\n%s") %(", ".join(nameservers))
			Log.i(text)
		return text

	def _layoutFinished(self):
		self.setTitle(_("%s Network - Name servers" %self._service.name()))

	def _remove(self):
		cfg = self["config"].getCurrent()
		if cfg:
			self._nsconfig.remove(cfg[1])
			self._createSetup()

	def _add4(self):
		self._nsconfig.add4()
		self._createSetup()

	def _add6(self):
		self._nsconfig.add6()
		self._createSetup()

	def __onClose(self):
		if self._isServiceRemoved:
			return
		self._nsconfig.save()

	def _reload(self):
		self._nsconfig.reload()
		self._createSetup()

	def _createSetup(self):
		self["config"].setList( self._nsconfig.getList() )

class NetworkTimeserverConfiguration(object):
	def __init__(self, nm):
		self._nm = nm
		self._timeservers = []

	def reload(self):
		self._timeservers = []
		timeservers = list(self._nm.getTimeservers())
		for timeserver in timeservers:
			self._timeservers.append(ConfigText(default=timeserver))

	def getList(self):
		return [ getConfigListEntry("Time server", ts) for ts in self._timeservers ]

	def add(self):
		self._timeservers.append(ConfigText(default="0.pool.ntp.org"))

	def remove(self, cfg):
		self._timeservers.remove(cfg)

	def save(self):
		servers = [x.value for x in self._timeservers]
		self._nm.setTimeservers(StringList(servers))

class NetworkTimeserverConfig(ConfigListScreen, Screen, ServiceBoundConfiguration):

	def __init__(self, session):
		Screen.__init__(self, session, windowTitle=_("Time server configuration"))
		ConfigListScreen.__init__(self, [], session=session)
		self.skinName = "NetworkServiceNSConfig"

		self._nm = eNetworkManager.getInstance()
		self._tsconfig = NetworkTimeserverConfiguration(self._nm)

		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("New"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Reset"))
		self["activedns"] = StaticText(self.getActiveTimeserversText())
		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self._remove,
			"green": self._add,
			"blue": self._reload,
			"save": self.close,
			"cancel": self.close,
			"ok" : self.close,
		}, -2)

		self["config"].onSelectionChanged.append(self._checkButtons)

		choices_timeupdates = { eNetworkManager.TIME_UPDATES_AUTO : _("auto"), eNetworkManager.TIME_UPDATES_MANUAL : _("manual") }
		self._config_timeupdates = ConfigSelection(choices_timeupdates, default=self._nm.timeUpdates())
		self._config_timeupdates.addNotifier(self._onConfigChange, initial_call=False)
		self.__timeservers_changed_conn = self._nm.timeserversChanged.connect(self._reload)

		self.onClose.append(self.__onClose)
		self._reload()

	def _checkButtons(self):
		cfg = self["config"].getCurrent() and  self["config"].getCurrent()[1]
		self["key_red"].text = _("Delete") if cfg != self._config_timeupdates else ""

	def _onConfigChange(self, element=None):
		self._nm.setTimeUpdates(self._config_timeupdates.value)
		self._createSetup()

	def getActiveTimeserversText(self):
		timeservers = list(self._nm.getTimeservers())
		text = ""
		if timeservers:
			text = _("Active time servers:\n%s") %(", ".join(timeservers))
			Log.i(text)
		return text

	def _remove(self):
		cfg = self["config"].getCurrent()
		if cfg and cfg[1] != self._config_timeupdates:
			self._tsconfig.remove(cfg[1])
			self._createSetup()

	def _add(self):
		self._tsconfig.add()
		self._createSetup()

	def __onClose(self):
		self._tsconfig.save()

	def _reload(self):
		self._tsconfig.reload()
		self._createSetup()

	def _createSetup(self):
		self["activedns"].text = self.getActiveTimeserversText()
		lst = [getConfigListEntry(_("NTP Time Updates"), self._config_timeupdates)]
		lst.extend(self._tsconfig.getList())
		self["config"].list = lst

