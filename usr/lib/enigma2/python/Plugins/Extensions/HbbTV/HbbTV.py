from enigma import eHbbtv, eServiceReference, ePoint, eSize, eRect, getDesktop, eTimer, eDVBVolumecontrol
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.LocationBox import MovieLocationBox
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigSelection
from Components.PluginComponent import plugins
from Components.UsageConfig import preferredPath
from Components.VideoWindow import VideoWindow

from Plugins.Extensions.Browser.Browser import Browser
from Plugins.Extensions.Browser.Downloads import downloadManager, DownloadJob

config.plugins.hbbtv = ConfigSubsection()
config.plugins.hbbtv.enabled = ConfigEnableDisable(default=True)
config.plugins.hbbtv.testsuite = ConfigSelection([("mainmenu", _("Menu")), ("extensions", _("Extensions")), ("plugins", _("Plugin Browser")), ("disabled", _("Disabled"))], default="disabled")
config.plugins.hbbtv.text = ConfigEnableDisable(default=True)

from datetime import datetime
from urlparse import urlparse

class HbbTVVideoWindow(Screen):
	skin = """
		<screen name="HbbTVVideoWindow" flags="wfNoBorder" zPosition="-1" position="0,0" size="1280,720" title="HbbTVVideoWindow" backgroundColor="transparent">
			<widget name="video" position="0,0" zPosition="0" size="0,0" backgroundColor="transparent"/>
		</screen>
	"""

	def __init__(self, session, point=ePoint(0, 0), size=eSize(0, 0)):
		Screen.__init__(self, session)
		desktopSize = getDesktop(0).size()
		self["video"] = VideoWindow(decoder=0, fb_width=desktopSize.width(), fb_height=desktopSize.height())

		self.__point = point
		self.__size = size
		self.__retainedPoint = point
		self.__retainedSize = size

		self.__isFullscreen = False
		self.onLayoutFinish.append(self._onLayoutFinished)

	def _onLayoutFinished(self):
		self.setRect(self.__point, self.__size, force=True)

	def setRect(self, point, size, retain=True, force=False):
		if point.x() != self.__point.x() or point.y() != self.__point.y() or force:
			self.instance.move(point)
			self.__point = point
		if size.width() != self.__size.width() or size.height() != self.__size.height() or force:
			self.instance.resize(size)
			self.__size = size
			self["video"].instance.resize(size)

		if retain:
			self.__retainedPoint = point
			self.__retainedSize = size

	def toggleFullscreen(self):
		if self.__isFullscreen:
			self.setRect(self.__retainedPoint, self.__retainedSize)
			self.__isFullscreen = False
		else:
			point = ePoint(0, 0)
			size = getDesktop(0).size()
			self.setRect(point, size, retain=False)
			self.__isFullscreen = True
		return self.__isFullscreen

