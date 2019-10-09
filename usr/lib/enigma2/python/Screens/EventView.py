from __future__ import division
from __future__ import print_function
from Screen import Screen
from Screens.TimerEdit import TimerSanityConflict
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.UsageConfig import preferredTimerPath
from Components.Sources.ServiceEvent import ServiceEvent
from enigma import eEPGCache, eTimer, eServiceReference
from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT
from TimerEntry import TimerEntry
from time import localtime

from Plugins.Plugin import PluginDescriptor
from Components.PluginComponent import plugins
from Screens.ChoiceBox import ChoiceBox

class EventViewBase:
	ADD_TIMER = 0
	REMOVE_TIMER = 1
	
	def __init__(self, event, ref, callback=None, similarEPGCB=None):
		self.similarEPGCB = similarEPGCB
		self.cbFunc = callback
		self.currentService=ref
		self.isRecording = (not ref.ref.flags & eServiceReference.isGroup) and ref.ref.getPath() and ref.ref.getPath()[0] == '/'
		self.event = event
		self["Service"] = ServiceEvent()
		self["epg_description"] = ScrollLabel()
		self["datetime"] = Label()
		self["channel"] = Label()
		self["duration"] = Label()
		self["key_red"] = Button("")
		if similarEPGCB is not None:
			self.SimilarBroadcastTimer = eTimer()
			self.SimilarBroadcastTimer_conn = self.SimilarBroadcastTimer.timeout.connect(self.getSimilarEvents)
		else:
			self.SimilarBroadcastTimer = None
		self.key_green_choice = self.ADD_TIMER
		if self.isRecording:
			self["key_green"] = Button("")
		else:
			self["key_green"] = Button(_("Add timer"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		self["actions"] = ActionMap(["OkCancelActions", "EventViewActions"],
			{
				"cancel": self.close,
				"ok": self.close,
				"pageUp": self.pageUp,
				"pageDown": self.pageDown,
				"prevEvent": self.prevEvent,
				"nextEvent": self.nextEvent,
				"timerAdd": self.timerAdd,
				"openSimilarList": self.openSimilarList,
				"openPlugins" : self._openPlugins
			})
		self.onShown.append(self.onCreate)
		self._pluginList = []
		self._checkPlugins()

	def _checkPlugins(self, additionalPlugins = []):
		self._pluginList = additionalPlugins[:]
		self._pluginList.extend([(p.name, p, False) for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EVENTVIEW)])
		if self._pluginList:
			if len(self._pluginList) > 1:
				self["key_blue"].setText(_("More ..."))
			else:
				self["key_blue"].setText(self._pluginList[0][0])
		else:
			self["key_blue"].setText("")

	def _openPlugins(self):
		if self._pluginList:
			if len(self._pluginList) > 1:
				self.session.openWithCallback(self._onPluginSelected, ChoiceBox, list=self._pluginList, windowTitle=_("More ..."))
			else:
				self._onPluginSelected(self._pluginList[0])

	def _onPluginSelected(self, p=None):
		noargs = p and p[2]
		fnc = p and p[1]
		if fnc:
			if noargs: #noarg for multiepgcallback backwards compat
				fnc()
			else:
				fnc(self.session, self.event, self.currentService)

	def onCreate(self):
		self.setService(self.currentService)
		self.setEvent(self.event)

	def prevEvent(self):
		if self.cbFunc is not None:
			self.cbFunc(self.setEvent, self.setService, -1)

	def nextEvent(self):
		if self.cbFunc is not None:
			self.cbFunc(self.setEvent, self.setService, +1)

	def removeTimer(self, timer):
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)
		self["key_green"].setText(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
	
	def timerAdd(self):
		if self.isRecording:
			return
		event = self.event
		serviceref = self.currentService
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				cb_func = lambda ret : not ret or self.removeTimer(timer)
				self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
				break
		else:
			newEntry = RecordTimerEntry(self.currentService, checkOldTimers = True, dirname = preferredTimerPath(), *parseEvent(self.event))
			self.session.openWithCallback(self.finishedAdd, TimerEntry, newEntry)

	def finishedAdd(self, answer):
		print("finished add")
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self["key_green"].setText(_("Remove timer"))
			self.key_green_choice = self.REMOVE_TIMER
		else:
			self["key_green"].setText(_("Add timer"))
			self.key_green_choice = self.ADD_TIMER
			print("Timeredit aborted")		

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

	def setService(self, service):
		self.currentService=service
		self["Service"].newService(self.currentService.ref)
		if self.isRecording:
			self["channel"].setText(_("Recording"))
		else:
			name = self.currentService.getServiceName()
			if name is not None:
				self["channel"].setText(name)
			else:
				self["channel"].setText(_("unknown service"))

	def sort_func(self,x,y):
		if x[1] < y[1]:
			return -1
		elif x[1] == y[1]:
			return 0
		else:
			return 1

	def setEvent(self, event):
		self.event = event
		if event is None:
			return
		text = event.getEventName()
		short = event.getShortDescription()
		ext = event.getExtendedDescription()
		if short and short != text:
			text += '\n\n' + short
		if ext:
			if text:
				text += '\n\n'
			text += ext

		self.setTitle(event.getEventName())
		self["epg_description"].setText(text)
		self["datetime"].setText(event.getBeginTimeString())
		self["duration"].setText(_("%d min")%(event.getDuration()//60))
		self["key_red"].setText("")
		if self.SimilarBroadcastTimer is not None:
			self.SimilarBroadcastTimer.start(400,True)

		serviceref = self.currentService
		eventid = self.event.getEventId()
		refstr = serviceref.ref.toString()
		isRecordEvent = False
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				isRecordEvent = True
				break
		if isRecordEvent and self.key_green_choice != self.REMOVE_TIMER:
			self["key_green"].setText(_("Remove timer"))
			self.key_green_choice = self.REMOVE_TIMER
		elif not isRecordEvent and self.key_green_choice != self.ADD_TIMER:
			self["key_green"].setText(_("Add timer"))
			self.key_green_choice = self.ADD_TIMER


	def pageUp(self):
		self["epg_description"].pageUp()

	def pageDown(self):
		self["epg_description"].pageDown()

	def getSimilarEvents(self):
	 # search similar broadcastings
		refstr = str(self.currentService)
		id = self.event.getEventId()
		epgcache = eEPGCache.getInstance()
		ret = epgcache.search(('NB', 100, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, refstr, id))
		if ret is not None:
			descr = self["epg_description"]
			text = descr.getText()
			text += '\n\n' + _('Similar broadcasts:')
			ret.sort(self.sort_func)
			for x in ret:
				t = localtime(x[1])
				text += '\n%d.%d.%d, %02d:%02d  -  %s'%(t[2], t[1], t[0], t[3], t[4], x[0])
			descr.setText(text)
			self["key_red"].setText(_("Similar"))

	def openSimilarList(self):
		if self.similarEPGCB is not None and self["key_red"].getText():
			id = self.event and self.event.getEventId()
			refstr = str(self.currentService)
			if id is not None:
				self.similarEPGCB(id, refstr)

class EventViewSimple(Screen, EventViewBase):
	def __init__(self, session, Event, Ref, callback=None, similarEPGCB=None):
		Screen.__init__(self, session)
		self.skinName = "EventView"
		EventViewBase.__init__(self, Event, Ref, callback, similarEPGCB)

class EventViewEPGSelect(Screen, EventViewBase):
	def __init__(self, session, event, ref, callback=None, singleEPGCB=None, multiEPGCB=None, similarEPGCB=None):
		Screen.__init__(self, session)
		self.skinName = "EventView"
		EventViewBase.__init__(self, event, ref, callback, similarEPGCB)
		self["key_yellow"].setText(_("Single EPG"))
		self["epgactions"] = ActionMap(["EventViewEPGActions"],
			{
				"openSingleServiceEPG": singleEPGCB,
			})
		additionalPlugins=[]
		if multiEPGCB:
			additionalPlugins=[(_("Multi EPG"), multiEPGCB, True)]
		self._checkPlugins(additionalPlugins=additionalPlugins)
