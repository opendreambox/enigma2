from __future__ import division
from __future__ import print_function
from enigma import ePicLoad, eRect, eSize, eTimer, getDesktop, gPixmapPtr

from Screens.Screen import Screen
from Tools.Directories import resolveFilename, pathExists, fileExists, SCOPE_MEDIA
from Plugins.Plugin import PluginDescriptor

from Components.Pixmap import Pixmap, MovingPixmap
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.Sources.StaticText import StaticText
from Components.FileList import FileList
from Components.AVSwitch import AVSwitch
from Components.Sources.List import List
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, ConfigText, ConfigOnOff, getConfigListEntry
from Components.Label import Label

from skin import componentSizes, TemplatedListFonts
from six.moves import range

def getScale():
	return AVSwitch().getFramebufferScale()

config.pic = ConfigSubsection()
config.pic.framesize = ConfigInteger(default=30, limits=(0, 99))
config.pic.slidetime = ConfigInteger(default=10, limits=(5, 60))
config.pic.resize = ConfigSelection(default="2", choices = [("0", _("simple")), ("1", _("better")), ("2", _("fast JPEG"))])
config.pic.resize.value = 2 # 2 = fast JPEG (non JPEG fallback to 1)
config.pic.cache = ConfigOnOff(default=True)
config.pic.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))
config.pic.infoline = ConfigOnOff(default=True)
config.pic.loop = ConfigOnOff(default=True)
config.pic.bgcolor = ConfigSelection(default="#000000", choices = [("#ffffff", _("white")),("#000000", _("black")),("#18188b", _("blue")),("#9f1313", _("red")), ("#a08500", _("yellow")), ("#1f771f", _("green"))])
config.pic.textcolor = ConfigSelection(default="#38FF48", choices = [("#ffffff", _("white")),("#000000", _("black")),("#18188b", _("blue")),("#9f1313", _("red")), ("#a08500", _("yellow")), ("#38FF48", _("green"))])
config.pic.thumbDelay = ConfigInteger(default=500, limits=(0,999))

def setPixmap(dest, ptr, scaleSize, aspectRatio):
	if scaleSize.isValid() and aspectRatio.isValid():
		pic_scale_size = ptr.size().scale(scaleSize, aspectRatio)

		dest_size = dest.getSize()
		dest_width = dest_size.width()
		dest_height = dest_size.height()

		pic_scale_width = pic_scale_size.width()
		pic_scale_height = pic_scale_size.height()

