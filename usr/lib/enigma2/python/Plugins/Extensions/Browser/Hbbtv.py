from enigma import eHbbtv, eServiceReference, ePoint, eSize, getDesktop
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.VideoWindow import VideoWindow
from Components.PluginComponent import plugins

from Browser import Browser
from MoviePlayer import MoviePlayer

class HbbtvVideoOverlay(Screen):
	skin = """
		<screen name="HbbtvVideoOverlay" flags="wfNoBorder" position="0,0" size="1280,720" title="HbbtvVideoOverlay" >
			<widget name="Video" position="0,0" zPosition="9999" size="0,0" backgroundColor="transparent"/>
		</screen>
	"""

	def __init__(self, session, point = ePoint(0,0), size = eSize(0,0) ):
		Screen.__init__(self, session)
		desktopSize = getDesktop(0).size()
		self.__video = VideoWindow(decoder = 0, fb_width=1280, fb_height=720)
		self["Video"] = self.__video
		self.__point = point
		self.__size = size
		self.onFirstExecBegin.append(self.__onFirstExecBegin)

	def __onFirstExecBegin(self):
		self.setRect(self.__point, self.__size)

	def setRect(self, point, size):
		self.__video.move(point)
		self.__video.resize(size)
		self.__point = point
		self.__size = size

