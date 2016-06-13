from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent
from skin import parseColor, parseFont
from enigma import eListbox, eRect, eEnv
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, fileExists
from Components.config import config
from enigma import RT_WRAP, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont, eListbox, eServiceReference, eServiceCenter, iServiceInformation, eListboxPythonMultiContent, eListboxServiceContent, eEPGCache
from ServiceReference import ServiceReference
from Components.MultiContent import MultiContentEntryText
from time import time
from enigma import eLabel, eSize, eEnv, eServiceReference
from skin import TemplatedColors
import NavigationInstance
from time import localtime
from timer import TimerEntry
from re import compile

class PiconLoader():
	def __init__(self):
		self.nameCache = { }
		config.usage.configselection_piconspath.addNotifier(self.piconPathChanged, initial_call = False)
		self.partnerbox = compile('1:0:[0-9a-fA-F]+:[1-9a-fA-F]+[0-9a-fA-F]*:[1-9a-fA-F]+[0-9a-fA-F]*:[1-9a-fA-F]+[0-9a-fA-F]*:[1-9a-fA-F]+[0-9a-fA-F]*:[0-9a-fA-F]+:[0-9a-fA-F]+:[0-9a-fA-F]+:http')

	def getPicon(self, sRef):
		pos = sRef.rfind(':')
		pos2 = sRef.rfind(':', 0, pos)
		if pos - pos2 == 1 or self.partnerbox.match(sRef) is not None:
			sRef = sRef[:pos2].replace(':', '_')
		else:
			sRef = sRef[:pos].replace(':', '_')
		pngname = self.nameCache.get(sRef, "")
		if pngname == "":
			pngname = self.findPicon(sRef)
			if pngname != "":
				self.nameCache[sRef] = pngname
			if pngname == "": # no picon for service found
				pngname = self.nameCache.get("default", "")
				if pngname == "": # no default yet in cache..
					pngname = self.findPicon("picon_default")
					if pngname != "":
						self.nameCache["default"] = pngname
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

