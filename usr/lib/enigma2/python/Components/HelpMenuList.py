from __future__ import print_function
from GUIComponent import GUIComponent

from enigma import eListboxPythonMultiContent, eListbox, gFont, \
	RT_VALIGN_CENTER
from Tools.KeyBindings import queryKeyBinding, getKeyDescription
from skin import componentSizes, TemplatedListFonts
#getKeyPositions

# [ ( actionmap, context, [(action, help), (action, help), ...] ), (actionmap, ... ), ... ]

class HelpMenuList(GUIComponent):
	def __init__(self, helplist, callback):
		GUIComponent.__init__(self)
		self.onSelChanged = [ ]
		self.l = eListboxPythonMultiContent()
		self.callback = callback
		self.extendedHelp = False

		l = [ ]
		sizes = componentSizes[componentSizes.HELP_MENU_LIST]
		textX = sizes.get("textX", 5)
		textY = sizes.get("textY", 35)
		textWidth = sizes.get("textWidth", 1000)
		textHeight = sizes.get("textHeight", 35)
		for (actionmap, context, actions) in helplist:
			if not actionmap.enabled:
				continue
			for (action, help) in actions:
				buttons = queryKeyBinding(context, action)

				# do not display entries which are not accessible from keys
				if not len(buttons):
					continue

				name = None
				flags = 0

				for n in buttons:
					(name, flags) = (getKeyDescription(n[0]), n[1])
					if name is not None:
						break

				if flags & 8: # for long keypresses, prepend l_ into the key name.
					name = (name[0], "long")
					
				entry = [ (actionmap, context, action, name ) ]

				if isinstance(help, list):
					self.extendedHelp = True
					print("extendedHelpEntry found")
					entry.extend((
						(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, textWidth, textHeight, 0, RT_VALIGN_CENTER, help[0]),
						(eListboxPythonMultiContent.TYPE_TEXT, 0, textY, textWidth, textHeight, 1, RT_VALIGN_CENTER, help[1])
					))
				else:
					entry.append( (eListboxPythonMultiContent.TYPE_TEXT, textX, 0, textWidth, textHeight, 0, RT_VALIGN_CENTER, help) )
					
				l.append(entry)

		self.l.setList(l)

		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		self.l.setFont(1, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setItemHeight(sizes.get(componentSizes.ITEM_HEIGHT, 30))

	def ok(self):
		# a list entry has a "private" tuple as first entry...
		l = self.getCurrent()
		if l is None:
			return
		# ...containing (Actionmap, Context, Action, keydata).
		# we returns this tuple to the callback.
		self.callback(l[0], l[1], l[2])

	def getCurrent(self):
		sel = self.l.getCurrentSelection()
		return sel and sel[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def selectionChanged(self):
		for x in self.onSelChanged:
			x()
