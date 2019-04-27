from enigma import eLabel, eSize, eServiceReference, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont, eListbox, eServiceCenter, eListboxPythonMultiContent, eListboxServiceContent, eEPGCache,\
	getDesktop, eTimer
from skin import parseColor, parseFont, TemplatedColors, componentSizes, TemplatedListFonts
from timer import TimerEntry
from Components.config import config
from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent
from ServiceReference import ServiceReference
from Tools.Log import Log
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, fileExists

from time import time, localtime
from Tools.PiconResolver import PiconResolver

from datetime import datetime

import NavigationInstance

class PiconLoader():
	def __init__(self):
		self.nameCache = { }
		config.usage.configselection_piconspath.addNotifier(self.piconPathChanged, initial_call = False)

	def getPicon(self, sRef):
		pngname = PiconResolver.getPngName(sRef, self.nameCache, self.findPicon)
		if fileExists(pngname):
			return LoadPixmap(cached = True, path = pngname)
		else:
			return None

	def findPicon(self, sRef):
		pngname = "%s%s.png" % (config.usage.configselection_piconspath.value, sRef)
		if not fileExists(pngname):
			pngname = ""
		return pngname

	def piconPathChanged(self, configElement = None):
		self.nameCache.clear()

	def finish(self):
		config.usage.configselection_piconspath.removeNotifier(self.piconPathChanged)

