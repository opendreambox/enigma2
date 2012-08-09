from enigma import getDesktop, eListboxPythonMultiContent, eListbox, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont, eTimer, getPrevAsciiCode

from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, getConfigListEntry, KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_0, KEY_DELETE, KEY_BACKSPACE, KEY_OK, KEY_TOGGLEOW, KEY_ASCII
from Components.ConfigList import ConfigList
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryProgress
from Components.Sources.Boolean import Boolean
from Components.Sources.CanvasSource import CanvasSource

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from Tools.BoundFunction import boundFunction

from Bookmarks import BookmarkEditor
from BrowserDB import Bookmark, BrowserDB
from Downloads import downloadManager
from EnhancedInput import EnhancedInput

from time import localtime, strftime

class BrowserMenu(Screen):
	ACTION_BOOKMARK = 0
	ACTION_COOKIES = 1
	ACTION_STORAGE_PATH = 2

	MENU_BOOKMARKS = 0
	MENU_SETTINGS = 1
	MENU_HISTORY = 2
	MENU_DOWNLOADS = 3
	MENU_CERTS = 4
	MENU_COOKIES = 5

	size = getDesktop(0).size()
	width = int(size.width() * 0.9)
	height = int(size.height() * 0.85)
	bof = height - 35 #Button-Offset
	skin = """
		<screen name="BrowserMenu" position="center,center" size="%(w)d,%(h)d" title="Web Browser - Menu" >
			<widget name="menu" position="0,0" zPosition="1" size="200,%(h)d" backgroundColor="#000000" transparent="1" />
			<widget source="line" render="Canvas" position="203,0" zPosition="2" size="4,%(h)d" backgroundColor="#000000" transparent="1" alphatest="on"/>
			<widget name="list" position="210,0" zPosition="1" size="%(listW)d,%(listH)d" backgroundColor="#000000" transparent="1" />
			<widget name="statuslabel" position="210,%(inputY)d" size="%(listW)d,25" font="Regular;20"  zPosition="2" halign="center" valign="center" backgroundColor="#000000" transparent="0" />
			<widget name="input" position="210,%(inputY)d" zPosition="1" size="%(listW)d,25" font="Regular;20" halign="left" valign="bottom" backgroundColor="#000000" transparent="1"/>
			<widget name="config" position="210,0" zPosition="1" size="%(listW)d,%(configH)d" backgroundColor="#000000" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/button_red_off.png" position="210,%(btnY)d" size="15,16" alphatest="on" />
			<widget source="button_red" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_red.png" position="210,%(btnY)d" size="15,16" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="red" position="230,%(btnTxtY)d" size="100,20" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="top"/>

			<ePixmap pixmap="skin_default/buttons/button_green_off.png" position="340,%(btnY)d" size="15,16" zPosition="1" alphatest="on" />
			<widget source="button_green" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_green.png" position="340,%(btnY)d" size="15,16" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="green" position="360,%(btnTxtY)d" size="100,20" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="top"/>

			<ePixmap pixmap="skin_default/buttons/button_yellow_off.png" position="470,%(btnY)d" size="15,16" alphatest="on" />
			<widget source="button_yellow" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_yellow.png" position="470,%(btnY)d" size="15,16" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="yellow" position="490,%(btnTxtY)d" size="100,20" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="top"/>

			<ePixmap pixmap="skin_default/buttons/button_blue_off.png" position="600,%(btnY)d" size="15,16" alphatest="on" />
			<widget source="button_blue" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_blue.png" position="600,%(btnY)d" size="15,16" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="blue" position="620,%(btnTxtY)d" size="200,20" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="top"/>
		</screen>
		""" %{ 	"w" : width,
				"h" : height,
				"listW" : width - 210, "listH" : height - 90,
				"inputY" : height - 80,
				"configH" : height - 25,
				"btnY" : bof + 2,
				"btnTxtY" : bof
			}

	def __init__(self, session, currentTitle, currentUrl):
		Screen.__init__(self, session)

		self.currentUrl = currentUrl
		self.currentTitle = currentTitle

		#Menu
		self.menu = MenuList([
						(_("Bookmarks"), self.MENU_BOOKMARKS),
						(_("History"), self.MENU_HISTORY),
						(_("Downloads"), self.MENU_DOWNLOADS),
						(_("Certificates"), self.MENU_CERTS),
						(_("Cookies"), self.MENU_COOKIES),
						(_("Settings"), self.MENU_SETTINGS),
					], enableWrapAround = True)
		self["menu"] = self.menu

		self["statuslabel"] = Label("")
		self["statuslabel"].hide()

		#Color Buttons
		self["button_red"] = Boolean(False)
		self["button_green"] = Boolean(False)
		self["button_yellow"] = Boolean(False)
		self["button_blue"] = Boolean(False)
		self.red = Label("")
		self.green = Label("")
		self.yellow = Label("")
		self.blue = Label("")
		self["red"] = self.red
		self["green"] = self.green
		self["yellow"] = self.yellow
		self["blue"] = self.blue



		#Lists
		self.detailList = MenuList([], enableWrapAround = True, content = eListboxPythonMultiContent)
		self.detailConfigList = ConfigList([])
		self.detailConfigList.l.setSeperation( (BrowserMenu.width - 210) / 2 )
		config.plugins.WebBrowser.storage.enabled.addNotifier(self.__cfgExpandableElementChanged, initial_call = False)
		config.plugins.WebBrowser.storage.enabled.addNotifier(self.__cfgStoragePathChanged, initial_call = False)
		config.plugins.WebBrowser.storage.path.addNotifier(self.__cfgStoragePathChanged, initial_call = False)

		self.detailInput = EnhancedInput()

		self["list"] = self.detailList
		self["config"] = self.detailConfigList
		self["input"] = self.detailInput
		self["line"] = CanvasSource()

		self.__cfgCreateSetup()

		self.__db = BrowserDB.getInstance()
		self.__curMenu = self.MENU_BOOKMARKS
		self.__bmList = None
		self.__hisList = None
		self.__crtList = None
		self.__ckList = None
		self.__bmNeedle = ""
		self.__bmFilterTimer = eTimer()
		self.__bmFilterTimer.callback.append(self.__bmFilterCB)
		self.__hisNeedle = ""
		self.__hisFilterTimer = eTimer()
		self.__hisFilterTimer.callback.append(self.__hisFilterCB)
		self.__dlRefreshTimer = eTimer()
		self.__dlRefreshTimer.callback.append(self.__dlBuildList)
		self.__statusTimer = eTimer()
		self.__statusTimer.callback.append(self.__hideStatus)
		self.__actions = []

		self.onFirstExecBegin.append(self.__drawSeparator)
		self.onFirstExecBegin.append(self.__onMenuChanged)
		self.onExecBegin.append(self.__reloadData)
		self.onShow.append(self.setKeyboardModeAscii)

		self["actions"] = ActionMap(["BrowserActions", "ColorActions"],
		{
			"ok" : self.__actionOk,
			"enter" : self.__actionOk,
			"exit" : self.__actionExit,
			"pageUp" : self.__actionMenuUp,
			"pageDown" : self.__actionMenuDown,
			"up" : boundFunction(self.__action, "up"),
			"down" : boundFunction(self.__action, "down"),
			"left" : boundFunction(self.__action, "left"),
			"right" : boundFunction(self.__action, "right"),
			"red" : boundFunction(self.__action, "red"),
			"green" : boundFunction(self.__action, "green"),
			"yellow" : boundFunction(self.__action, "yellow"),
			"blue" : boundFunction(self.__action, "blue"),
			"backspace" : boundFunction(self.__action, "backspace"),
			"delete" : boundFunction(self.__action, "delete"),
			"ascii": boundFunction(self.__action, "ascii"),
			# TODO "text" : self.__text
		}, -2)

		self["numberactions"] = NumberActionMap(["NumberActions"],
		{
			"1": self.__keyNumberGlobal,
			"2": self.__keyNumberGlobal,
			"3": self.__keyNumberGlobal,
			"4": self.__keyNumberGlobal,
			"5": self.__keyNumberGlobal,
			"6": self.__keyNumberGlobal,
			"7": self.__keyNumberGlobal,
			"8": self.__keyNumberGlobal,
			"9": self.__keyNumberGlobal,
			"0": self.__keyNumberGlobal
		}, -2)

		self.__actionFuncs = {
			self.MENU_BOOKMARKS : {
				"up" : self.detailList.up,
				"down" : self.detailList.down,
				"left" : self.detailList.pageUp,
				"right" : self.detailList.pageDown,
				"ok" : self.__bmOk,
				"enter" : self.__bmOk,
				"red" : self.__bmDelete,
				"green" : self.__bmAdd,
				"yellow" : self.__bmEdit,
				"blue" : self.__bmSetCurrentAsHome,
				"backspace" : self.__bmKeyBackspace,
				"delete" : self.__bmKeyDelete,
				"ascii": self.__bmKeyAscii,
				},
			self.MENU_HISTORY : {
				"up" : self.detailList.up,
				"down" : self.detailList.down,
				"left" : self.detailList.pageUp,
				"right" : self.detailList.pageDown,
				"ok" : self.__hisOk,
				"enter" : self.__hisOk,
				"red" : self.__hisClear,
				"blue" : self.__hisSetCurrentAsHome,
				"backspace" : self.__hisKeyBackspace,
				"delete" : self.__hisKeyDelete,
				"ascii": self.__hisKeyAscii,
				},
			self.MENU_SETTINGS : {
				"up" : self.__cfgKeyUp,
				"down" : self.__cfgKeyDown,
				"left" : self.__cfgKeyLeft,
				"right" : self.__cfgKeyRight,
				"ok" : self.__cfgKeyOK,
				"enter" : self.__cfgKeyOK,
				"red" : self.__cfgCancel,
				"green" : self.__cfgSave,
				"backspace" : self.__cfgKeyBackspace,
				"delete" : self.__cfgKeyDelete,
				"ascii": self.__cfgKeyAscii,
				},
			self.MENU_DOWNLOADS : {
				"up" : self.detailList.up,
				"down" : self.detailList.down,
				"left" : self.detailList.pageUp,
				"right" : self.detailList.pageDown,
				"red" : self.__dlAbort,
				},
			self.MENU_CERTS : {
				"up" : self.detailList.up,
				"down" : self.detailList.down,
				"left" : self.detailList.pageUp,
				"right" : self.detailList.pageDown,
				"red" : self.__crtDelete,
				"green" : self.__crtDetails,
				},
			self.MENU_COOKIES : {
				"up" : self.detailList.up,
				"down" : self.detailList.down,
				"left" : self.detailList.pageUp,
				"right" : self.detailList.pageDown,
				"red" : self.__ckDelete,
				"blue" : self.__ckDeleteAll,
				}
		}

	def __close(self):
		config.plugins.WebBrowser.storage.enabled.removeNotifier(self.__cfgExpandableElementChanged)
		config.plugins.WebBrowser.storage.enabled.removeNotifier(self.__cfgStoragePathChanged)
		config.plugins.WebBrowser.storage.path.removeNotifier(self.__cfgStoragePathChanged)
		self.close(self.__actions)

	def __actionOk(self):
		if self["statuslabel"].visible:
			self["statuslabel"].hide()
		else:
			self.__action("ok")

	def __actionExit(self):
		if self["statuslabel"].visible:
			self["statuslabel"].hide()
		else:
			if self.detailConfigList.isChanged():
				self.__cfgSave()
			self.__close()

	def __actionMenuUp(self):
		self.menu.up()
		self.__onMenuChanged()

	def __actionMenuDown(self):
		self.menu.down()
		self.__onMenuChanged()

	def __reloadData(self):
		self.__bmList = self.__db.getBookmarks()
		self.__hisList = self.__db.getHistory()
		self.__crtList = self.__db.getCerts()
		self.__ckList = self.__db.getCookies()

	def __action(self, action):
		print "[BrowserMenu].__action :: action='%s'" %action
		fnc = self.__actionFuncs[self.__curMenu].get(action, None)
		if fnc != None:
			fnc()

	def __text(self):
		if self.__curMenu == self.MENU_SETTINGS:
			self.__cfgKeyText()
		elif self.__curMenu == self.MENU_BOOKMARKS:
			pass

	def __keyNumberGlobal(self, number):
		if self.__curMenu == self.MENU_SETTINGS:
			self.__cfgKeyNumberGlobal(number)
		elif self.__curMenu == self.MENU_BOOKMARKS:
			self.__bmKeyNumberGlobal(number)
		elif self.__curMenu == self.MENU_HISTORY:
			self.__hisKeyNumberGlobal(number)

	def __onMenuChanged(self):
		self.__bmFilterTimer.stop()
		self.__hisFilterTimer.stop()
		self.__dlRefreshTimer.stop()

		self.__curMenu = self.menu.getCurrent()[1]
		if self.__curMenu == self.MENU_BOOKMARKS:
			self.__showMenuList(True)
			self.__setButtons(_("Delete"), _("Add"), _("Edit"), _("Set as Startpage"))
			self.__bmBuildList()
			self.detailInput.setText(self.__bmNeedle)
		elif self.__curMenu == self.MENU_HISTORY:
			self.__showMenuList(True)
			self.__setButtons(_("Clear"), "", "", _("Set as Startpage"))
			self.__hisBuildList()
			self.detailInput.setText(self.__hisNeedle)
		elif self.__curMenu == self.MENU_SETTINGS:
			self.__showConfigList()
			self.__setButtons(_("Cancel"), _("Save"), "", "")
		elif self.__curMenu == self.MENU_DOWNLOADS:
			self.__showMenuList()
			self.__setButtons(_("Abort"), "", "", "")
			self.__dlBuildList()
		elif self.__curMenu == self.MENU_CERTS:
			self.__showMenuList()
			self.__setButtons(_("Delete"), _("Details"), "", "")
			self.__crtBuildList()
		elif self.__curMenu == self.MENU_COOKIES:
			self.__showMenuList()
			self.__setButtons(_("Delete"), "", "", _("Delete All"))
			self.__ckBuildList()

	def __setButtons(self, red, green, yellow, blue):
		self.red.setText(red)
		self.__setButtonPixmapVisible(self["button_red"], red)
		self.green.setText(green)
		self.__setButtonPixmapVisible(self["button_green"], green)
		self.yellow.setText(yellow)
		self.__setButtonPixmapVisible(self["button_yellow"], yellow)
		self.blue.setText(blue)
		self.__setButtonPixmapVisible(self["button_blue"], blue)

	def __setButtonPixmapVisible(self, B, label):
		show = True
		if label == "":
			show = False
		B.setBoolean(show)

	def __showMenuList(self, hasFilter = False):
		if self.detailConfigList.visible:
			self.detailConfigList.hide()

		if not self.detailList.visible:
			self.detailList.show()
		if hasFilter:
			self.detailInput.show()
		else:
			self.detailInput.hide()

	def __showConfigList(self):
		if self.detailList.visible == 1:
			self.detailList.hide()
			self.detailInput.hide()
		if self.detailConfigList.visible == 0:
			self.detailConfigList.show()

	def __drawSeparator(self):
		self["line"].fill(0, 0, 4, BrowserMenu.height, 0xFF9900)
		self["line"].flush()

	def __setStatus(self, text):
		print "[BrowserMenu].__setStatus"
		self["statuslabel"].setText(text)
		self["statuslabel"].show()
		self.__statusTimer.startLongTimer(3)

	def __hideStatus(self):
		self["statuslabel"].hide()
		self.__statusTimer.stop()

	# Config List Methods
	def __cfgCreateSetup(self):
		list = [
			getConfigListEntry(_("Home Page"), config.plugins.WebBrowser.home),
			getConfigListEntry(_("Page to load on startup"), config.plugins.WebBrowser.startPage),
			getConfigListEntry(_("Search Provider"), config.plugins.WebBrowser.searchProvider),
			getConfigListEntry(_("Run fullscreen"), config.plugins.WebBrowser.fullscreen),
			getConfigListEntry(_("Offset in scroll mode (px)"), config.plugins.WebBrowser.scrollOffset),
			getConfigListEntry(_("Target directory for downloads"), config.plugins.WebBrowser.downloadpath),
			getConfigListEntry(_("Enable persistent storage"), config.plugins.WebBrowser.storage.enabled),
		]
		if config.plugins.WebBrowser.storage.enabled.value:
			list.append(getConfigListEntry(_("Path for persistent storage"), config.plugins.WebBrowser.storage.path))

		self.detailConfigList.setList(list)

	def __cfgExpandableElementChanged(self, element):
		self.__cfgCreateSetup()

	def __cfgSave(self):
		for x in self.detailConfigList.list:
			x[1].save()
		self.__setStatus(_("Settings have been saved successfully!"))

	def __cfgStoragePathChanged(self, element):
		action = [self.ACTION_STORAGE_PATH,True]
		if not action in self.__actions:
			self.__actions.append(action)

	def __cfgCancel(self):
		dlg = self.session.openWithCallback(self.__cfgCancelCB, MessageBox, _("Do you really want to discard all changes?"), type = MessageBox.TYPE_YESNO)
		dlg.setTitle(_("Discard changed settings?"))

	def __cfgCancelCB(self, confirmed):
		for x in self.detailConfigList.list:
			x[1].cancel()
		self.__setStatus(_("All changes to the settings have been discarded!"))

	def __cfgKeyText(self):
		from Screens.VirtualKeyBoard import VirtualKeyBoard
		self.session.openWithCallback(self.__cfgVirtualKeyBoardCallback, VirtualKeyBoard, title = self.detailConfigList.getCurrent()[0], text = self.detailConfigList.getCurrent()[1].getValue())

	def __cfgVirtualKeyBoardCallback(self, callback = None):
		if callback is not None and len(callback):
			self.detailConfigList.getCurrent()[1].setValue(callback)
			self.detailConfigList.invalidate(self.detailConfigList.getCurrent())

	def  __cfgKeyOK(self):
		self.detailConfigList.handleKey(KEY_OK)

	def  __cfgKeyUp(self):
		self.detailConfigList.instance.moveSelection(eListbox.moveUp)

	def  __cfgKeyDown(self):
		self.detailConfigList.instance.moveSelection(eListbox.moveDown)

	def  __cfgKeyLeft(self):
		self.detailConfigList.handleKey(KEY_LEFT)

	def __cfgKeyRight(self):
		self.detailConfigList.handleKey(KEY_RIGHT)

	def __cfgKeyHome(self):
		self.detailConfigList.handleKey(KEY_HOME)

	def __cfgKeyEnd(self):
		self.detailConfigList.handleKey(KEY_END)

	def __cfgKeyDelete(self):
		self.detailConfigList.handleKey(KEY_DELETE)

	def __cfgKeyBackspace(self):
		self.detailConfigList.handleKey(KEY_BACKSPACE)

	def __cfgKeyToggleOW(self):
		self.detailConfigList.handleKey(KEY_TOGGLEOW)

	def __cfgKeyAscii(self):
		self.detailConfigList.handleKey(KEY_ASCII)

	def __cfgKeyNumberGlobal(self, number):
		self.detailConfigList.handleKey(KEY_0 + number)

	#Bookmark List Methods
	def __bmOk(self):
		print "[BrowserMenu].__bmOk"
		if self.detailList.getSelectedIndex() > 0 and  self.detailList.getCurrent() != None:
			current = self.detailList.getCurrent()[0]
			print "[BrowserMenu].__bmOk, current = '%s'" %current
			self.__actions.append( (self.ACTION_BOOKMARK, current.url) )
			self.close( self.__actions )
		else:
			self.__bmAdd(Bookmark(-1, self.currentTitle, self.currentUrl))

	def __bmAdd(self, bookmark = None):
		self.session.openWithCallback(self.__bmEditCB, BookmarkEditor, bookmark)

	def __bmEdit(self):
		if self.detailList.getSelectedIndex() > 0 and  self.detailList.getCurrent() != None:
			cur = self.detailList.getCurrent()[0]
			self.session.openWithCallback(self.__bmEditCB, BookmarkEditor, cur)

	def __bmEditCB(self, bookmark):
		if bookmark != None:
			self.__db.setBookmark(bookmark)
			self.__bmReload()
			self.__setStatus(_("Bookmark '%s' saved succesfully!" %bookmark.name))

	def __bmDelete(self):
		if self.detailList.getCurrent() != None:
			name = self.detailList.getCurrent()[0].name
			print "[BrowserMenu].__bmDelete, name='%s'" %name
			dlg = self.session.openWithCallback( self.__bmDeleteCB, MessageBox, _("Do you really want to delete the bookmark '%s'?") %name, type = MessageBox.TYPE_YESNO )
			dlg.setTitle(_("Delete Bookmark?"))

	def __bmDeleteCB(self, confirmed):
		if confirmed:
			self.__db.deleteBookmark( self.detailList.getCurrent()[0] )
			name = self.detailList.getCurrent()[0]
			self.__setStatus(_("Bookmark '%s' deleted!" %name))
			self.__bmReload()

	def __bmSetCurrentAsHome(self):
		cur = self.detailList.getCurrent()[0]
		self.__setUrlAsHome(cur.url)

	def __bmGetEntryComponent(self, bookmark):
		w = self.width - 225
		res = [ bookmark ]
		res.append(MultiContentEntryText(pos = (10, 1), size = (w, 25), font = 0, flags = RT_VALIGN_CENTER, text = bookmark.name))
		res.append(MultiContentEntryText(pos = (10, 30), size = (w, 25), font = 1, flags = RT_VALIGN_CENTER, text = bookmark.url))
		return res

	def __bmBuildList(self):
		print "[BrowserMenu].__bmBuildList"
		self.detailList.l.setFont(0, gFont("Regular", 22))
		self.detailList.l.setFont(1, gFont("Regular", 16))
		self.detailList.l.setItemHeight(55)
		list = []
		#Suggest current page for adding

		default = Bookmark(-2, _("Add '%s' to Bookmarks" %self.currentTitle), self.currentUrl)
		list.append(self.__bmGetEntryComponent(default))
		for b in self.__bmList:
			list.append(self.__bmGetEntryComponent(b))
		self.detailList.setList(list)

	def __bmReload(self, needle = ""):
		print "[BrowserMenu].__bmReload"
		self.__bmNeedle = needle
		self.__bmList = self.__db.getBookmarks(needle)
		self.__bmBuildList()

	def __bmFilterCB(self):
		print "[BrowserMenu].__bmFilterCB"
		needle = self.detailInput.getText()
		if needle != self.__bmNeedle:
			self.__bmReload(needle)
		else:
			self.__bmFilterTimer.stop()

	def __bmKeyNumberGlobal(self, number):
		self.detailInput.number(number)
		self.__bmFilterTimer.startLongTimer(1)

	def __bmKeyAscii(self):
		self.detailInput.handleAscii(getPrevAsciiCode())
		self.__bmFilterTimer.startLongTimer(1)

	def __bmKeyDelete(self):
		self.detailInput.delete()
		self.__bmFilterTimer.startLongTimer(1)

	def __bmKeyBackspace(self):
		self.detailInput.deleteBackward()
		self.__bmFilterTimer.startLongTimer(1)

	#History list methods
	def __hisSetCurrentAsHome(self):
		if self.detailList.getCurrent() != None:
			cur = self.detailList.getCurrent()[0]
			self.__setUrlAsHome(cur.url)

	def __setUrlAsHome(self, url):
		config.plugins.WebBrowser.home.value = url
		config.plugins.WebBrowser.home.save()
		self.__setStatus(_("Home page has been set to '%s'" %url))

	def __hisClear(self):
		dlg = self.session.openWithCallback(self.__hisClearCB, MessageBox, _("Do you really want to clear the History?"), type = MessageBox.TYPE_YESNO)
		dlg.setTitle(_("Clear History?"))

	def __hisClearCB(self, confirmed):
		if confirmed:
			self.__db.clearHistory()
			self.__hisReload()
			self.__setStatus(_("History cleared!"))

	def __hisGetEntryComponent(self, historyItem):
		w = self.width - 225
		res = [ historyItem ]
		date = strftime("%Y-%m-%d", localtime(historyItem.timestamp))
		time = strftime("%H:%M:%S", localtime(historyItem.timestamp))
		res.append(MultiContentEntryText(pos = (10, 1), size = (150, 25), font = 1, flags = RT_VALIGN_CENTER, text = date))
		res.append(MultiContentEntryText(pos = (10, 28), size = (150, 25), font = 1, flags = RT_VALIGN_CENTER, text = time))
		res.append(MultiContentEntryText(pos = (190, 1), size = (w-210, 25), font = 0, flags = RT_VALIGN_CENTER, text = historyItem.title))
		res.append(MultiContentEntryText(pos = (190, 28), size = (w-210, 25), font = 1, flags = RT_VALIGN_CENTER, text = historyItem.url))
		return res

	def __hisReload(self, needle = ""):
		print "[BrowserMenu].__hisReload"
		self.__hisNeedle = needle
		self.__hisList = self.__db.getHistory(needle)
		self.__hisBuildList()

	def __hisBuildList(self):
		print "[BrowserMenu].__hisBuildList"
		self.detailList.l.setFont(0, gFont("Regular", 22))
		self.detailList.l.setFont(1, gFont("Regular", 16))
		self.detailList.l.setItemHeight(55)
		history = []
		for h in self.__hisList:
			history.append(self.__hisGetEntryComponent(h))
		self.detailList.setList(history)

	def __hisOk(self):
		if self.detailList.getCurrent() != None:
			current = self.detailList.getCurrent()[0]
			self.__actions.append( (self.ACTION_BOOKMARK, current.url) )
			self.close( self.__actions )

	def __hisFilterCB(self):
		needle = self.detailInput.getText()
		if needle != self.__hisNeedle:
			self.__hisReload(needle)
		else:
			self.__hisFilterTimer.stop()

	def __hisKeyNumberGlobal(self, number):
		self.detailInput.number(number)
		self.__hisFilterTimer.startLongTimer(1)

	def __hisKeyAscii(self):
		self.detailInput.handleAscii(getPrevAsciiCode())
		self.__hisFilterTimer.startLongTimer(1)

	def __hisKeyDelete(self):
		self.detailInput.delete()
		self.__hisFilterTimer.startLongTimer(1)

	def __hisKeyBackspace(self):
		self.detailInput.deleteBackward()
		self.__hisFilterTimer.startLongTimer(1)

	#Download list methods
	def __dlGetEntryComponent(self, job):
		w = self.width - 225
		nw = w - 320 #nameWidth
		stp = nw + 10 #statusTextPos
		spp = stp + 160 #statusProgressPos
		sptp = spp + 110 #statusProgressTextPos

		res = [ job ]
		print "%s :: %s :: %s/%s" %(job.name, job.getStatustext(), job.progress, job.end)
		res.append(MultiContentEntryText(pos = (0, 1), size = (nw, 24), font=1, flags = RT_HALIGN_LEFT, text = job.name))
		res.append(MultiContentEntryText(pos = (stp, 1), size = (150, 24), font=1, flags = RT_HALIGN_RIGHT, text = job.getStatustext()))
		res.append(MultiContentEntryProgress(pos = (spp, 1), size = (100, 24), percent = int(100*job.progress/float(job.end))))
		res.append(MultiContentEntryText(pos = (sptp, 1), size = (70, 24), font=1, flags = RT_HALIGN_RIGHT, text = str(100*job.progress/float(job.end)) + "%"))
		return res

	def __dlBuildList(self):
		print "[BrowserMenu].__dlBuildList"
		self.detailList.l.setFont(0, gFont("Regular", 22))
		self.detailList.l.setFont(1, gFont("Regular", 16))
		self.detailList.l.setItemHeight(25)
		downloads = []
		for job in downloadManager.getPendingJobs():
			downloads.append(self.__dlGetEntryComponent(job))
		self.detailList.setList(downloads)
		if not self.__dlRefreshTimer.isActive():
			self.__dlRefreshTimer.startLongTimer(3)

	def __dlAbort(self):
		print "[BrowserMenu].__dlAbort"
		cur = self.detailList.getCurrent()
		if cur != None:
			job = cur[0]
			dlg = self.session.openWithCallback( self.__dlAbortCB, MessageBox, _("Do you really want to abort downloading '%s'?") %job.name, type = MessageBox.TYPE_YESNO)
			dlg.setTitle(_("Abort Download?"))

	#Certificate list methods
	def __dlAbortCB(self, confirmed):
		if confirmed:
			self.detailList.getCurrent()[0].remove(downloadManager.jobDone)
			self.__dlBuildList()

	def __crtGetEntryComponent(self, cert):
		w = self.width - 225
		res = [ cert ]
		cn = "CN: %s" %(str(cert.cert.get_subject().commonName))
		res.append(MultiContentEntryText(pos = (10, 1), size = (150, 25), font = 1, flags = RT_VALIGN_CENTER, text = str(cert.notBefore())))
		res.append(MultiContentEntryText(pos = (10, 28), size = (150, 25), font = 1, flags = RT_VALIGN_CENTER, text = str(cert.notAfter())))
		res.append(MultiContentEntryText(pos = (190, 1), size = (w-210, 25), font = 0, flags = RT_VALIGN_CENTER, text = str(cert.host)))
		res.append(MultiContentEntryText(pos = (190, 28), size = (w-210, 25), font = 1, flags = RT_VALIGN_CENTER, text = cn))
		res.append(MultiContentEntryText(pos = (10, 60), size = (w-20, 25), font = 0, flags = RT_VALIGN_CENTER, text = str(cert.cert.digest("sha1")) ))
		return res

	def __crtReload(self):
		print "[BrowserMenu].__crtReload"
		self.__crtList = self.__db.getCerts()
		self.__crtBuildList()


	def __crtBuildList(self):
		print "[BrowserMenu].__crtBuildList"
		self.detailList.l.setFont(0, gFont("Regular", 22))
		self.detailList.l.setFont(1, gFont("Regular", 16))
		self.detailList.l.setItemHeight(85)
		certs = []
		for c in self.__crtList:
			certs.append(self.__crtGetEntryComponent(c))
		self.detailList.setList(certs)

	def __crtDelete(self):
		if self.detailList.getSelectedIndex() >= 0 and self.detailList.getCurrent() != None:
			cert = self.detailList.getCurrent()[0]
			print "[BrowserMenu].__crtDelete, host=%s,SHA1 fingerprint=%s" %(cert.host,cert.cert.digest("sha1"))
			text = _("Do you really want to remove the following certificate from the list of trusted certificates?\n\nHostname: %s\nSHA1-Fingerprint: %s") %(cert.host, cert.cert.digest("sha1"))
			dlg = self.session.openWithCallback( self.__crtDeleteCB, MessageBox, text, type = MessageBox.TYPE_YESNO )
			dlg.setTitle(_("Remove trusted certificate?"))

	def __crtDeleteCB(self, confirmed):
		print "[BrowserMenu].__crtDeleteCB"
		if confirmed:
			cert = self.detailList.getCurrent()[0]
			self.__db.deleteCert(cert)
			self.__crtReload()

	def __crtDetails(self):
		print "[BrowserMenu].__crtDetails"
		if self.detailList.getSelectedIndex() >= 0 and self.detailList.getCurrent() != None:
			cert = self.detailList.getCurrent()[0]

			text = _("Issued for:")
			for item in cert.cert.get_subject().get_components():
				text += "\n%s : %s" %(item[0], item[1])
			text += _("\n\nIssued from:")
			for item in cert.cert.get_issuer().get_components():
				text += "\n%s : %s" %(item[0], item[1])

			text += _("\n\nValidity:\n")
			text += _("From: %s\n") %cert.notBefore()
			text += _("Until: %s\n") %cert.notAfter()
			text += _("Expired: %s\n") %(_("Yes") if cert.cert.has_expired() else _("No"))

			dlg = self.session.open(MessageBox, text, type = MessageBox.TYPE_INFO)
			dlg.setTitle(_("Certificate Details (%s)") %cert.host)

	def __ckReload(self):
		print "[BrowserMenu].__ckReload"
		self.__ckList = self.__db.getCookies()
		self.__ckBuildList()

	def __ckBuildList(self):
		print "[BrowserMenu].__ckBuildList"
		self.detailList.l.setFont(0, gFont("Regular", 22))
		self.detailList.l.setFont(1, gFont("Regular", 16))
		self.detailList.l.setFont(2, gFont("Regular", 13))
		self.detailList.l.setItemHeight(75)
		cookies = []
		for c in self.__ckList:
			cookies.append(self.__ckGetEntryComponent(c))
		self.detailList.setList(cookies)

	def __ckGetEntryComponent(self, cookie):
		w = self.width - 225
		res = [ cookie ]
		date = strftime("%Y-%m-%d", localtime(cookie.expires))
		time = strftime("%H:%M:%S", localtime(cookie.expires))
		res.append(MultiContentEntryText(pos = (10, 1), size = (150, 25), font = 1, flags = RT_VALIGN_CENTER, text = date))
		res.append(MultiContentEntryText(pos = (10, 28), size = (150, 25), font = 1, flags = RT_VALIGN_CENTER, text = time))
		res.append(MultiContentEntryText(pos = (180, 1), size = (w-200, 25), font = 0, flags = RT_VALIGN_CENTER, text = cookie.domain))
		res.append(MultiContentEntryText(pos = (180, 28), size = (w-200, 25), font = 1, flags = RT_VALIGN_CENTER, text = cookie.path))
		res.append(MultiContentEntryText(pos = (10, 60), size = (w-20, 15), font = 2, flags = RT_VALIGN_CENTER, text = cookie.raw))
		return res

	def __ckDelete(self):
		if self.detailList.getSelectedIndex() >= 0 and self.detailList.getCurrent() != None:
			cookie = self.detailList.getCurrent()[0]
			text = _("Do you really want to delete the following cookie?\nDomain: %s\nPath: %s\nKey: %s\nRaw-Content:\n%s") %(cookie.domain, cookie.path, cookie.key, cookie.raw)
			dlg = self.session.openWithCallback( self.__ckDeleteCB, MessageBox, text, type = MessageBox.TYPE_YESNO )
			dlg.setTitle(_("Delete Cookie?"))

	def __ckDeleteCB(self, confirmed):
		print "[BrowserMenu].__ckDeleteCB"
		if confirmed:
			self.__db.deleteCookie(self.detailList.getCurrent()[0])
			self.__ckReload()
			action = [self.ACTION_COOKIES,True]
			if not action in self.__actions:
				self.__actions.append(action)

	def __ckDeleteAll(self):
		if self.detailList.getSelectedIndex() >= 0 and self.detailList.getCurrent() != None:
			cookie = self.detailList.getCurrent()[0]
			text = _("Do you really want to delete ALL cookies?")
			dlg = self.session.openWithCallback( self.__ckDeleteAllCB, MessageBox, text, type = MessageBox.TYPE_YESNO )
			dlg.setTitle(_("Delete Cookie?"))

	def __ckDeleteAllCB(self, confirmed):
		print "[BrowserMenu].__ckDeleteCB"
		if confirmed:
			self.__db.deleteAllCookies()
			self.__ckReload()
			action = [self.ACTION_COOKIES,True]
			if not action in self.__actions:
				self.__actions.append(action)
