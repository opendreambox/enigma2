from enigma import eNetworkManager

from Components.Label import Label
from Components.Pixmap import Pixmap
#from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Screens.WizardLanguage import WizardLanguage
from Screens.Rc import Rc
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from NetworkConfig import NetworkConfigGeneral, ServiceIPConfiguration, ServiceNSConfiguration, translateState

class NetworkWizardNew(WizardLanguage, Rc, NetworkConfigGeneral):
	STEP_ID_TECH = 3
	STEP_ID_SVCS = 4
	skin = """
		<screen name="NetworkWizardNew" position="center,70" size="1200,620" title="NetworkWizard">
			<ePixmap pixmap="Default-HD/buttons/red.png" position="270,15" size="200,40" alphatest="on" />
			<widget name="languagetext" position="270,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="button_green" render="Pixmap" pixmap="Default-HD/buttons/green.png" position="475,15" size="200,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="button_green_text" position="475,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />

			<widget source="button_yellow" render="Pixmap" pixmap="Default-HD/buttons/yellow.png" position="685,15" size="200,40" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="button_yellow_text" position="685,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />

			<widget name="wizard" position="0,0" size="240,620" pixmap="Default-HD/wizard.png" />
			<widget name="rc" position="40,60" size="160,500" zPosition="1" pixmaps="skin_default/rc0.png,skin_default/rc1.png,skin_default/rc2.png" alphatest="blend" />
			<widget name="arrowdown" position="-100,-100" size="37,70" pixmap="skin_default/arrowdown.png" zPosition="2" alphatest="on" />
			<widget name="arrowdown2" position="-100,-100" size="37,70" pixmap="skin_default/arrowdown.png" zPosition="2" alphatest="on" />
			<widget name="arrowup" position="-100,-100" size="37,70" pixmap="skin_default/arrowup.png" zPosition="2" alphatest="on" />
			<widget name="arrowup2" position="-100,-100" size="37,70" pixmap="skin_default/arrowup.png" zPosition="2" alphatest="on" />
			<widget name="text" position="280,70" size="880,240" font="Regular;23" backgroundColor="background" transparent="1" />
			<widget source="list" render="Listbox" position="280,320" size="880,250" scrollbarMode="showOnDemand" zPosition="1">
				<convert type="TemplatedMultiContent">
					{"templates":
						{	"default" : ( 20, [ MultiContentEntryText(pos = (5, 0), size = (870, 20), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1)]),
							"service" : (50, [
								MultiContentEntryPixmapAlphaTest(pos = (0, 0), size = (50, 50), png = 1), #type icon
								MultiContentEntryText(pos = (830, 0), size = (50, 50), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 2), #signal strength
								MultiContentEntryText(pos = (55, 0), size = (770, 24), font=0, flags = RT_HALIGN_LEFT, text = 3), #service name
								MultiContentEntryText(pos = (55, 30), size = (385, 18), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4), #ip
								MultiContentEntryText(pos = (395, 30), size = (385, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), #state
							]),
						},
					"fonts": [gFont("Regular", 22), gFont("Regular", 16)]
					}
				</convert>
			</widget>
			<widget name="state_label" position="335,585" size="700,30" font="Regular;23" halign="right" backgroundColor="background" transparent="1" />
			<widget name="state" position="1040,585" size="150,30" font="Regular;23" halign="right" backgroundColor="background" transparent="1" />

			<widget name="config" position="280,350" size="880,270" zPosition="2" itemHeight="30" scrollbarMode="showOnDemand" transparent="1"/>
			<widget source="VKeyIcon" render="Pixmap" position="1110,20" size="70,30" zPosition="1" pixmap="Default-HD/icons/text.png" alphatest="blend">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="HelpWindow" position="453,250" size="1,1" zPosition="1" transparent="1" />
		</screen>"""

	def __init__(self, session, interface = None):
		self.xmlfile = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkManager/networkwizard.xml")

		WizardLanguage.__init__(self, session, showSteps = False, showStepSlider = False)
		Rc.__init__(self)
		NetworkConfigGeneral.__init__(self)

		self._services = self["list"]
		self._services.buildfunc = self._buildListEntry
		self._services.setStyle("default")

		self["wizard"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)
		self["button_green"] = Boolean(False)
		self["button_green_text"] = Label(_("Connect"))
		self["button_green_text"].hide()
		self["button_yellow"] = Boolean(False)
		self["button_yellow_text"] = Label(_("Rescan"))
		self["button_yellow_text"].hide()
		self["state_label"] = Label(_("Connection State:"))
		self["state"] = Label( translateState(self._nm.state()) )

		self._ipconfig = None
		self._nsconfig = None

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
		if self.currStep == self.STEP_ID_SVCS:
			self._rescan()

	def updateValues(self):
		WizardLanguage.updateValues(self)
		if self.currStep == self.STEP_ID_SVCS:
			self._services.setStyle("service")
			self["button_green"].boolean = True
			self["button_green_text"].show()
			self["button_yellow"].boolean = True
			self["button_yellow_text"].show()
			self._services.buildfunc = self._buildServiceListEntry
		else:
			self._services.setStyle("default")
			self["button_green"].boolean = False
			self["button_green_text"].hide()
			self["button_yellow"].boolean = False
			self["button_yellow_text"].hide()
			self._services.buildfunc = self._buildListEntry

	def selChanged(self):
		WizardLanguage.selChanged(self)
		if self.currStep == self.STEP_ID_SVCS:
			service = self._currentService
			if service:
				if not service.state() in (eNetworkManager.STATE_IDLE, eNetworkManager.STATE_FAILURE):
					self["button_green_text"].setText(_("Disconnect"))
				else:
					self["button_green_text"].setText(_("Connect"))

	def _technologiesChanged(self):
		if self.currStep == self.STEP_ID_TECH:
			self["config"].list = self.getTechnologyConfig()

	def _techPoweredChanged(self, powered):
		if self.currStep == self.STEP_ID_TECH:
			self["config"].list = self.getTechnologyConfig()

	def technologiesSet(self):
		pass

	def _servicesChanged(self, *args):
		self["state"].setText( translateState( self._nm.state() ) )
		if self.currStep == self.STEP_ID_SVCS:
			self["list"].updateList( self.getServiceList() )

	def ipConfigurationRequired(self):
		if not self._nm.state() in (eNetworkManager.STATE_ONLINE, eNetworkManager.STATE_READY):
			return True #TODO check if ips are already set
		return False

	def isNetworkConnected(self):
		state = self._nm.state()
		return state in (eNetworkManager.STATE_ONLINE, eNetworkManager.STATE_READY)

	def getAddressConfig(self):
		self._ipconfig = ServiceIPConfiguration(self._nm.getServices()[0])
		self._ipconfig.reload()
		return self._ipconfig.getList()

	def _reloadAddressConfig(self):
		self["config"].list = self._ipconfig.getList()

	def saveAddressConfig(self):
		self._ipconfig.save()

	def isOnline(self):
		return self._nm.state() == eNetworkManager.STATE_ONLINE

	def getNameserverConfig(self):
		self._nsconfig = ServiceNSConfiguration( self._nm.getServices()[0] )

	def saveNameserverConfig(self):
		self._nsconfig.save()
