from Renderer import Renderer

from enigma import eCanvas, eRect, gRGB, eSize
from Components.AVSwitch import AVSwitch
from skin import parseSize, parsePosition

class Canvas(Renderer):
	GUI_WIDGET = eCanvas

	def __init__(self):
		Renderer.__init__(self)
		self.sequence = None
		self.draw_count = 0

	def pull_updates(self):
		if self.instance is None:
			return

		# do an incremental update
		list = self.source.drawlist
		if list is None:
			return

		# if the lists sequence count changed, re-start from begin
		if list[0] != self.sequence:
			self.sequence = list[0]
			self.draw_count = 0

		self.draw(list[1][self.draw_count:])
		self.draw_count = len(list[1])

	def draw(self, list):
		for l in list:
			if l[0] == 1:
				self.instance.fillRect(eRect(l[1], l[2], l[3], l[4]), gRGB(l[5]))
			elif l[0] == 2:
				self.instance.writeText(eRect(l[1], l[2], l[3], l[4]), gRGB(l[5]), gRGB(l[6]), l[7], l[8], l[9])
			else:
				print "drawlist entry:", l
				raise RuntimeError("invalid drawlist entry")

	def changed(self, what):
		self.pull_updates()

	def applySkin(self, desktop, parent):
		self.sequence = None
		fix_fb_aspect = None
		canvas_size = None
		size = None
		pos = None
		size_idx = None
		pos_idx = None
		attribs = []

		idx = 0
		for (attrib, value) in self.skinAttributes:
			if attrib == "correct_aspect":
				fix_fb_aspect = value
				continue
			elif attrib == "canvas_size":
				s = parseSize(value, ((1,1),(1,1)), desktop=desktop, guiObject=self.instance)
				canvas_size = s.width(), s.height()
				continue
			elif attrib == "size":
				s = parseSize(value, ((1,1),(1,1)), desktop=desktop, guiObject=self.instance)
				size = s.width(), s.height()
				size_idx = idx
			elif attrib == "position":
				p = parsePosition(value, ((1,1),(1,1)), desktop=desktop, guiObject=self.instance)
				pos = p.x(), p.y()
				pos_idx = idx
			attribs.append((attrib, value))
			idx += 1

		if fix_fb_aspect and size and pos is not None:
			aspect = AVSwitch().getFramebufferScale()
			if fix_fb_aspect == 'height':
				fixed_height = (size[1] * aspect[0]) / aspect[1]
				y_corr = fixed_height - size[1]
				attribs[pos_idx] = ("position", str(pos[0])+','+str(pos[1] - y_corr))
				attribs[size_idx] = ("size", str(size[0])+','+str(fixed_height))
			elif fix_fb_aspect == 'width':
				fixed_width = (size[0] * aspect[1]) / aspect[0]
				x_corr = size[0] - fixed_width
				attribs[pos_idx] = ("position", str(pos[0] + x_corr)+','+str(pos[1]))
				attribs[size_idx] = ("size", str(fixed_width)+','+str(size[1]))

		self.skinAttributes = attribs

		ret = Renderer.applySkin(self, desktop, parent)

		if canvas_size is not None:
			size = canvas_size

		if size:
			self.instance.setSize(eSize(size[0], size[1]))

		self.pull_updates()

		return ret
