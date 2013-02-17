# -*- coding: UTF-8 -*-

from coherence.base import Coherence

from coherence.upnp.devices.control_point import ControlPoint
from coherence.upnp.devices.media_renderer import MediaRenderer
from coherence.upnp.devices.media_server import MediaServer
from coherence.upnp.devices.media_server_client import MediaServerClient

class Statics:
	CONTAINER_ID_ROOT = 0
	CONTAINER_ID_SERVERLIST = -1

	ITEM_TYPE_AUDIO = "audio"
	ITEM_TYPE_CONTAINER = "container"
	ITEM_TYPE_PICTURE = "picture"
	ITEM_TYPE_SERVER = "server"
	ITEM_TYPE_FILE = "file"
	ITEM_TYPE_VIDEO = "video"

	META_ALBUM = 'album'
	META_ALBUM_ART_URI = 'album_art_uri'
	META_ARTIST = 'artist'
	META_BITRATE = 'bitrate'
	META_CHILD_COUNT = 'child_count'
	META_DATE = 'date'
	META_DURATION = 'duration'
	META_GENRE = 'genre'
	META_METATYPE = 'metatype'
	META_RESOLUTION = 'resolution'
	META_SIZE = 'size'
	META_TITLE = 'title'
	META_TYPE = 'type'
	META_URI = 'uri'

	SORT_TITLE_ASC = "+dc:title"
	SORT_TITLE_DSC = "+dc:title"

'''
This is a "managed" UPnP A/V Controlpoint which eases the use of UPnP, for Browsing media or adding a Renderer
please see the helper classes (UPnPBrowser and AbstractUPnPRenderer) for more
'''
class ManagedControlPoint(object):
	def __init__(self):
		self.coherence = Coherence({'logmode':'warning'})
		self._controlPoint = ControlPoint(self.coherence, auto_client=['MediaServer','MediaRenderer'])
		self._controlPoint.connect(self._onMediaServerDetected, 'Coherence.UPnP.ControlPoint.MediaServer.detected')
		self._controlPoint.connect(self._onMediaServerRemoved, 'Coherence.UPnP.ControlPoint.MediaServer.removed')
		self._controlPoint.connect(self._onMediaRendererDetected, 'Coherence.UPnP.ControlPoint.MediaRenderer.detected')
		self._controlPoint.connect(self._onMediaRendererRemoved, 'Coherence.UPnP.ControlPoint.MediaRenderer.removed')
		self._controlPoint.connect(self._onMediaDeviceDectected, 'Coherence.UPnP.Device.detection_completed')

		self.__mediaServerClients = {}
		self.__mediaRendererClients = {}
		self.__mediaDevices = {}

		self.__browser = []
		self.__devices = []

		self.onMediaServerDetected = []
		self.onMediaServerRemoved  = []
		self.onMediaRendererDetected = []
		self.onMediaRendererRemoved = []
		self.onMediaDeviceDectected = []

	def _onMediaServerDetected(self, client, udn):
		print "[DLNA] MediaServer Detected: %s (%s)" % (client.device.get_friendly_name(), client.device.get_friendly_device_type())
		self.__mediaServerClients[udn] = client
		for fnc in self.onMediaServerDetected:
			fnc(udn, client)

	def _onMediaServerRemoved(self, udn):
		if self.__mediaServerClients.get(udn, None) != None:
			del self.__mediaServerClients[udn]
			for fnc in self.onMediaServerRemoved:
				fnc(udn)

	def _onMediaRendererDetected(self, client, udn):
		print "[DLNA] MediaRenderer detected: %s (%s, %s)" % (client.device.get_friendly_name(), client.device.get_friendly_device_type(), udn)
		self.__mediaRendererClients[udn] = client
		for fnc in self.onMediaRendererDetected:
			fnc(udn, client)

	def _onMediaRendererRemoved(self, udn):
		print "[DLNA] MediaRenderer removed: %s" % (udn)
		if self.__mediaRendererClients.get(udn, None) != None:
			client = self.__mediaRendererClients[udn]
			del self.__mediaRendererClients[udn]
			for fnc in self.onMediaRendererRemoved:
				fnc(udn)

	def _onMediaDeviceDectected(self, device):
		print "[DLNA] Device found: %s (%s)" % (device.get_friendly_name(), device.get_friendly_device_type())
		self.__mediaDevices[device.udn] = device

	def registerRenderer(self, classDef, **kwargs):
		renderer = MediaRenderer(self.coherence, classDef, no_thread_needed=True, **kwargs)
		self.__devices.append(renderer)
		return renderer

	def registerServer(self, classDef, **kwargs):
		server = MediaServer(self.coherence, classDef, no_thread_needed=True, **kwargs)
		self.__devices.append(server)
		return server

	def getServerList(self):
		return self.__mediaServerClients.values()

	def getRenderingControlClientList(self):
		return self.__mediaRendererClients.values()

	def getDeviceName(self, client):
		return client.device.get_friendly_name().encode( "utf-8" )

	def shutdown(self):
		for device in self.__devices:
			device.unregister()
		self._controlPoint.shutdown()