#		print "pic scale size %dx%d" %(pic_scale_width, pic_scale_height)
#		print "dest area size %dx%d" %(dest_width, dest_height)

		if pic_scale_width == dest_width: # v center
			dest_rect = eRect(0, (dest_height - pic_scale_height) // 2, pic_scale_width, pic_scale_height)
		else: # h center
			dest_rect = eRect((dest_width - pic_scale_width) // 2, 0, pic_scale_width, pic_scale_height)

#		print "dest rect", (dest_rect.left(), dest_rect.top(), dest_rect.width(), dest_rect.height())

		dest.instance.setScale(1)
		dest.instance.setScaleDest(dest_rect)
	else:
#		print "no scale!"
		dest.instance.setScale(0)
	dest.instance.setPixmap(ptr)

class picshow(Screen):
	skin = """
		<screen name="picshow" position="center,80" size="1200,610" title="PicturePlayer">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40"  />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40"  />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40"  />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40"  />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="global.CurrentTime" render="Label" position="1130,12" size="60,25" font="Regular;22" halign="right">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="820,12" size="300,25" font="Regular;22" halign="right">
				<convert type="ClockToText">Format:%A %d. %B</convert>
			</widget>
			<eLabel position="10,50" size="1180,1" backgroundColor="grey" />
			<eLabel position="380,50" size="1,585" backgroundColor="grey" />
			<widget name="path" position="400,60" size="790,30" font="Regular;24"/>
			<eLabel position="380,90" size="810,1" backgroundColor="grey" />
			<widget source="label" render="Label" position="20,370" size="330,140" font="Regular;19"/>
			<widget name="thn" position="40,60" size="300,300" />
			<widget name="filelist" position="400,95" size="790,510" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
		{
			"cancel": self.KeyExit,
			"red": self.KeyExit,
			"green": self.KeyGreen,
			"yellow": self.KeyYellow,
			"blue": self.KeyBlue,
			"ok": self.KeyOk
		}, -1)

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Thumbnails"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Setup"))
		self["label"] = StaticText("")
		self["thn"] = Pixmap()


		currDir = config.pic.lastDir.value
		if not pathExists(currDir):
			currDir = "/"

		self["path"] = Label(currDir)

		self.filelist = FileList(currDir, matchingPattern = "(?i)^.*\.(jpeg|jpg|jpe|png|bmp|gif)")
		self["filelist"] = self.filelist
		self["filelist"].onSelectionChanged.append(self.selectionChanged)

		self.ThumbTimer = eTimer()
		self.ThumbTimer_conn = self.ThumbTimer.timeout.connect(self.showThumb)

		self.picload = ePicLoad()
		self.picload_conn = self.picload.PictureData.connect(self.showPic)

		self.onLayoutFinish.append(self.setConf)

	def showPic(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr != None:
			setPixmap(self["thn"], ptr, self._scaleSize, self._aspectRatio)
			self["thn"].show()

		text = picInfo.split('\n',1)
		self["label"].setText(text[1])
		self["key_yellow"].setText(_("Exif"))

	def showThumb(self):
		if not self.filelist.canDescent():
			if self.filelist.getCurrentDirectory() and self.filelist.getFilename():
				if self.picload.getThumbnail(self.filelist.getCurrentDirectory() + self.filelist.getFilename()) == 1:
					self.ThumbTimer.start(config.pic.thumbDelay.value, True)

	def selectionChanged(self):
		if not self.filelist.canDescent():
			self.ThumbTimer.start(config.pic.thumbDelay.value, True)
		else:
			self["label"].setText("")
			self["thn"].hide()
			self["key_yellow"].setText("")

	def KeyGreen(self):
		#if not self.filelist.canDescent():
		self.session.openWithCallback(self.callbackView, Pic_Thumb, self.filelist.getFileList(), self.filelist.getSelectionIndex(), self.filelist.getCurrentDirectory())

	def KeyYellow(self):
		if not self.filelist.canDescent():
			self.session.open(Pic_Exif, self.picload.getInfo(self.filelist.getCurrentDirectory() + self.filelist.getFilename()))

	def KeyBlue(self):
		self.session.openWithCallback(self.setConf ,Pic_Setup)

	def KeyOk(self):
		if self.filelist.canDescent():
			self.filelist.descent()
			self["path"].setText(self.filelist.getCurrentDirectory())
		else:
			self.session.openWithCallback(self.callbackView, Pic_Full_View, self.filelist.getFileList(), self.filelist.getSelectionIndex(), self.filelist.getCurrentDirectory())

	def setConf(self):
		self.setTitle(_("PicturePlayer"))
		sc = getScale()
		self._aspectRatio = eSize(sc[0], sc[1])
		self._scaleSize = self["thn"].instance.size()
		#0=Width 1=Height 2=Aspect 3=use_cache 4=resize_type 5=Background(#AARRGGBB)
		params = (self._scaleSize.width(), self._scaleSize.height(), sc[0], sc[1], config.pic.cache.value, int(config.pic.resize.value), "#00000000")
		self.picload.setPara(params)

	def callbackView(self, val=0):
		if val > 0:
			self.filelist.moveToIndex(val)

	def KeyExit(self):
		self.ThumbTimer.stop()
		del self.picload_conn
		del self.picload

		if self.filelist.getCurrentDirectory() is None:
			config.pic.lastDir.value = "/"
		else:
			config.pic.lastDir.value = self.filelist.getCurrentDirectory()

		config.pic.save()
		self.close()

#------------------------------------------------------------------------------------------

class Pic_Setup(Screen, ConfigListScreen):

	def __init__(self, session):
		Screen.__init__(self, session)
		# for the skin: first try MediaPlayerSettings, then Setup, this allows individual skinning
		self.skinName = ["PicturePlayerSetup", "Setup" ]
		self.setup_title = _("Settings")
		self.onChangedEntry = [ ]
		self.session = session

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"ok": self.keySave,
			}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Slideshow: Interval between pictures (sec)"), config.pic.slidetime))
		self.list.append(getConfigListEntry(_("Slideshow: Repeat"), config.pic.loop))
		self.list.append(getConfigListEntry(_("Fullscreen: Show info line"), config.pic.infoline))
		self.list.append(getConfigListEntry(_("Fullscreen: Text color"), config.pic.textcolor))
		self.list.append(getConfigListEntry(_("Fullscreen: Background color"), config.pic.bgcolor))
		self.list.append(getConfigListEntry(_("Fullscreen: Frame size"), config.pic.framesize))
		self.list.append(getConfigListEntry(_("Thumbnails: Enable cache"), config.pic.cache))
		self.list.append(getConfigListEntry(_("Thumbnails: Delay before loading (msec)"), config.pic.thumbDelay))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

#---------------------------------------------------------------------------

class Pic_Exif(Screen):
	skin = """
		<screen name="Pic_Exif" position="center,120" size="820,520" title="Info">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel	position="10,50"   size="800,1" backgroundColor="grey"/>
			<widget source="menu" render="Listbox" position="10,55" size="800,455" zPosition="1" enableWrapAround="1" scrollbarMode="showOnDemand" selectionDisabled="1">
				<convert type="TemplatedMultiContent">
					{"template": [  MultiContentEntryText(pos=(10,6),size=(280,30),flags=RT_HALIGN_LEFT,text=0),
					MultiContentEntryText(pos=(300,6),size=(490,30),flags=RT_HALIGN_LEFT,text=1)],
					"fonts": [gFont("Regular",22)],
					"itemHeight": 35 }
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session, exiflist):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"cancel": self.close
		}, -1)

		self["key_red"] = StaticText(_("Close"))

		exifdesc = [_("filename")+':', "EXIF-Version:", "Make:", "Camera:", "Date/Time:", "Width / Height:", "Flash used:", "Orientation:", "User Comments:", "Metering Mode:", "Exposure Program:", "Light Source:", "CompressedBitsPerPixel:", "ISO Speed Rating:", "X-Resolution:", "Y-Resolution:", "Resolution Unit:", "Brightness:", "Exposure Time:", "Exposure Bias:", "Distance:", "CCD-Width:", "ApertureFNumber:"]
		list = []

		for x in range(len(exiflist)):
			if x>0:
				list.append((exifdesc[x], exiflist[x]))
			else:
				name = exiflist[x].split('/')[-1]
				list.append((exifdesc[x], name))
		self["menu"] = List(list)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Info"))

