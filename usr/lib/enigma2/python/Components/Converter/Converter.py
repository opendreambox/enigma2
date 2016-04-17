from Components.Element import AnimatedElement

class Converter(AnimatedElement):
	def __init__(self, arguments):
		AnimatedElement.__init__(self)
		self.converter_arguments = arguments

	def __repr__(self):
		return str(type(self)) + "(" + self.converter_arguments + ")"

	def handleCommand(self, cmd):
		self.source.handleCommand(cmd)
