from __future__ import division
from __future__ import print_function
from enigma import eDVBResourceManager,\
	eDVBFrontendParametersSatellite

from Screens.Screen import Screen
from Screens.ScanSetup import ScanSetup
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor

from Components.Sources.FrontendStatus import FrontendStatus
from Components.ActionMap import ActionMap
from Components.NimManager import nimmanager, getConfigSatlist
from Components.MenuList import MenuList
from Components.config import ConfigSelection, getConfigListEntry
from Components.TuneTest import Tuner

class Satfinder(ScanSetup):
	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(self.feid)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print("getFrontend failed")
			else:
				print("getRawChannel failed")
		else:
			print("getResourceManager instance failed")
		return False

	def __init__(self, session, feid):
		self.initcomplete = False
		self.feid = feid
		self.oldref = None
		ScanSetup.__init__(self, session, 'S')

		if not self.openFrontend():
			self.oldref = session.nav.getCurrentlyPlayingServiceReference()
			session.nav.stopService() # try to disable foreground service
			if not self.openFrontend():
				if session.pipshown: # try to disable pip
					session.pipshown = False
					session.deleteDialog(session.pip)
					del session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen

		self.tuner = Tuner(self.frontend)
		self["introduction"].setText("")
		self["Frontend"] = FrontendStatus(frontend_source = lambda : self.frontend, update_interval = 100)
		self.initcomplete = True
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.session.nav.playService(self.oldref)

	def createSetup(self):
		self.plpidAutoEntry = None
		self.fecEntry = None
		self.systemEntry = None
		self.modulationEntry = None
		self.satelliteEntry = None
		self.enableMisEntry = None
		self.plsModeEntry = None
		self.tunerEntry = None

		self.list = []

		self.typeOfScanEntry = getConfigListEntry(_('Tune'), self.tuning_type)
		self.list.append(self.typeOfScanEntry)
		self.satEntry = getConfigListEntry(_('Satellite'), self.tuning_sat)
		self.list.append(self.satEntry)

		nim = nimmanager.nim_slots[self.feid]

		self.systemEntry = None
		if self.tuning_type.value == "manual_transponder":
			if nim.isCompatible("DVB-S2"):
				self.systemEntry = getConfigListEntry(_('System'), self.scan_sat.system)
				self.list.append(self.systemEntry)
			else:
				# downgrade to dvb-s, in case a -s2 config was active
				self.scan_sat.system.value = eDVBFrontendParametersSatellite.System_DVB_S
			self.list.append(getConfigListEntry(_('Frequency'), self.scan_sat.frequency))
			self.list.append(getConfigListEntry(_('Inversion'), self.scan_sat.inversion))
			self.list.append(getConfigListEntry(_('Symbol rate'), self.scan_sat.symbolrate))
			self.list.append(getConfigListEntry(_('Polarization'), self.scan_sat.polarization))
			if self.scan_sat.system.value == eDVBFrontendParametersSatellite.System_DVB_S2:
				self.modulationEntry = getConfigListEntry(_('Modulation'), nim.can_modulation_auto and self.scan_sat.modulation_auto or self.scan_sat.modulation)
				mod = self.modulationEntry[1].value
				if mod == eDVBFrontendParametersSatellite.Modulation_8PSK:
					self.fecEntry = getConfigListEntry(_("FEC"), nim.can_auto_fec_s2 and self.scan_sat.fec_s2_8psk_auto or self.scan_sat.fec_s2_8psk)
				else:
					self.fecEntry = getConfigListEntry(_("FEC"), nim.can_auto_fec_s2 and self.scan_sat.fec_s2_qpsk_auto or self.scan_sat.fec_s2_qpsk)
				self.list.append(self.fecEntry)
				self.list.append(self.modulationEntry)
				self.list.append(getConfigListEntry(_('Roll-off'), self.scan_sat.rolloff))
				self.list.append(getConfigListEntry(_('Pilot'), self.scan_sat.pilot))
				if nim.can_multistream_s2:
					self.enableMisEntry = getConfigListEntry(_('Multistream'), self.scan_sat.enable_mis)
					self.list.append(self.enableMisEntry)
					if self.scan_sat.enable_mis.value:
						self.list.append(getConfigListEntry(_('Stream ID'), self.scan_sat.is_id))
				if nim.can_pls_s2:
					self.plsModeEntry = getConfigListEntry(_('PLS Mode'), self.scan_sat.pls_mode)
					self.list.append(self.plsModeEntry)
					if self.scan_sat.pls_mode.value != eDVBFrontendParametersSatellite.PLS_Unknown:
						self.list.append(getConfigListEntry(_('PLS Code'), self.scan_sat.pls_code))
			else:
				self.fecEntry = getConfigListEntry(_("FEC"), self.scan_sat.fec)
				self.list.append(self.fecEntry)
		elif self.tuning_transponder and self.tuning_type.value == "predefined_transponder":
			self.list.append(getConfigListEntry(_("Transponder"), self.tuning_transponder))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur is None:
			pass
		elif cur == self.satEntry:
			self.updateSats()
			self.createSetup()
		else:
			ScanSetup.newConfig(self)
		if self.systemEntry and cur == self.systemEntry or \
			cur == self.tuning_type:
			self.retune(None)

	def sat_changed(self, config_element):
		self.newConfig()
		self.retune(config_element)

	def retune(self, configElement):
		returnvalue = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
		satpos = int(self.tuning_sat.value)
		if self.tuning_type.value == "manual_transponder":
			if self.scan_sat.system.value == eDVBFrontendParametersSatellite.System_DVB_S:
				fec = self.scan_sat.fec.value
				mod = eDVBFrontendParametersSatellite.Modulation_QPSK
			else:
				mod = self.modulationEntry[1].value
				fec = self.fecEntry[1].value
			returnvalue = (
				self.scan_sat.frequency.float,
				self.scan_sat.symbolrate.value,
				self.scan_sat.polarization.value,
				fec,
				self.scan_sat.inversion.value,
				satpos,
				self.scan_sat.system.value,
				mod,
				self.scan_sat.rolloff.value,
				self.scan_sat.pilot.value,
				self.scan_sat.is_id.value if self.scan_sat.enable_mis.value else -1,
				self.scan_sat.pls_mode.value,
				self.scan_sat.pls_code.value if self.scan_sat.pls_mode.value < eDVBFrontendParametersSatellite.PLS_Unknown else 0)
			self.tune(returnvalue)
		elif self.tuning_type.value == "predefined_transponder":
			tps = nimmanager.getTransponders(satpos)
			l = len(tps)
			if l > self.tuning_transponder.index:
				transponder = tps[self.tuning_transponder.index]
				returnvalue = (transponder[1] // 1000, transponder[2] // 1000,
					transponder[3], transponder[4], 2, satpos, transponder[5], transponder[6], transponder[8], transponder[9])
				self.tune(returnvalue)

	def createConfig(self, foo):
		self.tuning_transponder = None
		self.tuning_type = ConfigSelection(choices = [("manual_transponder", _("Manual transponder")), ("predefined_transponder", _("Predefined transponder"))])
		orb_pos=192
		if foo is not None:
			orb_pos = foo.get("orbital_position", 192)
		self.tuning_sat = getConfigSatlist(orb_pos, nimmanager.getSatListForNim(self.feid))
		ScanSetup.createConfig(self, foo)
		self.updateSats()

		for x in (self.tuning_sat, self.scan_sat.frequency,
			self.scan_sat.inversion, self.scan_sat.symbolrate,
			self.scan_sat.polarization, self.scan_sat.fec,
			self.scan_sat.fec_s2_8psk, self.scan_sat.fec_s2_8psk_auto, 
			self.scan_sat.fec_s2_qpsk, self.scan_sat.fec_s2_qpsk_auto,
			self.scan_sat.modulation, self.scan_sat.modulation_auto,
			self.scan_sat.enable_mis, self.scan_sat.is_id, 
			self.scan_sat.pls_mode, self.scan_sat.pls_code,
			self.scan_sat.pilot, self.scan_sat.rolloff):
			x.addNotifier(self.retune, initial_call = False)

	def updateSats(self):
		orb_pos = self.tuning_sat.orbital_position
		if orb_pos is not None:
			transponderlist = nimmanager.getTransponders(orb_pos)
			list = []
			default = None
			index = 0
			for x in transponderlist:
				if x[3] == 0:
					pol = "H"
				elif x[3] == 1:
					pol = "V"
				elif x[3] == 2:
					pol = "CL"
				elif x[3] == 3:
					pol = "CR"
				else:
					pol = "??"
				if x[4] == 0:
					fec = "FEC Auto"
				elif x[4] == 1:
					fec = "FEC 1/2"
				elif x[4] == 2:
					fec = "FEC 2/3"
				elif x[4] == 3:
					fec = "FEC 3/4"
				elif x[4] == 4:
					fec = "FEC 5/6"
				elif x[4] == 5:
					fec = "FEC 7/8"
				elif x[4] == 6:
					fec = "FEC 8/9"
				elif x[4] == 7:
					fec = "FEC 3/5"
				elif x[4] == 8:
					fec = "FEC 4/5"
				elif x[4] == 9:
					fec = "FEC 9/10"
				elif x[4] == 15:
					fec = "FEC None"
				else:
					fec = "FEC Unknown"
				e = str(x[1]) + "," + str(x[2]) + "," + pol + "," + fec
				if default is None:
					default = str(index)
				list.append((str(index), e))
				index += 1
			self.tuning_transponder = ConfigSelection(choices = list, default = default)
			self.tuning_transponder.addNotifier(self.retune, initial_call = False)

	def keyGo(self):
		self.retune(self.tuning_type)

	def restartPrevService(self, yesno):
		if yesno:
			if self.frontend:
				self.frontend = None
				del self.raw_channel
		else:
			self.oldref = None
		self.close(None)

	def keyCancel(self):
		if self.oldref:
			self.session.openWithCallback(self.restartPrevService, MessageBox, _("Zap back to service before satfinder?"), MessageBox.TYPE_YESNO)
		else:
			self.restartPrevService(False)

	def tune(self, transponder):
		if self.initcomplete:
			if transponder is not None:
				self.tuner.tune(transponder)

