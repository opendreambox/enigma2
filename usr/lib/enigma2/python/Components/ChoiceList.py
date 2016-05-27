from MenuList import MenuList
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, gFont
from skin import TemplatedListFonts, componentSizes
from Tools.LoadPixmap import LoadPixmap

from Tools.Log import Log

#return (eListboxPythonMultiContent.TYPE_TEXT, pos[0], pos[1], size[0], size[1], font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)

def ChoiceEntryComponent(key = "", text = ["--"]):
	res = [ text ]
	"""
	<component type="ChoiceList" itemHeight="30" textWidth="800" textHeight="25" textX="45" textY="0" pixmapWidth="35" pixmapHeight="25" fillerCount="200" />
	"""
	sizes = componentSizes[componentSizes.CHOICELIST]
	tx = sizes.get("textX", 45)
	ty = sizes.get("textY", 0)
	tw = sizes.get("textWidth", 800)
	th = sizes.get("textHeight", 25)
	pxw = sizes.get("pixmapWidth", 35)
	pxh = sizes.get("pixmapHeight", 25)
	fillers = sizes.get("fillerCount", 200)
	if text[0] == "--":
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, tw, th, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "-" * fillers))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, tx, ty, tw, th, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, text[0]))
		png = (key != "False") and LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/key_" + key + ".png")) or None
		if png is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 5, 0, pxw, pxh, png))

	return res

class ChoiceList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)

		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		itemHeight = componentSizes.itemHeight(componentSizes.CHOICELIST, 30)
		self.l.setItemHeight(itemHeight)
		self.selection = selection

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)