#----------------------------------------------------------------------------------------

T_INDEX = 0
T_FRAME_POS = 1
T_PAGE = 2
T_NAME = 3
T_FULL = 4

class Pic_Thumb(Screen):
	SKIN_COMPONENT_KEY = "PicturePlayer"
	SKIN_COMPONENT_DESCRIPTION_SIZE = "thumbDescriptionSize"
	SKIN_COMPONENT_MARGIN =  "thumpMargin"
	SKIN_COMPONENT_SPACE_X = "thumbSpaceX"
	SKIN_COMPONENT_SPACE_Y = "thumbSpaceY"
	SKIN_COMPONENT_THUMP_X = "thumbX"
	SKIN_COMPONENT_THUMP_Y = "thumbY"

	def __init__(self, session, piclist, lastindex, path):

		self.textcolor = config.pic.textcolor.value
		self.color = config.pic.bgcolor.value

		tlf = TemplatedListFonts()
		self._labelFontSize = tlf.size(tlf.SMALLER)
		self._labelFontFace = tlf.face(tlf.SMALLER)

		sizes = componentSizes[Pic_Thumb.SKIN_COMPONENT_KEY]
		self._descSize = sizes.get(Pic_Thumb.SKIN_COMPONENT_DESCRIPTION_SIZE, 35)
		self._margin = sizes.get(Pic_Thumb.SKIN_COMPONENT_MARGIN, 10)
		self._spaceX = sizes.get(Pic_Thumb.SKIN_COMPONENT_SPACE_X, 55)
		self._spaceY = sizes.get(Pic_Thumb.SKIN_COMPONENT_SPACE_Y, 30)
		self._thumbX = sizes.get(Pic_Thumb.SKIN_COMPONENT_THUMP_X, 190)
		self._thumbY = sizes.get(Pic_Thumb.SKIN_COMPONENT_THUMP_Y, 200)

		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.thumbsX = size_w // (self._spaceX + self._thumbX) # thumbnails in X
		self.thumbsY = size_h // (self._spaceY + self._thumbY) # thumbnails in Y
		self.thumbsC = self.thumbsX * self.thumbsY # all thumbnails

		self.positionlist = []
		skincontent = ""

		posX = -1
		for x in range(self.thumbsC):
			posY = x // self.thumbsX
			posX += 1
			if posX >= self.thumbsX:
				posX = 0

			absX = self._spaceX + (posX * (self._spaceX + self._thumbX))
			absY = self._spaceY + (posY * (self._spaceY + self._thumbY))
			self.positionlist.append((absX, absY))
			absX += self._margin
			absY += self._margin
			skincontent += '<widget source="label%s" render="Label" position="%s,%s" size="%s,%s" font="%s;%s" valign="top" halign="center" zPosition="2" transparent="1" foregroundColor="%s"/>' % (x, absX, absY + self._thumbY - self._descSize, self._thumbX, self._descSize, self._labelFontFace, self._labelFontSize, self.textcolor)
			skincontent += '<widget name="thumb%s" position="%s,%s" size="%s,%s" zPosition="2" transparent="1" />' % (x, absX, absY, self._thumbX, self._thumbY - self._descSize - self._margin)

		# Screen, backgroundlabel and MovingPixmap
		doubleMargin = self._margin * 2
		self.skin = """<screen position="0,0" size="{0},{1}" flags="wfNoBorder" >
			<eLabel position="0,0" zPosition="0" size="{0},{1}" backgroundColor="{2}" /> \
			<widget name="frame" position="35,30" size="{3},{4}" pixmap="pic_frame.png" zPosition="1" alphatest="on" />{5}</screen>""".format(size_w, size_h, self.color, self._thumbX + doubleMargin, self._thumbY + doubleMargin, skincontent)

		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions"],
		{
			"cancel": self.Exit,
			"ok": self.KeyOk,
			"left": self.key_left,
			"right": self.key_right,
			"up": self.key_up,
			"down": self.key_down,
			"showEventInfo": self.StartExif,
		}, -1)

		self["frame"] = MovingPixmap()
		for x in range(self.thumbsC):
			self["label"+str(x)] = StaticText()
			self["thumb"+str(x)] = Pixmap()

		self.Thumbnaillist = []
		self.filelist = []
		self.currPage = -1
		self.dirlistcount = 0
		self.path = path

		index = 0
		framePos = 0
		Page = 0
		for x in piclist:
			if x[0][1] == False:
				self.filelist.append((index, framePos, Page, x[0][0],  path + x[0][0]))
				index += 1
				framePos += 1
				if framePos > (self.thumbsC -1):
					framePos = 0
					Page += 1
			else:
				self.dirlistcount += 1

		self.maxentry = len(self.filelist)-1
		self.index = lastindex - self.dirlistcount
		if self.index < 0:
			self.index = 0

		self.picload = ePicLoad()
		self.picload_conn = self.picload.PictureData.connect(self.showPic)

		self.onLayoutFinish.append(self.setPicloadConf)

		self.ThumbTimer = eTimer()
		self.ThumbTimer_conn = self.ThumbTimer.timeout.connect(self.showPic)

	def setPicloadConf(self):
		sc = getScale()
		self._aspectRatio = eSize(sc[0], sc[1])
		self._scaleSize = self["thumb0"].instance.size()
		self.picload.setPara([self._scaleSize.width(), self._scaleSize.height(), sc[0], sc[1], config.pic.cache.value, int(config.pic.resize.value), self.color])
		self.paintFrame()

	def paintFrame(self):
		#print "index=" + str(self.index)
		if self.maxentry < self.index or self.index < 0:
			return

		pos = self.positionlist[self.filelist[self.index][T_FRAME_POS]]
		self["frame"].moveTo( pos[0], pos[1], 1)
		self["frame"].startMoving()

		if self.currPage != self.filelist[self.index][T_PAGE]:
			self.currPage = self.filelist[self.index][T_PAGE]
			self.newPage()

	def newPage(self):
		self.Thumbnaillist = []
		#clear Labels and Thumbnail
		for x in range(self.thumbsC):
			self["label"+str(x)].setText("")
			self["thumb"+str(x)].hide()
		#paint Labels and fill Thumbnail-List
		for x in self.filelist:
			if x[T_PAGE] == self.currPage:
				self["label"+str(x[T_FRAME_POS])].setText("(" + str(x[T_INDEX]+1) + ") " + x[T_NAME])
				self.Thumbnaillist.append([0, x[T_FRAME_POS], x[T_FULL]])

		#paint Thumbnail start
		self.showPic()

	def showPic(self, picInfo=""):
		for x in range(len(self.Thumbnaillist)):
			if self.Thumbnaillist[x][0] == 0:
				if self.picload.getThumbnail(self.Thumbnaillist[x][2]) == 1: #zu tun probier noch mal
					self.ThumbTimer.start(config.pic.thumbDelay.value, True)
				else:
					self.Thumbnaillist[x][0] = 1
				break
			elif self.Thumbnaillist[x][0] == 1:
				self.Thumbnaillist[x][0] = 2
				ptr = self.picload.getData()
				if ptr != None:
					setPixmap(self["thumb" + str(self.Thumbnaillist[x][1])], ptr, self._scaleSize, self._aspectRatio)
					self["thumb" + str(self.Thumbnaillist[x][1])].show()

	def key_left(self):
		self.index -= 1
		if self.index < 0:
			self.index = self.maxentry
		self.paintFrame()

	def key_right(self):
		self.index += 1
		if self.index > self.maxentry:
			self.index = 0
		self.paintFrame()

	def key_up(self):
		self.index -= self.thumbsX
		if self.index < 0:
			self.index =self.maxentry
		self.paintFrame()

	def key_down(self):
		self.index += self.thumbsX
		if self.index > self.maxentry:
			self.index = 0
		self.paintFrame()

	def StartExif(self):
		if self.maxentry < 0:
			return
		self.session.open(Pic_Exif, self.picload.getInfo(self.filelist[self.index][T_FULL]))

	def KeyOk(self):
		if self.maxentry < 0:
			return
		self.old_index = self.index
		self.session.openWithCallback(self.callbackView, Pic_Full_View, self.filelist, self.index, self.path)

	def callbackView(self, val=0):
		self.index = val
		if self.old_index != self.index:
			self.paintFrame()
	def Exit(self):
		del self.picload_conn
		del self.picload
		self.close(self.index + self.dirlistcount)

