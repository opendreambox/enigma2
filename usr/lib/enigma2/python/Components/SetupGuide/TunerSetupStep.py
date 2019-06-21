from Components.SetupGuide.BaseStep import SetupConfigStep
from Screens.Satconfig import NimSetupBase
from Components.NimManager import nimmanager
from Tools.Log import Log
from Components.SetupGuide.InitialSetupSteps import initialSetupSteps

class TunerSetupStep(SetupConfigStep, NimSetupBase):
	def __init__(self, parent, slotid):
		SetupConfigStep.__init__(self, parent)
		NimSetupBase.__init__(self, slotid)

	def _getConfig(self):
		return self._configList

	def prepare(self):
		self.createConfigMode()
		self.createSetup()
		nim = nimmanager.nim_slots[self.slotid]
		self.title = nim.slot_name
		self.text = nim.friendly_full_description
		return True

	@property
	def configContent(self):
		if not self.list:
			self.createSetup()
		return self.list

	def left(self):
		self.newConfig()

	def right(self):
		self.newConfig()

	def onOk(self):
		old_configured_sats = nimmanager.getConfiguredSats()
		self.run()
		new_configured_sats = nimmanager.getConfiguredSats()
		self.unconfed_sats = old_configured_sats - new_configured_sats
		self.satpos_to_remove = None
#		self.deleteConfirmed((None, "no"))

		return True

def addNIMSteps():
	for nim in nimmanager.nim_slots:
		Log.w("%s-%s (%s:%s)" %(nim.slot, nim.friendly_full_description, nim.inputs, nim.channel))
		inputs = nim.inputs is not None and len(nim.inputs) or 0
		if not inputs or nim.channel < inputs:
			initialSetupSteps.add({
				initialSetupSteps.PRIO_TUNER : { 
					"class" : TunerSetupStep,
					"args" : [nim.slot,]
				}
			})
			Log.w("added!")
initialSetupSteps.onPrepare.append(addNIMSteps)

