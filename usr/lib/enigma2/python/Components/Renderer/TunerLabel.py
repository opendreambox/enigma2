from Renderer import Renderer
from Components.NimManager import nimmanager
from enigma import eLabel

class TunerLabel(Renderer):
	def __init__(self, tuner_no):
		Renderer.__init__(self)
		self.tuner_no = int(tuner_no)

	GUI_WIDGET = eLabel

	def postWidgetCreate(self, instance):
		if self.tuner_no < nimmanager.getSlotCount():
			slot_name = nimmanager.getNimSlotInputName(self.tuner_no)
			self.instance.setText(slot_name)
