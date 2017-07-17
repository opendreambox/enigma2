from enigma import eDVBDB
from Screen import Screen
from Components.SystemInfo import SystemInfo
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.NimManager import nimmanager, NimManager
from Components.config import getConfigListEntry, config, ConfigNothing, ConfigSatlist
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.ServiceStopScreen import ServiceStopScreen

from time import mktime, localtime
from datetime import datetime

class NimSetup(Screen, ConfigListScreen, ServiceStopScreen):
	def createSimpleSetup(self, list, mode):
		nim = self.nimConfig
		if mode == "single":
			list.append(getConfigListEntry(_("Satellite"), nim.diseqcA))
			list.append(getConfigListEntry(_("Send DiSEqC"), nim.simpleSingleSendDiSEqC))
		else:
			list.append(getConfigListEntry(_("Port A"), nim.diseqcA))

		if mode in ("toneburst_a_b", "diseqc_a_b", "diseqc_a_b_c_d"):
			list.append(getConfigListEntry(_("Port B"), nim.diseqcB))
			if mode == "diseqc_a_b_c_d":
				list.append(getConfigListEntry(_("Port C"), nim.diseqcC))
				list.append(getConfigListEntry(_("Port D"), nim.diseqcD))
			if mode != "toneburst_a_b":
				list.append(getConfigListEntry(_("Set Voltage and 22KHz"), nim.simpleDiSEqCSetVoltageTone))
				list.append(getConfigListEntry(_("Send DiSEqC only on satellite change"), nim.simpleDiSEqCOnlyOnSatChange))

	def createPositionerSetup(self, list):
		nim = self.nimConfig
		list.append(getConfigListEntry(_("Longitude"), nim.longitude))
		list.append(getConfigListEntry(" ", nim.longitudeOrientation))
		list.append(getConfigListEntry(_("Latitude"), nim.latitude))
		list.append(getConfigListEntry(" ", nim.latitudeOrientation))
		if SystemInfo["CanMeasureFrontendInputPower"] & (1 << self.slotid):
			self.advancedPowerMeasurement = getConfigListEntry(_("Use Power Measurement"), nim.powerMeasurement)
			list.append(self.advancedPowerMeasurement)
			if nim.powerMeasurement.value:
				list.append(getConfigListEntry(_("Power threshold in mA"), nim.powerThreshold))
				self.turningSpeed = getConfigListEntry(_("Rotor turning speed"), nim.turningSpeed)
				list.append(self.turningSpeed)
				if nim.turningSpeed.value == "fast epoch":
					self.turnFastEpochBegin = getConfigListEntry(_("Begin time"), nim.fastTurningBegin)
					self.turnFastEpochEnd = getConfigListEntry(_("End time"), nim.fastTurningEnd)
					list.append(self.turnFastEpochBegin)
					list.append(self.turnFastEpochEnd)
		else:
			if nim.powerMeasurement.value:
				nim.powerMeasurement.value = False
				nim.powerMeasurement.save()
		if not nim.powerMeasurement.value:
			list.append(getConfigListEntry(_("Rotor speed in degree per second"), nim.degreePerSecond))

		if config.usage.setup_level.index >= 2: # expert
			list.append(getConfigListEntry(_("Rotor is exclusively controlled by this dreambox"), nim.positionerExclusively))

	def createConfigMode(self):
		# FIXMEE
		# no support for satpos depends, equal to and loopthough setting for nims with
		# with multiple inputs and multiple channels
		if self.nim.isCompatible("DVB-S") and self.nim.inputs is None:
			getConfigModeTuple = nimmanager.getConfigModeTuple
			choices = [ getConfigModeTuple("nothing"), getConfigModeTuple("simple"), getConfigModeTuple("advanced") ]
			#if len(nimmanager.getNimListOfType(nimmanager.getNimType(self.slotid), exception = x)) > 0:
			#	choices.append(getConfigModeTuple("equal"))
			#	choices.append(getConfigModeTuple("satposdepends"))
			if len(nimmanager.canEqualTo(self.slotid)) > 0:
				choices.append(getConfigModeTuple("equal"))
			if len(nimmanager.canDependOn(self.slotid)) > 0:
				choices.append(getConfigModeTuple("satposdepends"))
			if len(nimmanager.canConnectTo(self.slotid)) > 0:
				choices.append(getConfigModeTuple("loopthrough"))
			self.nimConfig.sat.configMode.setChoices(dict(choices), default = "nothing")

	def createSetup(self, fill_advanced_sat=True):
		print "Creating setup"
		self.list = [ ]

		self.multiType = None
		self.configMode = None
		self.diseqcModeEntry = None
		self.advancedSatsEntry = None
		self.advancedLnbsEntry = None
		self.advancedDiseqcMode = None
		self.advancedUsalsEntry = None
		self.advancedLof = None
		self.advancedPowerMeasurement = None
		self.turningSpeed = None
		self.turnFastEpochBegin = None
		self.turnFastEpochEnd = None
		self.uncommittedDiseqcCommand = None
		self.cableScanType = None
		self.have_advanced = False
		self.advancedUnicable = None
		self.advancedType = None
		self.advancedManufacturer = None
		self.advancedSCR = None
		self.advancedConnected = None
		self.unicableUsePinEntry = None
		
		multiType = self.nimConfig.multiType
		self.multiType = getConfigListEntry(_("Tuner type"), multiType)
		if multiType.enabled:
			self.list.append(self.multiType)

		curType = self.nim.types[multiType.value]
		if curType.startswith("DVB-S"):
			self.configMode = getConfigListEntry(_("Configuration Mode"), self.nimConfig.sat.configMode)
			self.list.append(self.configMode)
			configMode = self.nimConfig.sat.configMode.value
			if configMode == "simple":			#simple setup
				self.diseqcModeEntry = getConfigListEntry(_("Mode"), self.nimConfig.diseqcMode)
				self.list.append(self.diseqcModeEntry)
				if self.nimConfig.diseqcMode.value in ("single", "toneburst_a_b", "diseqc_a_b", "diseqc_a_b_c_d"):
					self.createSimpleSetup(self.list, self.nimConfig.diseqcMode.value)
				if self.nimConfig.diseqcMode.value == "positioner":
					self.createPositionerSetup(self.list)
			elif configMode == "equal":
				choices = []
				nimlist = nimmanager.canEqualTo(self.nim.slot)
				for id in nimlist:
					#choices.append((str(id), str(chr(65 + id))))
					choices.append((str(id), nimmanager.getNimDescription(id)))
				self.nimConfig.connectedTo.setChoices(choices)
				#self.nimConfig.connectedTo = updateConfigElement(self.nimConfig.connectedTo, ConfigSelection(choices = choices))
				self.list.append(getConfigListEntry(_("Tuner"), self.nimConfig.connectedTo))
			elif configMode == "satposdepends":
				choices = []
				nimlist = nimmanager.canDependOn(self.nim.slot)
				for id in nimlist:
					#choices.append((str(id), str(chr(65 + id))))
					choices.append((str(id), nimmanager.getNimDescription(id)))
				self.nimConfig.connectedTo.setChoices(choices)
				#self.nimConfig.connectedTo = updateConfigElement(self.nimConfig.connectedTo, ConfigSelection(choices = choices))
				self.list.append(getConfigListEntry(_("Tuner"), self.nimConfig.connectedTo))
			elif configMode == "loopthrough":
				choices = []
				print "connectable to:", nimmanager.canConnectTo(self.slotid)
				connectable = nimmanager.canConnectTo(self.slotid)
				for id in connectable:
					choices.append((str(id), nimmanager.getNimDescription(id)))
				self.nimConfig.connectedTo.setChoices(choices)
				self.nimConfig.sat.configMode.connectedToChanged(self.nimConfig.connectedTo) # call connectedTo Notifier
				#self.nimConfig.connectedTo = updateConfigElement(self.nimConfig.connectedTo, ConfigSelection(choices = choices))
				self.list.append(getConfigListEntry(_("Tuner"), self.nimConfig.connectedTo))
			elif configMode == "nothing":
				pass
			elif configMode == "advanced": # advanced
				# SATs
				self.advancedSatsEntry = getConfigListEntry(_("Satellite"), self.nimConfig.advanced.sats)
				self.list.append(self.advancedSatsEntry)
				cur_orb_pos = self.nimConfig.advanced.sats.orbital_position
				if cur_orb_pos is not None and fill_advanced_sat:
					satlist = self.nimConfig.advanced.sat.keys()
					if cur_orb_pos not in satlist:
						cur_orb_pos = satlist[0]
					currSat = self.nimConfig.advanced.sat[cur_orb_pos]
					self.fillListWithAdvancedSatEntrys(currSat)
				self.have_advanced = True
			if config.usage.setup_level.index >= 2: # expert
				name = self.nim.description
				if name == "Alps BSBE2":
					self.list.append(getConfigListEntry(_("Tone Amplitude"), self.nimConfig.toneAmplitude))
				if self.nimConfig.scpcSearchRange.fe_id is not None and configMode != "nothing":
					self.list.append(getConfigListEntry(_("SCPC optimized search range"), self.nimConfig.scpcSearchRange))

		elif curType.startswith("DVB-C"):
			self.configMode = getConfigListEntry(_("Configuration Mode"), self.nimConfig.cable.configMode)
			self.list.append(self.configMode)
			if self.nimConfig.cable.configMode.value == "enabled":
				if self.nim.description != "Si2169C":
					self.cableScanType=getConfigListEntry(_("Used service scan type"), self.nimConfig.cable.scan_type)
					self.list.append(self.cableScanType)
					if self.nimConfig.cable.scan_type.value == "provider":
						self.list.append(getConfigListEntry(_("Provider to scan"), self.nimConfig.cable.scan_provider))
					else:
						if self.nimConfig.cable.scan_type.value == "bands":
							self.list.append(getConfigListEntry(_("Scan band EU VHF I"), self.nimConfig.cable.scan_band_EU_VHF_I))
							self.list.append(getConfigListEntry(_("Scan band EU MID"), self.nimConfig.cable.scan_band_EU_MID))
							self.list.append(getConfigListEntry(_("Scan band EU VHF III"), self.nimConfig.cable.scan_band_EU_VHF_III))
							self.list.append(getConfigListEntry(_("Scan band EU UHF IV"), self.nimConfig.cable.scan_band_EU_UHF_IV))
							self.list.append(getConfigListEntry(_("Scan band EU UHF V"), self.nimConfig.cable.scan_band_EU_UHF_V))
							self.list.append(getConfigListEntry(_("Scan band EU SUPER"), self.nimConfig.cable.scan_band_EU_SUPER))
							self.list.append(getConfigListEntry(_("Scan band EU HYPER"), self.nimConfig.cable.scan_band_EU_HYPER))
							self.list.append(getConfigListEntry(_("Scan band US LOW"), self.nimConfig.cable.scan_band_US_LOW))
							self.list.append(getConfigListEntry(_("Scan band US MID"), self.nimConfig.cable.scan_band_US_MID))
							self.list.append(getConfigListEntry(_("Scan band US HIGH"), self.nimConfig.cable.scan_band_US_HIGH))
							self.list.append(getConfigListEntry(_("Scan band US SUPER"), self.nimConfig.cable.scan_band_US_SUPER))
							self.list.append(getConfigListEntry(_("Scan band US HYPER"), self.nimConfig.cable.scan_band_US_HYPER))
							self.list.append(getConfigListEntry(_("Scan band US JUMBO"), self.nimConfig.cable.scan_band_US_JUMBO))
							self.list.append(getConfigListEntry(_("Scan band US ULTRA"), self.nimConfig.cable.scan_band_US_ULTRA))
						elif self.nimConfig.cable.scan_type.value == "steps":
							self.list.append(getConfigListEntry(_("Frequency scan step size(khz)"), self.nimConfig.cable.scan_frequency_steps))
						if self.nim.description != "ATBM781x":
							self.list.append(getConfigListEntry(_("Scan QAM16"), self.nimConfig.cable.scan_mod_qam16))
							self.list.append(getConfigListEntry(_("Scan QAM32"), self.nimConfig.cable.scan_mod_qam32))
							self.list.append(getConfigListEntry(_("Scan QAM64"), self.nimConfig.cable.scan_mod_qam64))
							self.list.append(getConfigListEntry(_("Scan QAM128"), self.nimConfig.cable.scan_mod_qam128))
							self.list.append(getConfigListEntry(_("Scan QAM256"), self.nimConfig.cable.scan_mod_qam256))
							self.list.append(getConfigListEntry(_("Scan SR6900"), self.nimConfig.cable.scan_sr_6900))
							self.list.append(getConfigListEntry(_("Scan SR6875"), self.nimConfig.cable.scan_sr_6875))
							self.list.append(getConfigListEntry(_("Scan additional SR"), self.nimConfig.cable.scan_sr_ext1))
							self.list.append(getConfigListEntry(_("Scan additional SR"), self.nimConfig.cable.scan_sr_ext2))
			self.have_advanced = False
		elif curType.startswith("DVB-T"):
			self.configMode = getConfigListEntry(_("Configuration Mode"), self.nimConfig.terrest.configMode)
			self.list.append(self.configMode)
			self.have_advanced = False
			if self.nimConfig.terrest.configMode.value == "enabled":
				self.list.append(getConfigListEntry(_("Terrestrial provider"), self.nimConfig.terrest.provider))
				self.list.append(getConfigListEntry(_("Enable 5V for active antenna"), self.nimConfig.terrest.use5V))
		else:
			self.have_advanced = False
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def newConfig(self):
		checkList = (self.configMode, self.diseqcModeEntry, self.advancedSatsEntry, \
			self.advancedLnbsEntry, self.advancedDiseqcMode, self.advancedUsalsEntry, \
			self.advancedLof, self.advancedPowerMeasurement, self.turningSpeed, \
			self.advancedType, self.advancedSCR, self.advancedManufacturer, self.advancedUnicable, \
			self.advancedConnected, self.uncommittedDiseqcCommand, self.cableScanType, self.multiType, \
			self.unicableUsePinEntry
		)

		current = self["config"].getCurrent()

		if current == self.multiType:
			self.nimConfig.save()
			self.nim = nimmanager.nim_slots[self.slotid]
			self.nimConfig = self.nim.config

		for x in checkList:
			if current == x:
				self.createSetup()
				break

	def fixTurnFastEpochTime(self):
		for x in self.list:
			if x in (self.turnFastEpochBegin, self.turnFastEpochEnd):
				# workaround for storing only hour*3600+min*60 value in configfile
				# not really needed.. just for cosmetics..
				tm = localtime(x[1].value)
				dt = datetime(1970, 1, 1, tm.tm_hour, tm.tm_min)
				x[1].value = int(mktime(dt.timetuple()))

	def refillAdvancedSats(self):
		if self.have_advanced and self.nim.config.sat.configMode.value == "advanced":
			self.createSetup(False)
			satlist = self.nimConfig.advanced.sat.keys()
			for orb_pos in satlist:
				curSat = self.nimConfig.advanced.sat[orb_pos]
				self.fillListWithAdvancedSatEntrys(curSat)
				self.fixTurnFastEpochTime()
			self["config"].list = self.list
		else:
			self.fixTurnFastEpochTime()

	def run(self):
		self.refillAdvancedSats()
		nimmanager.sec.update()
		self.saveAll()

	def fillListWithAdvancedSatEntrys(self, Sat):
		lnbnum = int(Sat.lnb.value)
		currLnb = self.nimConfig.advanced.lnb[lnbnum]

		if isinstance(currLnb, ConfigNothing):
			currLnb = None

		# LNBs
		self.advancedLnbsEntry = getConfigListEntry(_("LNB"), Sat.lnb)
		self.list.append(self.advancedLnbsEntry)

		if currLnb:
			self.list.append(getConfigListEntry(_("Priority"), currLnb.prio))
			self.advancedLof = getConfigListEntry(_("Type"), currLnb.lof)
			self.list.append(self.advancedLof)
			if currLnb.lof.value == "user_defined":
				self.list.append(getConfigListEntry(_("LOF/L"), currLnb.lofl))
				self.list.append(getConfigListEntry(_("LOF/H"), currLnb.lofh))
				self.list.append(getConfigListEntry(_("Threshold"), currLnb.threshold))
