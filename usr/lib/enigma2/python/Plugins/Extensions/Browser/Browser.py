import _webview
from webview import eWebView
from enigma import eEnv, getDesktop, getPrevAsciiCode, eTimer, eListboxPythonStringContent, eDict, eServiceReference, eRCInput
import enigma
enigma.eWebView = eWebView

from Components.ActionMap import NumberActionMap, ActionMap, HelpableActionMap
from Components.config import config, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo, ConfigDirectory
from Components.Input import Input
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.Sources.Boolean import Boolean
from Components.Sources.CanvasSource import CanvasSource
from Components.Sources.StaticText import StaticText
from Components.Sources.WebNavigation import WebNavigation

from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Tools.BoundFunction import boundFunction

from BrowserDB import BrowserDB, HistoryItem, Certificate, Cookie
from BrowserMenu import BrowserMenu
from Downloads import downloadManager, DownloadJob
from EnhancedInput import EnhancedInput
from MoviePlayer import MoviePlayer

from base64 import b64decode, b64encode
from urllib import unquote as url_unquote, quote_plus as url_quote_plus
from urlparse import urlparse

from Hbbtv import Hbbtv

config.plugins.WebBrowser = ConfigSubsection()
config.plugins.WebBrowser.home = ConfigText(default = "http://box.dream-multimedia-tv.de")
config.plugins.WebBrowser.startPage = ConfigSelection([ ("home", _("Home Page")), ("lastvisted", _("Last visted")) ])
config.plugins.WebBrowser.lastvisited = ConfigText(default = "http://box.dream-multimedia-tv.de")
config.plugins.WebBrowser.searchProvider = ConfigSelection([ ("http://www.google.de/search?q=", _("Google")), ("http://www.bing.com/search?q=", _("Bing")) ])
config.plugins.WebBrowser.fullscreen = ConfigYesNo( default = False )
config.plugins.WebBrowser.scrollOffset = ConfigSelection([ ("75", "75"), ("150", "150"), ("200", "200") ])
config.plugins.WebBrowser.storage = ConfigSubsection()
config.plugins.WebBrowser.storage.enabled = ConfigYesNo( default = False )
config.plugins.WebBrowser.storage.path = ConfigDirectory(default = "/media/hdd/webkit-data")
config.plugins.WebBrowser.downloadpath = ConfigDirectory(default = "/media/hdd")

