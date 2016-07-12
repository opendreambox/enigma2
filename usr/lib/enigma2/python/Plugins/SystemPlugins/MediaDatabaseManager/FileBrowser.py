# -*- coding: UTF-8 -*-
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.FileList import FileList
from Components.Label import MultiColorLabel
from Components.Pixmap import Pixmap
from Screens.Screen import Screen

from os import path as os_path

class FileBrowser(Screen):
	title = _("File Browser")
	select = _("Select")

	skin = """
		<screen name="FileBrowser_Generic" position="center,120" size="820,520"  title="%s" >
			<widget name="green" position="10,5" size="200,40" pixmap="skin_default/buttons/green.png" alphatest="on"/>
			<widget name="key_green" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="filelist" position="10,60" size="800,420" scrollbarMode="showOnDemand"/>
			<widget name="status" position="10,490" size="800,20" font="Regular;18" halign="left" foregroundColors="white,white,white" backgroundColors="background,#00DD00,#DD0000"/>
		</screen>""" % (title)

	def __init__(self, session, showDirectories=True, showFiles=True, showMountpoints=True, matchingPattern=None, useServiceRef=False, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=False, additionalExtensions=None, closeOnSelection=False):
		Screen.__init__(self, session)
		self.skinName = "FileBrowser_Generic"

		defaultDir = None  # TODO Fix / Config value
		self._closeOnSelection = closeOnSelection
		self._filelist = FileList(defaultDir, showDirectories=showDirectories, showFiles=showFiles, showMountpoints=showMountpoints, matchingPattern=matchingPattern, useServiceRef=useServiceRef, inhibitDirs=inhibitDirs, inhibitMounts=inhibitMounts, isTop=isTop, enableWrapAround=enableWrapAround, additionalExtensions=additionalExtensions)

		self["filelist"] = self._filelist
		self["status"] = MultiColorLabel("")

		self["key_green"] = Button(_("Add"))
		self["green"] = Pixmap()

		self["actions"] = ActionMap(["ListboxActions", "OkCancelActions", "ColorActions"],
		{
			"ok" : self.ok,
			"cancel" : self.close,
			"moveUp" : self.moveUp,
			"moveDown" : self.moveDown,
			"pageUp" : self.pageUp,
			"pageDown" : self.pageDown,
			"green" : self.selectCurrent,
		});
		self.onShown.append(self._onShown)

	def _onShown(self):
		self.summaries.setText(self.title, 1)
		self._onSelectionChanged()
		self._filelist.onSelectionChanged.append(self._onSelectionChanged)

	def _onSelectionChanged(self):
		# Update LCD Stuff
		curDir = self._filelist.getCurrentDirectory()
		if curDir != None:
			self.summaries.setText(curDir , 2)
		else:
			self.summaries.setText("" , 2)

		text = None
		if self._filelist.canDescent():
			text = self._filelist.getFilename()
			if text != None:
				text = "./%s" % (text.split('/')[-2])
				self.summaries.setText(text, 3)
			else:
				self.summaries.setText("", 3)

	def createSummary(self):
		return Simple4LineLCDScreen

	def ok(self):
		if self._filelist.canDescent():
			self._filelist.descent()
		else:
			self.selectCurrent()

	def moveUp(self):
		self._filelist.up()

	def moveDown(self):
		self._filelist.down()

	def pageUp(self):
		self._filelist.pageUp()

	def pageDown(self):
		self._filelist.pageDown()

	def selectCurrent(self):
		if self._filelist.canDescent():
			dir = os_path.dirname(self._filelist.getFilename()) + "/"
			if self.selectDirectory(dir):
				self.setStatus(dir)
			else:
				self.setStatus(dir, True)
		else:
			file = self._filelist.getFilename()
			if self.selectFile(self._filelist.getServiceRef()):
				self.setStatus(file)
			else:
				self.setStatus(file, True)

	def setStatus(self, file, error=False):
		if error:
			self["status"].setText(_("ERROR: Cannot add '%s'") % file)
			self["status"].setForegroundColorNum(2)
			self["status"].setBackgroundColorNum(2)
		else:
			self["status"].setText(_("Added '%s'") % file)
			self["status"].setForegroundColorNum(1)
			self["status"].setBackgroundColorNum(1)

	def selectDirectory(self, dir):
		return self.selectFile(dir)

	def selectFile(self, file):
		if file:
			if self._closeOnSelection:
				self.close(file)
				return True

		return False

# -*- coding: UTF-8 -*-

from Components.Label import Label
from Screens.Screen import Screen

class Simple4LineLCDScreen(Screen):
	skin = (
	"""<screen name="Simple4LineLCDScreen" position="0,0" size="132,64" id="1">
		<widget name="text1" position="4,0" size="132,18" font="Regular;16"/>
		<widget name="text2" position="4,19" size="132,14" font="Regular;10"/>
		<widget name="text3" position="4,34" size="132,14" font="Regular;10"/>
		<widget name="text4" position="4,49" size="132,14" font="Regular;10"/>
	</screen>""",
	"""<screen name="Simple4LineLCDScreen" position="0,0" size="96,64" id="2">
		<widget name="text1" position="0,0" size="96,18" font="Regular;16"/>
		<widget name="text2" position="0,19" size="96,14" font="Regular;10"/>
		<widget name="text3" position="0,34" size="96,14" font="Regular;10"/>
		<widget name="text4" position="0,49" size="96,14" font="Regular;10"/>
	</screen>""")

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label(_("File Browser"))
		self["text2"] = Label("")
		self["text3"] = Label("")
		self["text4"] = Label("")

	def setText(self, text, line):
		if line == 1:
			if len(text) > 15:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 15:
					text = text[-15:]
		else:
			if len(text) > 20:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 20:
					text = text[-20:]
		textleer = "	"
		text = text + textleer * 10
		if line == 1:
			self["text1"].setText(text)
		elif line == 2:
			self["text2"].setText(text)
		elif line == 3:
			self["text3"].setText(text)
		elif line == 4:
			self["text4"].setText(text)