#			self.list.append(getConfigListEntry(_("12V Output"), currLnb.output_12v))

			if currLnb.lof.value == "unicable":
				self.advancedUnicable = getConfigListEntry("Unicable "+_("Configuration Mode"), currLnb.unicable)
				self.list.append(self.advancedUnicable)
				if currLnb.unicable.value == "unicable_user":
					product_name = "unicable_user"
					self._checkUnicableLofUpdateRequired(currLnb, self._lastUnicableManufacturerName, product_name)
					self._lastUnicableProductName = product_name

					self.list.append(getConfigListEntry(_("Mode"), currLnb.satcruser_mode))
					self.advancedSCR = getConfigListEntry(_("Channel"), currLnb.satcruser)
					self.list.append(self.advancedSCR)
					self.list.append(getConfigListEntry(_("Frequency"), currLnb.satcrvcouser[currLnb.satcruser.index]))
					self.list.append(getConfigListEntry(_("LOF/L"), currLnb.lofl))
					self.list.append(getConfigListEntry(_("LOF/H"), currLnb.lofh))
					self.list.append(getConfigListEntry(_("Threshold"), currLnb.threshold))
				elif currLnb.unicable.value == "unicable_matrix":
					try:
						manufacturer_name = currLnb.unicableMatrix.manufacturer.value
						product_name = currLnb.unicableMatrix.product.value
					except:
						manufacturer_name = product_name = "unicable_matrix"

					self._checkUnicableLofUpdateRequired(currLnb, manufacturer_name, product_name)
					self._lastUnicableManufacturerName = manufacturer_name
					self._lastUnicableProductName = product_name

					matrixConfig = currLnb.unicableMatrix
					self.advancedManufacturer = getConfigListEntry(_("Manufacturer"), matrixConfig.manufacturer)
					self.advancedType = getConfigListEntry(_("Type"), matrixConfig.product)
					self.list.append(self.advancedManufacturer)
					self.list.append(self.advancedType)
					if isinstance(matrixConfig.scrs, ConfigNothing):
						self.advancedSCR = getConfigListEntry(_("Channel"), matrixConfig.scr)
						self.list.append(self.advancedSCR)
						self.list.append(getConfigListEntry(_("Frequency"), matrixConfig.vco[matrixConfig.scr.index]))
					else:
						self.list.append(getConfigListEntry(_("Usable SCRs"), matrixConfig.scrs))
				elif currLnb.unicable.value == "unicable_lnb":
					try:
						product_name = currLnb.unicableLnb.product.value
						manufacturer_name = currLnb.unicableLnb.manufacturer.value
					except:
						manufacturer_name = product_name = "unicable_lnb"
					self._checkUnicableLofUpdateRequired(currLnb, manufacturer_name, product_name)
					self._lastUnicableManufacturerName = manufacturer_name
					self._lastUnicableProductName = product_name

					lnbConfig = currLnb.unicableLnb
					self.advancedManufacturer = getConfigListEntry(_("Manufacturer"), lnbConfig.manufacturer)
					self.advancedType = getConfigListEntry(_("Type"), lnbConfig.product)
					self.list.append(self.advancedManufacturer)
					self.list.append(self.advancedType)
					if isinstance(lnbConfig.scrs, ConfigNothing):
						self.advancedSCR = getConfigListEntry(_("Channel"), lnbConfig.scr)
						self.list.append(self.advancedSCR)
						self.list.append(getConfigListEntry(_("Frequency"), lnbConfig.vco[lnbConfig.scr.index]))
					else:
						self.list.append(getConfigListEntry(_("Usable SCRs"), lnbConfig.scrs))
				self.unicableUsePinEntry = getConfigListEntry(_("Use PIN"), currLnb.unicable_use_pin)
				self.list.append(self.unicableUsePinEntry)
				if currLnb.unicable_use_pin.value: 
					self.list.append(getConfigListEntry(_("PIN"), currLnb.unicable_pin))

				choices = []
				connectable = nimmanager.canConnectTo(self.slotid)
				for id in connectable:
					choices.append((str(id), nimmanager.getNimDescription(id)))
				if len(choices):
					self.advancedConnected = getConfigListEntry(_("connected"), self.nimConfig.advanced.unicableconnected)
					self.list.append(self.advancedConnected)
					if self.nimConfig.advanced.unicableconnected.value == True:
						self.nimConfig.advanced.unicableconnectedTo.setChoices(choices)
						self.list.append(getConfigListEntry(_("Connected to"),self.nimConfig.advanced.unicableconnectedTo))
			else:	#kein Unicable
				self.list.append(getConfigListEntry(_("Voltage mode"), Sat.voltage))
				self.list.append(getConfigListEntry(_("Tone mode"), Sat.tonemode))

			self.list.append(getConfigListEntry(_("Increased voltage"), currLnb.increased_voltage))

			if lnbnum < 33:
				self.advancedDiseqcMode = getConfigListEntry(_("DiSEqC mode"), currLnb.diseqcMode)
				self.list.append(self.advancedDiseqcMode)
			if currLnb.diseqcMode.value != "none":
				self.list.append(getConfigListEntry(_("Toneburst"), currLnb.toneburst))
				self.list.append(getConfigListEntry(_("Committed DiSEqC command"), currLnb.commitedDiseqcCommand))
				self.list.append(getConfigListEntry(_("Fast DiSEqC"), currLnb.fastDiseqc))
				self.list.append(getConfigListEntry(_("Sequence repeat"), currLnb.sequenceRepeat))
				if currLnb.diseqcMode.value == "1_0":
					self.list.append(getConfigListEntry(_("Command order"), currLnb.commandOrder1_0))
				else:
					if currLnb.uncommittedDiseqcCommand.index:
						if currLnb.commandOrder.value == "ct":
							currLnb.commandOrder.value = "cut"
						elif currLnb.commandOrder.value == "tc":
							currLnb.commandOrder.value = "tcu"
					else:
						if currLnb.commandOrder.index & 1:
							currLnb.commandOrder.value = "tc"
						else:
							currLnb.commandOrder.value = "ct"
					self.list.append(getConfigListEntry(_("Command order"), currLnb.commandOrder))
					self.uncommittedDiseqcCommand = getConfigListEntry(_("Uncommitted DiSEqC command"), currLnb.uncommittedDiseqcCommand)
					self.list.append(self.uncommittedDiseqcCommand)
					self.list.append(getConfigListEntry(_("DiSEqC repeats"), currLnb.diseqcRepeats))
				if currLnb.diseqcMode.value == "1_2":
					self.list.append(getConfigListEntry(_("Longitude"), currLnb.longitude))
					self.list.append(getConfigListEntry(" ", currLnb.longitudeOrientation))
					self.list.append(getConfigListEntry(_("Latitude"), currLnb.latitude))
					self.list.append(getConfigListEntry(" ", currLnb.latitudeOrientation))
					if SystemInfo["CanMeasureFrontendInputPower"] & (1 << self.slotid):
						self.advancedPowerMeasurement = getConfigListEntry(_("Use Power Measurement"), currLnb.powerMeasurement)
						self.list.append(self.advancedPowerMeasurement)
						if currLnb.powerMeasurement.value:
							self.list.append(getConfigListEntry(_("Power threshold in mA"), currLnb.powerThreshold))
							self.turningSpeed = getConfigListEntry(_("Rotor turning speed"), currLnb.turningSpeed)
							self.list.append(self.turningSpeed)
							if currLnb.turningSpeed.value == "fast epoch":
								self.turnFastEpochBegin = getConfigListEntry(_("Begin time"), currLnb.fastTurningBegin)
								self.turnFastEpochEnd = getConfigListEntry(_("End time"), currLnb.fastTurningEnd)
								self.list.append(self.turnFastEpochBegin)
								self.list.append(self.turnFastEpochEnd)
					else:
						if currLnb.powerMeasurement.value:
							currLnb.powerMeasurement.value = False
							currLnb.powerMeasurement.save()
					if not currLnb.powerMeasurement.value:
						self.list.append(getConfigListEntry(_("Rotor speed in degree per second"), currLnb.degreePerSecond))
					self.advancedUsalsEntry = getConfigListEntry(_("Use usals for this sat"), Sat.usals)
					self.list.append(self.advancedUsalsEntry)
					if not Sat.usals.value:
						self.list.append(getConfigListEntry(_("Stored position"), Sat.rotorposition))
					if config.usage.setup_level.index >= 2: # expert
						self.list.append(getConfigListEntry(_("Rotor is exclusively controlled by this dreambox"), self.nimConfig.positionerExclusively))

	def _checkUnicableLofUpdateRequired(self, currLnb, manufacturer, product_name):
		from Components.NimManager import configLOFChanged
		if self._lastUnicableManufacturerName != manufacturer or self._lastUnicableProductName != product_name:
			configLOFChanged(currLnb.lof)

	def keySave(self):
		old_configured_sats = nimmanager.getConfiguredSats()
		self.run()
		new_configured_sats = nimmanager.getConfiguredSats()
		self.unconfed_sats = old_configured_sats - new_configured_sats
		self.satpos_to_remove = None
		self.deleteConfirmed((None, "no"))

	def deleteConfirmed(self, confirmed):
		if confirmed[1] == "yes" or confirmed[1] == "yestoall":
			eDVBDB.getInstance().removeServices(-1, -1, -1, self.satpos_to_remove)

		if self.satpos_to_remove is not None:
			self.unconfed_sats.remove(self.satpos_to_remove)

		self.satpos_to_remove = None
		for orbpos in self.unconfed_sats:
			self.satpos_to_remove = orbpos
			orbpos = self.satpos_to_remove
			try:
				# why we need this cast?
				sat_name = str(nimmanager.getSatDescription(orbpos))
			except:
				if orbpos > 1800: # west
					orbpos = 3600 - orbpos
					h = _("W")
				else:
					h = _("E")
				sat_name = ("%d.%d" + h) % (orbpos / 10, orbpos % 10)
				
			if confirmed[1] == "yes" or confirmed[1] == "no":
				self.session.openWithCallback(self.deleteConfirmed, ChoiceBox, _("Delete no more configured satellite\n%s?") %(sat_name), [(_("Yes"), "yes"), (_("No"), "no"), (_("Yes to all"), "yestoall"), (_("No to all"), "notoall")], allow_cancel = False)
			if confirmed[1] == "yestoall" or confirmed[1] == "notoall":
				self.deleteConfirmed(confirmed)
			break
		else:
			self.restoreService(_("Zap back to service before tuner setup?"))

	def __init__(self, session, slotid):
		Screen.__init__(self, session)
		self.list = [ ]
		
		ServiceStopScreen.__init__(self)
		self.stopService()

		ConfigListScreen.__init__(self, self.list)

		self["actions"] = ActionMap(["SetupActions", "SatlistShortcutAction"],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"nothingconnected": self.nothingConnectedShortcut
		}, -2)

		self.slotid = slotid
		self.nim = nimmanager.nim_slots[slotid]
		self.nimConfig = self.nim.config

		self._lastUnicableManufacturerName = None
		self._lastUnicableProductName = None

		self.createConfigMode()
		self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.restoreService(_("Zap back to service before tuner setup?"))

	def saveAll(self):
		if self.nim.isCompatible("DVB-S"):
			# reset connectedTo to all choices to properly store the default value
			choices = []
			nimlist = nimmanager.getNimListOfType("DVB-S", self.slotid)
			for id in nimlist:
				choices.append((str(id), nimmanager.getNimDescription(id)))
			self.nimConfig.connectedTo.setChoices(choices)
		for x in self["config"].list:
			x[1].save()

	def cancelConfirm(self, result):
		if not result:
			return

		self.refillAdvancedSats()

		for x in self["config"].list:
			x[1].cancel()

		# we need to call saveAll to reset the connectedTo choices
		self.saveAll()
		self.restoreService(_("Zap back to service before tuner setup?"))

	def nothingConnectedShortcut(self):
		if type(self["config"].getCurrent()[1]) is ConfigSatlist:
			self["config"].getCurrent()[1].setValue("3601")
			self["config"].invalidateCurrent()

