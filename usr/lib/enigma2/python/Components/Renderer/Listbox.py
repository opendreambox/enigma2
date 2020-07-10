from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from enigma import eListbox, ePoint

# the listbox renderer is the listbox, but no listbox content.
# the content will be provided by the source (or converter).

# the source should emit the 'changed' signal whenever
# it has a new listbox content.

# the source needs to have the 'content' property for the
# used listbox content

# it should expose exactly the non-content related functions
# of the eListbox class. more or less.

class Listbox(Renderer, object):
	def __init__(self):
		Renderer.__init__(self)
		self.__content = None
		self.__mode = eListbox.layoutVertical
		self.__wrap_around = False
		self.__selection_enabled = True
		self.__scrollbarMode = "showOnDemand"
		self.__backlogMode = False
		self.__margin = ePoint(0,0)
		self.__selectionZoom = 1.0

	GUI_WIDGET = eListbox

	def contentChanged(self):
		self.content = self.source.content

	def setContent(self, content):
		self.__content = content
		if self.instance is not None:
			self.instance.setContent(self.__content)

	content = property(lambda self: self.__content, setContent)

	def setMode(self, mode):
		self.__mode = mode
		if self.instance:
			self.instance.setMode(self.__mode)

	mode = property(lambda self: self.__mode, setMode)

	def setMargin(self, leftRight, topBottom):
		self.__margin = ePoint(leftRight, topBottom)
		if self.instance:
			self.instance.setMargin(self.__margin)

	margin = property(lambda self: self.__margin, setMargin)

	def setSelectionZoom(self, factor):
		self.__selectionZoom = factor
		if self.instance:
			self.instance.setSelectionZoom(factor)

	selectionZoom = property(lambda self: self.__selectionZoom, setSelectionZoom)

	def postWidgetCreate(self, instance):
		if self.__content is not None:
			instance.setContent(self.__content)
		self.instance.setMode(self.__mode)
		self.instance.setMargin(self.__margin)
		self.setSelectionZoom(self.__selectionZoom)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		self.wrap_around = self.wrap_around # trigger
		self.selection_enabled = self.selection_enabled # trigger
		for (attrib, value) in self.skinAttributes:
			if attrib == "scrollbarMode":
				self.__scrollbarMode = value
				break
			elif attrib == "mode":
				mode = {
					'vertical' : eListbox.layoutVertical,
					'grid' : eListbox.layoutGrid,
					'horizontal' : eListbox.layoutHorizontal
				}[value]
				self.mode = mode
			elif attrib == "margin":
				leftRight, bottomTop = [int(x) for x in value.split(",")]
				self.__margin = ePoint(leftRight, bottomTop)
			elif attrib == "selectionZoom":
				self.selectionZoom = float(value)
		self.scrollbarMode = self.scrollbarMode # trigger
		self.backlogMode = self.backlogMode # trigger

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def setWrapAround(self, wrap_around):
		self.__wrap_around = wrap_around
		if self.instance is not None:
			self.instance.setWrapAround(self.__wrap_around)

	wrap_around = property(lambda self: self.__wrap_around, setWrapAround)

	def setBacklogMode(self, mode):
		self.__backlogMode = mode
		if self.instance is not None:
			self.instance.setBacklogMode(self.__backlogMode)

	backlogMode = property(lambda self: self.__backlogMode, setBacklogMode)

	def selectionChanged(self):
		self.source.selectionChanged(self.index)

	def getIndex(self):
		if self.instance is None:
			return 0
		return self.instance.getCurrentIndex()

	def moveToIndex(self, index):
		if self.instance is None:
			return
		self.instance.moveSelectionTo(index)

	index = property(getIndex, moveToIndex)

	def move(self, direction):
		if self.instance is not None:
			self.instance.moveSelection(direction)

	def setSelectionEnabled(self, enabled):
		self.__selection_enabled = enabled
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

	selection_enabled = property(lambda self: self.__selection_enabled, setSelectionEnabled)

	def setScrollbarMode(self, mode):
		self.__scrollbarMode = mode
		if self.instance is not None:
			self.instance.setScrollbarMode(int(
				{ "showOnDemand": 0,
				  "showAlways": 1,
				  "showNever": 2,
				}[mode]))

	scrollbarMode = property(lambda self: self.__scrollbarMode, setScrollbarMode)

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

	def changed(self, what):
		if hasattr(self.source, "mode"):
			self.mode = self.source.mode
		if hasattr(self.source, "margin"):
			self.margin = self.source.margin
		if hasattr(self.source, "selectionZoom"):
			self.selectionZoom = self.source.selectionZoom
		if hasattr(self.source, "selectionEnabled"):
			self.selection_enabled = self.source.selectionEnabled
		if hasattr(self.source, "scrollbarMode"):
			self.scrollbarMode = self.source.scrollbarMode
		if hasattr(self.source, "backlogMode"):
			self.backlogMode = self.source.backlogMode
		if len(what) > 1 and isinstance(what[1], str) and what[1] == "style":
			return
		elif len(what) > 1 and isinstance(what[1], str) and what[1] == "hide":
			self.instance.hide()
			return
		elif len(what) > 1 and isinstance(what[1], str) and what[1] == "show":
			self.instance.show()
			return
		self.content = self.source.content

	def entry_changed(self, index):
		if self.instance is not None:
			self.instance.entryChanged(index)