class ServiceList(HTMLComponent, GUIComponent):
	MODE_NORMAL = 0
	MODE_FAVOURITES = 1

	KEY_BEGIN_MARGIN = "beginMargin"
	KEY_END_MARGIN = "endMargin"
	KEY_PICON_WIDTH = "piconWidth"
	KEY_PICON_WIDTH_BIG = "piconWidthBig"
	KEY_PICON_OFFSET = "piconOffset"
	KEY_PROGRESS_BAR_WIDTH = "progressBarWidth"
	KEY_PROGRESS_BAR_MARGIN = "progressBarMargin"
	KEY_PROGRESS_BAR_HEIGHT = "progressBarHeight"
	KEY_SERVICE_INFO_HEIGHT_ADD ="serviceInfoHeightAdd"
	KEY_SERVICE_ITEM_HEIGHT = "serviceItemHeight"
	KEY_SERVICE_ITEM_HEIGHT_LARGE ="serviceItemHeightLarge"
	KEY_SERVICE_NUMBER_WIDTH = "serviceNumberWidth"
	KEY_TEXT_OFFSET = "textOffset"

	def getDesktopWith(self):
		return getDesktop(0).size().width()
	def __init__(self, session = None):
		GUIComponent.__init__(self)

		self._componentSizes = componentSizes[componentSizes.SERVICE_LIST]
		Log.i(self._componentSizes)
		tlf = TemplatedListFonts()

		upper_service_name_limit = self.getDesktopWith() / 3
		config.usage.configselection_servicenamecolwidth.limits = [(100, upper_service_name_limit),]
		self.session = session
		self.mode = self.MODE_NORMAL

		self.picFolder = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/folder.png"))
		self.picMarker = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/marker.png"))
		self.picDVB_S = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_dvb_s-fs8.png"))
		self.picDVB_C = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_dvb_c-fs8.png"))
		self.picDVB_T = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_dvb_t-fs8.png"))
		self.picServiceGroup = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "ico_service_group-fs8.png"))
		self.markedForeground = 0xffffff
		self.markedBackground = 0xff0000
		self.markedForegroundSelected = 0xffffff
		self.markedBackgroundSelected = 0x800000

		colors = TemplatedColors().colors
		if "ListboxMarkedForeground" in colors:
			self.markedForeground = colors["ListboxMarkedForeground"]
		if "ListboxMarkedBackground" in colors:
			self.markedBackground = colors["ListboxMarkedBackground"]
		if "ListboxMarkedAndSelectedForeground" in colors:
			self.markedForegroundSelected = colors["ListboxMarkedAndSelectedForeground"]
		if "ListboxMarkedAndSelectedBackground" in colors:
			self.markedBackgroundSelected = colors["ListboxMarkedAndSelectedBackground"]

		self.serviceNotAvail = 0xbbbbbb
		self.serviceEventProgressbarColor = None
		self.serviceEventProgressbarColorSelected = None
		self.serviceEventProgressbarBackColor = None
		self.serviceEventProgressbarBackColorSelected = None
		self.serviceEventProgressbarBorderColor = None
		self.serviceEventProgressbarBorderColorSelected = None
		self.serviceDescriptionColor = 0xe7b53f
		self.serviceDescriptionColorSelected = 0xe7b53f
		self.recordingColor = 0xff4A3C
		self.recordingColorSelected = 0xff4A3C
		self.additionalInfoColor =  None
		self.additionalInfoColorSelected =  None
		self.picServiceEventProgressbar = None
		self.selectionPixmapStandard = None
		self.selectionPixmapBig = None
		self.l = eListboxServiceContent()
		self.l.setBuildFunc(self.buildOptionEntry, True)
		self.l.setFont(0, gFont(tlf.face(TemplatedListFonts.SMALL), tlf.size(TemplatedListFonts.SMALL))) # AdditionalInfoFont
		self.l.setFont(1, gFont(tlf.face(TemplatedListFonts.MEDIUM), tlf.size(TemplatedListFonts.MEDIUM))) # ServiceNumberFont
		self.l.setFont(2, gFont(tlf.face(TemplatedListFonts.BIG), tlf.size(TemplatedListFonts.BIG))) # ServiceNameFont
		self.l.setFont(3, gFont(tlf.face(TemplatedListFonts.SMALL), tlf.size(TemplatedListFonts.SMALL))) # ServiceInfoFont
		self.serviceNameFont = gFont(tlf.face(TemplatedListFonts.BIG), tlf.size(TemplatedListFonts.BIG))
		self.serviceInfoFontHeight = tlf.size(TemplatedListFonts.SMALL)
		self.serviceInfoHeight = self.serviceInfoFontHeight + self._componentSizes.get(self.KEY_SERVICE_INFO_HEIGHT_ADD, 6)
		self.additionalInfoFont = gFont(tlf.face(TemplatedListFonts.SMALL), tlf.size(TemplatedListFonts.SMALL))
		self.list = []
		self.size = 0
		self.service_center = eServiceCenter.getInstance()
		self.numberoffset = 0
		self.is_playable_ignore = eServiceReference()
		self.root = None

		self.itemHeight = self._componentSizes.get(self.KEY_SERVICE_ITEM_HEIGHT, 28)
		self.itemHeightHigh = self._componentSizes.get(self.KEY_SERVICE_ITEM_HEIGHT_LARGE, 60)
		self.l.setItemHeight(self.itemHeight)
		self.onSelectionChanged = [ ]
		self.recordingList = {}
		self.piconLoader = PiconLoader()
		if self.session:
			self.session.nav.RecordTimer.on_state_change.append(self.onTimerEntryStateChange)
		config.usage.configselection_showrecordings.addNotifier(self.getRecordingList, initial_call = True)
		config.usage.configselection_bigpicons.addNotifier(self.setItemHeight, initial_call = True)
		config.usage.configselection_secondlineinfo.addNotifier(self.setItemHeight, initial_call = False)
		self._reloadTimer = eTimer()
		self.__reloadTimerConn = self._reloadTimer.timeout.connect(self._reload)

	def onShow(self):
		GUIComponent.onShow(self)
		self._resetTimer()

	def onHide(self):
		GUIComponent.onHide(self)
		self._reloadTimer.stop()

	def _reload(self):
		self.l.refresh()
		self._resetTimer()

	def _resetTimer(self):
		secs = 60 - datetime.now().second #next full minute
		self._reloadTimer.startLongTimer(secs)

	def getRecordingList(self,configElement = None):
		self.recordingList = {}
		if config.usage.configselection_showrecordings.value:
			if NavigationInstance.instance.getRecordings():
				for timer in NavigationInstance.instance.RecordTimer.timer_list:
					if timer.state == TimerEntry.StateRunning and not timer.justplay and hasattr(timer, "Filename"):
						self.recordingList[str(timer.service_ref)] = 1

	def onTimerEntryStateChange(self,timer):
		if config.usage.configselection_showrecordings.value:
			if hasattr(timer, "Filename") and not timer.justplay and timer.state == TimerEntry.StateRunning:
				self.recordingList[str(timer.service_ref)] = 1
			else:
				if self.recordingList.has_key(str(timer.service_ref)):
					del self.recordingList[str(timer.service_ref)]

	def setItemHeight(self, configElement = None):
		if (config.usage.configselection_bigpicons.value or config.usage.configselection_secondlineinfo.value != "0") and self.mode == self.MODE_FAVOURITES:
			self.l.setItemHeight(self.itemHeightHigh)
			if self.instance is not None and self.selectionPixmapBig:
				self.instance.setSelectionPicture(self.selectionPixmapBig)
		else:
			self.l.setItemHeight(self.itemHeight)
			if self.instance is not None and self.selectionPixmapStandard:
				self.instance.setSelectionPicture(self.selectionPixmapStandard)

	def _buildOptionEntryProgressBar(self, event, xoffset, width, height):
		percent = 0
		progressW = self._progressBarWidth()
		progressH = self._componentSizes.get(self.KEY_PROGRESS_BAR_HEIGHT, 8)
		if event and event.getDuration():
			now = int(time())
			percent = 100 * (now - event.getBeginTime()) / event.getDuration()
		top = int((height - progressH) / 2)
		if self.picServiceEventProgressbar is None:
			return(eListboxPythonMultiContent.TYPE_PROGRESS, xoffset, top, progressW, progressH, percent, 1, self.serviceEventProgressbarColor, self.serviceEventProgressbarColorSelected, self.serviceEventProgressbarBackColor, self.serviceEventProgressbarBackColorSelected)
		else:
			return(eListboxPythonMultiContent.TYPE_PROGRESS_PIXMAP, xoffset, top, progressW, progressH, percent, self.picServiceEventProgressbar, 1, self.serviceEventProgressbarBorderColor, self.serviceEventProgressbarBorderColorSelected, self.serviceEventProgressbarBackColor, self.serviceEventProgressbarBackColorSelected)

	def _progressBarWidth(self, withOffset=False, withProgressBarSize=True):
		width = 0
		if withProgressBarSize:
			width += self._componentSizes.get(self.KEY_PROGRESS_BAR_WIDTH, 52)
		if withOffset:
			width += self._componentSizes.get(self.KEY_PROGRESS_BAR_MARGIN, 8)
		return width

	def _calcTextWidth(self, text, font=None, size=None):
		if size:
			self.textRenderer.resize(size)
		if font:
			self.textRenderer.setFont(font)
		self.textRenderer.setText(text)
		return self.textRenderer.calculateSize().width()

	def _buildOptionEntryServicePixmap(self, service):
		pixmap = None
		if service.flags & eServiceReference.isMarker:
			pixmap = self.picMarker
		elif service.flags & eServiceReference.isGroup:
			pixmap = self.picServiceGroup
		elif service.flags & eServiceReference.isDirectory:
			pixmap = self.picFolder
		else:
			orbpos = service.getUnsignedData(4) >> 16;
			if orbpos == 0xFFFF:
				pixmap = self.picDVB_C
			elif orbpos == 0xEEEE:
				pixmap = self.picDVB_T
			else:
				pixmap = self.picDVB_S
		return pixmap

	def _buildOptionEntryAddTimeDisplay(self, event, isPlayable, columnStyle):
		addtimedisplay = ""
		addtimedisplayWidth = 0
		if not ( config.usage.configselection_showadditionaltimedisplay.value != "0" and event and isPlayable ):
			return addtimedisplay, addtimedisplayWidth

		textTpl = ""
		maxTimeValue = 9999
		if config.usage.configselection_showadditionaltimedisplay.value == "1": # percent
			now = int(time())
			percent = 100 * (now - event.getBeginTime()) / event.getDuration()
			addtimedisplay = "%d%%" % percent
			textTpl = "100%"
		elif config.usage.configselection_showadditionaltimedisplay.value == "2": # remain
			now = int(time())
			remain =  int((event.getBeginTime() + event.getDuration() - now) / 60)
			addtimedisplay = "+%d min" %(remain,)
			textTpl = "+%d min" %(maxTimeValue,)
		elif config.usage.configselection_showadditionaltimedisplay.value == "3": # Remain / duration
			now = int(time())
			remain =  int((event.getBeginTime() + event.getDuration() - now) / 60)
			duration = int(event.getDuration() / 60)
			addtimedisplay = "+%d/%d min"  % (remain, duration)
			textTpl = "+%d/%d min"  % (maxTimeValue, maxTimeValue)
		elif config.usage.configselection_showadditionaltimedisplay.value == "4": # elapsed
			now = int(time())
			elapsed =  int((now - event.getBeginTime()) / 60)
			addtimedisplay = "%d min" % (elapsed,)
			textTpl = "%d min" % (maxTimeValue,)
		elif config.usage.configselection_showadditionaltimedisplay.value == "5": # elapsed / duration
			now = int(time())
			elapsed =  int((now - event.getBeginTime()) / 60)
			duration = int(event.getDuration() / 60)
			addtimedisplay = "%d/%d min"  % (elapsed, duration)
			textTpl = "%d/%d min"  % (maxTimeValue, maxTimeValue)
		elif config.usage.configselection_showadditionaltimedisplay.value == "6": # elapsed / remain /  duration
			now = int(time())
			elapsed =  int((now - event.getBeginTime()) / 60)
			remain =  int((event.getBeginTime() + event.getDuration() - now) / 60)
			duration = int(event.getDuration() / 60)
			addtimedisplay = "%d/+%d/%d min"  % (elapsed, remain, duration)
			textTpl = "%d/+%d/%d min"  % (maxTimeValue, maxTimeValue, maxTimeValue)
		elif config.usage.configselection_showadditionaltimedisplay.value == "7": #  begin - end time
			beginTime = localtime(event.getBeginTime())
			endTime = localtime(event.getBeginTime()+event.getDuration())
			addtimedisplay = "%02d:%02d - %02d:%02d" % (beginTime[3],beginTime[4],endTime[3],endTime[4])
			textTpl = "00:00 - 00:000"
		if columnStyle:
			addtimedisplayWidth = self._calcTextWidth(textTpl, font=self.additionalInfoFont, size=eSize(self.getDesktopWith() / 3, 0))
		return addtimedisplay, addtimedisplayWidth

	def _buildOptionEntryServicePicon(self, service):
		if service.flags & eServiceReference.mustDescent:
			alist = ServiceReference(service).list()
			first_in_alternative = alist and alist.getNext()
			if first_in_alternative:
				service_str = first_in_alternative.toString()
			else:
				service_str = service.toString()
		else:
			service_str = service.toString()
		return self.piconLoader.getPicon(service_str)

	def _checkHasRecording(self, service, isPlayable):
		if not config.usage.configselection_showrecordings.value:
			return False
		if self.recordingList.has_key(service.toString()):
			return True
		if isPlayable and len(self.recordingList) and service.flags & eServiceReference.mustDescent:
			alist = ServiceReference(service).list()
			while True:
				aservice = alist.getNext()
				if not aservice.valid():
					break
				if self.recordingList.has_key(aservice.toString()):
					return True
		return False

	def buildOptionEntry(self, service, **args):
		width = self.l.getItemSize().width()
		width -= self._componentSizes.get(self.KEY_END_MARGIN, 5)
		height = self.l.getItemSize().height()
		selected = args["selected"]
		res = [ None ]
		showListNumbers = config.usage.configselection_showlistnumbers.value
		showPicons = self.mode == self.MODE_FAVOURITES and config.usage.configselection_showpicons.value
		showServiceName = self.mode == self.MODE_NORMAL or (self.mode == self.MODE_FAVOURITES and config.usage.configselection_showservicename.value)
		showProgressbar = config.usage.show_event_progress_in_servicelist.value
		progressbarPosition = config.usage.configselection_progressbarposition.value
		servicenameWidth = config.usage.configselection_servicenamecolwidth.value
		columnStyle = config.usage.configselection_columnstyle.value
		additionalposition = config.usage.configselection_additionaltimedisplayposition.value
		bigPicons = self.mode == self.MODE_FAVOURITES and config.usage.configselection_bigpicons.value
		secondlineinfo = config.usage.configselection_secondlineinfo.value
		# get service information
		service_info = self.service_center.info(service)
		isMarker = service.flags & eServiceReference.isMarker
		isPlayable = not(service.flags & eServiceReference.isDirectory or isMarker)
		recording = self._checkHasRecording(service, isPlayable)

		marked = 0
		if self.l.isCurrentMarked() and selected:
			marked = 2
		elif self.l.isMarked(service):
			if selected:
				marked = 2
			else:
				marked = 1
		if marked == 1: #  marked
			additionalInfoColor = serviceDescriptionColor = forgroundColor = self.markedForeground
			backgroundColor = self.markedBackground
			forgroundColorSel = backgroundColorSel = additionalInfoColorSelected = serviceDescriptionColorSelected = None
		elif marked == 2: # marked and selected
			additionalInfoColorSelected = serviceDescriptionColorSelected = forgroundColorSel = self.markedForegroundSelected
			backgroundColorSel = self.markedBackgroundSelected
			forgroundColor = additionalInfoColor = serviceDescriptionColor = backgroundColor = None
		else:
			if recording:
				forgroundColor = additionalInfoColor = serviceDescriptionColor = self.recordingColor
				forgroundColorSel = additionalInfoColorSelected = serviceDescriptionColorSelected = self.recordingColorSelected
				backgroundColor = backgroundColorSel = None
			else:
				forgroundColor = forgroundColorSel = backgroundColor = backgroundColorSel = None
				serviceDescriptionColor = self.serviceDescriptionColor
				serviceDescriptionColorSelected = self.serviceDescriptionColorSelected
				additionalInfoColor = self.additionalInfoColor
				additionalInfoColorSelected = self.additionalInfoColorSelected

		if (marked == 0 and isPlayable and service_info and not service_info.isPlayable(service, self.is_playable_ignore)):
			forgroundColor = forgroundColorSel = additionalInfoColor = additionalInfoColorSelected = serviceDescriptionColor = serviceDescriptionColorSelected = self.serviceNotAvail

		# set windowstyle
		if marked > 0:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width , height, 1, RT_HALIGN_RIGHT, "", forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))

		info = self.service_center.info(service)
		serviceName = info and info.getName(service) or "<n/a>"
		event = info and info.getEvent(service)
		index = self.getCurrentIndex()
		xoffset = self._componentSizes.get(self.KEY_BEGIN_MARGIN, 5)
		pixmap = self._buildOptionEntryServicePixmap(service)
		drawProgressbar = isPlayable and showProgressbar
		progressBarWidth = self._progressBarWidth(withOffset=True)
		textOffset = self._componentSizes.get(self.KEY_TEXT_OFFSET, 10)

		if pixmap is not None:
			pixmap_size = self.picMarker.size()
			pix_width = pixmap_size.width()
			pix_height = pixmap_size.height()
			ypos = (height - pix_height) / 2
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, xoffset, ypos, pix_width, pix_height, pixmap))
			xoffset += pix_width + self._componentSizes.get(self.KEY_PICON_OFFSET, 8)

		if self.mode != self.MODE_NORMAL:
			# servicenumber
			if not (service.flags & eServiceReference.isMarker) and showListNumbers:
				markers_before = self.l.getNumMarkersBeforeCurrent()
				text = "%d" % (self.numberoffset + index + 1 - markers_before)
				nameWidth = self._componentSizes.get(self.KEY_SERVICE_NUMBER_WIDTH, 50)
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, nameWidth , height, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
				xoffset += nameWidth + textOffset

		# picons
		if isPlayable and showPicons:
			picon = self._buildOptionEntryServicePicon(service)
			if bigPicons:
				pix_width = self._componentSizes.get(self.KEY_PICON_WIDTH_BIG, 108)
			else:
				pix_width = self._componentSizes.get(self.KEY_PICON_WIDTH, 58)
			if picon:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, xoffset, 0, pix_width, height, picon))
			xoffset += pix_width
			xoffset += self._componentSizes.get(self.KEY_PICON_OFFSET, 8)

		# progressbar between servicenumber and servicename
		if drawProgressbar and progressbarPosition == "0":
			res.append(self._buildOptionEntryProgressBar(event, xoffset, width, height))
			xoffset += progressBarWidth
		addtimedisplay, addtimedisplayWidth = self._buildOptionEntryAddTimeDisplay(event, isPlayable, columnStyle)

		if columnStyle:
			rwidth = 0
			# servicename
			if (isPlayable and showServiceName) or not isPlayable:
				if isPlayable:
					rwidth = servicenameWidth # space for servicename
				else:
					rwidth = width - xoffset # space for servicename
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, rwidth , height, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
				xoffset += rwidth + textOffset
				# progressbar between servicename and service description
				if drawProgressbar and progressbarPosition == "1":
					res.append(self._buildOptionEntryProgressBar(event, xoffset, width, height))
					xoffset += progressBarWidth
			if event and isPlayable:
				rwidth = width - xoffset
				if drawProgressbar and progressbarPosition == "2":
					rwidth -= self._progressBarWidth(withOffset=True, withProgressBarSize=False)
					rwidth -= self._progressBarWidth(withOffset=True, withProgressBarSize=True)
				if addtimedisplay != "" :
					if additionalposition == "0":
						# add time text before service description
						res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, addtimedisplayWidth, height, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, addtimedisplay, additionalInfoColor, additionalInfoColorSelected, backgroundColor, backgroundColorSel))
						addoffset = addtimedisplayWidth + textOffset
						xoffset += addoffset
						rwidth -= addoffset
					elif additionalposition == "1":
						rwidth -= addtimedisplayWidth + textOffset
				# service description
				if secondlineinfo != "0" and self.mode == self.MODE_FAVOURITES:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, rwidth, self.serviceInfoHeight, 3, RT_HALIGN_LEFT|RT_VALIGN_CENTER, event.getEventName(), serviceDescriptionColor, serviceDescriptionColorSelected, backgroundColor, backgroundColorSel))
					if secondlineinfo == "1": # shortdescription
						text = event.getShortDescription()
					else:
						event_next = eEPGCache.getInstance().lookupEventTime(service, -1, 1)
						if event_next:
							beginTime = localtime(event_next.getBeginTime())
							endTime = localtime(event_next.getBeginTime()+event_next.getDuration())
							text = "%02d:%02d - %02d:%02d %s" % (beginTime[3],beginTime[4],endTime[3],endTime[4], event_next.getEventName())
						else:
							text = "%s: n/a" % _("upcoming event")
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, self.serviceInfoHeight, rwidth, height - self.serviceInfoHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, text, additionalInfoColor, additionalInfoColorSelected, backgroundColor, backgroundColorSel))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, rwidth, height, 3, RT_HALIGN_LEFT|RT_VALIGN_CENTER, event.getEventName(), serviceDescriptionColor, serviceDescriptionColorSelected, backgroundColor, backgroundColorSel))
				# progressbar after service description
				xoffset += rwidth
				if drawProgressbar and progressbarPosition == "2":
					xoffset += self._progressBarWidth(withOffset=True, withProgressBarSize=False)
					res.append(self._buildOptionEntryProgressBar(event, xoffset, width, height))
					xoffset += progressBarWidth
				# add time text at last position
				if addtimedisplay != "" and additionalposition == "1":
					xoffset += textOffset
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, addtimedisplayWidth , height, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, addtimedisplay, additionalInfoColor, additionalInfoColorSelected, backgroundColor, backgroundColorSel))
		else:
			if event and isPlayable:
				maxLength = width - xoffset
				if drawProgressbar and progressbarPosition == "2":
					# progressbar after service description
					maxLength -= progressBarWidth
				length = self._calcTextWidth(serviceName, font=self.serviceNameFont, size=eSize(maxLength,0)) + textOffset
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, length , height, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
				xoffset += length
				if addtimedisplay != "":
					if additionalposition == "1":
						# add time text after service description
						text = "(%s %s)" % (event.getEventName(), addtimedisplay)
					else:
						# add time text before service description
						text = "(%s %s)" % (addtimedisplay, event.getEventName())
				else:
					text = "(%s)" % (event.getEventName())
				length = width - xoffset
				if drawProgressbar and progressbarPosition == "2":
					# progressbar after service description
					length -= progressBarWidth
				# service description
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, length , height, 3, RT_HALIGN_LEFT|RT_VALIGN_CENTER, text, serviceDescriptionColor, serviceDescriptionColorSelected, backgroundColor, backgroundColorSel))
				if drawProgressbar and progressbarPosition == "2":
					xoffset += length + textOffset / 2
					res.append(self._buildOptionEntryProgressBar(event, xoffset, width, height))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, width - xoffset , height, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
		return res

	def applySkin(self, desktop, parent):
		attribs = [ ]
		for (attrib, value) in self.skinAttributes:
			if attrib == "foregroundColorMarked":
				self.markedForeground = parseColor(value)
			elif attrib == "foregroundColorMarkedSelected":
				self.markedForegroundSelected = parseColor(value)
			elif attrib == "backgroundColorMarked":
				self.markedBackground = parseColor(value)
			elif attrib == "backgroundColorMarkedSelected":
				self.markedBackgroundSelected = parseColor(value)
			elif attrib == "foregroundColorServiceNotAvail":
				self.serviceNotAvail = parseColor(value)
			elif attrib == "colorEventProgressbar":
				self.serviceEventProgressbarColor = parseColor(value)
			elif attrib == "colorEventProgressbarSelected":
				self.serviceEventProgressbarColorSelected = parseColor(value)
			elif attrib == "forgroundColorEventProgressbarBorder":
				self.serviceEventProgressbarBackColor = parseColor(value)
			elif attrib == "backgroundColorEventProgressbarBorderSelected":
				self.serviceEventProgressbarBackColorSelected = parseColor(value)
			elif attrib == "colorEventProgressbarBorder":
				self.serviceEventProgressbarBorderColor = parseColor(value)
			elif attrib == "colorEventProgressbarBorderSelected":
				self.serviceEventProgressbarBorderColorSelected = parseColor(value)
			elif attrib == "colorServiceDescription":
				self.serviceDescriptionColor = parseColor(value)
			elif attrib == "colorServiceDescriptionSelected":
				self.serviceDescriptionColorSelected = parseColor(value)
			elif attrib == "colorRecording":
				self.recordingColor = parseColor(value)
			elif attrib == "colorRecordingSelected":
				self.recordingColorSelected = parseColor(value)
			elif attrib == "colorAdditionalInfo":
				self.additionalInfoColor = parseColor(value)
			elif attrib == "colorAdditionalInfoSelected":
				self.additionalInfoColorSelected = parseColor(value)
			elif attrib == "picServiceEventProgressbar":
				pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
				if pic:
					self.picServiceEventProgressbar = pic
			elif attrib == "serviceItemHeight":
				self.itemHeight = int(value)
			elif attrib == "serviceItemHeightHigh":
				self.itemHeightHigh = int(value)
			elif attrib == "serviceNameFont":
				self.l.setFont(2, parseFont(value, ((1,1),(1,1))))
				self.serviceNameFont = parseFont(value, ((1,1),(1,1)))
			elif attrib == "serviceInfoFont":
				self.l.setFont(3, parseFont(value, ((1,1),(1,1))))
				name, size = value.split(';')
				self.serviceInfoFontHeight = int(size)
			elif attrib == "serviceNumberFont":
				self.l.setFont(1, parseFont(value, ((1,1),(1,1))))
			elif attrib == "additionalInfoFont":
				self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				self.additionalInfoFont = parseFont(value, ((1,1),(1,1)))
			elif attrib == "selectionPixmap":
				pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
				if pic:
					self.selectionPixmapStandard = pic
					if not config.usage.configselection_bigpicons.value:
						self.instance.setSelectionPicture(self.selectionPixmapStandard)
			elif attrib == "selectionPixmapHigh":
				pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
				if pic:
					self.selectionPixmapBig = pic
					if config.usage.configselection_bigpicons.value:
						self.instance.setSelectionPicture(self.selectionPixmapBig)
			else:
				attribs.append((attrib, value))
		self.skinAttributes = attribs
		return GUIComponent.applySkin(self, desktop, parent)

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def setCurrent(self, ref):
		self.l.setCurrent(ref)

	def getCurrent(self):
		r = eServiceReference()
		self.l.getCurrent(r)
		return r

	def atBegin(self):
		return self.instance.atBegin()

	def atEnd(self):
		return self.instance.atEnd()

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def moveToChar(self, char):
		Log.d("Next char: %s" %(char,))
		index = self.l.getNextBeginningWithChar(char)
		indexup = self.l.getNextBeginningWithChar(char.upper())
		if indexup != 0:
			if (index > indexup or index == 0):
				index = indexup

		self.instance.moveSelectionTo(index)
		Log.i("Moving to character %s" %(char,))

	def moveToNextMarker(self):
		idx = self.l.getNextMarkerPos()
		self.instance.moveSelectionTo(idx)

	def moveToPrevMarker(self):
		idx = self.l.getPrevMarkerPos()
		self.instance.moveSelectionTo(idx)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		self.setMode(self.mode)
		self.textRenderer = eLabel(self.instance)
		self.textRenderer.resize(eSize(self.getDesktopWith() / 3, 0))
		self.textRenderer.hide()

	def preWidgetRemove(self, instance):
		if self.session:
			self.session.nav.RecordTimer.on_state_change.remove(self.onTimerEntryStateChange)
		instance.setContent(None)
		self.selectionChanged_conn = None
		config.usage.configselection_showrecordings.removeNotifier(self.getRecordingList)
		config.usage.configselection_bigpicons.removeNotifier(self.setItemHeight)
		config.usage.configselection_secondlineinfo.removeNotifier(self.setItemHeight)
		self.piconLoader.finish()

	def getRoot(self):
		return self.root

	def getRootServices(self):
		serviceHandler = eServiceCenter.getInstance()
		list = serviceHandler.list(self.root)
		dest = [ ]
		if list is not None:
			while 1:
				s = list.getNext()
				if s.valid():
					dest.append(s.toString())
				else:
					break
		return dest

	def setNumberOffset(self, offset):
		self.numberoffset = offset

	def setPlayableIgnoreService(self, ref):
		self.is_playable_ignore = ref

	def setRoot(self, root, justSet=False):
		self.root = root
		self.l.setRoot(root, justSet)
		if not justSet:
			self.l.sort()
		self.selectionChanged()

	def removeCurrent(self):
		self.l.removeCurrent()

	def addService(self, service, beforeCurrent=False):
		self.l.addService(service, beforeCurrent)

	def finishFill(self):
		self.l.FillFinished()
		self.l.sort()

# stuff for multiple marks (edit mode / later multiepg)
	def clearMarks(self):
		self.l.initMarked()

	def isMarked(self, ref):
		return self.l.isMarked(ref)

	def addMarked(self, ref):
		self.l.addMarked(ref)

	def removeMarked(self, ref):
		self.l.removeMarked(ref)

	def getMarked(self):
		i = self.l
		i.markedQueryStart()
		ref = eServiceReference()
		marked = [ ]
		while i.markedQueryNext(ref) == 0:
			marked.append(ref.toString())
			ref = eServiceReference()
		return marked

#just for movemode.. only one marked entry..
	def setCurrentMarked(self, state):
		self.l.setCurrentMarked(state)

	def setMode(self, mode):
		self.mode = mode
		self.setItemHeight()
