from enigma import eDVBFrontendParametersSatellite, eDVBFrontendParameters, eDVBResourceManager, eTimer, eSlot1I, iDVBFrontend

stateFailed = iDVBFrontend.stateFailed
stateTuning = iDVBFrontend.stateTuning
stateLock = iDVBFrontend.stateLock
stateLostLock = iDVBFrontend.stateLostLock

class Tuner:
	def __init__(self, frontend, ignore_rotor=False):
		self.frontend = frontend
		self.ignore_rotor = ignore_rotor

	# transponder = (frequency, symbolrate, polarisation, fec, inversion, orbpos, system, modulation, rolloff, pilot, tsid, onid)
	#                    0         1             2         3       4         5       6        7          8       9      10    11
	def tune(self, transponder):
		if self.frontend:
			print "tuning to transponder with data", transponder
			parm = eDVBFrontendParametersSatellite()
			parm.frequency = transponder[0] * 1000
			parm.symbol_rate = transponder[1] * 1000
			parm.polarisation = transponder[2]
			parm.fec = transponder[3]
			parm.inversion = transponder[4]
			parm.orbital_position = transponder[5]
			parm.system = transponder[6]
			parm.modulation = transponder[7]
			parm.rolloff = transponder[8]
			parm.pilot = transponder[9]
			feparm = eDVBFrontendParameters()
			feparm.setDVBS(parm, self.ignore_rotor)
			self.lastparm = feparm
			self.frontend.tune(feparm)

	def retune(self):
		if self.frontend:
			self.frontend.tune(self.lastparm)

	def getTransponderData(self):
		ret = { }
		if self.frontend:
			self.frontend.getTransponderData(ret, True)
		return ret