class Hbbtv(object):
	instance = None
	redButtonDescriptor = None
	textDescriptor = None

	def __init__(self, session):
		assert Hbbtv.instance is None, "Hbbtv is a singleton class and may only be initialized once!"
		Hbbtv.instance = self
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

	def connectCallbacks(self):
		print "[Hbbtv] connecting callbacks"
		self.eHbbtv.playServiceRequest.get().append(self.zap)
		self.eHbbtv.playStreamRequest.get().append(self.playStream)
		self.eHbbtv.pauseStreamRequest.get().append(self.pauseStream)
		self.eHbbtv.stopStreamRequest.get().append(self.stopStream)
		self.eHbbtv.nextServiceRequest.get().append(self.nextService)
		self.eHbbtv.prevServiceRequest.get().append(self.prevService)
		#AIT
		self.eHbbtv.setAitSignalsEnabled(True);
		self.eHbbtv.redButtonAppplicationReady.get().append(self.redButtonAppplicationReady)
		self.eHbbtv.textApplicationReady.get().append(self.textApplicationReady)
		self.eHbbtv.aitInvalidated.get().append(self.aitInvalidated)
		self.eHbbtv.createApplicationRequest.get().append(self.startApplicationByUri)
		self.eHbbtv.show.get().append(self.showBrowser)
		self.eHbbtv.hide.get().append(self.hideBrowser)

	def disconnectCallbacks(self):
		print "[Hbbtv] disconnecting callbacks"
		self.eHbbtv.playServiceRequest.get().remove(self.zap)
		self.eHbbtv.playStreamRequest.get().remove(self.playStream)
		self.eHbbtv.pauseStreamRequest.get().remove(self.pauseStream)
		self.eHbbtv.stopStreamRequest.get().remove(self.stopStream)
		self.eHbbtv.nextServiceRequest.get().remove(self.nextService)
		self.eHbbtv.prevServiceRequest.get().remove(self.prevService)
		#AIT
		self.eHbbtv.redButtonAppplicationReady.get().remove(self.redButtonAppplicationReady)
		self.eHbbtv.textApplicationReady.get().remove(self.textApplicationReady)
		self.eHbbtv.aitInvalidated.get().remove(self.aitInvalidated)
		self.eHbbtv.createApplicationRequest.get().remove(self.startApplicationByUri)
		self.eHbbtv.show.get().remove(self.showBrowser)
		self.eHbbtv.hide.get().remove(self.hideBrowser)

	def showBrowser(self):
		if self.__browser:
			pass
			#self.__browser.show()

	def hideBrowser(self):
		if self.__browser:
			pass
			#self.__browser.hide()

	def unsetBrowser(self):
		self.__browser = None

	def zap(self, sref):
		self.session.nav.playService(eServiceReference(sref))

	def isStreaming(self):
		if self.__currentStreamRef:
			return True
		return False

	def playStream(self, sref):
		self.__currentStreamRef = eServiceReference(sref)
		self.session.open(MoviePlayer, self.__currentStreamRef, stopCallback=self.actionStop, pauseCallback=self.actionPause)
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

	def nextService(self):
		from Screens.InfoBar import InfoBar
		ib = InfoBar.instance
		ib.zapDown()

	def prevService(self):
		from Screens.InfoBar import InfoBar
		ib = InfoBar.instance
		ib.zapUp()

	def redButtonAppplicationReady(self, appid):
		print "[Hbbtv].readButtonApplicationReady, appid=%s" %(appid)
		self._redButtonApp = appid
		app = self.eHbbtv.getApplication(self._redButtonApp)
		Hbbtv.redButtonDescriptor.name = app.getName()
		plugins.addPlugin(Hbbtv.redButtonDescriptor)
	
	def textApplicationReady(self, appid):
		print "[Hbbtv].textApplicationReady, appid=%s" %(appid)
		self._textApp = appid
		app = self.eHbbtv.getApplication(self._textApp)
		Hbbtv.textDescriptor.name = app.getName()
		plugins.addPlugin(Hbbtv.textDescriptor)

	def aitInvalidated(self):
		print "[Hbbtv].aitInvalidated"
		self._redButtonApp = None
		self._textApp = None
		if plugins.getPlugins(PluginDescriptor.WHERE_HBBTV).count(Hbbtv.redButtonDescriptor) > 0:
			plugins.removePlugin(Hbbtv.redButtonDescriptor)
		if plugins.getPlugins(PluginDescriptor.WHERE_TELETEXT).count(Hbbtv.textDescriptor) > 0:
			plugins.removePlugin(Hbbtv.textDescriptor)

	def isRedButtonAvailable(self):
		return self._redButtonApp != None

	def isTextAvailable(self):
		return self._textApp != None

	def showRedButtonApplication(self):
		print "[Hbbtv].Hbbtv.showRedButtonApplication"
		if self._redButtonApp is not None:
			self.startApplicationById(self._redButtonApp)

	def showTextApplication(self):
		print "[Hbbtv].Hbbtv.showTextApplication"
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
			self.__browser.onClose.append(self.unsetBrowser)

	def startApplicationById(self, appid):
		uri = self.eHbbtv.resolveApplicationLocator("dvb://current.ait/%s" %appid)
		if uri != "":
			self.startApplicationByUri(uri)

	def setVideoWindow(self, x, y, w, h):
		print "[Hbbtv].setVideoWindow x=%s, y=%s, w=%s, h=%s" %(x, y, w, h)
		if w < 1280 and h < 720:
			p = ePoint(x, y)
			s = eSize(w, h)
			if not self.__overlay:
				self.__overlay = self.session.instantiateDialog(HbbtvVideoOverlay, point = p, size = s)
			else:
				self.__overlay.setRect(p, s)
			self.__overlay.show()
		else:
			if self.__overlay:
				self.__overlay.hide()

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
		hbbtv = Hbbtv.instance
		if appid is not None and hbbtv is not None:
			hbbtv.startApplicationById(appid)

	@staticmethod
	def redButton(**kwargs):
		hbbtv = Hbbtv.instance
		if hbbtv is not None:
			if hbbtv.isRedButtonAvailable():
				hbbtv.showRedButtonApplication()

	@staticmethod
	def textButton(**kwargs):
		hbbtv = Hbbtv.instance
		if hbbtv is not None:
			if hbbtv.isTextAvailable():
				hbbtv.showTextApplication()

Hbbtv.redButtonDescriptor = PluginDescriptor(name="HbbTV", description=_("Show the current HbbTV Startapplication"), where=[PluginDescriptor.WHERE_HBBTV,], fnc=Hbbtv.redButton, needsRestart=False)
Hbbtv.textDescriptor = PluginDescriptor(name="HbbTV", description=_("Show the current HbbTV Teletext Application"), where=[PluginDescriptor.WHERE_TELETEXT,], fnc=Hbbtv.textButton, needsRestart=False)

def start(session, **kwargs):
	Hbbtv(session)

def autostart(reason, **kwargs):
	if reason == 1:
		if Hbbtv.instance is not None:
			Hbbtv.instance.disconnectCallbacks()
