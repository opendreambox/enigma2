# -*- coding: utf-8 -*-
from enigma import eNetworkManager, eNetworkService, eNetworkServicePtr, StringList, StringMap

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import getConfigListEntry, ConfigIP, ConfigOnOff, ConfigIP6, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
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

NETWORK_STATE_MAP = {
			"idle" : _("Idle"),
			"failure" : _("Failure"),
			"association" : _("Association"),
			"configuration" : _("Configuration"),
			"ready" : _("Connected"),
			"disconnect" : _("Disconnect"),
			"online" : _("Online"),
		}

SECURITY_TYPE_MAP = {
			"none" : _("None"),
			"wep"  : "WEP",
			"psk"  : "WPA",
			"wps"  : "WPS",
			"ieee8021x" : "ieee8021x",
		}

def translateState(state):
	return NETWORK_STATE_MAP.get(state, state)

class NetworkConfigGeneral(object):
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
		if tech is not None and  tech.type() == eNetworkService.TYPE_WIFI and tech.powered():
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
			name = "%s - scanning..." %name
		return (tech.path(), None, enabled, None, None, None, name, "")

	def _buildServiceListEntry(self, svcpath, service):
		#Log.i("service: %s/%s/%s" %(service.name(), service.type(), service.strength()))
		strength = ""
		security = ""
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
					security = SECURITY_TYPE_MAP.get(sec, sec.upper())
				else:
					security = "%s, %s" %(security, SECURITY_TYPE_MAP.get(sec, sec.upper()))
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


		return (service.path(), interfacepng, strength, service.name(), ip, translateState(service.state()), None, security)

class NetworkServiceConfig(Screen, NetworkConfigGeneral):
	skin = """
		<screen name="NetworkServiceConfig" position="center,center" size="560,500" title="Network Configuration" zPosition="0">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />

			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />

			<widget source="list" render="Listbox" position="5,50" size="550,420" scrollbarMode="showOnDemand" zPosition="1">
				<convert type="TemplatedMultiContent">
					{"template":[
							MultiContentEntryPixmapAlphaTest(pos = (0, 0), size = (50, 50), png = 1), #type icon
							MultiContentEntryText(pos = (55, 0), size = (400, 24), font=0, flags = RT_HALIGN_LEFT, text = 3), #service name
							MultiContentEntryText(pos = (450, 0), size = (100, 24), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, text = 7), #security
							MultiContentEntryText(pos = (450, 30), size = (100, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_TOP, text = 2), #signal strength
							MultiContentEntryText(pos = (55, 30), size = (220, 18), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4), #ip
							MultiContentEntryText(pos = (275, 30), size = (150, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), #state
							MultiContentEntryText(pos = (5, 0), size = (490, 50), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 6), #technology name
						],
					"itemHeight": 50,
					"fonts": [gFont("Regular", 22), gFont("Regular", 16)]
					}
				</convert>
			</widget>
			<widget name="hint" position="5,480" zPosition="1" size="560,20" font="Regular;16" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		NetworkConfigGeneral.__init__(self)

		self["key_red"] = Label(_("Reset"))
		self["key_green"] = Label(_("Scan"))
		self["key_yellow"] = Label(_("IP"))
		self["key_blue"] = Label(_("DNS"))
		self["hint"] = Label(_("Press OK to connect"))
		self["OkCancelActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
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
		self._hasWireless = False

		self._services.buildfunc = self._buildListEntry
		self._services.onSelectionChanged.append(self._selectionChanged)

		self._addNotifiers()
		self._createSetup()

		self.onClose.append(self._onClose)
		self.onLayoutFinish.append(self.layoutFinished)

	def _rescan(self):
		if isinstance(self._currentService, eNetworkServicePtr):
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

	def _techPoweredChanged(self, powered):
		if powered:
			self._rescan()
		self._createSetup()

	def layoutFinished(self):
		self.setTitle(_("Network Config"))
		self._checkButtons()

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
		self._config_ip6_mask = ConfigIP6()
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
		self._config_ip4_method.addNotifier(self._changed, initial_call=False)
		self._config_ip6_method.addNotifier(self._changed, initial_call=False)

		#change tracking
		#ipv4
		self._config_ip4_method.addNotifier(self._changedIP4, initial_call=False)
		self._config_ip4_address.addNotifier(self._changedIP4, initial_call=False)
		self._config_ip4_mask.addNotifier(self._changedIP4, initial_call=False)
		self._config_ip4_gw.addNotifier(self._changedIP4, initial_call=False)
		#ipv6
		self._config_ip6_method.addNotifier(self._changedIP6, initial_call=False)
		self._config_ip6_address.addNotifier(self._changedIP6, initial_call=False)
		self._config_ip6_mask.addNotifier(self._changedIP6, initial_call=False)
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
			self._config_ip6_mask.value = ip6.get(eNetworkService.KEY_NETMASK, "::")
			self._config_ip6_gw.value = ip6.get(eNetworkService.KEY_GATEWAY, "::")
			self._config_ip6_privacy.value = ip6.get(eNetworkService.KEY_PRIVACY, eNetworkService.IPV6_PRIVACY_DISABLED)
		self._isReloading = False
		self._changed(None)

	def getList(self):
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
				getConfigListEntry(_("Mask (IPv6)"), self._config_ip6_mask),
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
			self._service.setIpv4Config(StringMap(ip4_config))

		if self._ipv6Changed:
			Log.i("IPv6 Changed, saving!")
			if self._config_ip6_method.value == eNetworkService.METHOD_MANUAL:
				ip6_config = {
						eNetworkService.KEY_METHOD : self._config_ip6_method.value,
						eNetworkService.KEY_ADDRESS : self._config_ip6_address.value,
						eNetworkService.KEY_NETMASK : self._config_ip6_mask.value,
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
			self._service.setIpv6Config(StringMap(ip6_config))

class NetworkServiceIPConfig(ConfigListScreen, Screen, ServiceBoundConfiguration):
	skin = """
		<screen name="NetworkServiceIPConfig" position="center,center" size="560,400" title="Network: Service configuration">
			<!--
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			-->
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<!--
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			-->
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

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
		self._ipconfig.onChanged.append(self._createSetup)
		self._noSave = False

		self._reload()
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self._ipconfig.onChanged.remove(self._createSetup)
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
		return [ getConfigListEntry("Nameserver", ns) for ns in self._nameservers ]

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
	skin = """
		<screen name="NetworkServiceNSConfig" position="center,center" size="560,400" title="Service: Nameserver configuration">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green"
			 render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, service):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		ServiceBoundConfiguration.__init__(self, service)

		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("New (IPv4)"))
		self["key_yellow"] = StaticText(_("New (IPv6)"))
		self["key_blue"] = StaticText(_("Reset"))
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

	def _layoutFinished(self):
		self.setTitle(_("%s Network - Nameservers" %self._service.name()))

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
