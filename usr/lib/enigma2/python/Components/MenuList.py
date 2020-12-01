from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent

from enigma import eListboxPythonStringContent, eListbox, ePoint

class MenuList(HTMLComponent, GUIComponent):
	def __init__(self, list, enableWrapAround=False, content=eListboxPythonStringContent, mode=eListbox.layoutVertical, itemSize=0, itemWidth=0, itemHeight=0, margin=ePoint(0,0), selectionZoom=1.0):
		GUIComponent.__init__(self)
		self.list = list
		self.l = content()
		self.l.setList(self.list)
		self.onSelectionChanged = [ ]
		self.enableWrapAround = enableWrapAround
		self._mode = mode
		self._itemSize = itemSize
		self._itemWidth = itemWidth
		self._itemHeight = itemHeight
		self._margin = margin
		self._selectionZoom = selectionZoom

	def getCurrent(self):
		return self.l.getCurrentSelection()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setMode(self._mode)
		instance.setMargin(self._margin)
		instance.setSelectionZoom(self._selectionZoom)
		if self._itemSize:
			if self._mode == eListbox.layoutVertical:
				instance.setItemHeight(self._itemSize)
			else:
				instance.setItemWidth(self._itemSize)
		if self._itemHeight and self._itemWidth and self._mode == eListbox.layoutGrid:
			instance.setItemHeight(self._itemHeight)
			instance.setItemWidth(self._itemWidth)

		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		if self.enableWrapAround:
			self.instance.setWrapAround(self.enableWrapAround)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def selectionChanged(self):
		for f in self.onSelectionChanged:
			f()

	def getSelectionIndex(self):
		return self.l.getCurrentSelectionIndex()

	def getSelectedIndex(self):
		return self.l.getCurrentSelectionIndex()

	def setList(self, list):
		self.list = list
		self.l.setList(self.list)

	def moveToIndex(self, idx):
		if self.instance is not None:
			self.instance.moveSelectionTo(idx)

	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)

	def up(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)

	def down(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)

	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

	@property
	def currentPage(self):
		if self.instance:
			return self.instance.currentPage()
		return 0

	@property
	def totalPages(self):
		if self.instance:
			return self.instance.totalPages()
		return 0

	@property
	def itemWidth(self):
		if self.instance:
			return self.instance.itemWidth()
		return 0

	@property
	def itemHeight(self):
		if self.instance:
			return self.instance.itemHeight()
		return 0
