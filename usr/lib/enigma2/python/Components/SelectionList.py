from MenuList import MenuList
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap

from skin import componentSizes, TemplatedListFonts

selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/selectioncross.png"))

def SelectionEntryComponent(description, value, index, selected):
	sizes = componentSizes[componentSizes.SELECTION_LIST]
	tx = sizes.get("textX", 30)
	ty = sizes.get("textY", 0)
	tw = sizes.get("textWidth", 1000)
	th = sizes.get("textHeight", 30)
	pxw = sizes.get("pixmapWidth", 30)
	pxh = sizes.get("pixmapHeight", 30)

	res = [
		(description, value, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, tx, ty, tw, th, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, description)
	]
	if selected:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 0, 0, pxw, pxh, selectionpng))
	return res

class SelectionList(MenuList):
	def __init__(self, list = None, enableWrapAround = False):
		MenuList.__init__(self, list or [], enableWrapAround, content = eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		itemHeight = componentSizes.itemHeight(componentSizes.SELECTION_LIST, 30)
		self.l.setItemHeight(itemHeight)

	def addSelection(self, description, value, index, selected = True):
		self.list.append(SelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		idx = self.getSelectedIndex()
		item = self.list[idx][0]
		self.list[idx] = SelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def getSelectionsList(self):
		return [ (item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3] ]