class NimSelection(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.list = [None] * nimmanager.getSlotCount()
		self["nimlist"] = List(self.list)
		self.updateList()
		
		self.setResultClass()
		
		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.okbuttonClick ,
			"cancel": self.close
		}, -2)

	def setResultClass(self):
		self.resultclass = NimSetup

	def okbuttonClick(self):
		nim = self["nimlist"].getCurrent()
		nim = nim and nim[3]
		if nim is not None and not nim.empty and nim.isSupported():
			self.session.openWithCallback(self.updateList, self.resultclass, nim.slot)

	def showNim(self, nim):
		inputs = nim.inputs is not None and len(nim.inputs) or 0
		return True if not inputs or nim.channel < inputs else False

	def updateList(self):
		self.list = [ ]
		slot_names = [ x.slot_input_name for x in nimmanager.nim_slots ]
		for x in nimmanager.nim_slots:
			slotid = x.slot
			nimConfig = nimmanager.getNimConfig(x.slot)
			#text = nimConfig.configMode.value
			if self.showNim(x):
				text = ""
				if x.isCompatible("DVB-C"):
					if x.isMultiType():
						text += "DVB-C: "
					text += _(NimManager.config_mode_str[nimConfig.cable.configMode.value]) + "\n"
				if x.isCompatible("DVB-T"):
					if nimConfig.terrest.configMode.value == "enabled" and nimConfig.terrest.use5V.value:
						txt2 = " (+5 Volt)\n"
					else:
						txt2 = "\n" 
					if x.isMultiType():
						text += x.isCompatible("DVB-T2") and 'DVB-T2: ' or 'DVB-T: ' 
					text += _(NimManager.config_mode_str[nimConfig.terrest.configMode.value]) + txt2
				if x.isCompatible("DVB-S"):
					txt = '' if not x.isMultiType() else x.isCompatible("DVB-S2") and 'DVB-S2: ' or 'DVB-S: '
					configMode = nimConfig.sat.configMode.value
					if configMode in ("loopthrough", "equal", "satposdepends"):
						if configMode == "loopthrough":
							txt += nimConfig.sat.configMode.getText()
						else:
							txt += _(nimmanager.config_mode_str[configMode])
						txt += " %s %s" %(_("Tuner"), slot_names[int(nimConfig.connectedTo.value)])
					elif configMode == "nothing":
						txt += _(NimManager.config_mode_str[configMode])
					elif configMode == "simple":
						if nimConfig.diseqcMode.value in ("single", "toneburst_a_b", "diseqc_a_b", "diseqc_a_b_c_d"):
							txt += {"single": _("Single"), "toneburst_a_b": _("Toneburst A/B"), "diseqc_a_b": _("DiSEqC A/B"), "diseqc_a_b_c_d": _("DiSEqC A/B/C/D")}[nimConfig.diseqcMode.value] + "\n"
							txt += _("Sats") + ": " 
							satnames = []
							if nimConfig.diseqcA.orbital_position != 3601:
								satnames.append(nimmanager.getSatName(int(nimConfig.diseqcA.value)))
							if nimConfig.diseqcMode.value in ("toneburst_a_b", "diseqc_a_b", "diseqc_a_b_c_d"):
								if nimConfig.diseqcB.orbital_position != 3601:
									satnames.append(nimmanager.getSatName(int(nimConfig.diseqcB.value)))
							if nimConfig.diseqcMode.value == "diseqc_a_b_c_d":
								if nimConfig.diseqcC.orbital_position != 3601:
									satnames.append(nimmanager.getSatName(int(nimConfig.diseqcC.value)))
								if nimConfig.diseqcD.orbital_position != 3601:
									satnames.append(nimmanager.getSatName(int(nimConfig.diseqcD.value)))
							if len(satnames) <= 2:
								txt += ", ".join(satnames)
							elif len(satnames) > 2:
								# we need a newline here, since multi content lists don't support automtic line wrapping
								txt += ", ".join(satnames[:2]) + ",\n"
								txt += "         " + ", ".join(satnames[2:])
						elif nimConfig.diseqcMode.value == "positioner":
							txt += _("Positioner") + ":"
							if nimConfig.positionerMode.value == "usals":
								txt += _("USALS")
							elif nimConfig.positionerMode.value == "manual":
								txt += _("manual")
						else:	
							txt = _("simple")
					elif configMode == "advanced":
						txt += _("advanced")
					text += txt
				if not x.isSupported():
					text = _("tuner is not supported")

				self.list.append((slotid, x.friendly_full_description, text, x))
		self["nimlist"].setList(self.list)
		self["nimlist"].updateList(self.list)
