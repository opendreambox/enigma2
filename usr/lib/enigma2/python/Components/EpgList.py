from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent

from enigma import eLabel, eEPGCache, eListbox, eListboxPythonMultiContent, gFont, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER

from Components.config import config
from Tools.LoadPixmap import LoadPixmap

from time import localtime, time
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

from skin import TemplatedListFonts, componentSizes

EPG_TYPE_SINGLE = 0
EPG_TYPE_MULTI = 1
EPG_TYPE_SIMILAR = 2

class Rect:
	def __init__(self, x, y, width, height):
		self.__left = x
		self.__top = y
		self.__width = width
		self.__height = height

	def left(self):
		return self.__left

	def top(self):
		return self.__top

	def height(self):
		return self.__height

	def width(self):
		return self.__width

class EPGList(HTMLComponent, GUIComponent):
	SKIN_COMPONENT_KEY = "EPGList"
	SKIN_COMPONENT_ICON_HEIGHT = "iconHeight"
	SKIN_COMPONENT_ICON_WIDTH = "iconWidth"
	SKIN_COMPONENT_ICON_HPOS = "iconHPos"
	SKIN_COMPONENT_ITEM_MARGIN = "itemMargin"

	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer = None):
		self.days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
		self.timer = timer
		self.onSelChanged = [ ]
		if selChangedCB is not None:
			self.onSelChanged.append(selChangedCB)
		GUIComponent.__init__(self)
		self.type=type
		self.l = eListboxPythonMultiContent()

		tlf = TemplatedListFonts()
		self._font0 = gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG))
		self._font1 = gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL))
		self.l.setFont(0, self._font0)
		self.l.setFont(1, self._font1)
		self._textRenderer = None

		sizes = componentSizes[EPGList.SKIN_COMPONENT_KEY]
		self._iconWidth = sizes.get(EPGList.SKIN_COMPONENT_ICON_WIDTH, 21)
		self._iconHeight = sizes.get(EPGList.SKIN_COMPONENT_ICON_HEIGHT, 21)
		self._iconHPos = sizes.get(EPGList.SKIN_COMPONENT_ICON_HPOS, 4)
		self._itemMargin = sizes.get(EPGList.SKIN_COMPONENT_ITEM_MARGIN, 10)

		if type in (EPG_TYPE_SINGLE, EPG_TYPE_SIMILAR):
			self.l.setBuildFunc(self.buildSingleEntry)
		else:
			assert(type == EPG_TYPE_MULTI)
			self.l.setBuildFunc(self.buildMultiEntry)

		self.epgcache = eEPGCache.getInstance()
		self.clock_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock.png'))
		self.clock_add_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_add.png'))
		self.clock_pre_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_pre.png'))
		self.clock_post_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_post.png'))
		self.clock_prepost_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_prepost.png'))

	def getEventFromId(self, service, eventid):
		event = None
		if self.epgcache is not None and eventid is not None:
			event = self.epgcache.lookupEventId(service.ref, eventid)
		return event

	def getCurrentChangeCount(self):
		if self.type == EPG_TYPE_MULTI and self.l.getCurrentSelection() is not None:
			return self.l.getCurrentSelection()[0]
		return 0

	def getCurrent(self):
		idx=0
		if self.type == EPG_TYPE_MULTI:
			idx += 1
		tmp = self.l.getCurrentSelection()
		if tmp is None:
			return ( None, None )
		eventid = tmp[idx+1]
		service = ServiceReference(tmp[idx])
		event = self.getEventFromId(service, eventid)
		return ( event, service )

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def connectSelectionChanged(self, func):
		if not self.onSelChanged.count(func):
			self.onSelChanged.append(func)

	def disconnectSelectionChanged(self, func):
		self.onSelChanged.remove(func)

	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				x()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		instance.setContent(self.l)
		self._textRenderer = eLabel(instance)
		self._textRenderer.hide()

	def preWidgetRemove(self, instance):
		self.selectionChanged_conn = None
		instance.setContent(None)

	def _calcTextWidth(self, text, font=None, size=None):
		if size:
			self._textRenderer.resize(size)
		if font:
			self._textRenderer.setFont(font)
		self._textRenderer.setText(text)
		return self._textRenderer.calculateSize().width()

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		width = esize.width()
		height = esize.height()
		#precalc rect values
		weekday_width = self._calcTextWidth("Do", font=self._font0, size=esize) + self._itemMargin
		datetime_x = weekday_width + self._itemMargin
		datetime_width = self._calcTextWidth("00.00, 00:00", font=self._font0, size=esize) + self._itemMargin
		desc_x = datetime_x + datetime_width + self._itemMargin
		desc_width = width - desc_x - self._itemMargin
		if self.type in (EPG_TYPE_SINGLE, EPG_TYPE_SIMILAR):
			self.weekday_rect = Rect(0, 0, weekday_width, height)
			self.datetime_rect = Rect(datetime_x, 0, datetime_width, height)
			self.descr_rect = Rect(desc_x, 0, desc_width, height)
		else: # EPG_TYPE_MULTI
			xpos = self._itemMargin;
			w = width / 3;
			self.service_rect = Rect(xpos, 0, w, height)
			xpos += w + self._itemMargin;
			w = width / 6;
			self.start_end_rect = Rect(xpos, 0, w, height)
			self.progress_rect = Rect(xpos,  self._itemMargin / 2, w, height - self._itemMargin)
			xpos += w + self._itemMargin
			w = width - xpos - self._itemMargin;
			self.descr_rect = Rect(xpos, 0, w, height)


	def getClockPixmap(self, refstr, beginTime, duration, eventId):
		pre_clock = 1
		post_clock = 2
		clock_type = 0
		endTime = beginTime + duration
		for x in self.timer.timer_list:
			if x.service_ref.ref.toString() == refstr:
				if x.eit == eventId:
					return self.clock_pixmap
				beg = x.begin
				end = x.end
				if beginTime > beg and beginTime < end and endTime > end:
					clock_type |= pre_clock
				elif beginTime < beg and endTime > beg and endTime < end:
					clock_type |= post_clock
		if clock_type == 0:
			return self.clock_add_pixmap
		elif clock_type == pre_clock:
			return self.clock_pre_pixmap
		elif clock_type == post_clock:
			return self.clock_post_pixmap
		else:
			return self.clock_prepost_pixmap
		
	def getPixmapForEntry(self, service, eventId, beginTime, duration):
		rec=beginTime and (self.timer.isInTimer(eventId, beginTime, duration, service))
		if rec:
			clock_pic = self.getClockPixmap(service, beginTime, duration, eventId)
		else:
			clock_pic = None
		return (clock_pic, rec)

	def buildSingleEntry(self, service, eventId, beginTime, duration, name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r1=self.weekday_rect
		r2=self.datetime_rect
		r3=self.descr_rect
		textOffset = r3.left() + self._iconWidth + self._itemMargin
		t = localtime(beginTime)
		res = [
			None, # no private data needed
			(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]
		if rec:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.left(), self._iconHPos, self._iconWidth, self._iconHeight, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, textOffset, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, name)
			))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, name))
		return res

	def buildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r1=self.service_rect
		r2=self.progress_rect
		r3=self.descr_rect
		r4=self.start_end_rect
		res = [ None ] # no private data needed
		if rec:
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()-self._iconWidth, r1.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r1.left()+r1.width()-self._iconWidth, self._iconHPos, self._iconWidth, self._iconHeight, clock_pic)
			))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
		if beginTime is not None:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime+duration)