class Item(object):
	@staticmethod
	def getItemType(item):
		if item != None:
			if item.__class__.__name__ == MediaServerClient.__name__:
				return Statics.ITEM_TYPE_SERVER

			itemClass = item.upnp_class.encode( "utf-8" )
			if Item.isContainer(item):
				return Statics.ITEM_TYPE_CONTAINER

			elif itemClass.startswith("object.item"):
				type = item.upnp_class.split('.')[-1]
				if type == "videoItem" or type == "movie":
					return Statics.ITEM_TYPE_VIDEO
				elif type == "musicTrack" or type == "audioItem":
					return Statics.ITEM_TYPE_AUDIO
				elif type == "photo":
					return Statics.ITEM_TYPE_PICTURE

		return None

	@staticmethod
	def isServer(item):
		return Item.getItemType(item) == Statics.ITEM_TYPE_SERVER

	@staticmethod
	def getServerName(client):
		return client.device.get_friendly_name().encode( "utf-8" )

	'''
	Returns the title of the current item
	'''
	@staticmethod
	def getItemTitle(item):
		if Item.isServer(item):
			return Item.getServerName(item)

		if item.title != None:
			return item.title.encode( "utf-8" )
		else:
			return "<missing title>"

	'''
	returns the number of children for container items
	returns -1 for non-container items
	'''
	@staticmethod
	def getItemChildCount(item):
		if Item.getItemType(item) != Statics.ITEM_TYPE_SERVER and Item.isContainer(item):
			return item.childCount

		return -1

	'''
	Currently always returns a dict with the first url and meta-type, which is usually the original/non-transcoded source
	Raises an IllegalInstanceException if you pass in a container-item
	'''
	@staticmethod
	def getItemUriMeta(item):
		assert not Item.isContainer(item)

		for res in item.res:
			uri = res.data.encode( "utf-8" )
			meta = res.protocolInfo.split(":")[2].encode( "utf-8" )
			print "URL: %s\nMeta:%s" %(uri, meta)
			if uri:
				return {Statics.META_URI : uri, Statics.META_METATYPE : meta}

	@staticmethod
	def getItemId(item):
		if Item.isServer(item):
			return item.device.get_id()
		else:
			return item.id

	@staticmethod
	def getAttrOrDefault(instance, attr, default=None):
		val = getattr(instance, attr, default) or default
		try:
			return val.encode( "utf-8" )
		except:
			return val

	@staticmethod
	def getItemMetadata(item):
		type = Item.getItemType(item)
		meta = {}
		metaNA = _('n/a')

		if type == Statics.ITEM_TYPE_SERVER:
			meta = {
					Statics.META_TYPE : type,
					Statics.META_TITLE : Item.getServerName(item),
				}

		elif type == Statics.ITEM_TYPE_CONTAINER:
				meta = {
						Statics.META_TYPE : type,
						Statics.META_TITLE : Item.getAttrOrDefault(item, 'title', metaNA).encode( "utf-8" ),
						Statics.META_CHILD_COUNT : Item.getItemChildCount(item),
					}
		elif type == Statics.ITEM_TYPE_PICTURE or type == Statics.ITEM_TYPE_VIDEO:
			for res in item.res:
				meta = {
						Statics.META_TYPE : type,
						Statics.META_METATYPE : res.protocolInfo.split(":")[2].encode( "utf-8" ),
						Statics.META_TITLE : Item.getAttrOrDefault(item, 'title', metaNA).encode( "utf-8" ),
						Statics.META_DATE : Item.getAttrOrDefault(item, 'date', metaNA).encode( "utf-8" ),
						Statics.META_RESOLUTION : Item.getAttrOrDefault(item, 'resolution', metaNA).encode( "utf-8" ),
						Statics.META_SIZE : Item.getAttrOrDefault(item, 'size', -1),
						Statics.META_URI : Item.getAttrOrDefault(res, 'data'),
					}
				if type == Statics.ITEM_TYPE_PICTURE:
					meta[Statics.META_ALBUM] = Item.getAttrOrDefault(item, 'album', metaNA).encode( "utf-8" )
				elif type == Statics.ITEM_TYPE_VIDEO:
					meta[Statics.META_ALBUM_ART_URI] = Item.getAttrOrDefault(item, 'albumArtURI')

				return meta
		elif type == Statics.ITEM_TYPE_AUDIO:
			for res in item.res:
				meta = {
						Statics.META_TYPE : type,
						Statics.META_METATYPE : res.protocolInfo.split(":")[2].encode( "utf-8" ),
						Statics.META_TITLE : Item.getAttrOrDefault(item, 'title', metaNA).encode( "utf-8" ),
						Statics.META_ALBUM : Item.getAttrOrDefault(item, 'album', metaNA).encode( "utf-8" ),
						Statics.META_ARTIST : Item.getAttrOrDefault(item, 'artist', metaNA).encode( "utf-8" ),
						Statics.META_GENRE : Item.getAttrOrDefault(item, 'genre', metaNA).encode( "utf-8" ),
						Statics.META_DURATION : Item.getAttrOrDefault(item, 'duration', "0"),
						Statics.META_BITRATE : Item.getAttrOrDefault(item, 'bitrate', "0"),
						Statics.META_SIZE : Item.getAttrOrDefault(item, 'size', -1),
						Statics.META_ALBUM_ART_URI : Item.getAttrOrDefault(item, 'albumArtURI'),
						Statics.META_URI : Item.getAttrOrDefault(res, 'data'),
					}
		return meta

	@staticmethod
	def isContainer(item):
		print item.__class__.__name__
		if item.__class__.__name__ == MediaServerClient.__name__:
			return True
		return item.upnp_class.startswith("object.container")