class Browser(Screen, HelpableScreen):
	def __init__(self, session, fullscreen = False, url = None, isHbbtv = False, isTransparent = False):
		size = getDesktop(0).size()
		width = int(size.width() * 0.9)
		fwidth = int(size.width())
		height = int(size.height() * 0.85)
		fheight = int(size.height())
		Browser.skin = """
			<screen name="Browser" position="center,center" size="%(w)d,%(h)d" title="Web Browser" >
				<widget name="url" position="0,0" zPosition="1" size="%(w)d,25" font="Regular;20" halign="left" valign="bottom" backgroundColor="#000000" transparent="1" />
				<widget name="loading" position="%(loadingX)d,0" zPosition="2" size="150,25" font="Regular;20" halign="right" valign="bottom" backgroundColor="#000000" transparent="1"/>
				<widget name="urlList" position="0,30" zPosition="2" size="%(w)d,150" backgroundColor="#000000" transparent="0" />
				<widget name="text" position="%(textX)d,100" size="350,40" font="Regular;20"  zPosition="2" halign="center" valign="center" backgroundColor="#000000" transparent="0" />
				<widget source="webnavigation" render="WebView" position="0,25" zPosition="1" size="%(w)d,%(mainH)d" />
				<widget source="canvas" render="Canvas" position="0,25" zPosition="2" size="%(w)d,%(mainH)d" backgroundColor="#000000" transparent="1" alphatest="on"/>

				<ePixmap pixmap="skin_default/buttons/button_red_off.png" position="5,%(btnY)d" size="15,16" alphatest="on" />
				<widget source="button_red" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_red.png" position="5,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="red" position="25,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1" />

				<ePixmap pixmap="skin_default/buttons/button_green_off.png" position="195,%(btnY)d" size="15,16" alphatest="on" />
				<widget source="button_green" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_green.png" position="195,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="green" position="215,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<ePixmap pixmap="skin_default/buttons/button_yellow_off.png" position="385,%(btnY)d" size="15,16" alphatest="on" />
				<widget source="button_yellow" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_yellow.png" position="385,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="yellow" position="405,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<ePixmap pixmap="skin_default/buttons/button_blue_off.png" position="585,%(btnY)d" size="15,16" alphatest="on" />
				<widget source="button_blue" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_blue.png" position="585,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="blue" position="605,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<widget name="statuslabel" position="%(notifX)d,%(btnTxtY)d" size="350,20" font="Regular;18"  zPosition="3" halign="right" valign="center" backgroundColor="#000000" transparent="1" />
			</screen>
			""" %{	"w" : width,
					"h" : height,
					"loadingX" : width-150,
					"textX" : (width - 375) / 2,
					"mainH" : height-55,
					"btnY" : height-22,
					"btnTxtY" : height-24,
					"notifX" : width-350
				}

		Browser.skinFullscreen = """
			<screen name="BrowserFullscreen" flags="wfNoBorder" position="center,center" size="%(w)d,%(h)d" title="Web Browser" >
				<widget name="url" position="0,0" zPosition="1" size="%(w)d,25" font="Regular;20" halign="left" valign="bottom" backgroundColor="#000000" transparent="0" />
				<widget name="loading" position="%(loadingX)d,0" zPosition="2" size="150,25" font="Regular;20" halign="left" valign="bottom" backgroundColor="#000000" transparent="0"/>
				<widget name="urlList" position="0,30" zPosition="1" size="%(w)d,150" backgroundColor="#000000" transparent="0" />
				<widget name="text" position="%(textX)d,100" size="350,40" font="Regular;20"  zPosition="2" halign="center" valign="center" backgroundColor="#000000" transparent="0" />
				<widget source="webnavigation" render="WebView" position="0,0" zPosition="0" size="%(w)d,%(h)d" backgroundColor="#00000000"/>
				<widget source="canvas" render="Canvas" position="0,0" zPosition="1" size="%(w)d,%(h)d" backgroundColor="#000000" transparent="1" alphatest="on"/>

				<widget name="buttonBar" position="0,%(btnBarY)d" size="%(w)d,35" zPosition="0" backgroundColor="#000000" transparent="0" />
				<widget source="button_red_off" render="Pixmap" pixmap="skin_default/buttons/button_red_off.png" position="5,%(btnY)d" size="15,16" zPosition="1" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget source="button_red" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_red.png" position="5,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="red" position="25,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<widget source="button_green_off" render="Pixmap" pixmap="skin_default/buttons/button_green_off.png" position="195,%(btnY)d" size="15,16" zPosition="1" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget source="button_green" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_green.png" position="195,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="green" position="215,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<widget source="button_yellow_off" render="Pixmap" pixmap="skin_default/buttons/button_yellow_off.png" position="385,%(btnY)d" size="15,16" zPosition="1" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget source="button_yellow" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_yellow.png" position="385,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="yellow" position="405,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<widget source="button_blue_off" render="Pixmap" pixmap="skin_default/buttons/button_blue_off.png" position="585,%(btnY)d" size="15,16" zPosition="1" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget source="button_blue" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_blue.png" position="585,%(btnY)d" size="15,16" alphatest="on">
					<convert type="ConditionalShowHide" />
				</widget>
				<widget name="blue" position="605,%(btnTxtY)d" size="160,25" zPosition="1" font="Regular;18" halign="left" valign="top" backgroundColor="#000000" transparent="1"/>

				<widget name="statuslabel" position="%(notifX)d,%(btnTxtY)d" size="350,20" zPosition="1" font="Regular;18" halign="right" valign="center" backgroundColor="#000000" transparent="0" />
			</screen>
			""" %{	"w" : fwidth,
					"h" : fheight,
					"loadingX" : fwidth-150,
					"textX" : (fwidth - 375) / 2,
					"mainH" : fheight-55,
					"btnY" : fheight-27,
					"btnTxtY" : fheight-29,
					"btnBarY" : fheight - 35,
					"notifX" : fwidth-350
				}

		self.__isHbbtv = isHbbtv
		if self.__isHbbtv:
			isTransparent = fullscreen = True

		self.__isTransparent = isTransparent
		self.__fullscreen = fullscreen
		if self.__fullscreen:
			Browser.skin = Browser.skinFullscreen

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		if self.__fullscreen:
			self.skinName = "BrowserFullscreen"

		self.__startUrl = url

		self["loading"] = Label("")

		self.urlInput = EnhancedInput()
		self["url"] = self.urlInput

		self.textInput = Input()
		self["text"] = self.textInput
		self.textInput.hide()

		self.statuslabel = Label("")
		self["statuslabel"] = self.statuslabel
		self.statuslabel.hide();

		self.urlInputEnabled = False

		self.webnavigation = WebNavigation()
		self.webnavigation.zoomFactor = 1.0
		self.__onStoragePathChanged()
		self["webnavigation"] = self.webnavigation

		self.__urlList = MenuList([], enableWrapAround = True, content = eListboxPythonStringContent)
		self["urlList"] = self.__urlList

		self.canvas =  CanvasSource()
		self["canvas"] = self.canvas

		self["buttonBar"] = Label("")
		self["button_red_off"] = Boolean(True)
		self["button_green_off"] = Boolean(True)
		self["button_yellow_off"] = Boolean(True)
		self["button_blue_off"] = Boolean(True)
		self["button_red"] = Boolean(False)
		self["button_green"] = Boolean(False)
		self["button_yellow"] = Boolean(True)
		self["button_blue"] = Boolean(True)
		self["red"] = Label("")
		self["green"] = Label("")
		self["yellow"] = Label(_("Navigation"))
		self["blue"] = Label(_("Pagescroll"))

		self.__db = BrowserDB.getInstance()
		self.pageTitle = ""

		self.__urlSuggestionTimer = eTimer()
		self.__urlSuggestionTimer.callback.append(self.__onSuggestionTimeout)
		self.__inputTimer = eTimer()
		self.__inputTimer.callback.append(self.onInputTimer)
		self.__statusTimer = eTimer()
		self.__statusTimer.callback.append(self.__hideStatus)

		self.__scrollMode = False
		self.__zoomMode = False
		self.__isInput = False
		self.__hasSslErrors = False
		self.__handledUnsupportedContent = False
		self.__currentPEM = None
		self.__currentUser = None
		self.__currentPass = None
		self.__currentRealm = None
		self.__keyboardMode = eRCInput.getInstance().getKeyboardMode()

		self.onFirstExecBegin.append(self.__onFirstExecBegin)
		self.onClose.append(self.__onClose)

		self["helpableactions"] = HelpableActionMap(self, "BrowserActions",
		{
			"exit": (self.__actionExit, _("Close the browser")),
			"url": (self.__actionEnterUrl, _("Enter web address or search term")),
			"back": boundFunction(self.__actionNavigate, eWebView.navBack),
			"forward": boundFunction(self.__actionNavigate, eWebView.navForward),
			"left": self.__actionLeft,
			"right": self.__actionRight,
			"up": self.__actionUp,
			"down": self.__actionDown,
			"pageUp": (self.__actionPageUp, _("Page Up / Zoom in")),
			"pageDown": (self.__actionPageDown, _("Page Down / Zoom out")),
			"home" : self.__actionHome,
			"end": boundFunction(self.__actionNavigate, eWebView.navEnd),
			"tab": (boundFunction(self.__actionNavigate, eWebView.navTab), _("Tab")),
			"backspace": (self.__actionBackspace, _("Backspace / Navigate back")),
			"backtab": boundFunction(self.__actionNavigate, eWebView.navBacktab),
			"delete": (self.__actionDelete, _("Delete / Navigate forward")),
			"ascii": self.__actionAscii,
			"text" : (self.__actionVirtualAscii, _("Open Virtual Keyboard")),
			"ok" : self.__actionOk,
			"enter" : self.__actionEnter,
			"menu" : (self.__actionMenu, _("Menu")),
			"fullscreen" : self.__actionFullscreen,
			"play" : self.__actionPlay,
			"pause" : self.actionPause,
			"playpause" : self.__actionPlayPause,
			"stop" : self.actionStop,
		}, -2)

		self["coloractions"] = ActionMap(["ColorActions"],
		{
			"red" : self.__actionRed,
			"green" : self.__actionGreen,
			"yellow" : self.__actionYellow,
			"blue" : self.__actionBlue,
		})

		self["numberactions"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal
		})

		if Hbbtv.instance:
			Hbbtv.instance.setBrowser(self)

	def setBackgroundTransparent(self, enabled):
		self.webnavigation.setBackgroundTransparent(enabled)

	def __onClose(self):
		if Hbbtv.instance:
			Hbbtv.instance.unsetBrowser()

	def __setKeyBoardModeAscii(self):
		eRCInput.getInstance().setKeyboardMode(eRCInput.kmAscii)

	def __unsetKeyBoardModeAscii(self):
		eRCInput.getInstance().setKeyboardMode(self.__keyboardMode)

	def __setStatus(self, text):
		print "[Browser].__setStatus"
		self.statuslabel.setText(text)
		self.statuslabel.show()
		self.__statusTimer.startLongTimer(3)

	def __hideStatus(self):
		self["statuslabel"].hide()
		self.__statusTimer.stop()

	def __actionExit(self):
		self.session.openWithCallback(self.__actionExitCB, MessageBox, _("Do you really want to exit the browser?"), type = MessageBox.TYPE_YESNO)

	def __actionExitCB(self, confirmed):
		if confirmed:
			self.__urlSuggestionTimer.stop()
			self.__inputTimer.stop()
			config.plugins.WebBrowser.lastvisited.value = self.webnavigation.url
			config.plugins.WebBrowser.lastvisited.save()
			self.__persistCookies()
			self.close()

	def __onFirstExecBegin(self):
		#enable/disable transparent background
		self.setBackgroundTransparent(self.__isTransparent)
		#set Accept-Language header to current language
		lang = '-'.join(language.getLanguage().split('_'))
		self.webnavigation.setAcceptLanguage(lang)
		self.__registerCallbacks()
		self.__urlList.hide()
		self.__restoreCookies()
		if self.__fullscreen:
			self.__showHideBars(False)
			self.__showHideButtonBar(False)
		if self.__startUrl is None:
			if config.plugins.WebBrowser.startPage.value == "home":
				self.__actionHome()
			else:
				self.setUrl(config.plugins.WebBrowser.lastvisited.value)
		else:
			self.setUrl(self.__startUrl)

	def __clearCanvas(self):
		size = getDesktop(0).size()
		self.canvas.fill(0, 0, size.width(), size.height(), 0xFF000000)
		self.canvas.flush()

	def __onStoragePathChanged(self):
		if config.plugins.WebBrowser.storage.enabled.value:
			self.webnavigation.enablePersistentStorage(config.plugins.WebBrowser.storage.path.value)

	def __onMicroFocusChanged(self, x, y, w, h, isInput):
		if not self.__isHbbtv:
			if self.__isInput and not isInput:
				self.__unsetKeyBoardModeAscii()

			self.__isInput = isInput
			if self.__isInput:
				self.setKeyboardModeAscii()

			self.__clearCanvas()
			lw = 2  #line width
			y = y
			x = x - lw
			w = w + lw
			blo = ( y + h ) #bottom line offset
			color =0xFF9900 #line color

			self.canvas.fill(x, y, lw, h, color)#left line
			self.canvas.fill(x, blo, w, lw, color)#bottom line
			self.canvas.flush()#Done -> Flush

	def __onSuggestionTimeout(self):
		needle = self.urlInput.getText()
		if needle != "":
			list = self.__db.suggsetUrls(self.urlInput.getText())
			list.insert(0, needle)
			list.insert(1, _("Search for '%s'") %needle)
			self.__urlList.setList(list)
			self.__urlList.moveToIndex(0)
			self.__urlList.show()
		else:
			self.__urlList.hide()

	def __onAuthRequired(self, token, user, password, realm):
		if self.__currentUser != None and self.__currentPassword != None and realm == self.__currentRealm:
			d = eDict()
			d.setString("user", self.__currentUser)
			d.setString("password", self.__currentPassword)
			self.webnavigation.setDict(token, d)
			self.__currentUser = None
			self.__currentPassword = None
			self.__currentRealm = None
		else:
			msgbox = self.session.openWithCallback(self.__onAuthRequiredCB, HttpAuthenticationDialog, user, password, realm)
			msgbox.setTitle(_("Authentication required"))

	def __onAuthRequiredCB(self, dict):
		if dict != None:
			self.__currentUser = dict["user"]
			self.__currentPassword = dict["password"]
			self.__currentRealm = dict["realm"]
			self.setUrl(self.webnavigation.url)

	def __onProxyAuthRequired(self, token, user, password, realm):
		self.onAuthRequired(token, user, password, realm)

	def __onDownloadRequested(self, url):
		print "[Browser].__onDownloadRequested '%s'" %(url)
		filename = url_unquote(url).split("/")[-1]
		localfile = "%s/%s" %(config.plugins.WebBrowser.downloadpath.value, filename)
		downloadManager.AddJob(DownloadJob(url, localfile, filename))
		self.session.open(MessageBox, _("Download started..."), type = MessageBox.TYPE_INFO, timeout = 3)

	def __onUnsupportedContent(self, url, contentType):
		print "[Browser].__onUnsupportedContent 'url=%s; contentType='%s'" %(url, contentType)
		self.__handledUnsupportedContent = True
		if contentType.startswith("video") or contentType.startswith("audio"):
			list = [( _("Download"), ("download", url) ),
					( _("Play"), ("play", url) )]
			self.session.openWithCallback(self.__onUnsupportedContentCB, ChoiceBox, title=_("You've selected a media file what do you want to do?"), list = list)
		else:
			self.__onDownloadRequested(url)

	def __onUnsupportedContentCB(self, answer):
		if answer != None:
			answer = answer and answer[1]
			if answer[0] == "download":
				self.__onDownloadRequested(answer[1])
			else:
				service = eServiceReference(4097,0,answer[1])
				self.session.open(MoviePlayer, service)

	def __actionMenu(self):
		if not self.__isHbbtv:
			self.__urlSuggestionTimer.stop()
			self.__inputTimer.stop()
			self.__urlList.hide()
			self.__persistCookies()
			self.session.openWithCallback(self.__menuCB, BrowserMenu, self.pageTitle, self.webnavigation.url)

	def __menuCB(self, actions = None):
		if actions != None:
			for action in actions:
				if action[0] == BrowserMenu.ACTION_BOOKMARK:
					self.setUrl(action[1])
				elif action[0] == BrowserMenu.ACTION_COOKIES:
					self.__restoreCookies()
				elif action[0] == BrowserMenu.ACTION_STORAGE_PATH:
					self.__onStoragePathChanged()

		if self.skinName == "BrowserFullscreen" and not config.plugins.WebBrowser.fullscreen.value:
			self.__requireRestart()
		if self.skinName != "BrowserFullscreen" and config.plugins.WebBrowser.fullscreen.value:
			self.__requireRestart()

	def __requireRestart(self):
		text = _("Some of the configuration changes require a restart of the Browser.\nDo you want to restart the Browser now?")
		msgbox = self.session.openWithCallback(self.__requireRestartCB, MessageBox, text, type = MessageBox.TYPE_YESNO)
		msgbox.setTitle(_("Restart required"))

	def __requireRestartCB(self, confirmed):
		if confirmed:
			self.close(self.session, True, self.webnavigation.url)

	def __enableUrlInput(self):
		self.urlInputEnabled = True
		self.urlInput.markAll()
		self.__setKeyBoardModeAscii()
		if self.__fullscreen:
			self.__showHideBars()

	def __disableUrlInput(self, hide = True):
		self.urlInputEnabled = False
		self.__urlSuggestionTimer.stop()
		self.__urlList.hide()
		self.urlInput.markNone()
		if not self.__isInput:
			self.__unsetKeyBoardModeAscii()
		if self.__fullscreen and hide:
			self.__showHideBars(False)

	def __showHideButtonBar(self, visible = True):
		self["button_red_off"].setBoolean(visible)
		self["button_green_off"].setBoolean(visible)
		self["button_yellow_off"].setBoolean(visible)
		self["button_blue_off"].setBoolean(visible)
		self["button_red"] = Boolean(False)
		self["button_green"] = Boolean(False)
		self["button_yellow"].setBoolean(visible)
		self["button_blue"].setBoolean(visible)
		if visible:
			self["buttonBar"].show()
			self["red"].show()
			self["green"].show()
			self["yellow"].show()
			self["blue"].show()
		else:
			self["buttonBar"].hide()
			self["red"].hide()
			self["green"].hide()
			self["yellow"].hide()
			self["blue"].hide()

	def __showHideBars(self, visible = True):
		if self.__fullscreen:
			if visible:
				self.urlInput.show()
			else:
				self.urlInput.hide()

			if not self.__isHbbtv:
				self.__showHideButtonBar(visible)

	def __registerCallbacks(self):
		print "[Browser].__registerCallbacks"
		self.webnavigation.onUrlChanged.append(self.__onUrlChanged)
		self.webnavigation.onTitleChanged.append(self.__onTitleChanged)
		self.webnavigation.onLoadProgress.append(self.__onLoadProgress)
		self.webnavigation.onLoadFinished.append(self.__onLoadFinished)
		self.webnavigation.onDownloadRequested.append(self.__onDownloadRequested)
		self.webnavigation.onUnsupportedContent.append(self.__onUnsupportedContent)
		self.webnavigation.onMicroFocusChanged.append(self.__onMicroFocusChanged)
		self.webnavigation.onWindowRequested.append(self.__onWindowRequested)
		self.webnavigation.onSslErrors.append(self.__onSslErrors)
		self.webnavigation.onAuthRequired.append(self.__onAuthRequired)
		self.webnavigation.onProxyAuthRequired.append(self.__onProxyAuthRequired)

	def __actionOk(self):
		if self.textInput.visible:
			self.onInputTimer()
		elif self.urlInputEnabled:
			if self.__urlList.visible and self.__urlList.getSelectedIndex() > 0:
				if self.__urlList.getSelectedIndex() == 1:
					self.__searchUsingCurrentUrlValue()
					self.__disableUrlInput(False)
				else:
					self.urlInput.setText(self.__urlList.getCurrent())
					self.urlInput.end()
					self.__urlList.hide()
			else:
				self.setUrl(self.urlInput.getText())
				self.__isInput = False
				self.__disableUrlInput(False)

		else:
			self.__actionNavigate(eWebView.navOpenLink)

	def __actionEnter(self):
		if self.textInput.visible or self.urlInputEnabled:
			self.__actionOk()
		else:
			self.__actionNavigate(eWebView.navOpenLink)

	def __actionPlay(self):
		self.__actionNavigate(eWebView.navMediaPlay)

	def actionPause(self):
		self.__actionNavigate(eWebView.navMediaPause)

	def __actionPlayPause(self):
		self.__actionNavigate(eWebView.navMediaPlay) #playpause doesn't work anywhere, but play does (HBBTV)

	def actionStop(self):
		self.__actionNavigate(eWebView.navMediaStop)

	def __actionBackspace(self):
		if self.textInput.visible:
			self.restartTimer()
			self.textInput.deleteBackward()
		elif self.urlInputEnabled:
			self.urlInput.deleteBackward()
			self.__onUrlInputChanged()
		else:
			if self.__isInput:
				self.__actionNavigate(eWebView.navBackspace)
			else:
				self.__actionNavigate(eWebView.navBack)

	def __actionDelete(self):
		if self.textInput.visible:
			self.restartTimer()
			self.textInput.delete()
		elif self.urlInputEnabled:
			self.urlInput.delete()
			self.__onUrlInputChanged()
		else:
			if self.__isInput:
				self.__actionNavigate(eWebView.navDelete)
			else:
				self.__actionNavigate(eWebView.navForward)

	def __actionLeft(self):
		if self.urlInputEnabled:
			self.urlInput.left()
		elif self.__scrollMode:
			self.__scroll(0-int(config.plugins.WebBrowser.scrollOffset.value), 0)
		elif self.textInput.visible:
			self.restartTimer()
			self.textInput.left()
		else:
			self.__actionNavigate(eWebView.navLeft)

	def __actionRight(self):
		if self.urlInputEnabled:
			self.urlInput.right()
		elif self.__scrollMode:
			self.__scroll(int(config.plugins.WebBrowser.scrollOffset.value), 0)
		elif self.textInput.visible:
			self.restartTimer()
			self.textInput.right()
		else:
			self.__actionNavigate(eWebView.navRight)

	def __actionUp(self):
		if self.urlInputEnabled:
			if self.__urlList.visible:
				self.__urlList.up()
			#else:
			#	self.urlInput.up()
		elif self.__scrollMode:
			self.__scroll(0, 0-int(config.plugins.WebBrowser.scrollOffset.value))
		elif self.textInput.visible:
			self.restartTimer()
			self.textInput.up()
		else:
			self.__actionNavigate(eWebView.navUp)

	def __actionDown(self):
		if self.urlInputEnabled:
			if self.__urlList.visible:
				self.__urlList.down()
			#else:
			#	self.urlInput.down()
		elif self.__scrollMode:
			self.__scroll(0, int(config.plugins.WebBrowser.scrollOffset.value))
		elif self.textInput.visible:
			self.restartTimer()
			self.textInput.down()
		else:
			self.__actionNavigate(eWebView.navDown)

	def __scroll(self, dx, dy):
		self.webnavigation.scroll(dx, dy)

	def __actionRed(self):
		self.__actionNavigate(eWebView.navRed)

	def __actionGreen(self):
		self.__actionNavigate(eWebView.navGreen)

	def __actionYellow(self):
		if self.__isHbbtv:
			self.__actionNavigate(eWebView.navYellow)
		else:
			self.__scrollMode = not self.__scrollMode
			enDis = _("disabled")
			mode = _("Navigation")
			if self.__scrollMode:
				enDis = _("enabled")
				mode = _("Scrolling")
			text = _("Scroll mode is now %s") %enDis
			self["yellow"].setText(mode)
			self.__setStatus(text)

	def __actionBlue(self):
		if self.__isHbbtv:
			self.__actionNavigate(eWebView.navBlue)
		else:
			self.__zoomMode = not self.__zoomMode
			enDis = _("disabled")
			mode = _("Pagescroll")
			if self.__zoomMode:
				enDis = _("enabled")
				mode = _("Zoom")
			text = _("Zoom mode is now %s") %enDis
			self["blue"].setText(mode)
			self.__setStatus(text)

	def restartTimer(self):
		self.__inputTimer.stop()
		self.__inputTimer.startLongTimer(5)

	def __onUrlChanged(self, url):
		if url != None:
			self.__clearCanvas()
			self.urlInput.setText(url)
			self.urlInput.markNone()
			if self.__fullscreen and not self.__isHbbtv:
				self.__showHideBars()

	def __onTitleChanged(self, title):
		if title != None:
			self.pageTitle = title
			self.setTitle("Web Browser - %s" %self.pageTitle)

	def __onLoadProgress(self, progress):
		print "[Browser].loadProgress %s" %progress
		if(progress < 100):
			self["loading"].show()
			self["loading"].setText(_("Loading... %s%%" %progress))
		else:
			self["loading"].hide()
			self["loading"].setText("")

	def __onLoadFinished(self, val):
		print "[Browser].loadFinished %s" %val
		if val == 1:
			if not self.__isHbbtv:
				self.__db.addToHistory(HistoryItem(title = self.pageTitle, url = self.webnavigation.url));
			if self.__fullscreen:
				self.__showHideBars(False)
		else:
			if not self.__hasSslErrors and not self.__handledUnsupportedContent:
				self.__handledUnsupportedContent = False

	def __searchUsingCurrentUrlValue(self):
		needle = self.urlInput.getText()
		if needle != "":
			needle = needle.replace("http://", "").replace("https://", "").replace("ftp://", "")
			self.__onSearchRequested(needle)

	def __onSearchRequested(self, needle):
		if needle != "" and needle != None:
			needle = url_quote_plus(needle)
			url = "%s%s" %(config.plugins.WebBrowser.searchProvider.value, needle)
			self.setUrl(url)

	def __onWindowRequested(self, url):
		print "[Browser].__onWindowRequested :: '%s'" %url
		self.setUrl(url)

	def __onSslErrors(self, token, errors, pems):
		print "[Browser].__onSslErrors :: 'token='%s', errors='%s'" %(token, errors)
		self.__hasSslErrors = True

		cnt = 0
		perrors = {}
		pems.sort()
		for pem in pems:
			if pem.strip() != "":
				messages = perrors.get(pem, [])
				messages.append(errors[cnt])
				perrors[pem] = messages
				cnt += 1

		for pem, messages in perrors.iteritems():
			cert = Certificate(-1, self.__getCurrentNetloc(), pem)
			checkVal = self.__db.checkCert( cert ) == BrowserDB.CERT_UNKOWN
			if checkVal == BrowserDB.CERT_OK:
				print "[Browser].__onSslErrors :: netloc/pem combination known and trusted!"
				dict = eDict()
				dict.setFlag("ignore")
				self.webnavigation.setDict(token, dict)
			else:
				print "[Browser].__onSslErrors :: netloc/pem combination NOT known and/or trusted!"
				self.__currentPEM = pem

				errorstr = ""
				for m in messages:
					errorstr = "%s\n%s" %(m, errorstr)

				text = ""
				if checkVal == BrowserDB.CERT_UNKOWN:
					text = _("A certificate for the desired secure connection has the following errors:\n%s\nDo you want to add an exception for this certificate and accept connections to this host anyways?") %errorstr
				elif checkVal == BrowserDB.CERT_CHANGED:
					text = _("ATTENTION!\nPotential security breach detected!\nA certificate for the desired secure connection has CHANGED!\nIn addition it has the following errors:\n%s\nDo you want to add an exception for this certificate and accept connections to this host anyways?") %errorstr
				msgbox = self.session.openWithCallback( self.__onSslErrorCB, MessageBox, text, type = MessageBox.TYPE_YESNO)
				msgbox.setTitle(_("Certificate errors!"))

	def __onSslErrorCB(self, confirmed):
		self.__hasSslErrors = False
		if confirmed:
			print "[Browser].__onSslErrorCB :: loc='%s', PEM='%s'" %(self.__getCurrentNetloc(), self.__currentPEM)
			self.__db.addCert( Certificate(-1, self.__getCurrentNetloc(), self.__currentPEM) )
			self.setUrl(self.webnavigation.url)

	def __getCurrentNetloc(self):
		return self.__getNetloc(self.webnavigation.url)

	def __getNetloc(self, url):
		return urlparse(url).netloc

	def __actionHome(self):
		self.setUrl(config.plugins.WebBrowser.home.value)

	def __actionEnterUrl(self):
		if self.urlInputEnabled:
			self.__disableUrlInput()
		else:
			self.__enableUrlInput()

	def setUrl(self, url):
		if url != None:
			if url.find("://") == -1:
				url = "http://%s" %url
			if url:
				self.webnavigation.url = url

	def __actionAscii(self):
		if self.urlInputEnabled:
			self.urlInput.handleAscii(getPrevAsciiCode())
			self.__onUrlInputChanged()
		elif self.__isInput:
			self.webnavigation.changed(WebNavigation.COMMAND_ASCII_INPUT, getPrevAsciiCode())
		else:
			self.__actionNavigateNumber(chr(getPrevAsciiCode()))

	def __actionNavigateNumber(self, char):
		print "[Browser].__actionNavigateNumber %s" %char
		nav = { '0' : eWebView.nav0,
				'1' : eWebView.nav1,
				'2' : eWebView.nav2,
				'3' : eWebView.nav3,
				'4' : eWebView.nav4,
				'5' : eWebView.nav5,
				'6' : eWebView.nav6,
				'7' : eWebView.nav7,
				'8' : eWebView.nav8,
				'9' : eWebView.nav9,
				}

		action = nav.get(str(char), None)
		if action != None:
			self.__actionNavigate(action)

	def __actionVirtualAscii(self):
		self.session.openWithCallback(self.sendTextAsAscii, VirtualKeyBoard, title="Browser Input")

	def __actionPageUp(self):
		if self.__zoomMode:
			self.webnavigation.zoomFactor += 0.1
		else:
			self.__actionNavigate(eWebView.navPageUp)

	def __actionPageDown(self):
		if self.__zoomMode:
			self.webnavigation.zoomFactor -= 0.1
		else:
			self.__actionNavigate(eWebView.navPageDown)

	def sendTextAsAscii(self, text):
		if text != None:
			for c in text:
				self.webnavigation.changed(WebNavigation.COMMAND_ASCII_INPUT, ord(c))

	def __actionNavigate(self, param):
		if not self.urlInputEnabled and not self.textInput.visible:
			self.webnavigation.changed(WebNavigation.COMMAND_NAVIGATE, param)

	def keyNumberGlobal(self, number):
		if self.urlInputEnabled:
			self.urlInput.number(number)
			self.__onUrlInputChanged()
		elif self.__isInput:
			self.textInput.show()
			self.restartTimer()
			self.textInput.number(number)
		else:
			self.__actionNavigateNumber(number)

	def __onUrlInputChanged(self):
		if not self.__urlSuggestionTimer.isActive():
			self.__urlSuggestionTimer.startLongTimer(1)

	def onInputTimer(self):
		self.__inputTimer.stop()
		self.textInput.hide()
		text = self.textInput.getText()
		self.textInput.setText("")
		if text != "" and text != None:
			self.sendTextAsAscii(text)

	def __actionFullscreen(self):
		self.webnavigation.size = (self.width, self.height)
		self.webnavigation.position = (0, 0)

	def __restoreCookies(self):
		cookies = self.__db.getCookies()
		print "[Browser].__restoreCookies ::: restoring %s cookies" %len(cookies)
		rawCookies = []
		for cookie in cookies:
			rawCookies.append( b64encode(cookie.raw) )
		self.webnavigation.cookies = ','.join(rawCookies)

	def __persistCookies(self):
		rawCookies = self.webnavigation.cookies
		if rawCookies.strip() != "":
			rawCookies = rawCookies.split(",")
			cookies = []
			cookie = None
			for rawCookie in rawCookies:
				cookie = Cookie.fromRawString(b64decode(rawCookie))
				if cookie != None:
					cookies.append( cookie )
			print "[Browser].__persistCookies ::: persisting %s cookies" %len(cookies)
			self.__db.persistCookies(cookies)
		else:
			print "[Browser].__persistCookies ::: NO cookies to be persisted"

