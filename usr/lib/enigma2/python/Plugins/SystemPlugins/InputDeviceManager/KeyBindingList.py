from __future__ import print_function
from __future__ import absolute_import
from Components.GUIComponent import GUIComponent

from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_VALIGN_CENTER
from Tools.KeyBindings import keyDescriptions
from skin import componentSizes, TemplatedListFonts
from keyids import KEYIDS
from Tools.Log import Log

class KeyBindingList(GUIComponent):
	KEY_NAMES = {
		"KEY_MUTE" : _("Mute"),
		"KEY_MODE" : _("Mode"),
		"KEY_POWER" : _("Power"),
		"KEY_RED" : _("Red"),
		"KEY_BLUE" : _("Blue"),
		"KEY_GREEN" : _("Green"),
		"KEY_YELLOW" : _("Yellow"),
		"KEY_UP" : _("Up"),
		"KEY_DOWN" : _("Down"),
		"KEY_OK" : _("OK"),
		"KEY_LEFT" : _("Left"),
		"KEY_RIGHT" : _("Right"),
		"KEY_MENU" : _("Menu"),
		"KEY_VIDEO" : _("PVR"),
		"KEY_INFO" : _("Info"),
		"KEY_AUDIO" : _("Audio"),
		"KEY_TEXT" : _("TXT"),
		"KEY_PREVIOUS" : _("<"),
		"KEY_NEXT" : _(">"),
		"KEY_PLAY" : _("Play/Pause"),
		"KEY_CHANNELUP" : _("+"),
		"KEY_CHANNELDOWN" : _("-"),
		"KEY_EXIT" : _("Exit"),
		"KEY_STOP" : _("Stop"),
		"KEY_RECORD" : _("Record"),
		"KEY_VOLUMEUP" : _("Volume +"),
		"KEY_VOLUMEDOWN" : _("Volume -"),
		"KEY_FASTFORWARD" : _("Fast Forward"),
		"KEY_REWIND" : _("Rewind"),
	}

	KEY_ORDER = [
		"KEY_MUTE",
		"KEY_MODE",
		"KEY_POWER",
		"KEY_REWIND",
		"KEY_PLAY",
		"KEY_FASTFORWARD",
		"KEY_RECORD",
		"KEY_STOP",
		"KEY_TEXT",
		"KEY_RED",
		"KEY_GREEN",
		"KEY_YELLOW",
		"KEY_BLUE",
		"KEY_INFO",
		"KEY_MENU",
		"KEY_UP",
		"KEY_LEFT",
		"KEY_OK",
		"KEY_RIGHT",
		"KEY_DOWN",
		"KEY_AUDIO",
		"KEY_VIDEO",
		"KEY_VOLUMEUP",
		"KEY_EXIT",
		"KEY_CHANNELUP",
		"KEY_VOLUMEDOWN",
		"KEY_MIC",
		"KEY_CHANNELDOWN",
		"KEY_1",
		"KEY_2",
		"KEY_3",
		"KEY_4",
		"KEY_5",
		"KEY_6",
		"KEY_7",
		"KEY_8",
		"KEY_9",
		"KEY_PREVIOUS",
		"KEY_0",
		"KEY_NEXT",
	]
	
	def __init__(self, rcUsed, boundKeys):
		GUIComponent.__init__(self)
		self.onSelectionChanged = [ ]
		self.l = eListboxPythonMultiContent()
		self._rcUsed = rcUsed

		sizes = componentSizes[componentSizes.HELP_MENU_LIST]
		textX = sizes.get("textX", 5)
		textWidth = sizes.get("textWidth", 1000)
		textHeight = sizes.get("textHeight", 35)

		l = [ ]
		for key in self.KEY_ORDER:
			if key not in boundKeys:
				continue
			try:
				keyID = keyDescriptions[self._rcUsed][KEYIDS[key]][0]
				description = self.KEY_NAMES.get(key, keyID)
				entry = [(keyID, key)]
				entry.append( (eListboxPythonMultiContent.TYPE_TEXT, textX, 0, textWidth, textHeight, 0, RT_VALIGN_CENTER, description) )
				l.append(entry)
			except:
				Log.w("Key %s is unknown and skipped!" %(key,))
		self.l.setList(l)

		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		self.l.setFont(1, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setItemHeight(sizes.get(componentSizes.ITEM_HEIGHT, 30))

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
		for x in self.onSelectionChanged:
			x()
