from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from CeCDeviceList import CeCDeviceList

class CecConfig(ConfigListScreen, Screen):
	skin = """
		<screen name="CecConfig" position="center,center" size="560,400" title="HDMI CEC: Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)

		ConfigListScreen.__init__(self, [])
		config.cec.enabled.addNotifier(self._recreateSetup, initial_call=False)
		config.cec.sendpower.addNotifier(self._recreateSetup, initial_call=False)
		config.cec.enable_avr.addNotifier(self._recreateSetup, initial_call=False)
		config.cec.receivepower.addNotifier(self._recreateSetup, initial_call=False)
		config.cec.volume_forward.addNotifier(self._recreateSetup, initial_call=False)

		self._createSetup()

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		# SKIN Compat HACK!
		self["key_blue"] = StaticText(_("Devices"))
		# EO SKIN Compat HACK!
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"blue" : self._showDeviceList,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.layoutFinished)

	def _showDeviceList(self):
		self.session.open(CeCDeviceList)

	def __onClose(self):
		config.cec.enabled.removeNotifier(self._recreateSetup)
		config.cec.sendpower.removeNotifier(self._recreateSetup)
		config.cec.enable_avr.removeNotifier(self._recreateSetup)
		config.cec.receivepower.removeNotifier(self._recreateSetup)
		config.cec.volume_forward.removeNotifier(self._recreateSetup)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self._createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self._createSetup()

	def _recreateSetup(self, element):
		self._createSetup()

	def _createSetup(self):
		isExpert = config.usage.setup_level.index >= 2
		lst =  [getConfigListEntry(_("HDMI CEC"), config.cec.enabled),]
		if not config.cec.enabled.value:
			self["config"].list = lst
			return
		lst.extend([
			getConfigListEntry(_("OSD Name"), config.cec.name),
			getConfigListEntry(_("Power Handling")),
			getConfigListEntry(_("Send HDMI CEC Power Events"), config.cec.sendpower),
			])
		if config.cec.sendpower.value:
			lst.append(getConfigListEntry(_("Power on AV-Receiver"), config.cec.enable_avr))
			if config.cec.enable_avr.value and isExpert:
				lst.append(getConfigListEntry(_("Send explicit on/off to Audio System"), config.cec.avr_power_explicit))

		lst.extend([
				getConfigListEntry(_("Handle received HDMI CEC Power Events"), config.cec.receivepower),
			])

		if config.cec.receivepower.value and isExpert:
			lst.extend([
				getConfigListEntry(_("Power-On Events (For Experts Only)")),
				getConfigListEntry(_("Handle 'Routing Info' as power up/down"), config.cec.activate_on_routing_info),
				getConfigListEntry(_("Handle 'Routing Change' as power up/down"), config.cec.activate_on_routing_change),
				getConfigListEntry(_("Handle 'Active Source' as power up/down"), config.cec.activate_on_active_source),
				getConfigListEntry(_("Handle 'Set Stream' as power up"), config.cec.activate_on_stream),
				getConfigListEntry(_("Handle 'TV Power Status On' as power up"), config.cec.activate_on_tvpower),
				getConfigListEntry(_("Ignore Device Power States"), config.cec.ignore_powerstates),
				getConfigListEntry(_("Ignore 'Active Source' when not sent by the TV"), config.cec.ignore_active_source_nontv),
			])
		lst.extend([
			getConfigListEntry(_("Remote control")),
			getConfigListEntry(_("Allow remote control via CEC"), config.cec.receive_remotekeys),
			getConfigListEntry(_("Forward Volume keys to TV/AVR"), config.cec.volume_forward),
			getConfigListEntry(_("Remote control repeat delay (ms)"), config.cec.remote_repeat_delay),
		])
		if config.cec.volume_forward.value:
			lst.append(
				getConfigListEntry(_("Target for forwarded Volume keys"), config.cec.volume_target)
			)
		lst.extend([
			getConfigListEntry(_("General")),
			getConfigListEntry(_("Enable vendor specific handling"), config.cec.enable_vendor_quirks),
		])
		if isExpert:
			lst.append(getConfigListEntry(_("Ignore CeC ready-state on startup"), config.cec.ignore_ready_state))
		self["config"].list = lst

	def layoutFinished(self):
		self.setTitle(_("HDMI CEC: Setup"))

	def save(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		self.close(True, self.session)

	def cancel(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].cancel()
		self.close(False, self.session)

