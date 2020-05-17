from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from Components.NimManager import nimmanager
from enigma import eLabel

class TunerLabel(Renderer):
	def __init__(self, tuner_no, which='demod'):
		Renderer.__init__(self)
		tuner_no = int(tuner_no)
		self.which = which
		if which == 'input':
			# convert input to slot
			index = -1
			slotid = 0
			slots = len(nimmanager.nim_slots)
			while slotid < slots:
				slot = nimmanager.nim_slots[slotid]
				if slot.inputs is None or slot.channel < len(slot.inputs):
					index += 1
				if index >= tuner_no:
					break
				slotid += 1
			self.tuner_no = slotid
		else:
			self.tuner_no = int(tuner_no)
	GUI_WIDGET = eLabel

	def postWidgetCreate(self, instance):
		if self.tuner_no < nimmanager.getSlotCount():
			slot_name = nimmanager.getNimSlotInputName(self.tuner_no, self.which == 'input')
			self.instance.setText(slot_name)
