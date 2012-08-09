from enigma import eHbbtv, eServiceReference, ePoint, eSize, getDesktop
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigSelection
from Components.PluginComponent import plugins
from Components.VideoWindow import VideoWindow

from Plugins.Extensions.Browser.Browser import Browser
from Plugins.Extensions.Browser.MoviePlayer import MoviePlayer

config.plugins.hbbtv = ConfigSubsection()
config.plugins.hbbtv.enabled = ConfigEnableDisable(default=True)
config.plugins.hbbtv.testsuite = ConfigSelection([("mainmenu", _("Menu")), ("extensions", _("Extensions")), ("plugins", _("Plugins Browser")), ("disabled", _("Disabled"))], default="disabled")
config.plugins.hbbtv.text = ConfigEnableDisable(default=True)

class HbbTVVideoOverlay(Screen):
	skin = """
		<screen name="HbbTVVideoOverlay" flags="wfNoBorder" zPosition="9999" position="0,0" size="1280,720" title="HbbTVVideoOverlay" backgroundColor="transparent">
			<widget name="video" position="0,0" zPosition="9999" size="0,0" backgroundColor="transparent"/>
		</screen>
	"""

	def __init__(self, session, point = ePoint(0,0), size = eSize(0,0) ):
		Screen.__init__(self, session)
		desktopSize = getDesktop(0).size()
		self["video"] = VideoWindow(decoder = 0, fb_width=desktopSize.width(), fb_height=desktopSize.height())
		self.__point = point
		self.__size = size
		self.__isFullscreen = False

	def setRect(self, point, size):
		self.instance.move(point)
		self.instance.resize(size)
		self["video"].instance.resize(size)
		self.__point = point
		self.__size = size

	def toggleFullscreen(self):
		if self.__isFullscreen:
			self.setRect(self.__point, self.__size)
			self.__isFullscreen = False
		else:
			point = ePoint(0,0)
			size = getDesktop(0).size()

			self.instance.move(point)
			self.instance.resize(size)
			self["video"].instance.resize(size)
			self.__isFullscreen = True