class HbbTV(object):
	instance = None
	redButtonDescriptor = None
	textDescriptor = None

	def __init__(self, session):
		assert HbbTV.instance is None, "HbbTV is a singleton class and may only be initialized once!"
		HbbTV.instance = self

		self.session = session
		self._redButtonApp = None
		self._textApp = None
		self.eHbbtv = eHbbtv.getInstance()
		self.connectCallbacks()

		self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_STOPPED)

		from Screens.InfoBar import InfoBar
		InfoBar.instance.onServiceListRootChanged.append(self.setCurrentBouquet)
		InfoBar.instance.addExtension((self._getExtensionMenuText, self._showApplicationList, lambda: True), key="red")

		self.onClose = []

		self.__videoWindow = None
		self.__currentStreamRef = None
		self.__browser = None
		self.__lastService = None
		self.__restoreTimer = eTimer()
		self.__restoreTimer_conn = self.__restoreTimer.timeout.connect(self._restoreLastService)

	def connectCallbacks(self):
		print "[HbbTV] connecting callbacks"
		self.conns = [ ]
		self.conns.append(self.eHbbtv.playServiceRequest.connect(self.zap))
		self.conns.append(self.eHbbtv.playStreamRequest.connect(self.playStream))
		self.conns.append(self.eHbbtv.pauseStreamRequest.connect(self.pauseStream))
		self.conns.append(self.eHbbtv.seekStreamRequest.connect(self.seekStream))
		self.conns.append(self.eHbbtv.stopStreamRequest.connect(self.stopStream))
		self.conns.append(self.eHbbtv.nextServiceRequest.connect(self.nextService))
		self.conns.append(self.eHbbtv.prevServiceRequest.connect(self.prevService))
		self.conns.append(self.eHbbtv.setVolumeRequest.connect(self.setVolume))
		self.conns.append(self.eHbbtv.setVideoWindowRequest.connect(self.setVideoWindow))
		#AIT
		self.eHbbtv.setAitSignalsEnabled(True);
		self.conns.append(self.eHbbtv.redButtonAppplicationReady.connect(self.redButtonAppplicationReady))
		self.conns.append(self.eHbbtv.textApplicationReady.connect(self.textApplicationReady))
		self.conns.append(self.eHbbtv.aitInvalidated.connect(self.aitInvalidated))
		self.conns.append(self.eHbbtv.createApplicationRequest.connect(self.startApplicationByUri))
		self.conns.append(self.eHbbtv.show.connect(self.showBrowser))
		self.conns.append(self.eHbbtv.hide.connect(self.hideBrowser))

	def disconnectCallbacks(self):
		print "[HbbTV] disconnecting callbacks"
		self.conns = None
		for fnc in self.onClose:
			fnc()

	def _showVideoIfAvail(self):
		if self.__videoWindow != None:
			self.__videoWindow.show()

	def _hideVideoIfAvail(self):
		if self.__videoWindow != None:
			self.__videoWindow.hide()

	def _adjustLimits(self, var, lower, upper):
		var = int(var)
		var = max(var, lower)
		var = min(var, upper)
		return var

	def setVideoWindow(self, x, y, w, h):
		w = self._adjustLimits(w, 128, 1280)
		h = self._adjustLimits(h, 72, 720)
		x = self._adjustLimits(x, 0, 1280)
		y = self._adjustLimits(y, 0, 720)

		print "[Hbbtv].setVideoWindow x=%s, y=%s, w=%s, h=%s" % (x, y, w, h)
		if self.__browser:
			self.__browser.scaleRect(eRect(x, y, w, h), self._doSetVideoWindow)

	def _doSetVideoWindow(self, rect):
		print "[Hbbtv]._doSetVideoWindow x=%s, y=%s, w=%s, h=%s" % (rect.x(), rect.y(), rect.width(), rect.height())
		if self.__videoWindow == None:
			self.__videoWindow = self.session.instantiateDialog(HbbTVVideoWindow, point=rect.topLeft(), size=rect.size())
		self.__videoWindow.setRect(rect.topLeft(), rect.size())
		self.__videoWindow.show()

	def _unsetVideoWindow(self):
		if self.__videoWindow != None:
			self.session.deleteDialog(self.__videoWindow)
			self.__videoWindow = None

	def _toggleVideoFullscreen(self):
		if self.__videoWindow:
			if self.__videoWindow.toggleFullscreen():
				if self.__browser:
					self.__browser.hide()
			else:
				if self.__browser:
					self.__browser.show()

			return True

	def _saveStreamToDisk(self):
		if self.isStreaming():
			title = _("Please selection the location you want to download the current stream to.")
			self.session.openWithCallback(self._onSaveStreamToDisk, MovieLocationBox, title, preferredPath("<timer>"))
			return True
		return False

	def _onSaveStreamToDisk(self, path):
		if path is not None:
			parsed = urlparse(self.__currentStreamRef.getPath())
			file = parsed.path.split("/")[-1].split(".")
			host = parsed.netloc.split(":")[0]
			datestring = datetime.now().strftime("%Y%m%d_%H%M")
			extension = "mp4"
			filename = "%s_%s_%s.%s" % (datestring, host, file[0], extension)
			path = "%s%s" % (path, filename)
			downloadManager.AddJob(DownloadJob(self.__currentStreamRef.getPath(), path, filename))
			self.session.open(MessageBox, _("Download started..."), type=MessageBox.TYPE_INFO, timeout=3)

	def _onUrlChanged(self, url):
		self.stopStream()
		self._unsetVideoWindow()

	def showBrowser(self):
		self._showVideoIfAvail()
#		if self.__browser:
			#self.__browser.show()

	def hideBrowser(self):
		self._hideVideoIfAvail()