#				print "begin", begin
#				print "end", end
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, r4.left(), r4.top(), r4.width(), r4.height(), 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%02d.%02d - %02d.%02d"%(begin[3],begin[4],end[3],end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName)
				))
			else:
				percent = (nowTime - beginTime) * 100 / duration
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, r2.left(), r2.top(), r2.width(), r2.height(), percent),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName)
				))
		return res

	def rebuild(self):
		self.l.setList(self.list)

	def queryEPG(self, list, buildFunc=None):
		if self.epgcache is not None:
			if buildFunc is not None:
				return self.epgcache.lookupEvent(list, buildFunc)
			else:
				return self.epgcache.lookupEvent(list)
		return [ ]

	def fillMultiEPG(self, services, stime=-1):
		#t = time()
		test = [ (service.ref.toString(), 0, stime) for service in services ]
		test.insert(0, 'X0RIBDTCn')
		self.list = self.queryEPG(test)
		self.l.setList(self.list)
		#print time() - t
		self.selectionChanged()

	def updateMultiEPG(self, direction):
		#t = time()
		test = [ x[3] and (x[1], direction, x[3]) or (x[1], direction, 0) for x in self.list ]
		test.insert(0, 'XRIBDTCn')
		tmp = self.queryEPG(test)
		cnt=0
		for x in tmp:
			changecount = self.list[cnt][0] + direction
			if changecount >= 0:
				if x[2] is not None:
					self.list[cnt]=(changecount, x[0], x[1], x[2], x[3], x[4], x[5], x[6])
			cnt+=1
		self.l.setList(self.list)
		#print time() - t
		self.selectionChanged()

	def fillSingleEPG(self, service):
		#t = time()
		test = [ 'RIBDT', (service.ref.toString(), 0, -1, -1) ]
		self.list = self.queryEPG(test)
		self.l.setList(self.list)
		#print time() - t
		self.selectionChanged()

	def fillOutdatedSingleEPG(self, service):
		t = time()
		keep_time = config.misc.epgcache_outdated_timespan.value * 60 
		test = [ 'RIBDT', (service.ref.toString(), 0, t-keep_time*60, keep_time) ]
		self.list = self.queryEPG(test)
		self.l.setList(self.list)
		self.selectionChanged()

	def sortSingleEPG(self, type):
		list = self.list
		if list:
			event_id = self.getSelectedEventId()
			if type == 1:
				list.sort(key=lambda x: (x[4] and x[4].lower(), x[2]))
			else:
				assert(type == 0)
				list.sort(key=lambda x: x[2])
			self.l.invalidate()
			self.moveToEventId(event_id)

	def getSelectedEventId(self):
		x = self.l.getCurrentSelection()
		return x and x[1]

	def moveToService(self,serviceref):
		if not serviceref:
			return
		index = 0
		refstr = serviceref.toString()
		for x in self.list:
			if x[1] == refstr:
				self.instance.moveSelectionTo(index)
				break
			index += 1
			
	def moveToEventId(self, eventId):
		if not eventId:
			return
		index = 0
		for x in self.list:
			if x[1] == eventId:
				self.instance.moveSelectionTo(index)
				break
			index += 1

	def fillSimilarList(self, refstr, event_id):
		t = time()
	 # search similar broadcastings
		if event_id is None:
			return
		l = self.epgcache.search(('RIBDN', 1024, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, refstr, event_id))
		if l and len(l):
			l.sort(key=lambda x: x[2])
		self.l.setList(l)
		self.selectionChanged()
		print time() - t
