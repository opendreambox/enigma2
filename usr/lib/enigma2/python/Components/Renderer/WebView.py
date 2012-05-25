from Renderer import Renderer
from Components.Sources.WebNavigation import WebNavigation
from enigma import eWebView

class WebView(Renderer):
	GUI_WIDGET = eWebView

	def __init__(self):
		Renderer.__init__(self)

	def connect(self, source):
		Renderer.connect(self, source)

	def postWidgetCreate(self, instance):
		if self.source.url != None:
			self.instance.load(self.source.url)
		elif self.source.html != None:
			self.instance.setHtml(self.source.html)

	def changed(self, cmd, param = None):
		if self.instance:
			if cmd == WebNavigation.COMMAND_LOAD:
				self.instance.load(param)
			elif cmd == WebNavigation.COMMAND_NAVIGATE:
				self.instance.navigate(param)
			elif cmd == WebNavigation.COMMAND_ASCII_INPUT:
				self.instance.asciiInput(param)
			elif cmd == WebNavigation.COMMAND_SCROLL:
				self.instance.scroll(*param)
			elif cmd == WebNavigation.COMMAND_SET_HTML:
				self.instance.setHtml(param)
			elif cmd == WebNavigation.COMMAND_SET_DICT:
				self.instance.setDict(*param)
			elif cmd == WebNavigation.COMMAND_GET_ZOOM_FACTOR:
				param(self.instance.getZoomFactor())
			elif cmd == WebNavigation.COMMAND_SET_ZOOM_FACTOR:
				self.instance.setZoomFactor(param)
			elif cmd == WebNavigation.COMMAND_ENABLE_PERSISTENT_STORAGE:
				self.instance.enablePersistentStorage(param)
			elif cmd == WebNavigation.COMMAND_GET_COOKIES:
				param(self.instance.getRawCookies())
			elif cmd == WebNavigation.COMMAND_SET_COOKIES:
				self.instance.setRawCookies(param)
			elif cmd == WebNavigation.COMMAND_SET_TRANSPARENT:
				self.instance.setBackgroundTransparent(param)
			elif cmd == WebNavigation.COMMAND_SET_ACCEPT_LANGUAGE:
				self.instance.setAcceptLanguage(param)
			elif cmd == WebNavigation.COMMAND_LEFT_CLICK:
				self.instance.leftClick(param)
			elif cmd == WebNavigation.COMMAND_GET_POS:
				param(self.instance.position())
			elif cmd == WebNavigation.COMMAND_GET_SIZE:
				param(self.instance.size())
			elif cmd == WebNavigation.EVENT_URL_CHANGED:
				self.instance.urlChanged.get().append(param)
			elif cmd == WebNavigation.EVENT_TITLE_CHANGED:
				self.instance.titleChanged.get().append(param)
			elif cmd == WebNavigation.EVENT_LOAD_PROGRESS:
				self.instance.loadProgress.get().append(param)
			elif cmd == WebNavigation.EVENT_LOAD_FINISHED:
				self.instance.loadFinished.get().append(param)
			elif cmd == WebNavigation.EVENT_DOWNLOAD_REQUESTED:
				self.instance.downloadRequested.get().append(param)
			elif cmd == WebNavigation.EVENT_UNSUPPORTED_CONTENT:
				self.instance.unsupportedContent.get().append(param)
			elif cmd == WebNavigation.EVENT_MICROFOCUS_CHANGED:
				self.instance.microFocusChanged.get().append(param)
			elif cmd == WebNavigation.EVENT_WINDOW_REQUESTED:
				self.instance.windowRequested.get().append(param)
			elif cmd == WebNavigation.EVENT_SSL_ERRORS:
				self.instance.sslErrors.get().append(param)
			elif cmd == WebNavigation.EVENT_AUTH_REQUIRED:
				self.instance.authenticationRequired.get().append(param)
			elif cmd == WebNavigation.EVENT_PROXY_AUTH_REQUIRED:
				self.instance.proxyAuthenticationRequired.get().append(param)

