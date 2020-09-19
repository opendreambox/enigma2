from Components.Element import Element
from Tools.Directories import fileExists
from Tools.Log import Log
from Components.FrontPanelLed import FrontPanelLed as FPL
# this is not a GUI renderer.
class FrontpanelLed(Element):
	def __init__(self, which = 0, patterns = [(20, 0, 0xffffffff),(20, 0x55555555, 0x84fc8c04)], boolean = True):
		self.which = which
		self.boolean = boolean
		self.patterns = patterns
		Element.__init__(self)

	def changed(self, *args, **kwargs):
		if self.boolean:
			val = 1 if self.source.boolean else 0
		else:
			val = self.source.value

		if fileExists(FPL.COLOR_PATH): #new API
			return

		(speed, pattern, pattern_4bit) = self.patterns[val]

		try:
			open("/proc/stb/fp/led%d_pattern" % self.which, "w").write("%08x" % pattern)
		except IOError:
			pass
		if self.which == 0:
			try:
				open("/proc/stb/fp/led_set_pattern", "w").write("%08x" % pattern_4bit)
				open("/proc/stb/fp/led_set_speed", "w").write("%d" % speed)
			except IOError:
				pass
			try:
				open("/proc/stb/fp/led_pattern_speed", "w").write("%d" % speed)
			except IOError:
				pass