class HttpAuthenticationDialog(Screen):
	skin = """
		<screen position="center,center" size="600,120"  title="Authentication required">
			<widget source="realm" render="Label" position="5,0" zPosition="1" size="590,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget source="userTitle" render="Label" position="5,30" zPosition="1" size="120,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget source="passwordTitle" render="Label" position="5,70" zPosition="1" size="120,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget name="user" position="130,30" size="420,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="#000000" transparent="1"/>
			<widget name="password" position="130,70" size="420,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="#000000" transparent="1"/>
			<widget name="userActive" position="560,30" zPosition="1" size="40,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget name="passwordActive" position="560,70" zPosition="1" size="40,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
		</screen>"""

	def __init__(self, session, user = "", password = "", realm = ""):
		Screen.__init__(self, session)

		self.user = user
		self.password = password
		self.realm = realm

		self["realm"] = StaticText(self.realm)
		self["userTitle"] = StaticText(_("User:"))
		self["passwordTitle"] = StaticText(_("Password:"))

		self["userActive"] = Label("<")
		self["passwordActive"] = Label("<")

		self.inputUser = EnhancedInput( self.user )
		self["user"] = self.inputUser
		self.inputPassword = EnhancedInput( self.password, type = Input.PIN )
		self["password"] = self.inputPassword

		self["actions"] = ActionMap(["SimpleEditorActions"],
		{
			"ok" : self.__ok,
			"exit" : self.__cancel,
			"up" : self.__up,
			"down" : self.__down,
			"left" : self.__left,
			"right" : self.__right,
			"ascii" : self.__ascii,
			"delete" : self.__delete,
			"backspace" : self.__backspace
		})
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
		})

		self.userFocus = False
		self.onShow.append(self.__toggleInput)

	def __ok(self):
		user = self.inputUser.getText()
		password = self.inputPassword.getText()
		if user != None and password != None and user != "":
			self.close( { "user" : user, "password" : password, "realm" : self.realm} )
		else:
			self.close(None)

	def __cancel(self):
		self.close(None)

	def __up(self):
		self.__toggleInput()

	def __down(self):
		self.__toggleInput()

	def __toggleInput(self):
		self.userFocus = not self.userFocus
		if self.userFocus:
			self["userActive"].show()
			self.inputUser.end()
			self["passwordActive"].hide()
			self.inputPassword.markNone()
		else:
			self["userActive"].hide()
			self.inputUser.markNone()
			self["passwordActive"].show()
			self.inputPassword.end()

	def __left(self):
		if self.userFocus:
			self.inputUser.left()
		else:
			self.inputPassword.left()

	def __right(self):
		if self.userFocus:
			self.inputUser.right()
		else:
			self.inputPassword.right()

	def __delete(self):
		if self.userFocus:
			self.inputUser.delete()
		else:
			self.inputPassword.delete()

	def __backspace(self):
		if self.userFocus:
			self.inputUser.deleteBackward()
		else:
			self.inputPassword.deleteBackward()

	def __keyNumberGlobal(self, number):
		if self.userFocus:
			self.inputUser.number(number)
		else:
			self.inputPassword.number(number)

	def __ascii(self):
		if self.userFocus:
			self.inputUser.handleAscii(getPrevAsciiCode())
		else:
			self.inputPassword.handleAscii(getPrevAsciiCode())