# tunes a list of transponders and checks, if they lock and optionally checks the onid/tsid combination
# 1) add transponders with addTransponder()
# 2) call run(<checkPIDs = True>)
# 3) finishedChecking() is called, when the run is finished
class TuneTest:
	def __init__(self, feid, stopOnSuccess = -1, stopOnError = -1):
		self.stopOnSuccess = stopOnSuccess
		self.stopOnError = stopOnError
		self.feid = feid
		self.transponderlist = []
		self.currTuned = None
		print "TuneTest for feid %d" % self.feid
		if not self.openFrontend():
			self.oldref = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService() # try to disable foreground service
			if not self.openFrontend():
				if self.session.pipshown: # try to disable pip
					self.session.pipshown = False
					self.session.deleteDialog(self.session.pip)
					del self.session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen
		self.tuner = Tuner(self.frontend)
		self.timer = eTimer()
		self.timer_conn = self.timer.timeout.connect(self.updateStatus)

	def gotTsidOnid(self, tsidonid):
		if tsidonid == -1:
			print "******** got tsidonid failed"
			self.pidStatus = self.INTERNAL_PID_STATUS_FAILED
			self.tsid = -1
			self.onid = -1
		else:
			self.pidStatus = self.INTERNAL_PID_STATUS_SUCCESSFUL
			self.tsid = (tsidonid>>16)&0xFFFF
			self.onid = tsidonid&0xFFFF
			print "******** got tsid %04x, onid %04x" %(self.tsid, self.onid)
		self.timer.start(100, True)
		self.__requestTsidOnid_conn = None
		
	def updateStatus(self):
		fe_data = { }
		self.frontend.getFrontendStatus(fe_data)
		stop = False
		state = fe_data["tuner_state"]
		print "status:", state
		if state == stateTuning:
			print "TUNING"
			self.timer.start(100, True)
			self.progressCallback((self.getProgressLength(), self.tuningtransponder, self.STATUS_TUNING, self.currTuned))
		elif self.checkPIDs and self.pidStatus == self.INTERNAL_PID_STATUS_NOOP:
			print "2nd choice"
			if state == stateLock:
				print "acquiring TSID/ONID"
				class ePySlot1I(eSlot1I):
					def __init__(self, func):
						eSlot1I.__init__(self)
						self.cb_func = func
				self.__requestTsidOnid_conn = ePySlot1I(self.gotTsidOnid)
				self.raw_channel.requestTsidOnid(self.__requestTsidOnid_conn)
				self.pidStatus = self.INTERNAL_PID_STATUS_WAITING
			else:
				self.pidStatus = self.INTERNAL_PID_STATUS_FAILED
		elif self.checkPIDs and self.pidStatus == self.INTERNAL_PID_STATUS_WAITING:
			print "waiting for pids"			
		else:
			if state == stateLostLock or state == stateFailed:
				self.tuningtransponder = self.nextTransponder()
				self.failedTune.append([self.currTuned, self.oldTuned, "tune_failed", fe_data])  # last parameter is the frontend status)
				if self.stopOnError != -1 and self.stopOnError <= len(self.failedTune):
					stop = True
			elif state == stateLock:
				pidsFailed = False
				if self.checkPIDs:
					if self.currTuned is not None:
						if self.tsid != self.currTuned[10] or self.onid != self.currTuned[11]:
							self.failedTune.append([self.currTuned, self.oldTuned, "pids_failed", {"real": (self.tsid, self.onid), "expected": (self.currTuned[10], self.currTuned[11])}, fe_data])  # last parameter is the frontend status
							pidsFailed = True
						else:
							self.successfullyTune.append([self.currTuned, self.oldTuned, fe_data])  # 3rd parameter is the frontend status
							if self.stopOnSuccess != -1 and self.stopOnSuccess <= len(self.successfullyTune):
								stop = True
				elif not self.checkPIDs or (self.checkPids and not pidsFailed):  
					self.successfullyTune.append([self.currTuned, self.oldTuned, fe_data]) # 3rd parameter is the frontend status
					if self.stopOnSuccess != -1 and self.stopOnSuccess <= len(self.successfullyTune):
								stop = True
				self.tuningtransponder = self.nextTransponder()
			else:
				print "************* tuner_state:", state
				
			self.progressCallback((self.getProgressLength(), self.tuningtransponder, self.STATUS_NOOP, self.currTuned))
			
			if not stop:
				self.tune()
		if self.tuningtransponder < len(self.transponderlist) and not stop:
			if self.pidStatus != self.INTERNAL_PID_STATUS_WAITING:
				self.timer.start(100, True)
				print "restart timer"
			else:
				print "not restarting timers (waiting for pids)"
		else:
			self.progressCallback((self.getProgressLength(), len(self.transponderlist), self.STATUS_DONE, self.currTuned))
			print "finishedChecking"
			self.finishedChecking()
				
	def firstTransponder(self):
		print "firstTransponder:"
		index = 0
		if self.checkPIDs:
			print "checkPIDs-loop"
			# check for tsid != -1 and onid != -1 
			print "index:", index
			print "len(self.transponderlist):", len(self.transponderlist)
			while (index < len(self.transponderlist) and (self.transponderlist[index][10] == -1 or self.transponderlist[index][11] == -1)):
			 	index += 1
		print "FirstTransponder final index:", index
		return index
	
	def nextTransponder(self):
		print "getting next transponder", self.tuningtransponder
		index = self.tuningtransponder + 1
		if self.checkPIDs:
			print "checkPIDs-loop"
			# check for tsid != -1 and onid != -1 
			print "index:", index
			print "len(self.transponderlist):", len(self.transponderlist)
			while (index < len(self.transponderlist) and (self.transponderlist[index][10] == -1 or self.transponderlist[index][11] == -1)):
			 	index += 1

		print "next transponder index:", index
		return index
	
	def finishedChecking(self):
		print "finished testing"
		print "successfull:", self.successfullyTune
		print "failed:", self.failedTune
	
	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(self.feid)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print "getFrontend failed"
			else:
				print "getRawChannel failed"
		else:
			print "getResourceManager instance failed"
		return False

	def tune(self):
		print "tuning to", self.tuningtransponder
		if self.tuningtransponder < len(self.transponderlist):
			self.pidStatus = self.INTERNAL_PID_STATUS_NOOP
			self.oldTuned = self.currTuned
			self.currTuned = self.transponderlist[self.tuningtransponder]
			self.tuner.tune(self.transponderlist[self.tuningtransponder])		

	INTERNAL_PID_STATUS_NOOP = 0
	INTERNAL_PID_STATUS_WAITING = 1
	INTERNAL_PID_STATUS_SUCCESSFUL = 2
	INTERNAL_PID_STATUS_FAILED = 3
	
	def run(self, checkPIDs = False):
		self.checkPIDs = checkPIDs
		self.pidStatus = self.INTERNAL_PID_STATUS_NOOP
		self.failedTune = []
		self.successfullyTune = []
		self.tuningtransponder = self.firstTransponder()
		self.tune()
		self.progressCallback((self.getProgressLength(), self.tuningtransponder, self.STATUS_START, self.currTuned))
		self.timer.start(100, True)
	
	# transponder = (frequency, symbolrate, polarisation, fec, inversion, orbpos, <system>, <modulation>, <rolloff>, <pilot>, <tsid>, <onid>)
	#                    0         1             2         3       4         5       6        7              8         9        10       11
	def addTransponder(self, transponder):
		self.transponderlist.append(transponder)
		
	def clearTransponder(self):
		self.transponderlist = []
		
	def getProgressLength(self):
		count = 0
		if self.stopOnError == -1:
			count = len(self.transponderlist)
		else:
			if count < self.stopOnError:
				count = self.stopOnError
		if self.stopOnSuccess == -1:
			count = len(self.transponderlist)
		else:
			if count < self.stopOnSuccess:
				count = self.stopOnSuccess
		return count
		
	STATUS_START = 0
	STATUS_TUNING = 1
	STATUS_DONE = 2
	STATUS_NOOP = 3
	# can be overwritten
	# progress = (range, value, status, transponder)
	def progressCallback(self, progress):
		pass