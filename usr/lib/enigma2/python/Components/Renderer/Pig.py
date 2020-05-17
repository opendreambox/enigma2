##
## P(icture)i(n)g(raphics) renderer
##
from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from enigma import eVideoWidget, getDesktop

class Pig(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.Position = self.Size = None

	GUI_WIDGET = eVideoWidget

	def postWidgetCreate(self, instance):
		desk = getDesktop(0)
		instance.setDecoder(0)
		instance.setFBSize(desk.size())

	def applySkin(self, desktop, parent):
		ret = Renderer.applySkin(self, desktop, parent)
		if ret:
			self.Position = self.instance.position() # fixme, scaling!
			self.Size = self.instance.size()
		return ret

	def onShow(self):
		if self.instance:
			if self.Size:
				self.instance.resize(self.Size)
			if self.Position:
				self.instance.move(self.Position)

	def onHide(self):
		if self.instance:
			self.preWidgetRemove(self.instance)
