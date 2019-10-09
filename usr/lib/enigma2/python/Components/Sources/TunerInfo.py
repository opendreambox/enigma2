from __future__ import print_function
from Source import Source
from enigma import eDVBResourceManager

class TunerInfo(Source):
	FE_USE_MASK = 0
	INPUT_USE_MASK = 1

	def __init__(self):
		Source.__init__(self)
		self.isAnimated = False
		self.tuner_use_mask = 0
		self.input_use_mask = 0
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.frontendUseMaskChanged_conn = res_mgr.frontendUseMaskChanged.connect(self.tunerUseMaskChanged)
			self.frontendInputUseMaskChanged_conn = res_mgr.frontendInputUseMaskChanged.connect(self.tunerInputUseMaskChanged)
		else:
			print("no res_mgr!!")

	def tunerUseMaskChanged(self, mask):
		self.tuner_use_mask = mask
		self.changed((self.CHANGED_SPECIFIC, self.FE_USE_MASK))

	def tunerInputUseMaskChanged(self, mask):
		self.input_use_mask = mask
		self.changed((self.CHANGED_SPECIFIC, self.INPUT_USE_MASK))

	def getTunerUseMask(self):
		return self.tuner_use_mask

	def getInputUseMask(self):
		return self.input_use_mask

	def destroy(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.frontendUseMaskChanged_conn = None
			self.frontendInputUseMaskChanged_conn = None
		else:
			print("no res_mgr!!")
		Source.destroy(self)
