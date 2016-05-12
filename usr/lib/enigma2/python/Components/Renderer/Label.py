from Components.VariableText import VariableText
from Renderer import Renderer

from enigma import eLabel

class Label(VariableText, Renderer):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)

	GUI_WIDGET = eLabel

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def postWidgetCreate(self, instance):
		VariableText.postWidgetCreate(self, instance)
		instance.setDefaultAnimationEnabled(self.source.isAnimated)

	def changed(self, what):
		if what[0] == self.CHANGED_ANIMATED and self.instance:
			self.instance.setDefaultAnimationEnabled(self.source.isAnimated)
		elif what[0] == self.CHANGED_CLEAR:
			self.text = ""
		else:
			self.text = self.source.text