#---------------------------------------------------------------------------

class Pic_Full_View(Screen):
	def __init__(self, session, filelist, index, path):

		self.textcolor = config.pic.textcolor.value
		self.bgcolor = config.pic.bgcolor.value
		space = config.pic.framesize.value
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()

		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
				<eLabel position=\"0,0\" zPosition=\"0\" size=\""+ str(size_w) + "," + str(size_h) + "\" backgroundColor=\""+ self.bgcolor +"\" /> \
				<widget name=\"pic\" position=\"" + str(space) + "," + str(space) + "\" size=\"" + str(size_w-(space*2)) + "," + str(size_h-(space*2)) + "\" zPosition=\"1\" /> \
				<widget name=\"point\" position=\""+ str(space+5) + "," + str(space+2) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"skin_default/icons/record.png\"/> \
				<widget name=\"play_icon\" position=\""+ str(space+10) + "," + str(space+2) + "\" size=\"20,20\" zPosition=\"2\" pixmap=\"skin_default/icons/ico_mp_play.png\" /> \
				<widget source=\"file\" render=\"Label\" position=\""+ str(space+40) + "," + str(space) + "\" size=\""+ str(size_w-(space*2)-40) + ",45\" font=\"Regular;20\" valign=\"center\" foregroundColor=\"" + self.textcolor + "\" zPosition=\"2\" noWrap=\"1\" transparent=\"1\" /> \
			</screen>"

		Screen.__init__(self, session)

		self["PicturePlayerActions"] = HelpableActionMap(self, "PicturePlayerActions",
		{
			"cancel":	(self.Exit, _("Exit")),
			"playpause":	(self.PlayPause, _("Play/Pause")),
			"next":		(self.nextPic, _("Next")),
			"previous":	(self.prevPic, _("Prev")),
			"info":	(self.StartExif, _("Info"))
		}, -2);

		self["point"] = Pixmap()
		self["pic"] = Pixmap()
		self["play_icon"] = Pixmap()
		self["file"] = StaticText(_("please wait, loading picture..."))

		self.picVisible = False
		self._layoutFinished = False
		self.setFileList(filelist, index, path)

		self.picload = ePicLoad()
		self.picload_conn = self.picload.PictureData.connect(self.finish_decode)

		self.slideTimer = eTimer()
		self.slideTimer_conn = self.slideTimer.timeout.connect(self.slidePic)

		self.onLayoutFinish.append(self._onLayoutFinished)

	def setFileList(self, filelist, index, path):
		self.picReady = False
		self.old_index = 0
		self.filelist = []
		self.lastindex = index
		self.shownow = True
		self.dirlistcount = 0
		self.direction = 1 #cache next picture

		for x in filelist:
			if len(filelist[0]) == 3: #orig. filelist
				if x[0][1] == False:
					self.filelist.append(path + x[0][0])
				else:
					self.dirlistcount += 1
			elif len(filelist[0]) == 2: #scanlist
				if x[0][1] == False:
					self.filelist.append(x[0][0])
				else:
					self.dirlistcount += 1
			else: # thumbnaillist
				self.filelist.append(x[T_FULL])

		self.maxentry = len(self.filelist)-1
		self.index = index - self.dirlistcount
		if self.index < 0:
			self.index = 0
		if self._layoutFinished and self.maxentry >= 0:
			self.start_decode()

	def _onLayoutFinished(self):
		self._layoutFinished = True
		if self.maxentry >= 0:
			self.setPicloadConf()

	def setPicloadConf(self):
		sc = getScale()
		self._aspectRatio = eSize(sc[0], sc[1])
		self._scaleSize = self["pic"].instance.size()
		self.picload.setPara((self._scaleSize.width(), self._scaleSize.height(), sc[0], sc[1], 0, int(config.pic.resize.value), self.bgcolor))

		self["play_icon"].hide()
		if not config.pic.infoline.value:
			self["file"].setText("")
		self.start_decode()

	def ShowPicture(self):
		if self.shownow and self.pic_ready:
			if self.picVisible:
				self.picVisible = False
				empty = gPixmapPtr()
				self["pic"].instance.setPixmap(empty)

			ptr = self.picload.getData()
			if ptr != None:
				text = ""
				try:
					text = self.picInfo.split('\n',1)
					text = "(" + str(self.index+1) + "/" + str(self.maxentry+1) + ") " + text[0].split('/')[-1]
				except:
					pass

				self.shownow = False
				if not config.pic.infoline.value:
					self["play_icon"].hide()
					self["file"].setText("")
				else:
					self["file"].setText(text)
				self.lastindex = self.index

				setPixmap(self["pic"], ptr, self._scaleSize, self._aspectRatio)
				self.picVisible = True
			else:
				print("picture ready but no picture avail!!!!!!!")

			print("direction", self.direction)
			if self.direction > 0:
				self.next()
			else:
				self.prev()
			self.start_decode()

	def finish_decode(self, picInfo=""):
		self["point"].hide()
		self.picInfo = picInfo
		self.pic_ready = True
		self.ShowPicture()

	def start_decode(self):
		self.pic_ready = False
		self.picload.startDecode(self.filelist[self.index])
		self["point"].show()

	def next(self):
		self.direction = 1
		self.index += 1
		if self.index > self.maxentry:
			self.index = 0

	def prev(self):
		self.direction = -1
		self.index -= 1
		if self.index < 0:
			self.index = self.maxentry

	def slidePic(self):
		print("slide to next Picture index=" + str(self.lastindex))
		if config.pic.loop.value==False and self.lastindex == self.maxentry:
			self.PlayPause()
		self.shownow = True
		self.ShowPicture()

	def PlayPause(self):
		if self.slideTimer.isActive():
			self.slideTimer.stop()
			self["play_icon"].hide()
		else:
			self.slideTimer.start(config.pic.slidetime.value*1000)
			self["play_icon"].show()
			self.nextPic()

	def prevPic(self):
		self.shownow = True
		if self.direction < 0:
			self.ShowPicture()
		else:
			self.index = self.lastindex
			self.prev()
			self.start_decode()

	def nextPic(self):
		self.shownow = True
		if self.direction > 0:
			self.ShowPicture()
		else:
			self.index = self.lastindex
			self.next()
			self.start_decode()

	def StartExif(self):
		if self.maxentry < 0:
			return
		self.session.open(Pic_Exif, self.picload.getInfo(self.filelist[self.lastindex]))

	def Exit(self):
		self.slideTimer.stop()
		del self.picload_conn
		del self.picload
		self.close(self.lastindex + self.dirlistcount)

#------------------------------------------------------------------------------------------

def main(session, **kwargs):
	session.open(picshow)

def filescan_open(list, session, **kwargs):
	# Recreate List as expected by PicView
	filelist = [((file.path, False), None) for file in list]
	session.open(Pic_Full_View, filelist, 0, file.path)

def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath

	# Overwrite checkFile to only detect local
	class LocalScanner(Scanner):
		def checkFile(self, file):
			return fileExists(file.path)

	return \
		LocalScanner(mimetypes = ["image/jpeg", "image/png", "image/gif", "image/bmp"],
			paths_to_scan = 
				[
					ScanPath(path = "DCIM", with_subdirs = True),
					ScanPath(path = "", with_subdirs = False),
				],
			name = "Pictures", 
			description = _("View Photos..."),
			openfnc = filescan_open,
		)

def Plugins(**kwargs):
	return \
		[PluginDescriptor(name=_("PicturePlayer"), description=_("fileformats (BMP, PNG, JPG, GIF)"), icon="pictureplayer.png", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main),
		 PluginDescriptor(name=_("PicturePlayer"), where = PluginDescriptor.WHERE_FILESCAN, needsRestart = False, fnc = filescan)]
