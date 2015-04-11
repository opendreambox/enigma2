from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent
from TemplatedMultiContentComponent import TemplatedMultiContentComponent

from Tools.FuzzyDate import FuzzyTime
from Tools.Log import Log

from enigma import eListbox, eServiceReference
from Tools.LoadPixmap import LoadPixmap
from timer import TimerEntry
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

from skin import componentSizes

class TimerList(HTMLComponent, TemplatedMultiContentComponent, object):
#
#  | <Service>     <Name of the Timer>  |
#  | <start, end>              <state>  |

	COMPONENT_ID = componentSizes.TIMER_LIST
	default_template = """{
		"template": [
			MultiContentEntryText(pos = (0, 0), size = (width, 30), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=1),
			MultiContentEntryPixmapAlphaBlend(pos = (45, 5), size = (40, 40), png=2),
			MultiContentEntryText(pos = (0, 32), size = (width, 20), font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=3),
			MultiContentEntryText(pos = (0, 52), size = (width-150, 20), font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=4),
			MultiContentEntryText(pos = (width-150, 52), size = (150, 20), font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=5),
			MultiContentEntryPixmapAlphaBlend(pos=(490, 5), size=(40, 40), png=6),
		],
		"itemHeight" : 70,
		"fonts" : [gFont("Regular", 24), gFont("Regular", 20)]
	}"""

	def buildTimerEntry(self, timer, processed):
		pixmap = None
		if timer.service_ref.ref.flags & eServiceReference.isGroup:
			pixmap = self.picServiceGroup
		else:
			orbpos = timer.service_ref.ref.getUnsignedData(4) >> 16
			if orbpos == 0xFFFF:
				pixmap = self.picDVB_C
			elif orbpos == 0xEEEE:
				pixmap = self.picDVB_T
			else:
				pixmap = self.picDVB_S

		res = [ None ]

		res.append(timer.service_ref.getServiceName())
		res.append(pixmap)
		res.append(timer.name)

		repeatedtext = ""
		days = ( _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun") )

		if timer.repeated:
			flags = timer.repeated
			count = 0
			for x in (0, 1, 2, 3, 4, 5, 6):
					if (flags & 1 == 1):
						if (count != 0):
							repeatedtext += ", "
						repeatedtext += days[x]
						count += 1
					flags = flags >> 1
			if timer.justplay:
				if timer.end - timer.begin < 4: # rounding differences
					repeatedtext += ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.begin)[1]))
				else:
					repeatedtext += ((" %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60)) + _("(ZAP)")
			else:
				repeatedtext += ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60))
		else:
			if timer.justplay:
				if timer.end - timer.begin < 4:
					repeatedtext += (("%s, %s " + _("(ZAP)")) % (FuzzyTime(timer.begin)))
				else:
					repeatedtext += (("%s, %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,))) + _("(ZAP)")
			else:
				repeatedtext += (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,)))

		res.append(repeatedtext)

		if not processed:
			if timer.state == TimerEntry.StateWaiting:
				state = _("waiting")
			elif timer.state == TimerEntry.StatePrepared:
				state = _("about to start")
			elif timer.state == TimerEntry.StateRunning:
				if timer.justplay:
					state = _("zapped")
				else:
					state = _("recording...")
			elif timer.state == TimerEntry.StateEnded:
				state = _("done!")
			else:
				state = _("<unknown>")
		else:
			state = _("done!")

		if timer.disabled:
			state = _("disabled")
		res.append(state)
		png = None
		if timer.disabled:
			png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/redx.png"))

		res.append(png)
		return res

	def __init__(self, list):
		TemplatedMultiContentComponent.__init__(self)
		self.l.setBuildFunc(self.buildTimerEntry)
		self.list = list

		self.picDVB_S = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_dvb_s-fs8.png"))
		self.picDVB_C = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_dvb_c-fs8.png"))
		self.picDVB_T = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_dvb_t-fs8.png"))
		self.picServiceGroup = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_service_group-fs8.png"))

	def applySkin(self, desktop, parent):
		GUIComponent.applySkin(self, desktop, parent)
		self.applyTemplate(additional_locals={"width" : self.l.getItemSize().width()-30})
	
	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]
	
	GUI_WIDGET = eListbox
	
	def postWidgetCreate(self, instance):
		instance.setContent(self.l)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	currentIndex = property(getCurrentIndex, moveToIndex)
	currentSelection = property(getCurrent)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def invalidate(self):
		self.l.invalidate()

	def entryRemoved(self, idx):
		self.l.entryRemoved(idx)

