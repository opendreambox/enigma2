from Components.Converter.Converter import Converter
from Components.Element import cached

class StringListSelection(Converter, object):
	"extracts the first element of a the current string list  element for displaying it on LCD"
	def __init__(self, args):
		Converter.__init__(self, args)
		if args.isdigit():
			self.element_index = int(args)
		else:
			self.element_index = 0

	def selChanged(self):
		self.downstream_elements.changed((self.CHANGED_ALL, 0))

	@cached
	def getText(self):
		cur = self.source.current
		if cur and len(cur):
			return cur[self.element_index]
		return None

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_DEFAULT:
			self.source.onSelectionChanged.append(self.selChanged)
		Converter.changed(self, what)
