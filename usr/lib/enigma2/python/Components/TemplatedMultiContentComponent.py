from enigma import eListboxPythonMultiContent

from skin import componentSizes
from Components.GUIComponent import GUIComponent

class TemplatedMultiContentComponent(GUIComponent):
	COMPONENT_ID = ""
	default_template = ""

	"""Turns a python tuple list into a multi-content list which can be used in a listbox renderer."""
	def __init__(self):
		GUIComponent.__init__(self)

		self._list = []
		self.active_style = None
		self.selectionEnabled = True
		self._template = self._getTemplate()
		self._initialized = False

		self.buildfunc = None
		self.l = eListboxPythonMultiContent()

	def getList(self):
		return self._list

	def setList(self, lst):
		self._list = lst
		self.l.setList(self._list)

	list = property(getList, setList)

	def applySkin(self, desktop, parent):
		GUIComponent.applySkin(self, desktop, parent)
		self.applyTemplate()

	def applyTemplate(self, additional_locals={}):
		from enigma import gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT, RT_VALIGN_TOP, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, RT_WRAP, SCALE_NONE, SCALE_CENTER, SCALE_ASPECT, SCALE_WIDTH, SCALE_HEIGHT, SCALE_STRETCH, SCALE_FILL
		from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmap, MultiContentEntryPixmapAlphaTest, MultiContentEntryPixmapAlphaBlend, MultiContentTemplateColor, MultiContentEntryProgress, MultiContentEntryProgressPixmap

		l = locals()
		del l["self"] # cleanup locals a bit
		l.update(additional_locals)

		self.template = eval(self._template, {}, l)
		assert "template" in self.template or "templates" in self.template
		assert "template" in self.template or "default" in self.template["templates"] # we need to have a default template
		assert "fonts" in self.template

		if not "template" in self.template: # default template can be ["template"] or ["templates"]["default"]
			self.template["template"] = self.template["templates"]["default"][1]
			self.template["itemHeight"] = self.template["template"][0]

		assert "itemHeight" in self.template

		self._initialized = True
		self.initContent()

	def _getTemplate(self):
		tpl = componentSizes.template(self.COMPONENT_ID)
		if not tpl:
			tpl = self.default_template
		return tpl

	def initContent(self):
		# also setup fonts (also given by source)
		index = 0
		for f in self.template["fonts"]:
			self.l.setFont(index, f)
			index += 1

		self.l.setList(self.list)
		self.setTemplate(style=self.active_style, force=True)

	def setTemplate(self, style="default", force=False):
		self.l.setSelectionEnable(self.selectionEnabled)

		if style == self.active_style and not force:
			return

		self.active_style = style
		if not self._initialized:
			return

		# if skin defined "templates", that means that it defines multiple styles in a dict. template should still be a default
		templates = self.template.get("templates")
		template = self.template.get("template")
		itemheight = self.template["itemHeight"]
		selectionEnabled = self.template.get("selectionEnabled", True)
		scrollbarMode = self.template.get("scrollbarMode", None)

		if templates and style and style in templates: # if we have a custom style defined in the source, and different templates in the skin, look it up
			template = templates[style][1]
			itemheight = templates[style][0]
			if len(templates[style]) > 2:
				selectionEnabled = templates[style][2]
			if len(templates[style]) > 3:
				scrollbarMode = templates[style][3]

		self.l.setTemplate(template)
		self.l.setItemHeight(itemheight)
		self.selectionEnabled = selectionEnabled
		self.l.setSelectionEnable(selectionEnabled)
		if scrollbarMode is not None:
			self.scrollbarMode = scrollbarMode

