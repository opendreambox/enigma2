from Renderer import Renderer

from enigma import ePixmap

class Pixmap(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self._pulsate = False

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		instance.setScale(0)
		self.changed((self.CHANGED_DEFAULT,))
		if self._pulsate:
			self._doPulsate(instance)

	def canPulsate(self):
		return True

	def _doPulsate(self, instance):
		instance.setPulsate(self._pulsate)

	def changed(self, what):
		if what[0] == self.CHANGED_PULSATE:
			self._pulsate = what[1]
			if self.instance:
				self._doPulsate(self.instance)
		elif what[0] != self.CHANGED_CLEAR:
			if self.source and hasattr(self.source, "pixmap"):
				if self.instance:
					self.instance.setPixmap(self.source.pixmap)
					self._doPulsate(self.instance)

