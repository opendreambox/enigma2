from Source import Source

class WebNavigation(Source):
	COMMAND_LOAD = 0x000
	COMMAND_NAVIGATE = 0x001
	COMMAND_ASCII_INPUT = 0x002
	COMMAND_SCROLL = 0x003
	COMMAND_SET_HTML = 0x004
	COMMAND_SET_DICT = 0x005
	COMMAND_GET_ZOOM_FACTOR = 0x006
	COMMAND_SET_ZOOM_FACTOR = 0x007
	COMMAND_ENABLE_PERSISTENT_STORAGE = 0x008
	COMMAND_GET_COOKIES = 0x009
	COMMAND_SET_COOKIES = 0x010
	COMMAND_SET_TRANSPARENT = 0x011
	COMMAND_SET_ACCEPT_LANGUAGE = 0x012
	COMMAND_LEFT_CLICK = 0x013
	COMMAND_GET_POS = 0x014
	COMMAND_GET_SIZE = 0x015
	COMMAND_GET_UA = 0x016
	COMMAND_SET_UA = 0x017
	COMMAND_SET_HBBTV = 0x018
	COMMAND_SCALE = 0x019
	
	EVENT_URL_CHANGED = 0x100
	EVENT_TITLE_CHANGED = 0x101
	EVENT_LOAD_PROGRESS = 0x102
	EVENT_LOAD_FINISHED = 0x103
	EVENT_DOWNLOAD_REQUESTED = 0x104
	EVENT_UNSUPPORTED_CONTENT = 0x105
	EVENT_MICROFOCUS_CHANGED = 0x106
	EVENT_WINDOW_REQUESTED = 0x107
	EVENT_SSL_ERRORS = 0x108
	EVENT_AUTH_REQUIRED = 0x109
	EVENT_PROXY_AUTH_REQUIRED = 0x110
	
	def __init__(self, url = None, html = None):
		Source.__init__(self)
		self.url = url
		self.html = html
		self.onUrlChanged = []
		self.onTitleChanged = []
		self.onLoadProgress = []
		self.onLoadFinished = []		
		self.onDownloadRequested = []
		self.onUnsupportedContent = []
		self.onMicroFocusChanged = []
		self.onWindowRequested = []
		self.onSslErrors = []
		self.onAuthRequired = []
		self.onProxyAuthRequired = []
		self.__isFirstExec = True
		self.__zoomFactor = None
		self.__cookies = None
		self.__pos = None
		self.__size = None
		self.__useragent = None

	def execBegin(self):
		if self.__isFirstExec:
			self.__onFirstExecBegin()

	def __onFirstExecBegin(self):
		self.__isFirstExec = False
		self.changed(self.EVENT_URL_CHANGED, (self, self.__onUrlChanged))
		self.changed(self.EVENT_TITLE_CHANGED, (self, self.__onTitleChanged))
		self.changed(self.EVENT_LOAD_PROGRESS, (self, self.__onLoadProgress))
		self.changed(self.EVENT_LOAD_FINISHED, (self, self.__onLoadFinished))
		self.changed(self.EVENT_DOWNLOAD_REQUESTED, (self, self.__onDownloadRequested))
		self.changed(self.EVENT_UNSUPPORTED_CONTENT, (self, self.__onUnsupportedContent))
		self.changed(self.EVENT_MICROFOCUS_CHANGED, (self, self.__onMicroFocusChanged))
		self.changed(self.EVENT_WINDOW_REQUESTED, (self, self.__onWindowRequested))
		self.changed(self.EVENT_SSL_ERRORS, (self, self.__onSslErrors))
		self.changed(self.EVENT_AUTH_REQUIRED, (self, self.__onAuthRequired))
		self.changed(self.EVENT_PROXY_AUTH_REQUIRED, (self, self.__onProxyAuthRequired))

	def __setPos(self, pos):
		self.__pos = pos

	def __getPos(self):
		self.changed(self.COMMAND_GET_POS, self.__setPos)
		return self.__pos

	position = property(__getPos)

	def __setSize(self, size):
		self.__size = size

	def __getSize(self):
		self.changed(self.COMMAND_GET_SIZE, self.__setSize)
		return self.__size

	size = property(__getSize)

	def __getHtml(self):
		return self.__html

	def __setHtml(self, html):
		self.__html = html
		if html is not None:
			self.changed(self.COMMAND_SET_HTML, html)

	html = property(__getHtml, __setHtml)

	def __getUrl(self):
		return self.__url

	def __setUrl(self, url):
		self.__url = url
		if url is not None:
			self.changed(self.COMMAND_LOAD, url)

	url = property(__getUrl, __setUrl)

	def __getZoomFactor(self):
		self.changed(self.COMMAND_GET_ZOOM_FACTOR, self.__setZoomFactorInternal)
		return self.__zoomFactor
	
	def __setZoomFactor(self, factor):
		self.changed(self.COMMAND_SET_ZOOM_FACTOR, factor)
	
	def __setZoomFactorInternal(self, factor):
		self.__zoomFactor = factor
	
	zoomFactor = property(__getZoomFactor, __setZoomFactor)

	def __getCookies(self):
		self.changed(self.COMMAND_GET_COOKIES, self.__setCookiesInternal)
		return self.__cookies
	
	def __setCookiesInternal(self, cookies):
		self.__cookies = cookies
	
	def __setCookies(self, cookies):
		self.changed(self.COMMAND_SET_COOKIES, cookies)
		self.__cookies = cookies
	
	cookies = property(__getCookies, __setCookies)

	def scale(self, rect, callback):
		self.changed(self.COMMAND_SCALE, (rect, callback))

	def scroll(self, dx, dy):
		dx = int(dx)
		dy = int(dy)
		self.changed( self.COMMAND_SCROLL, (dx, dy) )

	def setDict(self, token, dict):
		assert token
		self.changed(self.COMMAND_SET_DICT, [token, dict])

	def enablePersistentStorage(self, path):
		assert path
		self.changed(self.COMMAND_ENABLE_PERSISTENT_STORAGE, path)

	def setBackgroundTransparent(self, enabled):
		self.changed(self.COMMAND_SET_TRANSPARENT, enabled)

	def setHbbtv(self, enabled):
		self.changed(self.COMMAND_SET_HBBTV, enabled)

	def setAcceptLanguage(self, language):
		self.changed(self.COMMAND_SET_ACCEPT_LANGUAGE, language)

	def leftClick(self, point):
		self.changed(self.COMMAND_LEFT_CLICK, point)

	def __onUrlChanged(self, url):
		self.__url = url
		for cb in self.onUrlChanged:
			cb(url)

	def __onTitleChanged(self, title):
		for cb in self.onTitleChanged:
			cb(title)

	def __onLoadProgress(self, progress):
		for cb in self.onLoadProgress:
			cb(progress)

	def __onLoadFinished(self, val):
		for cb in self.onLoadFinished:
			cb(val)
	
	def __onDownloadRequested(self, url):
		for cb in self.onDownloadRequested:
			cb(url)
	
	def __onUnsupportedContent(self, url, contentType):
		for cb in self.onUnsupportedContent:
			cb(url, contentType)
	
	def __onMicroFocusChanged(self, x, y, w, h, isInput):
		for cb in self.onMicroFocusChanged:
			cb(x, y, w, h, isInput)

	def __onWindowRequested(self, url):
		for cb in self.onWindowRequested:
			cb(url)
	
	def __onSslErrors(self, token, errors, pems):
		for cb in self.onSslErrors:
			cb(token, errors, pems)
	
	def __onAuthRequired(self, token, user, password, realm):
		for cb in self.onAuthRequired:
			cb(token, user, password, realm)

	def __onProxyAuthRequired(self, token, user, password, realm):
		for cb in self.onProxyAuthRequired:
			cb(token, user, password, realm)

	def __setUserAgentInternal(self, useragent):
		self.__useragent = useragent

	def __getUserAgent(self):
		self.changed(self.COMMAND_GET_UA, self.__setUserAgentInternal)
		return self.__useragent

	def __setUserAgent(self, useragent):
		self.changed(self.COMMAND_SET_UA, useragent)
		self.__useragent = useragent

	useragent = property(__getUserAgent, __setUserAgent)
