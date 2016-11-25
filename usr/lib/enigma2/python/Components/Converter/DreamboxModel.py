from Components.Converter.Converter import Converter

class DreamboxModel(Converter):
	MODEL_MAP = {
		"dm525"  : "DM525 HD",
		"dm520"  : "DM520 HD",
		"dm820"  : "DM820 HD",
		"dm900"  : "DM900 ultraHD",
		"dm7080" : "DM7080 HD",
	}

	def __init__(self, arguments):
		Converter.__init__(self, arguments)

	def getText(self):
		text = self.source.text
		return self.MODEL_MAP.get(text, text)
	text = property(getText)