class SatNimSelection(Screen):
	skin = """
		<screen position="140,165" size="400,130" title="select Slot">
			<widget name="nimlist" position="20,10" size="360,100" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		nimlist = nimmanager.getNimListOfType("DVB-S")
		nimMenuList = []
		for x in nimlist:
			nimMenuList.append((nimmanager.nim_slots[x].friendly_full_description, x))

		self["nimlist"] = MenuList(nimMenuList)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.okbuttonClick ,
			"cancel": self.close
		}, -1)

	def okbuttonClick(self):
		selection = self["nimlist"].getCurrent()[1]
		self.session.open(Satfinder, selection)

def SatfinderMain(session, **kwargs):
	nims = nimmanager.getNimListOfType("DVB-S")

	nimList = []
	for x in nims:
		nim = nimmanager.getNimConfig(x)
		if not nim.sat.configMode.value in ("loopthrough", "satposdepends", "nothing"):
			nimList.append(x)

	if len(nimList) == 0:
		session.open(MessageBox, _("No satellite frontend found!!"), MessageBox.TYPE_ERROR)
	else:
		if session.nav.RecordTimer.isRecording():
			session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to start the satfinder."), MessageBox.TYPE_ERROR)
		else:
			if len(nimList) == 1:
				session.open(Satfinder, nimList[0])
			else:
				session.open(SatNimSelection)

def SatfinderStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Satfinder"), SatfinderMain, "satfinder", None)]
	else:
		return []

def Plugins(**kwargs):
	if (nimmanager.hasNimType("DVB-S")):
		return PluginDescriptor(name=_("Satfinder"), description=_("Helps setting up your dish"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=SatfinderStart)
	else:
		return []