class HbbTV(object):
	instance = None
	redButtonDescriptor = None
	textDescriptor = None

	def __init__(self, session):
		assert HbbTV.instance is None, "HbbTV is a singleton class and may only be initialized once!"
		HbbTV.instance = self
		from Screens.InfoBar import InfoBar

		self.session = session
		self._redButtonApp = None
		self._textApp = None
		self.eHbbtv = eHbbtv.getInstance()
		self.connectCallbacks()

		InfoBar.instance.onServiceListRootChanged.append(self.setCurrentBouquet)
		InfoBar.instance.addExtension((self._getExtensionMenuText, self._showApplicationList, lambda: True), key = "red")

		self.__overlay = None
		self.__currentStreamRef = None
		self.__browser = None
		self.__fullscreen = True
		self.__lastService = None

	def connectCallbacks(self):
		print "[HbbTV] connecting callbacks"
		self.eHbbtv.playServiceRequest.get().append(self.zap)
		self.eHbbtv.playStreamRequest.get().append(self.playStream)
		self.eHbbtv.pauseStreamRequest.get().append(self.pauseStream)
		self.eHbbtv.stopStreamRequest.get().append(self.stopStream)
		self.eHbbtv.nextServiceRequest.get().append(self.nextService)
		self.eHbbtv.prevServiceRequest.get().append(self.prevService)
		self.eHbbtv.setVideoWindowRequest.get().append(self.setVideoWindow)
		#AIT
		self.eHbbtv.setAitSignalsEnabled(True);
		self.eHbbtv.redButtonAppplicationReady.get().append(self.redButtonAppplicationReady)
		self.eHbbtv.textApplicationReady.get().append(self.textApplicationReady)
		self.eHbbtv.aitInvalidated.get().append(self.aitInvalidated)
		self.eHbbtv.createApplicationRequest.get().append(self.startApplicationByUri)
		self.eHbbtv.show.get().append(self.showBrowser)
		self.eHbbtv.hide.get().append(self.hideBrowser)

	def disconnectCallbacks(self):
		print "[HbbTV] disconnecting callbacks"
		self.eHbbtv.playServiceRequest.get().remove(self.zap)
		self.eHbbtv.playStreamRequest.get().remove(self.playStream)
		self.eHbbtv.pauseStreamRequest.get().remove(self.pauseStream)
		self.eHbbtv.stopStreamRequest.get().remove(self.stopStream)
		self.eHbbtv.nextServiceRequest.get().remove(self.nextService)
		self.eHbbtv.prevServiceRequest.get().remove(self.prevService)
		self.eHbbtv.setVideoWindowRequest.get().remove(self.setVideoWindow)
		#AIT
		self.eHbbtv.redButtonAppplicationReady.get().remove(self.redButtonAppplicationReady)
		self.eHbbtv.textApplicationReady.get().remove(self.textApplicationReady)
		self.eHbbtv.aitInvalidated.get().remove(self.aitInvalidated)
		self.eHbbtv.createApplicationRequest.get().remove(self.startApplicationByUri)
		self.eHbbtv.show.get().remove(self.showBrowser)
		self.eHbbtv.hide.get().remove(self.hideBrowser)

	def setVideoWindow(self, x, y, w, h):
		print "[Hbbtv].setVideoWindow x=%s, y=%s, w=%s, h=%s" %(x, y, w, h)
		if w < 1280 or h < 720:
			p = ePoint(x+2, y+2)
			s = eSize(w-4, h-4)
			if self.__overlay == None:
				self.__overlay = self.session.instantiateDialog(HbbTVVideoOverlay, point = p, size = s)
			self.__overlay.setRect(p, s)
			self.__overlay.show()
			self.__fullscreen = False
		else:
			self.__fullscreen = True
			self._unsetVideoWindow()

	def _unsetVideoWindow(self):
		if self.__overlay != None:
			self.session.deleteDialog(self.__overlay)
			self.__overlay = None

	def _toggleVideoFullscreen(self):
		if self.__overlay:
			self.__overlay.toggleFullscreen()
			return True
		return False

	def _onUrlChanged(self, url):
		self._unsetVideoWindow()

	def showBrowser(self):
		if self.__browser:
			pass
			#self.__browser.show()

	def hideBrowser(self):
		if self.__browser:
			pass
			#self.__browser.hide()

	def _unsetBrowser(self):
		self._unsetVideoWindow()
		if self.__lastService:
			self.session.nav.playService(self.__lastService)
		self.__browser = None

	def zap(self, sref):
		self.session.nav.playService(eServiceReference(sref))

	def isStreaming(self):
		if self.__currentStreamRef:
			return True
		return False

	def playStream(self, sref):
		self.__currentStreamRef = eServiceReference(sref)
		if self.__fullscreen:
			self.session.open(MoviePlayer, self.__currentStreamRef, stopCallback=self.actionStop, pauseCallback=self.actionPause)
		else:
			self.__lastService = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.playService(eServiceReference(sref))
			self.__overlay.show()
		self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_PLAYING)

	def actionPause(self):
		if self.__browser:
			self.__browser.actionPause()

	def pauseStream(self):
		if self.isStreaming():
			pauseable = self.session.nav.getCurrentService().pause()
			if pauseable is None:
				self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_PLAYING)
			else:
				self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_PAUSED)

	def actionStop(self):
		if self.__browser:
			self.__browser.actionStop()

	def stopStream(self):
		if self.isStreaming():
			self.__currentStreamRef = None
			if not self.__fullscreen:
				if self.__lastService:
					self.session.nav.playService(self.__lastService)
				else:
					self.session.nav.stopService()

	def nextService(self):
		from Screens.InfoBar import InfoBar
		ib = InfoBar.instance
		ib.zapDown()

	def prevService(self):
		from Screens.InfoBar import InfoBar
		ib = InfoBar.instance
		ib.zapUp()

	def redButtonAppplicationReady(self, appid):
		print "[HbbTV].readButtonApplicationReady, appid=%s" %(appid)
		self._redButtonApp = appid
		app = self.eHbbtv.getApplication(self._redButtonApp)
		HbbTV.redButtonDescriptor.name = app.getName()
		plugins.addPlugin(HbbTV.redButtonDescriptor)
	
	def textApplicationReady(self, appid):
		print "[HbbTV].textApplicationReady, appid=%s" %(appid)
		if config.plugins.hbbtv.text.value:
			self._textApp = appid
			app = self.eHbbtv.getApplication(self._textApp)
			HbbTV.textDescriptor.name = app.getName()
			plugins.addPlugin(HbbTV.textDescriptor)

	def aitInvalidated(self):
		print "[HbbTV].aitInvalidated"
		self._redButtonApp = None
		self._textApp = None
		if plugins.getPlugins(PluginDescriptor.WHERE_HBBTV).count(HbbTV.redButtonDescriptor) > 0:
			plugins.removePlugin(HbbTV.redButtonDescriptor)
		if plugins.getPlugins(PluginDescriptor.WHERE_TELETEXT).count(HbbTV.textDescriptor) > 0:
			plugins.removePlugin(HbbTV.textDescriptor)

	def isRedButtonAvailable(self):
		return self._redButtonApp != None

	def isTextAvailable(self):
		return self._textApp != None

	def showRedButtonApplication(self):
		print "[HbbTV].HbbTV.showRedButtonApplication"
		if self._redButtonApp is not None:
			self.startApplicationById(self._redButtonApp)

	def showTextApplication(self):
		print "[HbbTV].HbbTV.showTextApplication"
		if self._textApp is not None:
			self.startApplicationById(self._textApp)

	def startApplicationByUri(self, uri):
		if uri.startswith("dvb://"):
			uri = self.eHbbtv.resolveApplicationLocator(uri)
		if uri != "":
			if self.__browser is not None:
				if self.__browser.execing:
					self.__browser.setUrl(uri)
					self.__browser.show()
					return

			self.__browser = self.session.open(Browser, True, uri, True)
			self.__browser.onClose.append(self._unsetBrowser)
			self.__browser.onPageLoadFinished.append(self.eHbbtv.pageLoadFinished)
			self.__browser.onActionTv.append(self._toggleVideoFullscreen)
			self.__browser.onUrlChanged.append(self._onUrlChanged)

	def startApplicationById(self, appid):
		uri = self.eHbbtv.resolveApplicationLocator("dvb://current.ait/%s" %appid)
		if uri != "":
			self.startApplicationByUri(uri)

	def setCurrentBouquet(self, ref):
		self.eHbbtv.setServiceList(ref.toString())

	def _getExtensionMenuText(self):
		return _("HbbTV Applications")

	def _showApplicationList(self):
		apps = eHbbtv.getInstance().getApplicationIdsAndName()
		if len(apps) == 0:
			apps.append( (_("No HbbTV Application available"), None) )
		self.session.openWithCallback(self._applicationSelected, ChoiceBox, title=_("Please select an HbbTV application"), list = apps)

	def _applicationSelected(self, appid):
		appid = appid and appid[1]
		hbbtv = HbbTV.instance
		if appid is not None and hbbtv is not None:
			hbbtv.startApplicationById(appid)

	@staticmethod
	def redButton(**kwargs):
		hbbtv = HbbTV.instance
		if hbbtv is not None:
			if hbbtv.isRedButtonAvailable():
				hbbtv.showRedButtonApplication()

	@staticmethod
	def textButton(**kwargs):
		hbbtv = HbbTV.instance
		if hbbtv is not None:
			if hbbtv.isTextAvailable():
				hbbtv.showTextApplication()

HbbTV.redButtonDescriptor = PluginDescriptor(name="HbbTV", description=_("Show the current HbbTV Startapplication"), where=[PluginDescriptor.WHERE_HBBTV,], fnc=HbbTV.redButton, needsRestart=False)
HbbTV.textDescriptor = PluginDescriptor(name="HbbTV", description=_("Show the current HbbTV Teletext Application"), where=[PluginDescriptor.WHERE_TELETEXT,], fnc=HbbTV.textButton, needsRestart=False)

def start(session, **kwargs):
	if HbbTV.instance is None:
		HbbTV(session)

def autostart(reason, **kwargs):
	if reason == 1:
		if HbbTV.instance is not None:
			HbbTV.instance.disconnectCallbacks()
