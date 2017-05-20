from Screen import Screen
from Screens.DefaultWizard import DefaultWizard
from ServiceScan import ServiceScan
from Components.config import config, ConfigSubsection, ConfigSelection, \
	ConfigYesNo, ConfigInteger, getConfigListEntry, ConfigSlider, ConfigOnOff, ConfigText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.ConfigList import ConfigListScreen
from Components.NimManager import nimmanager, getConfigSatlist
from Components.Label import Label
from Tools.Directories import resolveFilename, SCOPE_DEFAULTPARTITIONMOUNTDIR, SCOPE_DEFAULTDIR, SCOPE_DEFAULTPARTITION
from Tools.Transponder import ConvertToHumanReadable
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox
from enigma import eTimer, eDVBFrontendParametersSatellite, eComponentScan, \
	eDVBSatelliteEquipmentControl as secClass, eDVBFrontendParametersTerrestrial, \
	eDVBFrontendParametersCable, eConsoleAppContainer, eDVBResourceManager, \
	eDVBFrontendParameters, iDVBFrontend

feTerrestrial = iDVBFrontend.feTerrestrial
feSatellite = iDVBFrontend.feSatellite
feCable = iDVBFrontend.feCable
stateLock = iDVBFrontend.stateLock
stateFailed = iDVBFrontend.stateFailed
stateTuning = iDVBFrontend.stateTuning

can_t_t2_auto_delsys = [ 'Si2169C', 'ATBM781x' ]

def buildTerTransponder(frequency,
		system = eDVBFrontendParametersTerrestrial.System_DVB_T,
		inversion = 2, bandwidth = 0, crh = 5, crl = 5,
		modulation = 2, transmission = 2, guard = 4,
		hierarchy = 4, plp_id = -1):
#	print "system", system, "freq", frequency, "inv", inversion, "bw", bandwidth, "fech", crh, "fecl", crl, "mod", modulation, "tm", transmission, "guard", guard, "hierarchy", hierarchy, "plp_id", plp_id

	parm = eDVBFrontendParametersTerrestrial()
	parm.system = system
	parm.frequency = frequency
	parm.inversion = inversion
	parm.bandwidth = bandwidth
	parm.code_rate_HP = crh # only DVB-T
	parm.code_rate_LP = crl # this is the fec for DVB-T2
	parm.modulation = modulation
	parm.transmission_mode = transmission
	parm.guard_interval = guard
	parm.hierarchy = hierarchy # only DVB-T
	parm.plp_id = plp_id # only DVB-T2
	return parm

def getInitialTransponderList(tlist, pos):
	list = nimmanager.getTransponders(pos)
	for x in list:
		if x[0] == 0:		#SAT
			parm = eDVBFrontendParametersSatellite()
			parm.frequency = x[1]
			parm.symbol_rate = x[2]
			parm.polarisation = x[3]
			parm.fec = x[4]
			parm.inversion = x[7]
			parm.orbital_position = pos
			parm.system = x[5]
			parm.modulation = x[6]
			parm.rolloff = x[8]
			parm.pilot = x[9]
			parm.is_id = x[12]
			parm.pls_mode = x[13]
			parm.pls_code = x[14]
			tlist.append(parm)

def getInitialCableTransponderList(tlist, nim):
	list = nimmanager.getTranspondersCable(nim)
	for x in list:
		if x[0] == 1: #CABLE
			parm = eDVBFrontendParametersCable()
			parm.frequency = x[1]
			parm.symbol_rate = x[2]
			parm.modulation = x[3]
			parm.fec_inner = x[4]
			parm.inversion = parm.Inversion_Unknown
			#print "frequency:", x[1]
			#print "symbol_rate:", x[2]
			#print "modulation:", x[3]
			#print "fec_inner:", x[4]
			#print "inversion:", 2
			tlist.append(parm)

def getInitialTerrestrialTransponderList(tlist, region, can_t_t2_auto_delsys):
	list = nimmanager.getTranspondersTerrestrial(region)

	#self.transponders[self.parsedTer].append((2,freq,bw,const,crh,crl,guard,transm,hierarchy,inv))

	#def buildTerTransponder(frequency,
	#	system = eDVBFrontendParametersTerrestrial.System_DVB_T,
	#	inversion = 2, bandwidth = 0, crh = 5, crl = 5,
	#	modulation = 2, transmission = 2, guard = 4,
	#	hierarchy = 4, plp_id = -1):

	for x in list:
		if x[0] == 2: #TERRESTRIAL
			system = x[10] if not can_t_t2_auto_delsys or x[10] == eDVBFrontendParametersTerrestrial.System_DVB_T2 else eDVBFrontendParametersTerrestrial.System_DVB_T_T2
			parm = buildTerTransponder(x[1], system, x[9], x[2], x[4], x[5], x[3], x[7], x[6], x[8], x[11])
			tlist.append(parm)

cable_bands = {
	"DVBC_BAND_EU_VHF_I" : 1 << 0,
	"DVBC_BAND_EU_MID" : 1 << 1,
	"DVBC_BAND_EU_VHF_III" : 1 << 2,
	"DVBC_BAND_EU_SUPER" : 1 << 3,
	"DVBC_BAND_EU_HYPER" : 1 << 4,
	"DVBC_BAND_EU_UHF_IV" : 1 << 5,
	"DVBC_BAND_EU_UHF_V" : 1 << 6,
	"DVBC_BAND_US_LO" : 1 << 7,
	"DVBC_BAND_US_MID" : 1 << 8,
	"DVBC_BAND_US_HI" : 1 << 9,
	"DVBC_BAND_US_SUPER" : 1 << 10,
	"DVBC_BAND_US_HYPER" : 1 << 11,
	"DVBC_BAND_US_ULTRA" : 1 << 12,
	"DVBC_BAND_US_JUMBO" : 1 << 13,
}

class TransponderSearchSupport:
	def tryGetRawFrontend(self, feid, ret_boolean=True, do_close=True):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			raw_channel = res_mgr.allocateRawChannel(self.feid)
			if raw_channel:
				frontend = raw_channel.getFrontend()
				if frontend:
					if do_close:
						frontend.closeFrontend() # immediate close... 
					if ret_boolean:
						del raw_channel
						del frontend
						return True
					return raw_channel, frontend
		if ret_boolean:
			return False
		return (False, False)

def CableScanHelperDMM(nim_idx):
	bus = nimmanager.getI2CDevice(nim_idx)
	tunername = nimmanager.getNimName(nim_idx)
	cableScanHelpers = {
		'CXD1981': 'cxd1978',
		'Philips CU1216Mk3': 'tda1002x',
		'ATBM781x': 'atbm781x',
	}
	cmd = cableScanHelpers.get(tunername, None)
	if cmd is not None:
		cmd += " --init --scan --verbose --wakeup --inv 2 --bus %d" % bus
	return cmd

class CableTransponderSearchSupport:
	CableScanHelpers = [ CableScanHelperDMM ]

# functions for driver based blindscan

	def updateStateCable(self):
		self.frontendStateChangedCable(None)

	def frontendStateChangedCable(self, frontend_ptr):
		x = { }
		self.frontend.getFrontendStatus(x)
		assert x, "getFrontendStatus failed!"
		tuner_state = x["tuner_state"]
		if tuner_state in (stateLock, stateFailed) or frontend_ptr is None:
			d = { }
			self.frontend.getTransponderData(d, False)
			freq = int(round(float(d["frequency"]*2) / 1000)) * 1000
			freq /= 2

			if tuner_state == stateLock:
				parm = eDVBFrontendParametersCable()
				parm.frequency = freq
				fstr = str(parm.frequency)

				sr = d["symbol_rate"]
				sr_rounded = round(float(sr*2L) / 1000) * 1000
				sr_rounded /= 2
#				print "SR after round", sr_rounded
				parm.symbol_rate = int(sr_rounded)
				fstr += " "
				fstr += str(parm.symbol_rate/1000)

				parm.fec = d["fec_inner"]
				parm.inversion = eDVBFrontendParametersCable.Inversion_Unknown
				parm.modulation = d["modulation"]

				self.__tlist.append(parm)

				print "LOCKED at", freq, sr

				status = _("OK")

				self.frontend.tune(self.tparm)
			elif frontend_ptr:
				self.cable_search_session.close(True)
				return
			else:
				fstr = str(freq)
				status = _("in progress")
				print "SEARCHING at", freq

			tmpstr = _("Try to find used Transponders in cable network.. please wait...")
			tmpstr += "\n\n"
			tmpstr += fstr
			tmpstr += " "
			tmpstr += _("kHz")
			tmpstr += " - "
			tmpstr += status
			self.cable_search_session["text"].setText(tmpstr)

			self.updateStateTimer.start(1000, True)

	def cableTransponderSearchSessionClosed(self, *val):
		print "cableTransponderSearchSessionClosed, val", val
		self.appClosed_conn = None
		self.dataAvail_conn = None

		# driver based scan...
		self.frontendStateChanged_conn = None
		self.frontend = None
		self.channel = None
		self.updateStateTimer_conn = None
		self.updateStateTimer = None

		if val and len(val):
			if val[0]:
				self.setTransponderSearchResult(self.__tlist)
			else:
				if self.cable_search_container is not None:
					self.cable_search_container.sendCtrlC()
				self.setTransponderSearchResult(None)

		# external app based scan
		self.cable_search_container = None
		self.cable_search_session = None

		self.__tlist = None
		self.TransponderSearchFinished()

# functions for external app based transponder search support

	def cableTransponderSearchClosed(self, retval):
		print "cableTransponderSearch finished", retval
		self.cable_search_session.close(True)

	def getCableTransponderData(self, str):
		data = str.split()
		if len(data) and data[0] in ("OK", "FAILED"):
			if data[0] == 'OK':
				print str
				parm = eDVBFrontendParametersCable()
				qam = { "QAM16" : parm.Modulation_QAM16,
					"QAM32" : parm.Modulation_QAM32,
					"QAM64" : parm.Modulation_QAM64,
					"QAM128" : parm.Modulation_QAM128,
					"QAM256" : parm.Modulation_QAM256,
					"QAM_AUTO" : parm.Modulation_Auto }
				#inv = { "INVERSION_OFF" : parm.Inversion_Off,
				#	"INVERSION_ON" : parm.Inversion_On,
				#	"INVERSION_AUTO" : parm.Inversion_Unknown }
				fec = { "FEC_AUTO" : parm.FEC_Auto,
					"FEC_1_2" : parm.FEC_1_2,
					"FEC_2_3" : parm.FEC_2_3,
					"FEC_3_4" : parm.FEC_3_4,
					"FEC_5_6": parm.FEC_5_6,
					"FEC_7_8" : parm.FEC_7_8,
					"FEC_8_9" : parm.FEC_8_9,
					"FEC_NONE" : parm.FEC_None }
				parm.frequency = int(data[1])
				parm.symbol_rate = int(data[2])
				parm.fec_inner = fec[data[3]]
				parm.modulation = qam[data[4]]