#		if self.__browser:
			#self.__browser.hide()

	def _unsetBrowser(self):
		self._unsetVideoWindow()
		self.stopStream()
		self.__browser = None

	def zap(self, sref):
		self.session.nav.playService(eServiceReference(sref))

	def isStreaming(self):
		if self.__currentStreamRef:
			return True
		return False

	def playStream(self, sref):
		self.__restoreTimer.stop()
		self.__currentStreamRef = eServiceReference(sref)
		currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentService and currentService.valid():
			if currentService.toCompareString() != self.__currentStreamRef.toCompareString() and currentService.type == eServiceReference.idDVB:
				self.__lastService = currentService
				self._playStream(sref)
			else:
				self._unpauseStream()
		else:
			self._playStream(sref)

		self._showVideoIfAvail()

	def _playStream(self, sref):
		config.mediaplayer.useAlternateUserAgent.value = False
		self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_CONNECTING)
		self.session.nav.stopService()
		self.session.nav.playService(eServiceReference(sref))

	def actionPause(self):
		if self.__browser:
			self.__browser.actionPause()

	def _unpauseStream(self):
		pausable = self.session.nav.getCurrentService().pause()
		pausable.unpause()
		self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_PLAYING)

	def pauseStream(self):
		if self.isStreaming():
			pausable = self.session.nav.getCurrentService().pause()
			if pausable is None:
				self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_PLAYING)
			else:
				pausable.pause()
				self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_PAUSED)

	def seekStream(self, to):
		if not self.isStreaming():
			return

		s = self.session.nav.getCurrentService()
		if not s:
			return

		seekable = s.seek()
		if seekable is None or not seekable.isCurrentlySeekable():
			return
		seekable.seekTo(to)

	def actionStop(self):
		if self.__browser:
			self.__browser.actionStop()

	def stopStream(self):
		if self.isStreaming():
			self.session.nav.stopService()
			self.eHbbtv.setStreamState(eHbbtv.STREAM_STATE_STOPPED)
			self.__currentStreamRef = None
			self.__restoreTimer.startLongTimer(1)

	def setVolume(self, volume):
		vol = eDVBVolumecontrol.getInstance()
		vol.setVolume(volume)

	def _restoreLastService(self):
		if self.__lastService:
			self.session.nav.playService(self.__lastService)
			self.__lastService = None

	def nextService(self):
		from Screens.InfoBar import InfoBar
		ib = InfoBar.instance
		ib.zapDown()

	def prevService(self):
		from Screens.InfoBar import InfoBar
		ib = InfoBar.instance
		ib.zapUp()

	def redButtonAppplicationReady(self, appid):
		print "[HbbTV].readButtonApplicationReady, appid=%s" % (appid)
		self._redButtonApp = appid
		app = self.eHbbtv.getApplication(self._redButtonApp)
		HbbTV.redButtonDescriptor.name = app.getName()
		plugins.addPlugin(HbbTV.redButtonDescriptor)

	def textApplicationReady(self, appid):
		print "[HbbTV].textApplicationReady, appid=%s" % (appid)
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

			self.__browser = self.session.open(Browser, True, uri, True, hbbtvMenu=self._showApplicationList)
			self.__browser.onClose.append(self._unsetBrowser)
			self.__browser.onPageLoadFinished.append(self.eHbbtv.pageLoadFinished)
			self.__browser.onActionTv.append(self._toggleVideoFullscreen)
			self.__browser.onActionRecord.append(self._saveStreamToDisk)
			self.__browser.onUrlChanged.append(self._onUrlChanged)
			self.__browser.onExecBegin.append(self._showVideoIfAvail)
			self.__browser.onExecEnd.append(self._hideVideoIfAvail)

	def startApplicationById(self, appid):
		uri = self.eHbbtv.resolveApplicationLocator("dvb://current.ait/%s" % appid)
		if uri != "":
			self.startApplicationByUri(uri)

	def setCurrentBouquet(self, ref):
		self.eHbbtv.setServiceList(ref.toString())

	def _getExtensionMenuText(self):
		return _("HbbTV Applications")

	def _showApplicationList(self):
		apps = eHbbtv.getInstance().getApplicationIdsAndName()
		apps.append(("putpat.tv", "http://www.putpat.tv/device/phupaw9t"))
		if len(apps) == 0:
			apps.append((_("No HbbTV Application available"), None))
		self.session.openWithCallback(self._applicationSelected, ChoiceBox, title=_("Please select an HbbTV application"), list=apps)

	def _applicationSelected(self, appid):
		appid = appid and appid[1]
		if appid is not None:
			if str(appid).startswith("http"):
				self.startApplicationByUri(appid)
			else:
				self.startApplicationById(appid)

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

HbbTV.redButtonDescriptor = PluginDescriptor(name="HbbTV", description=_("Show the current HbbTV Startapplication"), where=[PluginDescriptor.WHERE_HBBTV, ], fnc=HbbTV.redButton, needsRestart=False)
HbbTV.textDescriptor = PluginDescriptor(name="HbbTV", description=_("Show the current HbbTV Teletext Application"), where=[PluginDescriptor.WHERE_TELETEXT, ], fnc=HbbTV.textButton, needsRestart=False)

def start(session, **kwargs):
	if HbbTV.instance is None:
		HbbTV(session)

def autostart(reason, **kwargs):
	if reason == 1:
		if HbbTV.instance is not None:
			HbbTV.instance.disconnectCallbacks()
