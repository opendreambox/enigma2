from __future__ import print_function
from twisted.web import client
from twisted.internet import reactor, defer, ssl
from twisted.internet._sslverify import ClientTLSOptions

class HTTPProgressDownloader(client.HTTPDownloader):
	def __init__(self, url, outfile, headers=None, agent="Dreambox HTTP Downloader"):
		client.HTTPDownloader.__init__(self, url, outfile, headers=headers, agent=agent)
		self.status = None
		self.progress_callback = None
		self.deferred = defer.Deferred()

	def noPage(self, reason):
		if self.status == "304":
			print(reason.getErrorMessage())
			client.HTTPDownloader.page(self, "")
		else:
			client.HTTPDownloader.noPage(self, reason)

	def gotHeaders(self, headers):
		if self.status == "200":
			if "content-length" in headers:
				self.totalbytes = int(headers["content-length"][0])
			else:
				self.totalbytes = 0
			self.currentbytes = 0.0
		return client.HTTPDownloader.gotHeaders(self, headers)

	def pagePart(self, packet):
		if self.status == "200":
			self.currentbytes += len(packet)
		if self.totalbytes and self.progress_callback:
			self.progress_callback(self.currentbytes, self.totalbytes)
		return client.HTTPDownloader.pagePart(self, packet)

	def pageEnd(self):
		return client.HTTPDownloader.pageEnd(self)

import urlparse
def url_parse(url, defaultPort=None):
	parsed = urlparse.urlparse(url)
	scheme = parsed[0]
	path = urlparse.urlunparse(('', '') + parsed[2:])
	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		else:
			defaultPort = 80
	host, port = parsed[1], defaultPort
	if ':' in host:
		host, port = host.split(':')
		port = int(port)
	return scheme, host, port, path

class downloadWithProgress:
	def __init__(self, url, outputfile, contextFactory=None, *args, **kwargs):
		scheme, host, port, path = url_parse(url)
		self.factory = HTTPProgressDownloader(url, outputfile, *args, **kwargs)
		if scheme == 'https':
			if contextFactory is None:
				class TLSSNIContextFactory(ssl.ClientContextFactory):
					def getContext(self, hostname=None, port=None):
						ctx = ssl.ClientContextFactory.getContext(self)
						ClientTLSOptions(host, ctx)
						return ctx
				contextFactory = TLSSNIContextFactory()
				self.connection = reactor.connectSSL(host, port, self.factory, contextFactory)

		else:
			self.connection = reactor.connectTCP(host, port, self.factory)

	def start(self):
		return self.factory.deferred

	def stop(self):
		if self.connection:
			print("[stop]")
			self.connection.disconnect()

	def addProgress(self, progress_callback):
		print("[addProgress]")
		self.factory.progress_callback = progress_callback