#				parm.inversion = inv[data[5]]
				parm.inversion = eDVBFrontendParametersCable.Inversion_Unknown
				self.__tlist.append(parm)
				status = _("OK")
			else:
				status = _("No signal")

			tmpstr = _("Try to find used Transponders in cable network.. please wait...")
			tmpstr += "\n\n"
			tmpstr += data[1]
			tmpstr += " "
			tmpstr += _("kHz")
			tmpstr += " - "
			tmpstr += status
			self.cable_search_session["text"].setText(tmpstr)

	def startCableTransponderSearch(self, nim_idx):
		tunername = nimmanager.getNimName(nim_idx)
		self.cable_search_container = None
		if tunername == "Si2169C":
			(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
			if not self.frontend:
				self.session.nav.stopService()
				(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
				if not self.frontend:
					if self.session.pipshown: # try to disable pip
						self.session.pipshown = False
						self.session.deleteDialog(self.session.pip)
						del self.session.pip
					(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
					if not self.frontend:
						print "couldn't allocate tuner %d for blindscan!!!" %nim_idx
						return
			self.__tlist = [ ]
			self.frontendStateChanged_conn = self.frontend.getStateChangeSignal().connect(self.frontendStateChangedCable)

			parm = eDVBFrontendParametersCable()
			parm.frequency = 47000
			parm.symbol_rate = (862000 - parm.frequency) / 1000
			parm.fec_inner = eDVBFrontendParametersCable.FEC_Auto
			parm.modulation = eDVBFrontendParametersCable.Modulation_Auto
			parm.inversion = eDVBFrontendParametersCable.Inversion_Unknown

			self.tparm = eDVBFrontendParameters()
			self.tparm.setDVBC(parm)
			self.frontend.tune(self.tparm)

			self.updateStateTimer = eTimer()
			self.updateStateTimer_conn = self.updateStateTimer.timeout.connect(self.updateStateCable)
			self.updateStateTimer.start(1000, True)

			tmpstr = _("Try to find used transponders in cable network.. please wait...")
			tmpstr += "\n\n..."
			self.cable_search_session = self.session.openWithCallback(self.cableTransponderSearchSessionClosed, MessageBox, tmpstr, MessageBox.TYPE_INFO)
		else:
			if not self.tryGetRawFrontend(nim_idx):
				self.session.nav.stopService()
				if not self.tryGetRawFrontend(nim_idx):
					if self.session.pipshown: # try to disable pip
						self.session.pipshown = False
						self.session.deleteDialog(self.session.pip)
						del self.session.pip
					if not self.tryGetRawFrontend(nim_idx):
						self.TransponderSearchFinished()
						return
			self.__tlist = [ ]
			self.cable_search_container = eConsoleAppContainer()
			self.appClosed_conn = self.cable_search_container.appClosed.connect(self.cableTransponderSearchClosed)
			self.dataAvail_conn = self.cable_search_container.dataAvail.connect(self.getCableTransponderData)
			cableConfig = config.Nims[nim_idx].cable

			cmd = None
			for fnc in self.CableScanHelpers:
				cmd = fnc(nim_idx)
				if cmd is not None:
					break

			if cmd is not None:
				if cableConfig.scan_type.value == "bands":
					if cmd.startswith("cxd1978") or cmd.startswith("tda1002x") or cmd.startswith("atbm781x"):
						cmd += " --scan-flags DVB-C"
						EU = False
						US = False
						VHF_I = False
						VHF_II = False
						VHF_III = False
						UHF_IV = False
						UHF_V = False
						SUPER = False
						HYPER = False

						if cableConfig.scan_band_EU_VHF_I.value:
							VHF_I = True
							EU = True
						if cableConfig.scan_band_EU_MID.value:
							VHF_II = True
							EU = True
						if cableConfig.scan_band_EU_VHF_III.value:
							VHF_III = True
							EU = True
						if cableConfig.scan_band_EU_UHF_IV.value:
							UHF_IV = True
							EU = True
						if cableConfig.scan_band_EU_UHF_V.value:
							UHF_V = True
							EU = True
						if cableConfig.scan_band_EU_SUPER.value:
							SUPER = True
							EU = True
						if cableConfig.scan_band_EU_HYPER.value:
							HYPER = True
							EU = True

						if cableConfig.scan_band_US_LOW.value:
							VHF_I = True
							US = True
						if cableConfig.scan_band_US_MID.value:
							VHF_II = True
							US = True
						if cableConfig.scan_band_US_HIGH.value:
							VHF_III = True
							US = True
						if cableConfig.scan_band_US_SUPER.value:
							SUPER = True
							US = True
						if cableConfig.scan_band_US_HYPER.value:
							HYPER = True
							US = True
						if cableConfig.scan_band_US_ULTRA.value:
							UHF_IV = True
							US = True
						if cableConfig.scan_band_US_JUMBO.value:
							UHF_V = True
							US = True

						if EU:
							cmd += ":EU"
						if US:
							cmd += ":US"
						if VHF_I:
							cmd += ":VHF_I"
						if VHF_II:
							cmd += ":VHF_II"
						if VHF_III:
							cmd += ":VHF_III"
						if UHF_IV:
							cmd += ":UHF_IV"
						if UHF_V:
							cmd += ":UHF_V"
						if SUPER:
							cmd += ":SUPER"
						if HYPER:
							cmd += ":HYPER"
					else: # legacy api maybe for external USB tuners...
						cmd += " --scan-bands "
						bands = 0
						if cableConfig.scan_band_EU_VHF_I.value:
							bands |= cable_bands["DVBC_BAND_EU_VHF_I"]
						if cableConfig.scan_band_EU_MID.value:
							bands |= cable_bands["DVBC_BAND_EU_MID"]
						if cableConfig.scan_band_EU_VHF_III.value:
							bands |= cable_bands["DVBC_BAND_EU_VHF_III"]
						if cableConfig.scan_band_EU_UHF_IV.value:
							bands |= cable_bands["DVBC_BAND_EU_UHF_IV"]
						if cableConfig.scan_band_EU_UHF_V.value:
							bands |= cable_bands["DVBC_BAND_EU_UHF_V"]
						if cableConfig.scan_band_EU_SUPER.value:
							bands |= cable_bands["DVBC_BAND_EU_SUPER"]
						if cableConfig.scan_band_EU_HYPER.value:
							bands |= cable_bands["DVBC_BAND_EU_HYPER"]
						if cableConfig.scan_band_US_LOW.value:
							bands |= cable_bands["DVBC_BAND_US_LO"]
						if cableConfig.scan_band_US_MID.value:
							bands |= cable_bands["DVBC_BAND_US_MID"]
						if cableConfig.scan_band_US_HIGH.value:
							bands |= cable_bands["DVBC_BAND_US_HI"]
						if cableConfig.scan_band_US_SUPER.value:
							bands |= cable_bands["DVBC_BAND_US_SUPER"]
						if cableConfig.scan_band_US_HYPER.value:
							bands |= cable_bands["DVBC_BAND_US_HYPER"]
						if cableConfig.scan_band_US_ULTRA.value:
							bands |= cable_bands["DVBC_BAND_US_ULTRA"]
						if cableConfig.scan_band_US_JUMBO.value:
							bands |= cable_bands["DVBC_BAND_US_JUMBO"]
						cmd += str(bands)
				else:
					cmd += " --scan-stepsize "
					cmd += str(cableConfig.scan_frequency_steps.value)

				if cmd.startswith("atbm781x"):
					cmd += " --timeout 800"
				else:
					if cableConfig.scan_mod_qam16.value:
						cmd += " --mod 16"
					if cableConfig.scan_mod_qam32.value:
						cmd += " --mod 32"
					if cableConfig.scan_mod_qam64.value:
						cmd += " --mod 64"
					if cableConfig.scan_mod_qam128.value:
						cmd += " --mod 128"
					if cableConfig.scan_mod_qam256.value:
						cmd += " --mod 256"
					if cableConfig.scan_sr_6900.value:
						cmd += " --sr 6900000"
					if cableConfig.scan_sr_6875.value:
						cmd += " --sr 6875000"
					if cableConfig.scan_sr_ext1.value > 450:
						cmd += " --sr "
						cmd += str(cableConfig.scan_sr_ext1.value)
						cmd += "000"
					if cableConfig.scan_sr_ext2.value > 450:
						cmd += " --sr "
						cmd += str(cableConfig.scan_sr_ext2.value)
						cmd += "000"

				print "DVB-C scan command: ", cmd

				# we need a timer here because our frontends are running in other threads... so delay is called later...
				self.delayTimer = eTimer()
				self.delayTimer_conn = self.delayTimer.timeout.connect(boundFunction(lambda self, cmd: self.cable_search_container and self.cable_search_container.execute(cmd), self, cmd))
				self.delayTimer.start(1000, True)

				tmpstr = _("Try to find used transponders in cable network.. please wait...")
				tmpstr += "\n\n..."
				self.cable_search_session = self.session.openWithCallback(self.cableTransponderSearchSessionClosed, MessageBox, tmpstr, MessageBox.TYPE_INFO)
			else:
				modulations = []
				symbol_rates = []
				frequencies = []

				if cableConfig.scan_type.value == "bands":
					if cableConfig.scan_band_US_LOW.value:
						frequencies.extend(range(54000, 84000 + 1, 6000))
					if cableConfig.scan_band_US_MID.value:
						frequencies.extend(range(91250, 115250 + 1, 6000))
						frequencies.extend(range(120000, 168000 + 1, 6000))
					if cableConfig.scan_band_US_HIGH.value:
						frequencies.extend(range(174000, 210000 + 1, 6000))
					if cableConfig.scan_band_US_SUPER.value:
						frequencies.extend(range(216000, 294000 + 1, 6000))
					if cableConfig.scan_band_US_HYPER.value:
						frequencies.extend(range(300000, 462000 + 1, 6000))
					if cableConfig.scan_band_US_ULTRA.value:
						frequencies.extend(range(468000, 642000 + 1, 6000))
					if cableConfig.scan_band_US_JUMBO.value:
						frequencies.extend(range(648000, 996000 + 1, 6000))

					if cableConfig.scan_band_EU_VHF_I.value:
						frequencies.extend(range(50500, 64500 + 1, 7000))
						frequencies.extend(range(69000, 77000 + 1, 8000))
					if cableConfig.scan_band_EU_MID.value:
						frequencies.append(101000)
						frequencies.extend(range(113000, 121000 + 1, 8000))
						frequencies.extend(range(128500, 170500 + 1, 7000))
					if cableConfig.scan_band_EU_VHF_III.value:
						frequencies.extend(range(177500, 226500 + 1, 7000))
					if cableConfig.scan_band_EU_SUPER.value:
						frequencies.extend(range(233500, 296500 + 1, 7000))
					if cableConfig.scan_band_EU_HYPER.value:
						frequencies.extend(range(306000, 466000 + 1, 8000))
					if cableConfig.scan_band_EU_UHF_IV.value:
						frequencies.extend(range(474000, 602000 + 1, 8000))
					if cableConfig.scan_band_EU_UHF_V.value:
						frequencies.extend(range(610000, 858000 + 1, 8000))
				else:
					frequencies.extend(range(17000, 999000 + 1, cableConfig.scan_frequency_steps.value))

				if cableConfig.scan_mod_qam16.value:
					modulations.append(eDVBFrontendParametersCable.Modulation_QAM16)
				if cableConfig.scan_mod_qam32.value:
					modulations.append(eDVBFrontendParametersCable.Modulation_QAM32)
				if cableConfig.scan_mod_qam64.value:
					modulations.append(eDVBFrontendParametersCable.Modulation_QAM64)
				if cableConfig.scan_mod_qam128.value:
					modulations.append(eDVBFrontendParametersCable.Modulation_QAM128)
				if cableConfig.scan_mod_qam256.value:
					modulations.append(eDVBFrontendParametersCable.Modulation_QAM256)
				if cableConfig.scan_sr_6900.value:
					symbol_rates.append(6900000)
				if cableConfig.scan_sr_6875.value:
					symbol_rates.append(6875000)
				if cableConfig.scan_sr_ext1.value > 450:
					symbol_rates.append(cableConfig.scan_sr_ext1.value * 1000)
				if cableConfig.scan_sr_ext2.value > 450:
					symbol_rates.append(cableConfig.scan_sr_ext2.value * 1000)

				for frequency in frequencies:
					for modulation in modulations:
						for symbol_rate in symbol_rates:
							parm = eDVBFrontendParametersCable()
							parm.frequency = frequency
							parm.symbol_rate = symbol_rate
							parm.fec_inner = eDVBFrontendParametersCable.FEC_Auto
							parm.modulation = modulation
							parm.inversion = eDVBFrontendParametersCable.Inversion_Unknown
							self.__tlist.append(parm)

				# XXX: I'm a hack. Please replace me!
				self.cable_search_session = self.session.openWithCallback(self.cableTransponderSearchSessionClosed, MessageBox, "", MessageBox.TYPE_INFO)
				self.cable_search_session.close(True)

class TerrestrialTransponderSearchSupport:

	def updateStateTerrestrial(self):
		self.frontendStateChangedTerrestrial(None)

	def frontendStateChangedTerrestrial(self, frontend_ptr):
		x = { }
		self.frontend.getFrontendStatus(x)
		assert x, "getFrontendStatus failed!"
		tuner_state = x["tuner_state"]
		if tuner_state in (stateLock, stateFailed) or frontend_ptr is None:
			d = { }
			self.frontend.getTransponderData(d, False)

			freq = int(round(float(d["frequency"]*2) / 1000)) * 1000
			freq /= 2

			if tuner_state == stateLock:
				d["tuner_type"] = feTerrestrial
				r = ConvertToHumanReadable(d)

				parm = eDVBFrontendParametersTerrestrial()
				parm.system = d["system"]
				parm.frequency = freq
				parm.bandwidth = d["bandwidth"]
				parm.guard_interval = d["guard_interval"]
				parm.modulation = d["constellation"]
				parm.transmission_mode = d["transmission_mode"]
				parm.inversion = eDVBFrontendParametersTerrestrial.Inversion_Unknown
				if parm.system == eDVBFrontendParametersTerrestrial.System_DVB_T:
					parm.code_rate_LP = d["code_rate_lp"]
					parm.code_rate_HP = d["code_rate_hp"]
					parm.hierarchy = d["hierarchy_information"]
				else:
					parm.code_rate_LP = d["fec_inner"]
					parm.plpid = d["plp_id"]

				fstr = r["system"] + " "

				fstr += str(parm.frequency)

				self.__tlist.append(parm)

				print "LOCKED", r["system"], freq

				status = _("OK")

				self.frontend.tune(self.tparm)
			elif frontend_ptr:
				self.terrestrial_search_session.close(True)
				return
			else:
				fstr = str(freq)
				status = _("in progress")
				print "SEARCHING at", freq

			tmpstr = _("Try to find used Transponders in terrestrial network.. please wait...")
			tmpstr += "\n\n"
			tmpstr += fstr
			tmpstr += " "
			tmpstr += _("kHz")
			tmpstr += " - "
			tmpstr += status
			self.terrestrial_search_session["text"].setText(tmpstr)

			self.updateStateTimer.start(1000, True)

	def terrestrialTransponderSearchSessionClosed(self, *val):
		print "terrestrialTransponderSearchSessionClosed, val", val
		# driver based scan...
		self.frontendStateChanged_conn = None
		self.frontend = None
		self.channel = None
		self.updateStateTimer_conn = None
		self.updateStateTimer = None

		if val and len(val):
			if val[0]:
				self.setTransponderSearchResult(self.__tlist)
			else:
				self.setTransponderSearchResult(None)

		self.__tlist = None
		self.TransponderSearchFinished()

	def startTerrestrialTransponderSearch(self, nim_idx):
		self.cable_search_container = None
		(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
		if not self.frontend:
			self.session.nav.stopService()
			(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
			if not self.frontend:
				if self.session.pipshown: # try to disable pip
					self.session.pipshown = False
					self.session.deleteDialog(self.session.pip)
					del self.session.pip
				(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
				if not self.frontend:
					print "couldn't allocate tuner %d for blindscan!!!" %nim_idx
					return
		self.__tlist = [ ]
		self.frontendStateChanged_conn = self.frontend.getStateChangeSignal().connect(self.frontendStateChangedTerrestrial)

		parm = eDVBFrontendParametersTerrestrial()
		parm.frequency = 47000000;
		parm.bandwidth = (862000000 - parm.frequency) / 1000000
		parm.code_rate_LP = parm.code_rate_HP = eDVBFrontendParametersTerrestrial.FEC_Auto
		parm.transmission_mode = eDVBFrontendParametersTerrestrial.TransmissionMode_Auto
		parm.guard_interval = eDVBFrontendParametersTerrestrial.GuardInterval_Auto
		parm.modulation = eDVBFrontendParametersTerrestrial.Modulation_Auto
		parm.inversion = eDVBFrontendParametersTerrestrial.Inversion_Unknown
		parm.hierarchy = eDVBFrontendParametersTerrestrial.Hierarchy_Auto
		parm.system = eDVBFrontendParametersTerrestrial.System_DVB_T2

		self.tparm = eDVBFrontendParameters()
		self.tparm.setDVBT(parm)
		self.frontend.tune(self.tparm)

		self.updateStateTimer = eTimer()
		self.updateStateTimer_conn = self.updateStateTimer.timeout.connect(self.updateStateTerrestrial)
		self.updateStateTimer.start(1000, True)

		tmpstr = _("Try to find used transponders in terrestrial network.. please wait...")
		tmpstr += "\n\n..."
		self.terrestrial_search_session = self.session.openWithCallback(self.terrestrialTransponderSearchSessionClosed, MessageBox, tmpstr, MessageBox.TYPE_INFO)

from time import time

FOUND_HISTORY_SIZE = 8

from Components.Sources.CanvasSource import CanvasSource
from Components.Sources.List import List
from Tools.Directories import fileExists

class SatBlindscanState(Screen):
	def __init__(self, session, fe_num, text):
		Screen.__init__(self, session)
		self["list"]=List()
		self["text"]=Label()
		self["text"].setText(text)
		self["post_action"]=Label()
		self["progress"]=Label()
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"green": self.keyGreen,
		}, -2)
		self.fe_num = fe_num
		self["constellation"] = CanvasSource()
		self.onLayoutFinish.append(self.updateConstellation)
		self.tmr = eTimer()
		self.tmr_conn = self.tmr.timeout.connect(self.updateConstellation)
		self.constellation_supported = None
		if fe_num != -1:
			self.post_action=1
			self.finished=0
			self.keyGreen()
		else:
			self.post_action=-1

	def keyGreen(self):
		if self.finished:
			self.close(True)
		elif self.post_action != -1:
			self.post_action ^= 1
			if self.post_action:
				self["post_action"].setText(_("MANUALLY start service searching, press green to change"))
			else:
				self["post_action"].setText(_("AUTOMATICALLY start service searching, press green to change"))

	def setFinished(self):
		if self.post_action:
			self.finished=1
			self["text"].setText(_("Transponder searching finished!"))
			self["post_action"].setText(_("Press green to start service searching!"))
		else:
			self.close(True)

	def getConstellationBitmap(self, cnt=1):
		ret = []
		path = "/proc/stb/frontend/%d/constellation_bitmap" %self.fe_num
		if self.constellation_supported is None:
			s = fileExists(path)
			self.constellation_supported = s
			if not s:
				self["constellation"].fill(0,0,256,256,0x25101010)
				self["constellation"].flush()

		if self.constellation_supported:
			while cnt > 0:
				f = open(path, "r")
				ret.append(f.readline())
				cnt -= 1
				f.close()
		return ret

	def updateConstellation(self, constellation_bitmap_list=None):
		if self.constellation_supported or self.constellation_supported is None:
			pass
		else:
			return
		self["constellation"].fill(0,0,256,256,0x25101010)
		if constellation_bitmap_list:
			bitmap_list = constellation_bitmap_list
		else:
			bitmap_list = self.getConstellationBitmap()
		for bitmap in bitmap_list:
			Q = []
			I = []
			for pos in range(0,30,2):
				try:
					val = int(bitmap[pos:pos+2], 16)
					val = 128 + (val - 256 if val > 127 else val)
				except ValueError:
					print "I constellation data broken at pos", pos
					val = 0
				I.append(val)
			for pos in range(30,60,2):
				try:
					val = int(bitmap[pos:pos+2], 16)
					val = 128 + (val - 256 if val > 127 else val)
				except ValueError:
					print "Q constellation data broken at pos", pos
					val = 0
				Q.append(val)
			for i in range(15):
				self["constellation"].fill(I[i],Q[i],1,1,0x25ffffff)
		self["constellation"].flush()
		if constellation_bitmap_list:
			self.tmr.start(3000, True)
		else:
			self.tmr.start(50, True)

	def keyOk(self):
		cur_sel = self["list"].current
		if cur_sel:
			self.updateConstellation(cur_sel[1])

	def keyCancel(self):
		self.tmr.stop()
		self.close(False)

class SatelliteTransponderSearchSupport:
	def satelliteTransponderSearchSessionClosed(self, *val):
		if self.frontend:
			self.frontendStateChanged_conn = None
			self.frontend = None
			self.channel = None
			self.updateStateTimer_conn = None
			self.updateStateTimer = None

		print "satelliteTransponderSearchSessionClosed, val", val
		if val and len(val):
			if val[0]:
				self.setTransponderSearchResult(self.__tlist)
			else:
				self.setTransponderSearchResult(None)
		self.satellite_search_session = None
		self.__tlist = None
		self.TransponderSearchFinished()

	def updateStateSat(self):
		self.frontendStateChangedSat(None)

	def frontendStateChangedSat(self, frontend_ptr):
		x = { }
		self.frontend.getFrontendStatus(x)
		assert x, "getFrontendStatus failed!"
		tuner_state = x["tuner_state"]

		if self.driver_wa and frontend_ptr and tuner_state in (stateLock, stateFailed):
			self.parm.symbol_rate = self.driver_wa
			self.driver_wa = False
			self.tuneNext()
			return

		if tuner_state in (stateLock, stateFailed) or frontend_ptr is None:
			band_base_freq = self.parm.frequency
			state = self.satellite_search_session

			d = { }
			self.frontend.getTransponderData(d, False)
			d["tuner_type"] = feSatellite
			r = ConvertToHumanReadable(d)

			if tuner_state == stateLock:
				freq = d["frequency"]

				# Hack for C-Band
				if self.scan_sat.bs_freq_limits[0] == 3400000 and self.scan_sat.bs_freq_limits[1] == 4200000:
					tuned_freq = abs(band_base_freq - 5150000)
					tune_offs = band_base_freq - tuned_freq
					freq -= tune_offs
					freq = 5150000 - freq

				parm = eDVBFrontendParametersSatellite()
				parm.frequency = int(round(float(freq*2) / 1000)) * 1000
				parm.frequency /= 2
				fstr = str(parm.frequency / 1000)
				if self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Horizontal:
					fstr += "H "
				elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Vertical:
					fstr += "V "
				elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
					fstr += "L "
				elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularRight:
					fstr += "R "
				sr = d["symbol_rate"]
#				print "SR before round", sr
				if sr < 0:
					print "WARNING blind SR is < 0... skip"
					if not self.auto_scan:
						self.parm.frequency += self.parm.symbol_rate
				else:
					sr_rounded = round(float(sr*2L) / 1000) * 1000
					sr_rounded /= 2
#					print "SR after round", sr_rounded
					parm.symbol_rate = int(sr_rounded)
					fstr += str(parm.symbol_rate/1000)
					parm.fec = d["fec_inner"]
					fstr += " "
					fstr += r["fec_inner"]
					parm.inversion = eDVBFrontendParametersSatellite.Inversion_Unknown
					parm.polarisation = d["polarization"]
					parm.orbital_position = d["orbital_position"]
					parm.system = d["system"]
					fstr += " "
					fstr += r["system"]
					parm.modulation = d["modulation"]
					fstr += " "
					fstr += r["modulation"]

					if parm.system == eDVBFrontendParametersSatellite.System_DVB_S2:
						parm.rolloff = d["rolloff"]
						parm.pilot = d["pilot"]
						parm.is_id = -1
						parm.pls_mode = eDVBFrontendParametersSatellite.PLS_Unknown
						parm.pls_code = 0

					if self.auto_scan:
						print "LOCKED at", freq
					else:
						print "LOCKED at", freq, "SEARCHED at", self.parm.frequency, "half bw", (135L*((sr+1000)/1000)/200), "half search range", (self.parm.symbol_rate/2)
						self.parm.frequency = freq
						self.parm.frequency += (135L*((sr+999)/1000)/200)
						self.parm.frequency += self.parm.symbol_rate/2

					if freq < self.min_freq or freq > self.max_freq:
						print "SKIPPED", freq, "out of search range"
					else:
						self.__tlist.append(parm)
						bm = state.getConstellationBitmap(5)
						self.tp_found.append((fstr, bm))
						state.updateConstellation(bm)

					if len(self.tp_found):
						state["list"].updateList(self.tp_found)
					else:
						state["list"].setList(self.tp_found)
						state["list"].setIndex(0)
			elif frontend_ptr:
				if self.auto_scan: #when driver based auto scan is used we got a tuneFailed event when the scan has scanned the last frequency...
					freq_old = self.parm.frequency
					sr_old = self.parm.symbol_rate
					self.parm = self.setNextRange()
					self.driver_wa = self.parm is not None and freq_old == self.parm.frequency and sr_old == self.parm.symbol_rate
				else:
					self.parm.frequency += self.parm.symbol_rate

			if self.auto_scan:
				freq = d["frequency"]

				# Hack for C-Band
				if self.scan_sat.bs_freq_limits[0] == 3400000 and self.scan_sat.bs_freq_limits[1] == 4200000:
					tuned_freq = abs(band_base_freq - 5150000)
					tune_offs = band_base_freq - tuned_freq
					freq -= tune_offs
					freq = 5150000 - freq

				mhz_complete, mhz_done = self.stats(freq)

				print "CURRENT freq", freq, "%d/%d" %(mhz_done, mhz_complete)

				check_finished = self.parm is None
			else:
				print "NEXT freq", self.parm.frequency
				mhz_complete, mhz_done = self.stats()
				check_finished = self.parm.frequency > self.range_list[self.current_range][1]
				if check_finished:
					self.parm = self.setNextRange()

			seconds_done = int(time() - self.start_time)

			if check_finished:
				if self.parm is None:
					tmpstr = _("%dMHz scanned") %mhz_complete
					tmpstr += ', '
					tmpstr += _("%d transponders found at %d:%02dmin") %(len(self.tp_found),seconds_done / 60, seconds_done % 60)
					state["progress"].setText(tmpstr)
					state.setFinished()

					self.frontendStateChanged_conn = None
					self.frontend = None
					self.channel = None
					self.updateStateTimer_conn = None
					self.updateStateTimer = None
					return

			if self.auto_scan:
				tmpstr = str((freq+500)/1000)
			else:
				tmpstr = str((self.parm.frequency+500)/1000)

			if self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Horizontal:
				tmpstr += "H"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_Vertical:
				tmpstr += "V"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularLeft:
				tmpstr += "L"
			elif self.parm.polarisation == eDVBFrontendParametersSatellite.Polarisation_CircularRight:
				tmpstr += "R"

			tmpstr += ', '
			tmpstr += "%d/%dMHz" %(mhz_done, mhz_complete)

			tmpstr += ", "
			tmpstr += _("%d transponder(s) found") %len(self.tp_found)

			tmpstr += ', '

			seconds_complete = (seconds_done * mhz_complete) / max(mhz_done, 1)
			tmpstr += _("%d:%02d/%d:%02dmin") %(seconds_done / 60, seconds_done % 60, seconds_complete / 60, seconds_complete % 60)

			state["progress"].setText(tmpstr)

			if self.auto_scan:
				self.updateStateTimer.start(1000, True)

			if not self.auto_scan or frontend_ptr is not None:
				if self.driver_wa:
					self.driver_wa = self.parm.symbol_rate
					self.parm.symbol_rate = 12345000
					tparm = eDVBFrontendParameters()
					tparm.setDVBS(self.parm, False)
					self.frontend.tune(tparm)
				else:
					self.tuneNext()
		elif tuner_state != stateTuning:
			print "unhandled tuner state", tuner_state

	def tuneNext(self):
		tparm = eDVBFrontendParameters()
		tparm.setDVBS(self.parm, False)
		self.frontend.tune(tparm)

	def setNextRange(self):
		if self.current_range is None:
			self.current_range = 0
		else:
			self.current_range += 1
		if len(self.range_list) > self.current_range:
			bs_range = self.range_list[self.current_range]
			print "Sat Blindscan current range", bs_range
			parm = eDVBFrontendParametersSatellite()

			# Hack for C-Band
			limits = self.scan_sat.bs_freq_limits
			idx = 1 if self.auto_scan and limits[0] == 3400000 and limits[1] == 4200000 else 0
			parm.frequency = bs_range[idx]

			if self.nim.isCompatible("DVB-S2"):
				steps = { 5 : 2000, 4 : 4000, 3 : 6000, 2 : 8000, 1 : 10000 }[self.scan_sat.bs_accuracy.value]
				parm.system = self.scan_sat.bs_system.value
				parm.pilot = eDVBFrontendParametersSatellite.Pilot_Unknown
				parm.rolloff = eDVBFrontendParametersSatellite.RollOff_alpha_0_35
			else:
				steps = 4000
				parm.system = eDVBFrontendParametersSatellite.System_DVB_S
			if self.auto_scan:
				parm.symbol_rate = (bs_range[1] - bs_range[0]) / 1000
			else:
				parm.symbol_rate = steps
			parm.fec = eDVBFrontendParametersSatellite.FEC_Auto
			parm.inversion = eDVBFrontendParametersSatellite.Inversion_Unknown
			parm.polarisation = bs_range[2]
			parm.orbital_position = self.orb_pos
			parm.modulation = eDVBFrontendParametersSatellite.Modulation_QPSK
			return parm
		return None

	def stats(self, freq=None):
		if freq is None:
			freq = self.parm.frequency
		mhz_complete = 0
		mhz_done = 0
		cnt = 0
		for range in self.range_list:
			mhz = (range[1] - range[0]) / 1000
			mhz_complete += mhz
			if cnt == self.current_range:
				# Hack for C-Band
				limits = self.scan_sat.bs_freq_limits
				if self.auto_scan and limits[0] == 3400000 and limits[1] == 4200000:
					mhz_done += (range[1] - freq) / 1000
				else:
					mhz_done += (freq - range[0]) / 1000
			elif cnt < self.current_range:
				mhz_done += mhz
			cnt += 1
		return mhz_complete, mhz_done

	def startSatelliteTransponderSearch(self, nim_idx, orb_pos):
		self.frontend = None
		self.orb_pos = orb_pos
		self.nim = nimmanager.nim_slots[nim_idx]
		tunername = nimmanager.getNimName(nim_idx)
		self.__tlist = [ ]
		self.tp_found = [ ]
		self.current_range = None
		self.range_list = [ ]
		tuner_no = -1
		self.auto_scan = False
		self.driver_wa = False

		self.auto_scan = tunername.startswith('Si216')
		if self.auto_scan or tunername in ("BCM4505", "BCM4506 (internal)", "BCM4506", "Alps BSBE1 C01A/D01A."):
			(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
			if not self.frontend:
				self.session.nav.stopService()
				(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
				if not self.frontend:
					if self.session.pipshown: # try to disable pip
						self.session.pipshown = False
						self.session.deleteDialog(self.session.pip)
						del self.session.pip
					(self.channel, self.frontend) = self.tryGetRawFrontend(nim_idx, False, False)
					if not self.frontend:
						print "couldn't allocate tuner %d for blindscan!!!" %nim_idx
						return
			self.frontendStateChanged_conn = self.frontend.getStateChangeSignal().connect(self.frontendStateChangedSat)

			band_cutoff_frequency = self.nim_sat_band_cutoff_frequency[nim_idx][orb_pos][0]

			s1 = self.scan_sat.bs_freq_start.value * 1000
			s2 = self.scan_sat.bs_freq_stop.value * 1000

			start = self.min_freq = min(s1,s2)
			stop = self.max_freq = max(s1,s2)

			if self.auto_scan: # hack for driver based blindscan... extend search range +/- 50Mhz
				limits = self.scan_sat.bs_freq_limits
				start -= 50000
				stop += 50000
				if start < limits[0]:
					start = limits[0]
				if stop >limits[1]:
					stop = limits[1]

			if self.scan_sat.bs_horizontal.value:
				if self.auto_scan and band_cutoff_frequency and stop > band_cutoff_frequency:
					if start < band_cutoff_frequency:
						self.range_list.append((start, min(stop, band_cutoff_frequency), eDVBFrontendParametersSatellite.Polarisation_Horizontal))
					if stop > band_cutoff_frequency:
						self.range_list.append((max(band_cutoff_frequency, start), stop, eDVBFrontendParametersSatellite.Polarisation_Horizontal))
				else:
					self.range_list.append((start, stop, eDVBFrontendParametersSatellite.Polarisation_Horizontal))

			if self.scan_sat.bs_vertical.value:
				if self.auto_scan and band_cutoff_frequency:
					if start < band_cutoff_frequency:
						self.range_list.append((start, min(stop, band_cutoff_frequency), eDVBFrontendParametersSatellite.Polarisation_Vertical))
					if stop > band_cutoff_frequency:
						self.range_list.append((max(band_cutoff_frequency, start), stop, eDVBFrontendParametersSatellite.Polarisation_Vertical))
				else:
					self.range_list.append((start, stop, eDVBFrontendParametersSatellite.Polarisation_Vertical))

			self.parm = self.setNextRange()
			if self.parm is not None:
				tparm = eDVBFrontendParameters()
				tparm.setDVBS(self.parm, False)
				self.frontend.tune(tparm)
				self.start_time = time()
				tmpstr = _("Try to find used satellite transponders...")
			else:
				tmpstr = _("Nothing to scan! Press Exit!")
			x = { }
			self.frontend.getFrontendData(x)
			tuner_no = x["tuner_number"]
		else:
			tmpstr = _("Blindscan is not supported by this tuner (%s)") %tunername
		self.satellite_search_session = self.session.openWithCallback(self.satelliteTransponderSearchSessionClosed, SatBlindscanState, tuner_no, tmpstr)
		if self.auto_scan:
			self.updateStateTimer = eTimer()
			self.updateStateTimer_conn = self.updateStateTimer.timeout.connect(self.updateStateSat)
			self.updateStateTimer.start(1000, True)

class DefaultSatLists(DefaultWizard):
	def __init__(self, session, silent = True, showSteps = False, default = False):
		self.xmlfile = "defaultsatlists.xml"
		DefaultWizard.__init__(self, session, silent, showSteps, neededTag = "services", default = default)
		print "configuredSats:", nimmanager.getConfiguredSats()

	def setDirectory(self):
		self.directory = []
		self.directory.append(resolveFilename(SCOPE_DEFAULTDIR))
		import os
		os.system("mount %s %s" % (resolveFilename(SCOPE_DEFAULTPARTITION), resolveFilename(SCOPE_DEFAULTPARTITIONMOUNTDIR)))
		self.directory.append(resolveFilename(SCOPE_DEFAULTPARTITIONMOUNTDIR))

	def statusCallback(self, status, progress):
		print "statusCallback:", status, progress
		from Components.DreamInfoHandler import DreamInfoHandler
		if status == DreamInfoHandler.STATUS_DONE:
			self["text"].setText(_("The installation of the default services lists is finished.") + "\n\n" + _("Please press OK to continue."))
			self.markDone()
			self.disableKeys = False

class ScanSetup(ConfigListScreen, Screen, TransponderSearchSupport, CableTransponderSearchSupport, SatelliteTransponderSearchSupport, TerrestrialTransponderSearchSupport):
	def __init__(self, session, systems_enabled = "SCT"):
		Screen.__init__(self, session)

		self.systems_enabled = systems_enabled
		self.finished_cb = None
		self.updateSatList()
		self.service = session.nav.getCurrentService()
		self.feinfo = None
		frontendData = None
		if self.service is not None:
			self.feinfo = self.service.frontendInfo()
			frontendData = self.feinfo and self.feinfo.getAll(True)

		self.createConfig(frontendData)

		del self.feinfo
		del self.service

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		if not self.scan_nims.value == "":
			self.createSetup()
			self["introduction"] = Label(_("Press OK to start the scan"))
		else:
			self["introduction"] = Label(_("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."))

	def runAsync(self, finished_cb):
		self.finished_cb = finished_cb
		self.keyGo()

	def updateSatList(self):
		self.satList = []
		for slot in nimmanager.nim_slots:
			if slot.isCompatible("DVB-S"):
				self.satList.append(nimmanager.getSatListForNim(slot.slot))
			else:
				self.satList.append(None)

	# systemChanged and satSystemChanged are needed for compatibility
	# with some DVB-S(2) specific plugins like satfinder, positioner setup...
	# no desire to adjust the whole plugins ;-)

	# notifier for self.scan_system
	def systemChanged(self, configElement):
		if configElement.value == "DVB-S":
			if self.scan_sat.system.value != eDVBFrontendParametersSatellite.System_DVB_S:
				self.scan_sat.system.value = eDVBFrontendParametersSatellite.System_DVB_S
		elif configElement.value == "DVB-S2":
			if self.scan_sat.system.value != eDVBFrontendParametersSatellite.System_DVB_S2:
				self.scan_sat.system.value = eDVBFrontendParametersSatellite.System_DVB_S2

	# notifier for self.scan_sat.system
	def satSystemChanged(self, configElement):
		if configElement.value == eDVBFrontendParametersSatellite.System_DVB_S:
			if self.scan_system.value != "DVB-S":
				self.scan_system.value = "DVB-S"
		elif configElement.value == eDVBFrontendParametersSatellite.System_DVB_S2:
			if self.scan_system.value != "DVB-S2":
				self.scan_system.value = "DVB-S2"

	def createSetup(self):
		self.list = []
		self.multiscanlist = []
		if self.scan_nims.value == "":
			return
		index_to_scan = int(self.scan_nims.value)
		print "ID: ", index_to_scan

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims)
		self.list.append(self.tunerEntry)

		if self.scan_nims == [ ]:
			return

		try:
			oldTypeOfScan = self.typeOfScanEntry[1].value
		except:
			oldTypeOfScan = None

		self.typeOfScanEntry = None
		self.plpidAutoEntry = None
		self.fecEntry = None
		self.systemEntry = None
		self.modulationEntry = None
		self.satelliteEntry = None
		self.enableMisEntry = None
		self.plsModeEntry = None
		nim = nimmanager.nim_slots[index_to_scan]

		if self.scan_system.value in ("DVB-S", "DVB-S2"):
			self.typeOfScanEntry = getConfigListEntry(_("Type of scan"), self.scan_type)
			self.list.append(self.typeOfScanEntry)
		elif self.scan_system.value == "DVB-C":
			self.typeOfScanEntry = getConfigListEntry(_("Type of scan"), self.scan_typecable)
			self.list.append(self.typeOfScanEntry)
		elif self.scan_system.value in ("DVB-T", "DVB-T2"):
			self.typeOfScanEntry = getConfigListEntry(_("Type of scan"), self.scan_typeterrestrial)
			self.list.append(self.typeOfScanEntry)

		# try to use the same scan type after system change
		current = self.typeOfScanEntry[1].value
		if oldTypeOfScan and current != oldTypeOfScan:
			# we map complete to multisat_yes and vice versa
			if oldTypeOfScan == "complete" and self.scan_system.value in ("DVB-S", "DVB-S2"):
				oldTypeOfScan = "multisat_yes"
			elif oldTypeOfScan == "multisat_yes" and self.scan_system.value in ("DVB-T", "DVB-T2", "DVB-C"):
				oldTypeOfScan = "complete"
			choices = self.typeOfScanEntry[1].getChoices()
			for ch in choices:
				if ch[0] == oldTypeOfScan:
					self.typeOfScanEntry[1].value = oldTypeOfScan
					break

		if self.typeOfScanEntry[1].value == 'single_transponder':
			self.scan_system.setChoices(self.systems)
		else:
			self.scan_system.setChoices(self.systems_filtered)

		if len(self.scan_system.getChoices()) > 1:
			self.systemEntry = getConfigListEntry(_('System'), self.scan_system)
			self.list.append(self.systemEntry)

		self.scan_networkScan.value = False
		self.scan_otherSDT.value = False
		if self.scan_system.value in ("DVB-S", "DVB-S2"):
			if self.scan_type.value == "single_transponder":
				self.updateSatList()
				self.list.append(getConfigListEntry(_('Satellite'), self.scan_satselection[index_to_scan]))
				self.list.append(getConfigListEntry(_('Frequency'), self.scan_sat.frequency))
				self.list.append(getConfigListEntry(_('Inversion'), self.scan_sat.inversion))
				self.list.append(getConfigListEntry(_('Symbol rate'), self.scan_sat.symbolrate))
				self.list.append(getConfigListEntry(_('Polarization'), self.scan_sat.polarization))
				if self.scan_system.value == "DVB-S":
					self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec))
				elif self.scan_system.value == "DVB-S2":
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
			elif self.scan_type.value == "single_satellite":
				self.updateSatList()
				self.list.append(getConfigListEntry(_("Satellite"), self.scan_satselection[index_to_scan]))
				self.scan_networkScan.value = True
			elif self.scan_type.value == "blind_scan":
				self.updateSatList()
				selected_sat_pos = self.scan_satselection[index_to_scan].value
				limit_list = self.nim_sat_frequency_range[index_to_scan][int(selected_sat_pos)]
				l = limit_list[0]
				self.scan_sat.bs_freq_limits = l
				limits = ( l[0]/1000, l[1]/1000 )

				# Hack for C-Band
				if limits[0] == 6100 and limits[1] == 7300:
					limits = ( 3400, 4200 )
					self.scan_sat.bs_freq_limits = ( limits[0]*1000, limits[1]*1000 )

				self.scan_sat.bs_freq_start = ConfigInteger(default = limits[0], limits = (limits[0], limits[1]))
				self.scan_sat.bs_freq_stop = ConfigInteger(default = limits[1], limits = (limits[0], limits[1]))
				self.satelliteEntry = getConfigListEntry(_("Satellite"), self.scan_satselection[index_to_scan])
				self.list.append(self.satelliteEntry)
				self.list.append(getConfigListEntry(_("Frequency start"), self.scan_sat.bs_freq_start))
				self.list.append(getConfigListEntry(_("Frequency stop"), self.scan_sat.bs_freq_stop))
				tunername = nimmanager.getNimName(index_to_scan)
				if nim.isCompatible("DVB-S2") and not tunername.startswith('Si216'):
					self.list.append(getConfigListEntry(_("Accuracy (higher is better)"), self.scan_sat.bs_accuracy))
				self.list.append(getConfigListEntry(_("Horizontal"), self.scan_sat.bs_horizontal))
				self.list.append(getConfigListEntry(_("Vertical"), self.scan_sat.bs_vertical))
			elif self.scan_type.value.find("multisat") != -1:
				tlist = []
				SatList = nimmanager.getSatListForNim(index_to_scan)
				for x in SatList:
					if self.Satexists(tlist, x[0]) == 0:
						tlist.append(x[0])
						sat = ConfigOnOff(default = self.scan_type.value.find("_yes") != -1 and True or False)
						configEntry = getConfigListEntry(nimmanager.getSatDescription(x[0]), sat)
						self.list.append(configEntry)
						self.multiscanlist.append((x[0], sat))
				self.scan_networkScan.value = True
		elif self.scan_system.value == "DVB-C":
			if self.scan_typecable.value == "single_transponder":
				self.list.append(getConfigListEntry(_("Frequency"), self.scan_cab.frequency))
				self.list.append(getConfigListEntry(_("Inversion"), self.scan_cab.inversion))
				self.list.append(getConfigListEntry(_("Symbol rate"), self.scan_cab.symbolrate))
				self.modulationEntry = getConfigListEntry(_('Modulation'), nim.can_modulation_auto and self.scan_cab.modulation_auto or self.scan_cab.modulation)
				self.list.append(self.modulationEntry)
				self.list.append(getConfigListEntry(_("FEC"), self.scan_cab.fec))
			elif nim.description == "ATBM781x" and self.scan_typecable.value == "complete":
				# the transponder searching of the external transponder search helper is not so good
				# for this frontend... so we enable network searching as default
				self.scan_networkScan.value = True
		elif self.scan_system.value in ("DVB-T", "DVB-T2"):
			if self.scan_typeterrestrial.value == "single_transponder":
				base_path = self.scan_ter if self.scan_system.value == "DVB-T" else self.scan_ter2
				self.list.append(getConfigListEntry(_("Frequency"), self.scan_ter.frequency))
				self.list.append(getConfigListEntry(_("Bandwidth"), base_path.bandwidth))
				self.list.append(getConfigListEntry(_("Inversion"), self.scan_ter.inversion))
				self.list.append(getConfigListEntry(_("Modulation"), base_path.modulation))
				self.list.append(getConfigListEntry(_("Transmission mode"), base_path.transmission))
				self.list.append(getConfigListEntry(_("Guard interval"), base_path.guard))
				if base_path == self.scan_ter2:
					self.list.append(getConfigListEntry(_("FEC"), self.scan_ter2.fec))
					self.plpidAutoEntry = getConfigListEntry(_("PLP ID Auto"), base_path.plp_id_auto)
					self.list.append(self.plpidAutoEntry)
					if not base_path.plp_id_auto.value:
						self.list.append(getConfigListEntry(_("PLP ID"), base_path.plp_id))
				else:
					self.list.append(getConfigListEntry(_("Hierarchy info"), self.scan_ter.hierarchy))
					self.list.append(getConfigListEntry(_("Code rate HP"), base_path.crh))
					self.list.append(getConfigListEntry(_("Code rate LP"), base_path.crl))

		self.list.append(getConfigListEntry(_("Network scan"), self.scan_networkScan))
		self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices))
		self.list.append(getConfigListEntry(_("Only Free scan"), self.scan_onlyfree))
		if config.usage.setup_level.index >= 2:
			self.list.append(getConfigListEntry(_("Lookup other SDT"), self.scan_otherSDT))
			self.list.append(getConfigListEntry(_("Skip empty transponders"), self.scan_skipEmpty))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0

	def newConfig(self):
		cur = self["config"].getCurrent()
		print "cur is", cur
		if cur is None:
			pass
		elif cur == self.typeOfScanEntry or \
			cur == self.tunerEntry or \
			(self.systemEntry and cur == self.systemEntry) or \
			(self.modulationEntry and cur == self.modulationEntry) or \
			(self.satelliteEntry and cur == self.satelliteEntry) or \
			(self.enableMisEntry and cur == self.enableMisEntry) or \
			(self.plsModeEntry and cur == self.plsModeEntry) or \
			(self.plpidAutoEntry and cur == self.plpidAutoEntry):
			self.createSetup()

	def nimChanged(self, configElement):
		choices = configElement.getChoices()
		nim_idx = choices[configElement.index][2]
		nim = nimmanager.nim_slots[nim_idx]

		systems = [ ]
		systems_filtered = [ ]
		if 'S' in self.systems_enabled:
			s2_en = nim.isEnabled("DVB-S2")
			if s2_en:
				systems.append(("DVB-S2", _("DVB-S2")))
				systems_filtered.append(("DVB-S2", _("DVB-S2")))
			if nim.isEnabled("DVB-S"):
				systems.append(("DVB-S", _("DVB-S")))
				if not s2_en:
					systems_filtered.append(("DVB-S", _("DVB-S")))

		if 'C' in self.systems_enabled and nim.isEnabled("DVB-C"):
			systems.append(("DVB-C", _("DVB-C")))
			systems_filtered.append(("DVB-C", _("DVB-C")))

		if 'T' in self.systems_enabled:
			t2_en = nim.isEnabled("DVB-T2")
			if t2_en:
				systems.append(("DVB-T2", _("DVB-T2")))
				systems_filtered.append(("DVB-T2", _("DVB-T2")))
			if nim.isEnabled("DVB-T"):
				systems.append(("DVB-T", _("DVB-T")))
				if not t2_en:
					systems_filtered.append(("DVB-T", _("DVB-T")))

		self.systems = systems
		self.systems_filtered = systems_filtered

		# for compability with old plugins...
		self.scan_sat.system = ConfigSelection(default = eDVBFrontendParametersSatellite.System_DVB_S, choices = [
			(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S")),
			(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S2"))])
		self.scan_sat.system.addNotifier(self.satSystemChanged, False, True, False)

		if nim_idx == self.tuned_slot:
			if self.tuned_type == feSatellite:
				system = self.defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S and "DVB-S" or "DVB-S2"
			elif self.tuned_type == feCable:
				system = "DVB-C"
			elif self.tuned_type == feTerrestrial:
				system = self.defaultTer["system"] == eDVBFrontendParametersTerrestrial.System_DVB_T and "DVB-T" or "DVB-T2"
			self.scan_system = ConfigSelection(default = system, choices = systems)
		else:
			self.scan_system = ConfigSelection(choices = systems)

		self.scan_system.addNotifier(self.systemChanged)

		self.scan_sat.pilot.value = eDVBFrontendParametersSatellite.Pilot_Unknown
		if nim.can_modulation_auto:
			self.scan_sat.modulation_auto.value = eDVBFrontendParametersSatellite.Modulation_Auto
			self.scan_cab.modulation_auto.value = eDVBFrontendParametersSatellite.Modulation_Auto
		if nim.can_auto_fec_s2:
			self.scan_sat.fec_s2_8psk_auto.value = eDVBFrontendParametersSatellite.FEC_Auto
			self.scan_sat.fec_s2_qpsk_auto.value = eDVBFrontendParametersSatellite.FEC_Auto

	def createConfig(self, frontendData):
					   #("Type", frontendData["system"], TYPE_TEXT),
					   #("Modulation", frontendData["modulation"], TYPE_TEXT),
					   #("Orbital position", frontendData["orbital_position"], TYPE_VALUE_DEC),
					   #("Frequency", frontendData["frequency"], TYPE_VALUE_DEC),
					   #("Symbolrate", frontendData["symbol_rate"], TYPE_VALUE_DEC),
					   #("Polarization", frontendData["polarization"], TYPE_TEXT),
					   #("Inversion", frontendData["inversion"], TYPE_TEXT),
					   #("FEC inner", frontendData["fec_inner"], TYPE_TEXT),
				   		#)
		#elif frontendData["tuner_type"] == "DVB-C":
			#return ( ("NIM", ['A', 'B', 'C', 'D'][frontendData["tuner_number"]], TYPE_TEXT),
					   #("Type", frontendData["tuner_type"], TYPE_TEXT),
					   #("Frequency", frontendData["frequency"], TYPE_VALUE_DEC),
					   #("Symbolrate", frontendData["symbol_rate"], TYPE_VALUE_DEC),
					   #("Modulation", frontendData["modulation"], TYPE_TEXT),
					   #("Inversion", frontendData["inversion"], TYPE_TEXT),
			#		   ("FEC inner", frontendData["fec_inner"], TYPE_TEXT),
				   		#)
		#elif frontendData["tuner_type"] == "DVB-T":
			#return ( ("NIM", ['A', 'B', 'C', 'D'][frontendData["tuner_number"]], TYPE_TEXT),
					   #("Type", frontendData["tuner_type"], TYPE_TEXT),
					   #("Frequency", frontendData["frequency"], TYPE_VALUE_DEC),
					   #("Inversion", frontendData["inversion"], TYPE_TEXT),
					   #("Bandwidth", frontendData["bandwidth"], TYPE_VALUE_DEC),
					   #("CodeRateLP", frontendData["code_rate_lp"], TYPE_TEXT),
					   #("CodeRateHP", frontendData["code_rate_hp"], TYPE_TEXT),
					   #("Constellation", frontendData["constellation"], TYPE_TEXT),
					   #("Transmission Mode", frontendData["transmission_mode"], TYPE_TEXT),
					   #("Guard Interval", frontendData["guard_interval"], TYPE_TEXT),
					   #("Hierarchy Inform.", frontendData["hierarchy_information"], TYPE_TEXT),

			defaultSat = {
				"orbpos": 192,
				"system": eDVBFrontendParametersSatellite.System_DVB_S,
				"frequency": 11836,
				"inversion": eDVBFrontendParametersSatellite.Inversion_Unknown,
				"symbolrate": 27500,
				"polarization": eDVBFrontendParametersSatellite.Polarisation_Horizontal,
				"fec": eDVBFrontendParametersSatellite.FEC_Auto,
				"fec_s2_8psk": eDVBFrontendParametersSatellite.FEC_2_3,
				"fec_s2_qpsk": eDVBFrontendParametersSatellite.FEC_2_3,
				"modulation": eDVBFrontendParametersSatellite.Modulation_QPSK,
				"is_id" : -1,
				"pls_mode" : eDVBFrontendParametersSatellite.PLS_Unknown,
				"pls_code" : 0 }
			defaultCab = {
				"frequency": 466,
				"inversion": eDVBFrontendParametersCable.Inversion_Unknown,
				"modulation": eDVBFrontendParametersCable.Modulation_QAM64,
				"fec": eDVBFrontendParametersCable.FEC_Auto,
				"symbolrate": 6900 }
			defaultTer = {
				"system" : eDVBFrontendParametersTerrestrial.System_DVB_T,
				"frequency" : 466000,
				"inversion" : eDVBFrontendParametersTerrestrial.Inversion_Unknown,
				"bandwidth" : eDVBFrontendParametersTerrestrial.Bandwidth_8MHz,
				"crh" : eDVBFrontendParametersTerrestrial.FEC_Auto,
				"crl" : eDVBFrontendParametersTerrestrial.FEC_Auto,
				"fec" : eDVBFrontendParametersTerrestrial.FEC_Auto,
				"modulation" : eDVBFrontendParametersTerrestrial.Modulation_Auto,
				"transmission_mode" : eDVBFrontendParametersTerrestrial.TransmissionMode_Auto,
				"guard_interval" : eDVBFrontendParametersTerrestrial.GuardInterval_Auto,
				"hierarchy": eDVBFrontendParametersTerrestrial.Hierarchy_Auto,
				"plp_id": -1
				}

			slot_number = -1
			ttype = 0
			if frontendData is not None:
				slot_number = frontendData.get("slot_number", -1)
				ttype = frontendData.get("tuner_type", 0)

			if slot_number != -1 and ttype:
				self.tuned_slot = slot_number
				self.tuned_type = ttype
				if ttype == feSatellite:
					defaultSat["system"] = frontendData.get("system", eDVBFrontendParametersSatellite.System_DVB_S)
					defaultSat["frequency"] = frontendData.get("frequency", 0) / 1000
					defaultSat["inversion"] = frontendData.get("inversion", eDVBFrontendParametersSatellite.Inversion_Unknown)
					defaultSat["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
					defaultSat["polarization"] = frontendData.get("polarization", eDVBFrontendParametersSatellite.Polarisation_Horizontal)
					defaultSat["modulation"] = frontendData.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK)
					if defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S2:
						if defaultSat["modulation"] == eDVBFrontendParametersSatellite.Modulation_QPSK:
							defaultSat["fec_s2_qpsk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_2_3)
						else:
							defaultSat["fec_s2_8psk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_2_3)
						defaultSat["rolloff"] = frontendData.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35)
						defaultSat["pilot"] = frontendData.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown)
						defaultSat["is_id"] = frontendData.get("is_id", -1)
						defaultSat["pls_mode"] = frontendData.get("pls_mode", eDVBFrontendParametersSatellite.PLS_Unknown)
						defaultSat["pls_code"] = frontendData.get("pls_code", 0)
					defaultSat["orbpos"] = frontendData.get("orbital_position", 0)
				elif ttype == feCable:
					defaultCab["frequency"] = frontendData.get("frequency", 0) / 1000
					defaultCab["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
					defaultCab["inversion"] = frontendData.get("inversion", eDVBFrontendParametersCable.Inversion_Unknown)
					defaultCab["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersCable.FEC_Auto)
					defaultCab["modulation"] = frontendData.get("modulation", eDVBFrontendParametersCable.Modulation_QAM16)
				elif ttype == feTerrestrial:
					defaultTer["system"] = frontendData.get("system", eDVBFrontendParametersTerrestrial.System_DVB_T)
					defaultTer["frequency"] = frontendData.get("frequency", 0)
					defaultTer["inversion"] = frontendData.get("inversion", eDVBFrontendParametersTerrestrial.Inversion_Unknown)
					defaultTer["bandwidth"] = frontendData.get("bandwidth", eDVBFrontendParametersTerrestrial.Bandwidth_8MHz)
					defaultTer["crh"] = frontendData.get("code_rate_hp", eDVBFrontendParametersTerrestrial.FEC_Auto)
					defaultTer["crl"] = frontendData.get("code_rate_lp", eDVBFrontendParametersTerrestrial.FEC_Auto)
					defaultTer["modulation"] = frontendData.get("constellation", eDVBFrontendParametersTerrestrial.Modulation_Auto)
					defaultTer["transmission_mode"] = frontendData.get("transmission_mode", eDVBFrontendParametersTerrestrial.TransmissionMode_Auto)
					defaultTer["guard_interval"] = frontendData.get("guard_interval", eDVBFrontendParametersTerrestrial.GuardInterval_Auto)
					defaultTer["hierarchy"] = frontendData.get("hierarchy_information", eDVBFrontendParametersTerrestrial.Hierarchy_Auto)
					defaultTer["plp_id"] = frontendData.get("plp_id", -1)
			else:
				slot_number = 0
				self.tuned_slot = -1

			self.defaultTer = defaultTer
			self.defaultCab = defaultCab
			self.defaultSat = defaultSat 

			self.scan_sat = ConfigSubsection()
			self.scan_cab = ConfigSubsection()
			self.scan_ter = ConfigSubsection()
			self.scan_ter2 = ConfigSubsection()

			self.scan_type = ConfigSelection(default = "single_transponder", choices = [("single_transponder", _("Single transponder")), ("single_satellite", _("Single satellite")), ("multisat", _("Multisat")), ("multisat_yes", _("Multisat")), ("blind_scan", _("Blindscan"))])
			self.scan_typecable = ConfigSelection(default = "single_transponder", choices = [("single_transponder", _("Single transponder")), ("complete", _("Complete"))])
			self.scan_typeterrestrial = ConfigSelection(default = "single_transponder", choices = [("single_transponder", _("Single transponder")), ("complete", _("Complete"))])
			self.scan_clearallservices = ConfigSelection(default = "no", choices = [("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
			self.scan_onlyfree = ConfigYesNo(default = False)
			self.scan_networkScan = ConfigYesNo(default = False)
			self.scan_skipEmpty = ConfigYesNo(default = True)
			self.scan_otherSDT = ConfigYesNo(default = False)

			tuned_slot = None
			idx = -1
			nim_list = []
			# collect all nims which are *not* set to "nothing"
			for n in nimmanager.nim_slots:
				idx += 1
#				if n.config_mode == "nothing":
#					continue
#				if n.config_mode == "advanced" and len(nimmanager.getSatListForNim(n.slot)) < 1:
#					continue
#				if n.config_mode in ("loopthrough", "satposdepends"):
#					# Skip connected LNBs
#					continue
					# TODO: this would cause trouble if someone connects a S2 tuner to an S Tuner
					# If so i'd propose we automatically only show the "most capable" tuner:
					#  * the T2 tuner if it's connected with a T-only tuner
					#  * the S2 tuner when it's connected with a S-only tuner ...
					# Listing both would be required whenever non-backwards-compatible demods show up
					# Currently none if the above is actually possible
				if n.isEnabled('DVB-S') or n.isEnabled('DVB-C') or n.isEnabled('DVB-T'):
					nim_list.append((str(n.slot), n.friendly_full_description, idx))
					if idx == slot_number:
						tuned_slot = str(n.slot)

			if not nim_list:
				self.scan_nims = ConfigText('')
			if tuned_slot:
				self.scan_nims = ConfigSelection(choices = nim_list, default = tuned_slot)
			else:
				self.scan_nims = ConfigSelection(choices = nim_list)

			# status
			self.scan_snr = ConfigSlider()
			self.scan_snr.enabled = False
			self.scan_agc = ConfigSlider()
			self.scan_agc.enabled = False
			self.scan_ber = ConfigSlider()
			self.scan_ber.enabled = False

			# sat
			self.scan_sat.frequency = ConfigInteger(default = defaultSat["frequency"], limits = (1, 99999))
			self.scan_sat.inversion = ConfigSelection(default = defaultSat["inversion"], choices = [
				(eDVBFrontendParametersSatellite.Inversion_Off, _("Off")),
				(eDVBFrontendParametersSatellite.Inversion_On, _("On")),
				(eDVBFrontendParametersSatellite.Inversion_Unknown, _("Auto"))])
			self.scan_sat.symbolrate = ConfigInteger(default = defaultSat["symbolrate"], limits = (1, 99999))
			self.scan_sat.polarization = ConfigSelection(default = defaultSat["polarization"], choices = [
				(eDVBFrontendParametersSatellite.Polarisation_Horizontal, _("horizontal")),
				(eDVBFrontendParametersSatellite.Polarisation_Vertical, _("vertical")),
				(eDVBFrontendParametersSatellite.Polarisation_CircularLeft, _("circular left")),
				(eDVBFrontendParametersSatellite.Polarisation_CircularRight, _("circular right"))])
			self.scan_sat.fec = ConfigSelection(default = defaultSat["fec"], choices = [
				(eDVBFrontendParametersSatellite.FEC_Auto, _("Auto")),
				(eDVBFrontendParametersSatellite.FEC_1_2, "1/2"),
				(eDVBFrontendParametersSatellite.FEC_2_3, "2/3"),
				(eDVBFrontendParametersSatellite.FEC_3_4, "3/4"),
				(eDVBFrontendParametersSatellite.FEC_5_6, "5/6"),
				(eDVBFrontendParametersSatellite.FEC_7_8, "7/8"),
				(eDVBFrontendParametersSatellite.FEC_None, _("None"))])

			fec_s2_qpsk = [
				(eDVBFrontendParametersSatellite.FEC_1_2, "1/2"),
				(eDVBFrontendParametersSatellite.FEC_2_3, "2/3"),
				(eDVBFrontendParametersSatellite.FEC_3_4, "3/4"),
				(eDVBFrontendParametersSatellite.FEC_3_5, "3/5"),
				(eDVBFrontendParametersSatellite.FEC_4_5, "4/5"),
				(eDVBFrontendParametersSatellite.FEC_5_6, "5/6"),
				(eDVBFrontendParametersSatellite.FEC_8_9, "8/9"),
				(eDVBFrontendParametersSatellite.FEC_9_10, "9/10")]
			fec_s2_8psk = [
				(eDVBFrontendParametersSatellite.FEC_2_3, "2/3"),
				(eDVBFrontendParametersSatellite.FEC_3_4, "3/4"),
				(eDVBFrontendParametersSatellite.FEC_3_5, "3/5"),
				(eDVBFrontendParametersSatellite.FEC_5_6, "5/6"),
				(eDVBFrontendParametersSatellite.FEC_8_9, "8/9"),
				(eDVBFrontendParametersSatellite.FEC_9_10, "9/10")]
			self.scan_sat.fec_s2_qpsk = ConfigSelection(default = defaultSat["fec_s2_qpsk"], choices = fec_s2_qpsk[:])
			self.scan_sat.fec_s2_8psk = ConfigSelection(default = defaultSat["fec_s2_8psk"], choices = fec_s2_8psk[:])
			fec_s2_qpsk.insert(0,(eDVBFrontendParametersSatellite.FEC_Auto, _("Auto")))
			fec_s2_8psk.insert(0,(eDVBFrontendParametersSatellite.FEC_Auto, _("Auto")))
			self.scan_sat.fec_s2_qpsk_auto = ConfigSelection(default = defaultSat["fec_s2_qpsk"], choices = fec_s2_qpsk)
			self.scan_sat.fec_s2_8psk_auto = ConfigSelection(default = defaultSat["fec_s2_8psk"], choices = fec_s2_8psk)

			modulations = [
				(eDVBFrontendParametersSatellite.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersSatellite.Modulation_8PSK, "8PSK")]
			self.scan_sat.modulation = ConfigSelection(default = defaultSat["modulation"], choices = modulations[:])
			modulations.insert(0,(eDVBFrontendParametersSatellite.Modulation_Auto, _("Auto")))
			self.scan_sat.modulation_auto = ConfigSelection(default = defaultSat["modulation"], choices = modulations)

			self.scan_sat.rolloff = ConfigSelection(default = defaultSat.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35), choices = [
				(eDVBFrontendParametersSatellite.RollOff_alpha_0_35, "0.35"),
				(eDVBFrontendParametersSatellite.RollOff_alpha_0_25, "0.25"),
				(eDVBFrontendParametersSatellite.RollOff_alpha_0_20, "0.20")])
			self.scan_sat.pilot = ConfigSelection(default = defaultSat.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown), choices = [
				(eDVBFrontendParametersSatellite.Pilot_Off, _("Off")),
				(eDVBFrontendParametersSatellite.Pilot_On, _("On")),
				(eDVBFrontendParametersSatellite.Pilot_Unknown, _("Auto"))])
			self.scan_sat.enable_mis = ConfigYesNo(default = defaultSat["is_id"] != -1)
			self.scan_sat.is_id = ConfigInteger(default = defaultSat["is_id"] if defaultSat["is_id"] != -1 else 0, limits = (0, 255))
			self.scan_sat.pls_mode = ConfigSelection(default = defaultSat["pls_mode"], choices = [
				(eDVBFrontendParametersSatellite.PLS_Root, "Root"),
				(eDVBFrontendParametersSatellite.PLS_Gold, "Gold"),
				(eDVBFrontendParametersSatellite.PLS_Combo, "Combo"),
				(eDVBFrontendParametersSatellite.PLS_Unknown, "Auto")])
			self.scan_sat.pls_code = ConfigInteger(default = defaultSat["pls_code"], limits = (0, 262143))

			self.scan_sat.bs_system = ConfigSelection(default = eDVBFrontendParametersSatellite.System_DVB_S2, 
				choices = [ (eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S + DVB-S2")),
					(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S only"))])

			self.scan_sat.bs_accuracy = ConfigSelection(default = 2, choices = [ (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")])

			self.scan_sat.bs_horizontal = ConfigYesNo(default = True)
			self.scan_sat.bs_vertical = ConfigYesNo(default = True)

			# cable
			self.scan_cab.frequency = ConfigInteger(default = defaultCab["frequency"], limits = (50, 999))
			self.scan_cab.inversion = ConfigSelection(default = defaultCab["inversion"], choices = [
				(eDVBFrontendParametersCable.Inversion_Off, _("Off")),
				(eDVBFrontendParametersCable.Inversion_On, _("On")),
				(eDVBFrontendParametersCable.Inversion_Unknown, _("Auto"))])

			modulations = [
				(eDVBFrontendParametersCable.Modulation_QAM16, "16-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM32, "32-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM64, "64-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM128, "128-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM256, "256-QAM")]
			self.scan_cab.modulation = ConfigSelection(default = defaultCab["modulation"], choices = modulations[:])
			modulations.insert(0,(eDVBFrontendParametersCable.Modulation_Auto, _("Auto")))
			self.scan_cab.modulation_auto = ConfigSelection(default = defaultCab["modulation"], choices = modulations)

			self.scan_cab.fec = ConfigSelection(default = defaultCab["fec"], choices = [
				(eDVBFrontendParametersCable.FEC_Auto, _("Auto")),
				(eDVBFrontendParametersCable.FEC_1_2, "1/2"),
				(eDVBFrontendParametersCable.FEC_2_3, "2/3"),
				(eDVBFrontendParametersCable.FEC_3_4, "3/4"),
				(eDVBFrontendParametersCable.FEC_5_6, "5/6"),
				(eDVBFrontendParametersCable.FEC_7_8, "7/8"),
				(eDVBFrontendParametersCable.FEC_8_9, "8/9"),
				(eDVBFrontendParametersCable.FEC_None, _("None"))])
			self.scan_cab.symbolrate = ConfigInteger(default = defaultCab["symbolrate"], limits = (1, 99999))

			# terrestial
			self.scan_ter.frequency = ConfigInteger(default = 466000, limits = (50000, 999000))
			self.scan_ter.inversion = ConfigSelection(default = defaultTer["inversion"], choices = [
				(eDVBFrontendParametersTerrestrial.Inversion_Off, _("Off")),
				(eDVBFrontendParametersTerrestrial.Inversion_On, _("On")),
				(eDVBFrontendParametersTerrestrial.Inversion_Unknown, _("Auto"))])
			self.scan_ter.hierarchy = ConfigSelection(default = defaultTer["hierarchy"], choices = [
				(eDVBFrontendParametersTerrestrial.Hierarchy_None, _("None")),
				(eDVBFrontendParametersTerrestrial.Hierarchy_1, "1"),
				(eDVBFrontendParametersTerrestrial.Hierarchy_2, "2"),
				(eDVBFrontendParametersTerrestrial.Hierarchy_4, "4"),
				(eDVBFrontendParametersTerrestrial.Hierarchy_Auto, _("Auto"))])

			# DVB-T choices
			self.scan_ter.bandwidth = ConfigSelection(default = defaultTer["bandwidth"], choices = [
				(eDVBFrontendParametersTerrestrial.Bandwidth_8MHz, "8MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_7MHz, "7MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_6MHz, "6MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_5MHz, "5MHz")])
			self.scan_ter.crh = ConfigSelection(default = defaultTer["crh"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_7_8, "7/8"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter.crl = ConfigSelection(default = defaultTer["crl"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_7_8, "7/8"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter.modulation = ConfigSelection(default = defaultTer["modulation"], choices = [
				(eDVBFrontendParametersTerrestrial.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM16, "QAM16"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM64, "QAM64"),
				(eDVBFrontendParametersTerrestrial.Modulation_Auto, _("Auto"))])
			self.scan_ter.transmission = ConfigSelection(default = defaultTer["transmission_mode"], choices = [
				(eDVBFrontendParametersTerrestrial.TransmissionMode_2k, "2K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_4k, "4K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_8k, "8K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_Auto, _("Auto"))])
			self.scan_ter.guard = ConfigSelection(default = defaultTer["guard_interval"], choices = [
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_32, "1/32"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_16, "1/16"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_8, "1/8"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_4, "1/4"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_Auto, _("Auto"))])

			# DVB-T2 choices
			self.scan_ter2.bandwidth = ConfigSelection(default = defaultTer["bandwidth"], choices = [
				(eDVBFrontendParametersTerrestrial.Bandwidth_10MHz, "10MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_8MHz, "8MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_7MHz, "7MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_6MHz, "6MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_5MHz, "5MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_1_712MHz, "1.712MHz")])
			self.scan_ter2.fec = ConfigSelection(default = defaultTer["fec"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_3_5, "3/5"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_4_5, "4/5"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter2.modulation = ConfigSelection(default = defaultTer["modulation"], choices = [
				(eDVBFrontendParametersTerrestrial.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM16, "QAM16"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM64, "QAM64"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM256, "QAM256"),
				(eDVBFrontendParametersTerrestrial.Modulation_Auto, _("Auto"))])
			self.scan_ter2.transmission = ConfigSelection(default = defaultTer["transmission_mode"], choices = [
				(eDVBFrontendParametersTerrestrial.TransmissionMode_1k, "1K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_2k, "2K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_2k, "4K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_8k, "8K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_16k, "16K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_32k, "32K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_Auto, _("Auto"))])
			self.scan_ter2.guard = ConfigSelection(default = defaultTer["guard_interval"], choices = [
				(eDVBFrontendParametersTerrestrial.GuardInterval_19_256, "19/256"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_19_128, "19/128"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_128, "1/128"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_32, "1/32"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_16, "1/16"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_8, "1/8"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_4, "1/4"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_Auto, _("Auto"))])
			plp_id = defaultTer["plp_id"]
			self.scan_ter2.plp_id_auto = ConfigYesNo(default = plp_id == -1)
			self.scan_ter2.plp_id = ConfigInteger(default = 0 if plp_id == -1 else plp_id, limits = (0, 255))

			self.scan_scansat = {}
			for sat in nimmanager.satList:
				#print sat[1]
				self.scan_scansat[sat[0]] = ConfigYesNo(default = False)

			sec = secClass.getInstance()

			self.nim_sat_frequency_range = []
			self.nim_sat_band_cutoff_frequency = []
			self.scan_satselection = []
			for slot in nimmanager.nim_slots:
				slot_id = slot.slot
				if slot.isCompatible("DVB-S"):
					satlist_for_slot = self.satList[slot_id]
					self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], satlist_for_slot))
					sat_freq_range = { }
					sat_band_cutoff = { }
					for sat in satlist_for_slot:
						orbpos = sat[0]
						sat_freq_range[orbpos] = sec.getFrequencyRangeList(slot_id, orbpos)
						sat_band_cutoff[orbpos] = sec.getBandCutOffFrequency(slot_id, orbpos)
					self.nim_sat_frequency_range.append(sat_freq_range)
					self.nim_sat_band_cutoff_frequency.append(sat_band_cutoff)
				else:
					self.nim_sat_frequency_range.append(None)
					self.nim_sat_band_cutoff_frequency.append(None)
					self.scan_satselection.append(None)

			if self.scan_nims.value != '':
				self.scan_nims.addNotifier(self.nimChanged)

			return True

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def updateStatus(self):
		print "updatestatus"

	def addSatTransponder(self, tlist, frequency, symbol_rate, polarisation, fec, inversion, orbital_position, system, modulation, rolloff, pilot, is_id, pls_mode, pls_code):
		s = "Add Sat: frequ: " + str(frequency) + " symbol: " + str(symbol_rate) + " pol: " + str(polarisation) + " fec: " + str(fec) + " inversion: " + str(inversion) + " modulation: " + str(modulation) + " system: " + str(system) + " rolloff" + str(rolloff) + " pilot" + str(pilot)
		if is_id != -1:
			s += " is_id: " + str(is_id)
			if pls_mode != eDVBFrontendParametersSatellite.PLS_Unknown:
				s += "pls_mode: " + str(pls_mode) + " pls_code: " + str(pls_code)
		s += "\norbpos: " + str(orbital_position)
		print s
		parm = eDVBFrontendParametersSatellite()
		parm.modulation = modulation
		parm.system = system
		parm.frequency = frequency * 1000
		parm.symbol_rate = symbol_rate * 1000
		parm.polarisation = polarisation
		parm.fec = fec
		parm.inversion = inversion
		parm.orbital_position = orbital_position
		parm.rolloff = rolloff
		parm.pilot = pilot
		parm.is_id = is_id
		parm.pls_mode = pls_mode
		parm.pls_code = pls_code
		tlist.append(parm)

	def addCabTransponder(self, tlist, frequency, symbol_rate, modulation, fec, inversion):
		print "Add Cab: frequ: " + str(frequency) + " symbol: " + str(symbol_rate) + " pol: " + str(modulation) + " fec: " + str(fec) + " inversion: " + str(inversion)
		parm = eDVBFrontendParametersCable()
		parm.frequency = frequency * 1000
		parm.symbol_rate = symbol_rate * 1000
		parm.modulation = modulation
		parm.fec = fec
		parm.inversion = inversion
		tlist.append(parm)

	def addTerTransponder(self, tlist, *args, **kwargs):
		tlist.append(buildTerTransponder(*args, **kwargs))

	def keyGo(self):
		if self.scan_nims.value == "":
			return
		tlist = []
		flags = None
		startScan = True
		removeAll = True
		index_to_scan = int(self.scan_nims.value)

		if self.scan_nims == [ ]:
			self.session.open(MessageBox, _("No tuner is enabled!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			return

		nim = nimmanager.nim_slots[index_to_scan]
		print "nim", nim.slot
		if self.scan_system.value in ("DVB-S", "DVB-S2"):
			print "is compatible with DVB-S"
			if self.scan_type.value == "single_transponder":
				# these lists are generated for each tuner, so this has work.
				assert len(self.satList) > index_to_scan
				assert len(self.scan_satselection) > index_to_scan

				nimsats = self.satList[index_to_scan]
				selsatidx = self.scan_satselection[index_to_scan].index

				# however, the satList itself could be empty. in that case, "index" is 0 (for "None").
				if len(nimsats):
					orbpos = nimsats[selsatidx][0]
					if self.scan_system.value == "DVB-S":
						fec = self.scan_sat.fec.value
						mod = eDVBFrontendParametersSatellite.Modulation_QPSK
					else:
						mod = self.modulationEntry[1].value
						fec = self.fecEntry[1].value

					print "add sat transponder"
					self.addSatTransponder(tlist, self.scan_sat.frequency.value,
								self.scan_sat.symbolrate.value,
								self.scan_sat.polarization.value,
								fec,
								self.scan_sat.inversion.value,
								orbpos,
								eDVBFrontendParametersSatellite.System_DVB_S if self.scan_system.value == "DVB-S" else eDVBFrontendParametersSatellite.System_DVB_S2, 
								mod,
								self.scan_sat.rolloff.value,
								self.scan_sat.pilot.value,
								self.scan_sat.is_id.value if self.scan_sat.enable_mis.value else -1,
								self.scan_sat.pls_mode.value,
								self.scan_sat.pls_code.value if self.scan_sat.pls_mode.value < eDVBFrontendParametersSatellite.PLS_Unknown else 0)
				removeAll = False
			elif self.scan_type.value == "single_satellite":
				sat = self.satList[index_to_scan][self.scan_satselection[index_to_scan].index]
				getInitialTransponderList(tlist, sat[0])
			elif self.scan_type.value.find("multisat") != -1:
				for x in self.multiscanlist:
					if x[1].value:
						print "   " + str(x[0])
						getInitialTransponderList(tlist, x[0])
			elif self.scan_type.value.find("blind_scan") != -1:
				startScan = False

		elif self.scan_system.value == "DVB-C":
			if self.scan_typecable.value == "single_transponder":
				self.addCabTransponder(tlist, self.scan_cab.frequency.value,
							self.scan_cab.symbolrate.value,
							self.modulationEntry[1].value,
							self.scan_cab.fec.value,
							self.scan_cab.inversion.value)
				removeAll = False
			elif self.scan_typecable.value == "complete":
				if config.Nims[index_to_scan].cable.scan_type.value == "provider":
					getInitialCableTransponderList(tlist, index_to_scan)
				else:
					startScan = False

		elif self.scan_system.value in ("DVB-T", "DVB-T2"):
			if self.scan_typeterrestrial.value == "single_transponder":
				base_path = self.scan_ter if self.scan_system.value == "DVB-T" else self.scan_ter2
				self.addTerTransponder(tlist,
					system = eDVBFrontendParametersTerrestrial.System_DVB_T if self.scan_system.value == "DVB-T" else eDVBFrontendParametersTerrestrial.System_DVB_T2,
					frequency = self.scan_ter.frequency.value * 1000,
					inversion = self.scan_ter.inversion.value,
					bandwidth = base_path.bandwidth.value,
					crh = self.scan_ter.crh.value,
					crl = self.scan_ter.crl.value if base_path == self.scan_ter else base_path.fec.value,
					modulation = base_path.modulation.value,
					transmission = base_path.transmission.value,
					guard = base_path.guard.value,
					hierarchy = self.scan_ter.hierarchy.value,
					plp_id = -1 if base_path == self.scan_ter or base_path.plp_id_auto.value else base_path.plp_id.value
					)
				removeAll = False
			elif self.scan_typeterrestrial.value == "complete":
				tunername = nimmanager.getNimName(index_to_scan)
				getInitialTerrestrialTransponderList(tlist, nimmanager.getTerrestrialDescription(index_to_scan), tunername in can_t_t2_auto_delsys)

		flags = self.scan_networkScan.value and eComponentScan.scanNetworkSearch or 0

		if self.scan_otherSDT.value:
			flags |= eComponentScan.scanOtherSDT

		if not self.scan_skipEmpty.value:
			flags |= eComponentScan.scanDontSkipEmptyTransponders

		tmp = self.scan_clearallservices.value
		if tmp == "yes":
			flags |= eComponentScan.scanRemoveServices
		elif tmp == "yes_hold_feeds":
			flags |= eComponentScan.scanRemoveServices
			flags |= eComponentScan.scanDontRemoveFeeds

		if tmp != "no" and not removeAll:
			flags |= eComponentScan.scanDontRemoveUnscanned

		if self.scan_onlyfree.value:
			flags |= eComponentScan.scanOnlyFree

		for x in self["config"].list:
			x[1].save()

		if startScan:
			self.startScan(tlist, flags, index_to_scan)
		else:
			self.flags = flags
			self.feid = index_to_scan
			self.tlist = []
			if self.scan_system.value == "DVB-C":
				self.startCableTransponderSearch(self.feid)
			elif self.scan_system.value in ("DVB-T", "DVB-T2"):
				self.startTerrestrialTransponderSearch(self.feid)
			else:
				sat = self.satList[index_to_scan][self.scan_satselection[index_to_scan].index]
				self.startSatelliteTransponderSearch(self.feid, sat[0])

	def setTransponderSearchResult(self, tlist):
		self.tlist = tlist

	def TransponderSearchFinished(self):
		if self.tlist is None:
			self.tlist = []
		else:
			self.startScan(self.tlist, self.flags, self.feid)

	def startScan(self, tlist, flags, feid):
		if len(tlist):
			# flags |= eComponentScan.scanSearchBAT
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
			else:
				self.session.open(ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
		else:
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

class ScanSimple(ConfigListScreen, Screen, TransponderSearchSupport, CableTransponderSearchSupport, TerrestrialTransponderSearchSupport):
	def getNetworksForNim(self, nim, type=None):
		if (type is None or type == "DVB-S") and nim.isEnabled("DVB-S"): 
			networks = nimmanager.getSatListForNim(nim.slot)
		else:
			networks = [ ]
		if (type is None or type == "DVB-C") and nim.isEnabled("DVB-C"):
			networks.append("DVB-C")
		if (type is None or type == "DVB-T") and nim.isEnabled("DVB-T"):
			networks.append("DVB-T")
		return networks

	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		nim_networks = { }
		self.finished_cb = None

		for nim in nimmanager.nim_slots:
			# collect networks provided by this tuner

			networks = self.getNetworksForNim(nim)
			print "nim %d provides" % nim.slot, networks

			if networks:
				nim_networks[nim] = networks

		# we save the config elements to use them on keyGo
		self.nim_enable = [ ]

		if nim_networks:
			dvb_c_nim = None
			dvb_t_nim = None
			nim_sat_networks = { }

			for nim, networks in nim_networks.iteritems():
				s = nim_sat_networks.get(nim, set())
				nim_sat_networks[nim] = s
				for x in networks:
					if isinstance(x, tuple):
						s.add(x)
					elif x == "DVB-C" and dvb_c_nim is None:
						dvb_c_nim = nim
					elif x == "DVB-T" and dvb_t_nim is None:
						dvb_t_nim = nim

			networks_handled = set()
			final_networks_sat = { }

			# remove nim for sat networkslist when another nim provides the same networks and more
			for nim, networks in reversed(nim_sat_networks.items()):
				other_nim_networks = set()
				for nim2, networks2 in nim_sat_networks.iteritems():
					if nim2 != nim:
						other_nim_networks |= networks2

				if not networks.issubset(other_nim_networks) or other_nim_networks.issubset(networks):
					networks -= networks_handled
					if networks:
						final_networks_sat[nim] = networks
						networks_handled |= networks
						# try to use the same nim for all systems when possible
						if "DVB-C" in nim_networks[nim]:
							dvb_c_nim = nim
						if "DVB-T" in nim_networks[nim]:
							dvb_t_nim = nim

			self.scan_otherSDT = ConfigYesNo(default = False)
			self.scan_clearallservices = ConfigSelection(default = "yes", choices = [("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
			self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices))
			if config.usage.setup_level.index >= 2:
				self.list.append(getConfigListEntry(_("Lookup other SDT"), self.scan_otherSDT))

			temp = { }

			for nim, networks in final_networks_sat.iteritems():
				if networks:
					sys = "DVB-S"
					nimconfig = ConfigYesNo(default = True)
					nimconfig.nim_index = nim.slot
					ent = getConfigListEntry(_("Scan ") + nim.slot_name + " - " + nim.description + " - " + sys, nimconfig)
					temp[ent[0]] = (ent, sys)

			if dvb_c_nim is not None:
				nim = dvb_c_nim
				sys = "DVB-C"
				nimconfig = ConfigYesNo(default = True)
				nimconfig.nim_index = nim.slot
				ent = getConfigListEntry(_("Scan ") + nim.slot_name + " - " + nim.description + " - " + sys, nimconfig)
				temp[ent[0]] = (ent, sys)

			if dvb_t_nim is not None:
				nim = dvb_t_nim
				sys = "DVB-T"
				nimconfig = ConfigYesNo(default = True)
				nimconfig.nim_index = nim.slot
				ent = getConfigListEntry(_("Scan ") + nim.slot_name + " - " + nim.description + " - " + sys, nimconfig)
				temp[ent[0]] = (ent, sys)

			for txt, ent in sorted(temp.iteritems()):
				configEntry = ent[0][1]
				if ent[1] == "DVB-S":
					nim = nimmanager.nim_slots[configEntry.nim_index]
					self.nim_enable.append((ent[1], configEntry, final_networks_sat[nim]))
				else:
					self.nim_enable.append((ent[1], configEntry))
				self.list.append(ent[0])

		ConfigListScreen.__init__(self, self.list)
		self["header"] = Label(_("Automatic Scan"))
		self["footer"] = Label(_("Press OK to scan"))

	def runAsync(self, finished_cb):
		self.finished_cb = finished_cb
		self.keyGo()

	def keyGo(self):
		self.scanList = []
		self.nim_iter=0
		self.buildTransponderList()

	def buildTransponderList(self): # this method is called multiple times because of asynchronous stuff
		APPEND_NOW = 0
		SEARCH_CABLE_TRANSPONDERS = 1
		SEARCH_TERRESTRIAL_TRANSPONDERS = 2
		action = APPEND_NOW

		scan_idx = self.nim_iter
		n = self.nim_iter < len(self.nim_enable) and self.nim_enable[scan_idx][1] or None
		self.nim_iter += 1
		if n:
			type = self.nim_enable[scan_idx][0]

			if n.value: # check if nim is enabled
				flags = 0
				nim = nimmanager.nim_slots[n.nim_index]

				tlist = [ ]
				if type == "DVB-S" and nim.isEnabled("DVB-S"): 
					# get initial transponders for each satellite to be scanned
					networks = self.nim_enable[scan_idx][2]
					for sat in networks:
						getInitialTransponderList(tlist, sat[0])
				elif type == "DVB-C" and nim.isEnabled("DVB-C"):
					if config.Nims[nim.slot].cable.scan_type.value == "provider":
						getInitialCableTransponderList(tlist, nim.slot)
					else:
						action = SEARCH_CABLE_TRANSPONDERS
				elif type == "DVB-T" and nim.isEnabled("DVB-T"):
					tunername = nimmanager.getNimName(n.nim_index)
					getInitialTerrestrialTransponderList(tlist, nimmanager.getTerrestrialDescription(nim.slot), tunername in can_t_t2_auto_delsys)

				if self.scan_otherSDT.value:
					flags |= eComponentScan.scanOtherSDT
				flags |= eComponentScan.scanNetworkSearch #FIXMEEE.. use flags from cables / satellites / terrestrial.xml
				tmp = self.scan_clearallservices.value
				if tmp == "yes":
					flags |= eComponentScan.scanRemoveServices
				elif tmp == "yes_hold_feeds":
					flags |= eComponentScan.scanRemoveServices
					flags |= eComponentScan.scanDontRemoveFeeds

				if action == APPEND_NOW:
					self.scanList.append({"transponders": tlist, "feid": nim.slot, "flags": flags})
				elif action == SEARCH_CABLE_TRANSPONDERS:
					self.flags = flags
					self.feid = nim.slot
					self.startCableTransponderSearch(nim.slot)
					return
				elif action == SEARCH_TERRESTRIAL_TRANSPONDERS:
					self.flags = flags
					self.feid = nim.slot
					self.startTerrestrialTransponderSearch(nim.slot)
					return
				else:
					assert False

			self.buildTransponderList() # recursive call of this function !!!
			return
		# when we are here, then the recursion is finished and all enabled nims are checked
		# so we now start the real transponder scan
		self.startScan(self.scanList)

	def startScan(self, scanList):
		if len(scanList):
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, ServiceScan, scanList = scanList)
			else:
				self.session.open(ServiceScan, scanList = scanList)
		else:
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def setTransponderSearchResult(self, tlist):
		if tlist is not None:
			self.scanList.append({"transponders": tlist, "feid": self.feid, "flags": self.flags})

	def TransponderSearchFinished(self):
		self.buildTransponderList()

	def keyCancel(self):
		self.close()

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0
