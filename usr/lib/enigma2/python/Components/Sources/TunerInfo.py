from Source import Source
from enigma import eDVBResourceManager

class TunerInfo(Source):
	FE_USE_MASK = 0

	def __init__(self):
		Source.__init__(self)
		self.isAnimated = False
		self.tuner_use_mask = 0
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.frontendUseMaskChanged_conn = res_mgr.frontendUseMaskChanged.connect(self.tunerUseMaskChanged)
		else:
			print "no res_mgr!!"

	def tunerUseMaskChanged(self, mask):
		self.tuner_use_mask = mask
		self.changed((self.CHANGED_SPECIFIC, self.FE_USE_MASK))

	def getTunerUseMask(self):
		return self.tuner_use_mask

	def destroy(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.frontendUseMaskChanged_conn = None
		else:
			print "no res_mgr!!"
		Source.destroy(self)
