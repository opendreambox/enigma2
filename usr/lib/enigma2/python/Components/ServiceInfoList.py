from enigma import eServiceCenter, eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

from Components.HTMLComponent import HTMLComponent
from Components.GUIComponent import GUIComponent

from skin import componentSizes, TemplatedListFonts

TYPE_TEXT = 0
TYPE_VALUE_HEX = 1
TYPE_VALUE_DEC = 2
TYPE_VALUE_HEX_DEC = 3
TYPE_SLIDER = 4

def to_unsigned(x):
	return x & 0xFFFFFFFF

def ServiceInfoListEntry(a, b, valueType=TYPE_TEXT, param=4):
	sizes = componentSizes[componentSizes.SERVICE_INFO_LIST]
	tx = sizes.get("textX", 0)
	ty = sizes.get("textY", 0)
	tw = sizes.get("textWidth", 200)
	th = sizes.get("textHeight", 30)
	t2x = sizes.get("text2X", 220)
	t2y = sizes.get("text2Y", 0)
	t2w = sizes.get("text2Width", 350)
	t2h = sizes.get("text2Height", 30)

	print "b:", b
	if not isinstance(b, str):
		if valueType == TYPE_VALUE_HEX:
			b = ("0x%0" + str(param) + "x") % to_unsigned(b)
		elif valueType == TYPE_VALUE_DEC:
			b = str(b)
		elif valueType == TYPE_VALUE_HEX_DEC:
			b = ("0x%0" + str(param) + "x (%dd)") % (to_unsigned(b), b)
		else:
			b = str(b)

	return [
		None, # No private data needed...
		#PyObject *type, *px, *py, *pwidth, *pheight, *pfnt, *pstring, *pflags;
		(eListboxPythonMultiContent.TYPE_TEXT, tx, ty, tw, th, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, a),
		(eListboxPythonMultiContent.TYPE_TEXT, t2x, t2y, t2w, t2h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, b)
	]

class ServiceInfoList(HTMLComponent, GUIComponent):
	def __init__(self, source):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.list = source
		self.l.setList(self.list)
		
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		itemHeight = componentSizes.itemHeight(componentSizes.SERVICE_INFO_LIST, 30)
		self.l.setItemHeight(itemHeight)
		self.serviceHandler = eServiceCenter.getInstance()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		self.instance.setContent(self.l)
