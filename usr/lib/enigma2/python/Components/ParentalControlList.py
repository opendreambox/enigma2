from MenuList import MenuList
from Components.ParentalControl import IMG_WHITESERVICE, IMG_WHITEBOUQUET, IMG_BLACKSERVICE, IMG_BLACKBOUQUET
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap

from skin import componentSizes, TemplatedListFonts

#Now there is a list of pictures instead of one...
entryPicture = {}

entryPicture[IMG_BLACKSERVICE] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock.png"))
entryPicture[IMG_BLACKBOUQUET] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lockBouquet.png"))
entryPicture[IMG_WHITESERVICE] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/unlock.png"))
entryPicture[IMG_WHITEBOUQUET] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/unlockBouquet.png"))

def ParentalControlEntryComponent(service, name, protectionType):
	sizes = componentSizes[componentSizes.PARENTAL_CONTROL_LIST]
	tx = sizes.get("textX", 50)
	ty = sizes.get("textY", 0)
	tw = sizes.get("textWidth", 300)
	th = sizes.get("textHeight", 32)
	pxw = sizes.get("pixmapWidth", 32)
	pxh = sizes.get("pixmapHeight", 32)

	locked = protectionType[0]
	sImage = protectionType[1]
	res = [
		(service, name, locked),
		(eListboxPythonMultiContent.TYPE_TEXT, tx, ty, tw, th, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, name)
	]
	#Changed logic: The image is defined by sImage, not by locked anymore
	if sImage != "":
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 0, pxw, pxh, entryPicture[sImage]))
	return res

class ParentalControlList(MenuList):
	def __init__(self, list, enableWrapAround = False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		itemHeight = componentSizes.itemHeight(componentSizes.PARENTAL_CONTROL_LIST, 32)
		self.l.setItemHeight(itemHeight)

	def toggleSelectedLock(self):
		from Components.ParentalControl import parentalControl
		print "self.l.getCurrentSelection():", self.l.getCurrentSelection()
		print "self.l.getCurrentSelectionIndex():", self.l.getCurrentSelectionIndex()
		curSel = self.l.getCurrentSelection()
		if curSel[0][2]:
			parentalControl.unProtectService(self.l.getCurrentSelection()[0][0])
		else:
			parentalControl.protectService(self.l.getCurrentSelection()[0][0])
		#Instead of just negating the locked- flag, now I call the getProtectionType every time...
		self.list[self.l.getCurrentSelectionIndex()] = ParentalControlEntryComponent(curSel[0][0], curSel[0][1], parentalControl.getProtectionType(curSel[0][0]))
		self.l.setList(self.list)