class ServiceList(HTMLComponent, GUIComponent):
	MODE_NORMAL = 0
	MODE_FAVOURITES = 1

	def __init__(self, session = None):
		GUIComponent.__init__(self)

		self.session = session
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
		self.l.setFont(0, gFont("Regular", 18)) # AdditionalInfoFont
		self.l.setFont(1, gFont("Regular", 20)) # ServiceNumberFont
		self.l.setFont(2, gFont("Regular", 22)) # ServiceNameFont
		self.l.setFont(3, gFont("Regular", 18)) # ServiceInfoFont
		self.serviceNameFont = gFont("Regular", 22)
		self.serviceInfoFontHeight = 18
		self.additionalInfoFont = gFont("Regular", 18)
		self.list = []
		self.size = 0
		self.service_center = eServiceCenter.getInstance()
		self.numberoffset = 0
		self.is_playable_ignore = eServiceReference()
		self.root = None
		self.mode = self.MODE_NORMAL
		self.itemHeight = 28
		self.l.setItemHeight(28)
		self.onSelectionChanged = [ ]
		self.recordingList = {}
		self.piconLoader = PiconLoader()
		if self.session:
			self.session.nav.RecordTimer.on_state_change.append(self.onTimerEntryStateChange)
		config.usage.configselection_showrecordings.addNotifier(self.getRecordingList, initial_call = True)
		config.usage.configselection_bigpicons.addNotifier(self.setItemHeight, initial_call = True)

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
		if config.usage.configselection_bigpicons.value and self.mode == self.MODE_FAVOURITES:
			self.l.setItemHeight(60)
			if self.instance is not None and self.selectionPixmapBig:
				self.instance.setSelectionPicture(self.selectionPixmapBig)
		else:
			self.l.setItemHeight(self.itemHeight)
			if self.instance is not None and self.selectionPixmapStandard:
				self.instance.setSelectionPicture(self.selectionPixmapStandard)

	def paintProgressBar(self, event, xoffset, width, height):
		percent = 0
		progressW = 52
		progressH = 8
		if event:
			now = int(time())
			percent = 100 * (now - event.getBeginTime()) / event.getDuration()
		top = int((height - progressH) / 2)
		if self.picServiceEventProgressbar is None:
			return(eListboxPythonMultiContent.TYPE_PROGRESS, xoffset, top, progressW, progressH, percent, 1, self.serviceEventProgressbarColor, self.serviceEventProgressbarColorSelected, self.serviceEventProgressbarBackColor, self.serviceEventProgressbarBackColorSelected)
		else:
			return(eListboxPythonMultiContent.TYPE_PROGRESS_PIXMAP, xoffset, top, progressW, progressH, percent, self.picServiceEventProgressbar, 1, self.serviceEventProgressbarBorderColor, self.serviceEventProgressbarBorderColorSelected, self.serviceEventProgressbarBackColor, self.serviceEventProgressbarBackColorSelected)

	def buildOptionEntry(self, service, **args):
		width = self.l.getItemSize().width()
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
		recording = False
		if config.usage.configselection_showrecordings.value:
			if self.recordingList.has_key(service.toString()):
				recording = True
			else:
				if isPlayable and len(self.recordingList) and service.flags & eServiceReference.mustDescent:
					alist = ServiceReference(service).list()
					while True:
						aservice = alist.getNext()
						if not aservice.valid():
							break
						if self.recordingList.has_key(aservice.toString()):
							recording = True
							break

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
		serviceName = info.getName(service) or "<n/a>"
		event = info.getEvent(service)
		index = self.getCurrentIndex()
		xoffset = 2
		pixmap = None
		drawProgressbar = isPlayable and showProgressbar
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
		if pixmap is not None:
			pixmap_size = self.picMarker.size()
			ypos = (height - pixmap_size.height()) / 2
			pix_width = pixmap_size.width()
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, xoffset, ypos, pix_width, height, pixmap))
			xoffset += pix_width + 8

		if self.mode != self.MODE_NORMAL:
			# servicenumber
			if not (service.flags & eServiceReference.isMarker) and showListNumbers:
				markers_before = self.l.getNumMarkersBeforeCurrent()
				text = "%d" % (self.numberoffset + index + 1 - markers_before)
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, 50 , height, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
				xoffset += 60
		# picons
		if isPlayable and showPicons:
			if service.flags & eServiceReference.mustDescent:
				alist = ServiceReference(service).list()
				first_in_alternative = alist and alist.getNext()
				if first_in_alternative:
					service_str = first_in_alternative.toString()
				else:
					service_str = service.toString()
			else:
				service_str = service.toString()
			picon = self.piconLoader.getPicon(service_str)
			if picon:
				pixmap_size = picon.size()
				ypos = (height - pixmap_size.height()) / 2
				pix_width = pixmap_size.width()
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, xoffset, ypos, pix_width, height, picon))
			if bigPicons:
				xoffset += 108
			else:
				xoffset += 58
		# progressbar between servicenumber and servicename
		if drawProgressbar and progressbarPosition == "0":
			res.append(self.paintProgressBar(event, xoffset, width, height))
			xoffset += 60
		addtimedisplay = ""
		addtimedisplayWidth = 0
		if config.usage.configselection_showadditionaltimedisplay.value != "0" and event and isPlayable:
			if columnStyle:
				self.textRenderer.setFont(self.additionalInfoFont)
			if config.usage.configselection_showadditionaltimedisplay.value == "1": # percent
				now = int(time())
				percent = 100 * (now - event.getBeginTime()) / event.getDuration()
				addtimedisplay = "%d%%" % percent
				if columnStyle:
					self.textRenderer.setText("100%")
			elif config.usage.configselection_showadditionaltimedisplay.value == "2": # remain
				now = int(time())
				remain =  int((event.getBeginTime() + event.getDuration() - now) / 60)
				addtimedisplay = "+%d min" % remain
				if columnStyle:
					self.textRenderer.setText("+%d min" % 9999)
			elif config.usage.configselection_showadditionaltimedisplay.value == "3": # Remain / duration
				now = int(time())
				remain =  int((event.getBeginTime() + event.getDuration() - now) / 60)
				duration = int(event.getDuration() / 60)
				addtimedisplay = "+%d/%d min"  % (remain, duration)
				if columnStyle:
					self.textRenderer.setText("+%d/%d min"  % (9999, 9999))
			elif config.usage.configselection_showadditionaltimedisplay.value == "4": # elapsed
				now = int(time())
				elapsed =  int((now - event.getBeginTime()) / 60)
				addtimedisplay = "%d min" % elapsed
				if columnStyle:
					self.textRenderer.setText("%d min" % 9999)
			elif config.usage.configselection_showadditionaltimedisplay.value == "5": # elapsed / duration
				now = int(time())
				elapsed =  int((now - event.getBeginTime()) / 60)
				duration = int(event.getDuration() / 60)
				addtimedisplay = "%d/%d min"  % (elapsed, duration)
				if columnStyle:
					self.textRenderer.setText("%d/%d min"  % (9999, 9999))
			elif config.usage.configselection_showadditionaltimedisplay.value == "6": # elapsed / remain /  duration
				now = int(time())
				elapsed =  int((now - event.getBeginTime()) / 60)
				remain =  int((event.getBeginTime() + event.getDuration() - now) / 60)
				duration = int(event.getDuration() / 60)
				addtimedisplay = "%d/+%d/%d min"  % (elapsed, remain, duration)
				if columnStyle:
					self.textRenderer.setText("%d/+%d/%d min"  % (9999, 9999, 9999))
			elif config.usage.configselection_showadditionaltimedisplay.value == "7": #  begin - end time
				beginTime = localtime(event.getBeginTime())
				endTime = localtime(event.getBeginTime()+event.getDuration())
				addtimedisplay = "%02d:%02d - %02d:%02d" % (beginTime[3],beginTime[4],endTime[3],endTime[4])
				if columnStyle:
					self.textRenderer.setText("00:00 - 00:000")
			if columnStyle:
				addtimedisplayWidth = self.textRenderer.calculateSize().width()
		if columnStyle:
			rwidth = 0
			# servicename
			if (isPlayable and showServiceName) or not isPlayable:
				if isPlayable:
					rwidth = servicenameWidth # space for servicename
				else:
					rwidth = width - xoffset # space for servicename
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, rwidth , height, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
				xoffset = xoffset + rwidth + 10
				# progressbar between servicename and service description
				if drawProgressbar and progressbarPosition == "1":
					res.append(self.paintProgressBar(event, xoffset, width, height))
					xoffset += 60
			if event and isPlayable:
				if addtimedisplay != "" and additionalposition == "1":
					if drawProgressbar and progressbarPosition == "2":
						rwidth = width - xoffset - addtimedisplayWidth
						rwidth -= 60
					else:
						rwidth = width - xoffset - addtimedisplayWidth
				else:
					rwidth = width-xoffset
					if drawProgressbar and progressbarPosition == "2":
						rwidth -= 60
				if addtimedisplay != "" and additionalposition == "0":
					# add time text before service description
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, addtimedisplayWidth, height, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, addtimedisplay, additionalInfoColor, additionalInfoColorSelected, backgroundColor, backgroundColorSel))
					addoffset = addtimedisplayWidth + 10
					xoffset += addoffset
					rwidth -= addoffset
				# service description
				if bigPicons and secondlineinfo != "0":
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, rwidth, self.serviceInfoFontHeight+6, 3, RT_HALIGN_LEFT|RT_VALIGN_CENTER, event.getEventName(), serviceDescriptionColor, serviceDescriptionColorSelected, backgroundColor, backgroundColorSel))
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
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, self.serviceInfoFontHeight+6, rwidth, height - (self.serviceInfoFontHeight+6), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, text, additionalInfoColor, additionalInfoColorSelected, backgroundColor, backgroundColorSel))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, rwidth, height, 3, RT_HALIGN_LEFT|RT_VALIGN_CENTER, event.getEventName(), serviceDescriptionColor, serviceDescriptionColorSelected, backgroundColor, backgroundColorSel))
				# progressbar after service description
				if drawProgressbar and progressbarPosition == "2":
					xoffset = xoffset + rwidth + 5
					res.append(self.paintProgressBar(event, xoffset, width, height))
					xoffset += 60
				elif addtimedisplay != "":
					xoffset = xoffset + rwidth
				# add time text at last position
				if addtimedisplay != "" and additionalposition == "1":
					res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, width-xoffset , height, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, addtimedisplay, additionalInfoColor, additionalInfoColorSelected, backgroundColor, backgroundColorSel))
		else:
			if event and isPlayable:
				self.textRenderer.setFont(self.serviceNameFont)
				self.textRenderer.setText(serviceName)
				length = self.textRenderer.calculateSize().width() + 10
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
				if drawProgressbar and progressbarPosition == "2":
					# progressbar after service description
					length = width-xoffset - 60
				else:
					length = width-xoffset
				# service description
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, length , height, 3, RT_HALIGN_LEFT|RT_VALIGN_CENTER, text, serviceDescriptionColor, serviceDescriptionColorSelected, backgroundColor, backgroundColorSel))
				if drawProgressbar and progressbarPosition == "2":
					xoffset += length + 5
					res.append(self.paintProgressBar(event, xoffset, width, height))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, width - xoffset , height, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName, forgroundColor, forgroundColorSel, backgroundColor, backgroundColorSel))
		return res

	def applySkin(self, desktop, parent):
		attribs = [ ]
		for (attrib, value) in self.skinAttributes:
			if attrib == "foregroundColorMarked":
				self.markedForeground = parseColor(value).argb()
			elif attrib == "foregroundColorMarkedSelected":
				self.markedForegroundSelected = parseColor(value).argb()
			elif attrib == "backgroundColorMarked":
				self.markedBackground = parseColor(value).argb()
			elif attrib == "backgroundColorMarkedSelected":
				self.markedBackgroundSelected = parseColor(value).argb()
			elif attrib == "foregroundColorServiceNotAvail":
				self.serviceNotAvail = parseColor(value).argb()
			elif attrib == "colorEventProgressbar":
				self.serviceEventProgressbarColor = parseColor(value).argb()
			elif attrib == "colorEventProgressbarSelected":
				self.serviceEventProgressbarColorSelected = parseColor(value).argb()
			elif attrib == "forgroundColorEventProgressbarBorder":
				self.serviceEventProgressbarBackColor = parseColor(value).argb()
			elif attrib == "backgroundColorEventProgressbarBorderSelected":
				self.serviceEventProgressbarBackColorSelected = parseColor(value).argb()
			elif attrib == "colorEventProgressbarBorder":
				self.serviceEventProgressbarBorderColor = parseColor(value).argb()
			elif attrib == "colorEventProgressbarBorderSelected":
				self.serviceEventProgressbarBorderColorSelected = parseColor(value).argb()
			elif attrib == "colorServiceDescription":
				self.serviceDescriptionColor = parseColor(value).argb()
			elif attrib == "colorServiceDescriptionSelected":
				self.serviceDescriptionColorSelected = parseColor(value).argb()
			elif attrib == "colorRecording":
				self.recordingColor = parseColor(value).argb()
			elif attrib == "colorRecordingSelected":
				self.recordingColorSelected = parseColor(value).argb()
			elif attrib == "colorAdditionalInfo":
				self.additionalInfoColor = parseColor(value).argb()
			elif attrib == "colorAdditionalInfoSelected":
				self.additionalInfoColorSelected = parseColor(value).argb()
			elif attrib == "picServiceEventProgressbar":
				pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
				if pic:
					self.picServiceEventProgressbar = pic
			elif attrib == "serviceItemHeight":
				self.itemHeight = int(value)
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
		print "Next char: ", char
		index = self.l.getNextBeginningWithChar(char)
		indexup = self.l.getNextBeginningWithChar(char.upper())
		if indexup != 0:
			if (index > indexup or index == 0):
				index = indexup

		self.instance.moveSelectionTo(index)
		print "Moving to character " + str(char)

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
		instance.selectionChanged.get().append(self.selectionChanged)
		self.setMode(self.mode)
		self.textRenderer = eLabel(self.instance)
		self.textRenderer.resize(eSize(400,0))
		self.textRenderer.hide()

	def preWidgetRemove(self, instance):
		if self.session:
			self.session.nav.RecordTimer.on_state_change.remove(self.onTimerEntryStateChange)
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)
		config.usage.configselection_showrecordings.removeNotifier(self.getRecordingList)
		config.usage.configselection_bigpicons.removeNotifier(self.setItemHeight)

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
