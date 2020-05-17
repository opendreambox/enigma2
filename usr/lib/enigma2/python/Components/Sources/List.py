from __future__ import absolute_import
from enigma import eListbox, ePoint
from Components.Sources.Source import Source
from Components.Element import cached

class List(Source, object):
	"""The datasource of a listbox. Currently, the format depends on the used converter. So
if you put a simple string list in here, you need to use a StringList converter, if you are
using a "multi content list styled"-list, you need to use the StaticMultiList converter, and
setup the "fonts". 

This has been done so another converter could convert the list to a different format, for example
to generate HTML."""
	def __init__(self, list = [ ], enableWrapAround = False, item_height = 25, fonts = [ ], buildfunc = None):
		Source.__init__(self)
		self.__list = list
		self.onSelectionChanged = [ ]
		self.item_height = item_height
		self.fonts = fonts
		self.disable_callbacks = False
		self.enableWrapAround = enableWrapAround
		self.__style = "default" # style might be an optional string which can be used to define different visualisations in the skin
		self.__buildfunc = buildfunc
		self.__selection_enabled = True
		self.__mode = eListbox.layoutVertical
		self.__margin = ePoint(0,0)
		self.__selectionZoom = 1.0

	def setList(self, list):
		self.__list = list
		self.changed((self.CHANGED_ALL,))

	list = property(lambda self: self.__list, setList)

	def entry_changed(self, index):
		if not self.disable_callbacks:
			self.downstream_elements.entry_changed(index)

	def modifyEntry(self, index, data):
		self.__list[index] = data
		self.entry_changed(index)

	def count(self):
		return len(self.__list)

	def selectionChanged(self, index):
		if self.disable_callbacks:
			return

		# update all non-master targets
		for x in self.downstream_elements:
			if x is not self.master:
				x.index = index

		for x in self.onSelectionChanged:
			x()

	@cached
	def getCurrent(self):
		return self.master is not None and self.master.current

	current = property(getCurrent)

	def setIndex(self, index):
		if self.master is not None:
			self.master.index = index

	@cached
	def getIndex(self):
		if self.master is not None:
			return self.master.index
		else:
			return 0

	setCurrentIndex = setIndex

	index = property(getIndex, setIndex)
	
	def selectNext(self):
		if self.getIndex() + 1 >= self.count():
			if self.enableWrapAround:
				self.index = 0
		else:
			self.index += 1

	def selectPrevious(self):
		if self.getIndex() - 1 < 0:
			if self.enableWrapAround:
				self.index = self.count() - 1
		else:
			self.index -= 1

	def moveSelection(self, direction):
		if self.master is not None:
			if hasattr(self.master, "content"):
				self.master.content.moveSelection(int(
					{ "moveUp": 0,
					  "moveDown": 1,
					  "moveTop": 2,
					  "moveEnd": 3,
					  "pageUp": 4,
					  "pageDown": 5,
					  "justCheck": 6,
					}[direction]))
	def pageUp(self):
		self.moveSelection("pageUp")

	def pageDown(self):
		self.moveSelection("pageDown")

	@cached
	def getStyle(self):
		return self.__style

	def setStyle(self, style):
		if self.__style != style:
			self.__style = style
			self.changed((self.CHANGED_SPECIFIC, "style"))

	style = property(getStyle, setStyle)

	@cached
	def getBuildFunc(self):
		return self.__buildfunc

	def setBuildFunc(self, buildfunc):
		if self.__buildfunc != buildfunc:
			self.__buildfunc = buildfunc
			self.changed((self.CHANGED_SPECIFIC, "buildfunc"))

	buildfunc = property(getBuildFunc, setBuildFunc)

	def setSelectionEnabled(self, enabled):
		if self.__selection_enabled != enabled:
			self.__selection_enabled = enabled
			self.changed((self.CHANGED_SPECIFIC, "selection_enabled"))

	selection_enabled = property(lambda self: self.__selection_enabled, setSelectionEnabled)

	def setMode(self, mode):
		if self.__mode != mode:
			self.__mode = mode
			self.changed((self.CHANGED_SPECIFIC, "mode"))

	mode = property(lambda self: self.__mode, setMode)

	def setMargin(self, margin):
		if self.__margin != margin:
			self.__margin = margin
			self.changed(self.CHANGED_SPECIFIC, "margin")

	margin = property(lambda self: self.__margin, setMargin)

	def setSelectionZoom(self, zoom):
		if self.__selectionZoom != zoom:
			self.__selectionZoom = zoom
			self.changed(self.CHANGED_SPECIFIC, "selectionZoom")

	selectionZoom = property(lambda self: self.__selectionZoom, setSelectionZoom)

	def hide(self):
		self.changed((self.CHANGED_SPECIFIC, "hide"))

	def show(self):
		self.changed((self.CHANGED_SPECIFIC, "show"))

	def updateList(self, list):
		"""Changes the list without changing the selection or emitting changed Events"""
		max_index = len(list) - 1
		old_index = min(max_index, self.index)
		self.disable_callbacks = True
		self.list = list
		self.index = old_index
		self.disable_callbacks = False
