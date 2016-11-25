from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from enigma import eListbox, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT
from skin import TemplatedColors, componentSizes, TemplatedListFonts

class SortableList(MenuList):
	def __init__(self, tuplelist):
		entries = []
		for (obj, text) in tuplelist:
			entries.append(self.buildEntry(obj, text))
		MenuList.__init__(self, entries, enableWrapAround=False, content=eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		itemHeight = componentSizes.itemHeight(componentSizes.SELECTION_LIST, 30)
		self.l.setItemHeight(itemHeight)
		self.markedForeground = 0xffffff
		self.markedBackground = 0xff0000
		colors = TemplatedColors().colors
		if "ListboxMarkedForeground" in colors:
			self.markedForeground = colors["ListboxMarkedForeground"]
		if "ListboxMarkedBackground" in colors:
			self.markedBackground = colors["ListboxMarkedBackground"]
		self.entry_marked = False

	GUI_WIDGET = eListbox

	def insertEntry(self, tup):
		if isinstance(tup, tuple):
			if len(self.list):
				idx = self.getSelectedIndex()
				item = self.list[idx][0]
				self.list[idx] = self.buildEntry(item[0], item[1])
			else:
				idx = 0
			self.list.insert(idx, self.buildEntry(tup[0], tup[1]))
			self.entry_marked = False
			self.setList(self.list)

	def removeCurrentEntry(self):
		if len(self.list):
			idx = self.getSelectedIndex()
			del self.list[idx]
			self.entry_marked = False
			self.setList(self.list)

	def toggleSelection(self):
		if len(self.list):
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = self.buildEntry(item[0], item[1], not item[2])
			self.entry_marked = not item[2]
			self.setList(self.list)

	def buildEntry(self, obj, text, marked=False):
		sizes = componentSizes[componentSizes.SELECTION_LIST]
		tx = sizes.get("textX", 30)
		ty = sizes.get("textY", 0)
		tw = sizes.get("textWidth", 1000)
		th = sizes.get("textHeight", 30)

		forgroundColor = backgroundColor = None
		if marked == 1: #  marked
			forgroundColor = self.markedForeground
			backgroundColor = self.markedBackground

		res = [
			(obj, text, marked),
			(eListboxPythonMultiContent.TYPE_TEXT, tx, ty, tw, th, 0, RT_HALIGN_LEFT, text, forgroundColor, forgroundColor, backgroundColor, None)
		]
		return res

	def keyUp(self):
		if self.instance is not None:
			if self.entry_marked:
				idx = self.getSelectedIndex()
				if idx >= 1:
					l = self.list
					self.setList(l[:idx-1]+[l[idx]]+[l[idx-1]]+l[idx+1:])
			self.instance.moveSelection(self.instance.moveUp)

	def keyDown(self):
		if self.instance is not None:
			if self.entry_marked:
				idx = self.getSelectedIndex()
				if idx < len(self.list)-1:
					l = self.list
					self.setList(l[:idx]+[l[idx+1]]+[l[idx]]+l[idx+2:])
			self.instance.moveSelection(self.instance.moveDown)

	def getList(self):
		res = []
		for item in self.list:
			res.append(item[0][:2])
		return res

class SortableListScreen:
	skin = """
		<screen name="SortableListScreen" position="center,center" size="580,500" title="Sortable List">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="10,50" size="560,405" scrollbarMode="showOnDemand"/>
			<widget name="info" position="10,460" zPosition="1" size="560,40" font="Regular;20" valign="center" transparent="1" />
		</screen>"""

	def __init__(self, session = None, tuplelist = []):
		self["list"] = SortableList(tuplelist)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["info"] = Label(_("Press OK to select entry to be moved"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
		{
			"save": self.keySave,
			"cancel": self.keyCancel,
			"up": self.keyUp,
			"upRepeated": self.keyUp,
			"down": self.keyDown,
			"downRepeated": self.keyDown,
			"ok": self.keyOk,
			"downUp": self.nothing,
			"upUp": self.nothing
		}, -2)

	def nothing(self):
		pass

	def keyOk(self):
		self["list"].toggleSelection()

	def keySave(self):
		self.close(self["list"].getList())

	def keyCancel(self):
		self.close(False)

	def keyUp(self):
		self["list"].keyUp()

	def keyDown(self):
		self["list"].keyDown()
