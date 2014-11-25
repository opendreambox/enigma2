from enigma import eTimer
from Converter import Converter
from Components.Renderer.Renderer import Renderer

class ConditionalShowHide(Converter, object):
	def __init__(self, argstr):
		Converter.__init__(self, argstr)
		args = argstr.split(',')
		self.invert = "Invert" in args
		self.blink = "Blink" in args
		if self.blink:
			self.blinktime = 500
		self.timer = None

	def blinkFunc(self):
		if self.blinking == True:
			for x in self.downstream_elements:
				if not x.canPulsate():
					x.visible = not x.visible

	def startBlinking(self):
		self.blinking = True
		if self.timer:
			self.timer.start(self.blinktime)
		for x in self.downstream_elements:
			if x.canPulsate():
				x.changed((Renderer.CHANGED_PULSATE, True))
				x.show()

	def stopBlinking(self):
		self.blinking = False
		if self.timer:
			self.timer.stop()

		for x in self.downstream_elements:
			if x.canPulsate():
				x.changed((Renderer.CHANGED_PULSATE, False))
			x.hide()

	def calcVisibility(self):
		b = self.source.boolean
		if b is None:
			return True
		b ^= self.invert
		return b

	def changed(self, what):
		vis = self.calcVisibility()
		if self.blink:
			if vis:
				self.startBlinking()
			else:
				self.stopBlinking()
		else:
			for x in self.downstream_elements:
				x.visible = vis

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		vis = self.calcVisibility()

		if self.blink:
			if not downstream.canPulsate():
				self.timer = eTimer()
				self.timer_conn = self.timer.timeout.connect(self.blinkFunc)
			if vis:
				self.startBlinking()
			else:
				self.stopBlinking()
		else:
			downstream.visible = self.calcVisibility()

	def destroy(self):
		self.timer_conn = None
