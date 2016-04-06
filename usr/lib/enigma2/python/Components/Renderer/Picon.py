##
## Picon renderer by Gruffy .. some speedups by Ghost
##
from Renderer import Renderer
from enigma import ePixmap, eEnv
from Tools.Directories import fileExists, SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, resolveFilename
from Tools.PiconResolver import PiconResolver

class Picon(Renderer):
	searchPaths = (eEnv.resolve('${datadir}/enigma2/%s/'),)

	def __init__(self):
		Renderer.__init__(self)
		self.path = "picon"
		self.nameCache = { }
		self.pngname = ""

	def applySkin(self, desktop, parent):
		attribs = [ ]
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.path = value
			else:
				attribs.append((attrib,value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		instance.setScale(1)

	def changed(self, what):
		if self.instance:
			pngname = ""
			sname = self.source.text
			if what[0] != self.CHANGED_CLEAR:
				pngname = PiconResolver.getPngName(sname, self.nameCache, self.findPicon)
				self.nameCache[sname] = pngname
			if pngname == "": # no picon for service found, resolve skin default picon
				tmp = resolveFilename(SCOPE_CURRENT_SKIN, "picon_default.png")
				if fileExists(tmp):
					pngname = tmp
				else:
					pngname = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/picon_default.png")
				self.nameCache["default"] = pngname

			if self.pngname != pngname:
				self.instance.setPixmapFromFile(pngname)
				self.pngname = pngname

	def findPicon(self, serviceName):
		for path in self.searchPaths:
			pngname = (path % self.path) + serviceName + ".png"
			if fileExists(pngname):
				return pngname
		return ""
