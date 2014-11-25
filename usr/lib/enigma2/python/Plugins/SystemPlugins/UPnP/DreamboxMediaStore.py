# -*- coding: utf-8 -*-

"""
This is a Media Backend that allows you to access live video streams on
a Dreambox. It depends on the Enigma2 web interface.
"""

from enigma import eMediaDatabase, eServiceReference, StringList
from Components.config import config
from Components.Sources.ServiceList import ServiceList
from Tools.Log import Log

from coherence.backend import ROOT_CONTAINER_ID, AbstractBackendStore, Container
from coherence.upnp.core import DIDLLite
from UPnPCore import DLNA, removeUPnPDevice

from Components.ResourceManager import resourcemanager

from urlparse import urlsplit

AUDIO_CONTAINER_ID = 100
AUDIO_ALL_CONTAINER_ID = 101
AUDIO_ARTIST_CONTAINER_ID = 102
AUDIO_ARTIST_ALL_CONTAINER_ID = 103
AUDIO_ALBUM_CONTAINER_ID = 104
VIDEO_CONTAINER_ID = 200
VIDEO_ALL_CONTAINER_ID = 201
VIDEO_RECORDINGS_CONTAINER_ID = 201
VIDEO_UNSEEN_CONTAINER_ID = 202
VIDEO_HD_CONTAINER_ID = 203
VIDEO_SD_CONTAINER_ID = 204

LIVE_CONTAINER_ID = 300

import sys
if sys.getdefaultencoding() != 'UTF-8':
	reload(sys)
	sys.setdefaultencoding('UTF-8')

def convertString(string):
	return string

class DBContainer(Container):
	ITEM_KEY_TITLE = "title"
	ITEM_KEY_ID = "id"
	ITEM_KEY_CATEGORY = "category"

	def __init__(self, db, name, parent):
		Container.__init__(self, parent, convertString(name))
		self._db = db
		self.location = None
		self.item = None
		self.children = None
		self._child_count = -1
		self._default_mime = "audio/*"
		self._default_additionalInfo = "*"

	def get_path(self):
		return self.location

	def get_item(self):
		if self.item is None:
			item = DIDLLite.Item(self.get_id(), self.parent.get_id(), self.name)
			item.childCount = self.get_child_count()
			self.item = item
			self.update_id += 1
		return self.item

	def _get_data(self, res):
		if res and not res.error():
			return res.data()
		elif res:
			self.warning("%s\n%s" %(res.errorDriverText(), res.errorDatabaseText()))
		else:
			self.warning("res is %s", res)
		return []

	def _set_item_resources(self, codec, size=0):
			if size < 0:
				size = 0
			mimetype = DLNA.getMimeType(codec, self._default_mime)
			dlna_params = "*"

			_,host_port,_,_,_ = urlsplit(self.store.urlbase)
			if host_port.find(':') != -1:
				host,port = tuple(host_port.split(':'))
			else:
				host = host_port

			res = DIDLLite.Resource('file://'+self.location, protocolInfo='internal:%s:%s:%s' % (host, mimetype, dlna_params))
			res.size = size
			self.item.res.append(res)

			ext =  self.location.split('.')[-1]
			url = "%s%s.%s" %(self.store.urlbase, self.get_id(), ext)
			res = DIDLLite.Resource(data=url, protocolInfo='http-get:*:%s:%s' %(mimetype, dlna_params))
			res.size = size
			self.item.res.append(res)

class Artist(DBContainer):
	schemaVersion = 1
	mimetype = 'directory'
	
	def get_children(self, start=0, end=0):
		if self.children is None:
			res = self._db.getAlbumsByArtist(self.name)
			items = self._get_data(res)
			self.children = []
			if(len(items) > 1):
				self.add_child( ArtistAll(self._db, self.name, _("-- All --"), self), external_id=AUDIO_ARTIST_ALL_CONTAINER_ID )
			for item in items:
				self.add_child( Album(self._db, item, self), external_id=int(item[eMediaDatabase.FIELD_ID]) )
		return self.children

	def get_item(self):
#		self.warning(self.name)
		if self.item is None:
			self.item = DIDLLite.MusicArtist(self.get_id(), self.parent.get_id(), self.name)
			self.item.childCount = self.get_child_count()
		return self.item

class Artists(DBContainer):
	schemaVersion = 1
	mimetype = 'directory'

	def get_children(self, start=0, end=0):
		if self.children is None:
			res = self._db.getAllArtists()
			Log.w(self.name)
			items = self._get_data(res)
			self.children = []
			for item in items:
				self.add_child( Artist(self._db, item[eMediaDatabase.FIELD_ARTIST], self), external_id=int(item[eMediaDatabase.FIELD_ID]) )
		return self.children

	def get_item(self):
		if self.item is None:
			self.item = DIDLLite.Music(self.get_id(), self.parent.get_id(), self.name)
			self.item.childCount = self.get_child_count()
		return self.item

class Album(DBContainer):
	schemaVersion = 1
	mimetype = 'directory'

	def __init__(self, db, item, parent):
		artist, album = item[eMediaDatabase.FIELD_ARTIST], item[eMediaDatabase.FIELD_ALBUM]
		self._db_item = item
		self.artist = artist
		DBContainer.__init__(self, db, album, parent)

	def get_children(self, start=0, end=0):
		if self.children is None:
			self.children = []
			res = self._db.filterByArtistAlbum(self.artist, self.name)
			items = self._get_data(res)
			for item in items:
				self.add_child( Track(self._db, item, self), external_id=int(item[eMediaDatabase.FIELD_FILE_ID]) )
		return self.children

	def get_item(self):
		if self.item is None:
			self.item = DIDLLite.MusicAlbum(id=self.get_id(), parentID=self.parent.get_id(), title=self.name)
			self.item.childCount = self.get_child_count()
			self.item.artist = self.artist
		return self.item

class ArtistAll(Album):
	schemaVersion = 1
	mimetype = 'directory'
	def __init__(self, db, artist, name, parent):
		item = {
				eMediaDatabase.FIELD_ARTIST : artist,
				eMediaDatabase.FIELD_ALBUM : name
			}
		Album.__init__(self, db, item, parent)

	def get_children(self, start=0, end=0):
		if self.children is None:
			self.children = []
			res = self._db.filterByArtist(self.parent.name)
			items = self._get_data(res)
			for item in items:
				self.add_child( Track(self._db, item, self), external_id=int(item[eMediaDatabase.FIELD_FILE_ID]) )
		return self.children

class Albums(DBContainer):
	schemaVersion = 1
	mimetype = 'directory'

	def get_children(self, start=0, end=0):
		if self.children is None:
			self.children = []
			res = self._db.getAllAlbums()
			items = self._get_data(res)
			for item in items:
				self.add_child( Album(self._db, item, self), external_id=int(item[eMediaDatabase.FIELD_ID]) )
		return self.children

	def get_item(self):
		if self.item is None:
			self.item = DIDLLite.Music(id=self.get_id(), parentID=self.parent.get_id(), title=self.name)
			self.item.childCount = self.get_child_count()
		return self.item

class AllTracks(DBContainer):
	schemaVersion = 1
	mimetype = 'directory'
	
	def get_children(self, start=0, end=0):
		if self.children is None:
			self.children = []
			limit = end - start if end - start > 0 else -1
			res = self._db.getAllAudio(limit, start)
			items = self._get_data(res)
			for item in items:
				self.add_child( Track(self._db, item, self), int(item[eMediaDatabase.FIELD_FILE_ID]) )
		return self.children

class Track(DBContainer):
	schemaVersion = 1

	def __init__(self, db, item, parent):
		self._db_item = item
		artist, album, title, size, date = item[eMediaDatabase.FIELD_ARTIST], item[eMediaDatabase.FIELD_ALBUM], item[eMediaDatabase.FIELD_TITLE], item[eMediaDatabase.FIELD_SIZE], item[eMediaDatabase.FIELD_DATE]
		DBContainer.__init__(self, db, title, parent)
		self.location = "%s/%s" %(item[eMediaDatabase.FIELD_PATH], item[eMediaDatabase.FIELD_FILENAME])
		self.artist = convertString(artist)
		self.title = convertString(title)
		self.album = convertString(album)
		self.size = size
		self.date = date

	def get_children(self,start=0,request_count=0):
		return []

	def get_item(self):
		if self.item is None:
			self.item = DIDLLite.MusicTrack(self.get_id(), self.parent.get_id(), self.name)
			self.item.childCount = 0
			self.item.artist = self.artist
			self.item.title = self.title
			self.item.album = self.album
			self.item.date = self.date
			codec = self._db_item['codec']
			self._set_item_resources(codec, self.size)
		return self.item

class VideoContainer(DBContainer):
	schemaVersion = 1
	mimetype = 'directory'

	def get_children(self, start=0, end=0):
		if self.children is None:
			self.children = []
			res = self._get_res()
			items = self._get_data(res)
			for item in items:
				self.add_child( Video(self._db, item, self), external_id=int(item[eMediaDatabase.FIELD_FILE_ID]) )
		return self.children

	def _get_res(self):
		return []

	def get_item(self):
		if self.item is None:
			self.item = DIDLLite.Container(id=self.get_id(), parentID=self.parent.get_id(), title=self.name)
			self.item.childCount = self.get_child_count()
		return self.item

class VideoRecordings(VideoContainer):
	def _get_res(self):
		return self._db.getAllRecordings()

class VideoUnseen(VideoContainer):
	def _get_res(self):
		return self._db.query("SELECT * from video WHERE lastplaypos=?;", StringList(["0"]))

class VideoHD(VideoContainer):
	def _get_res(self):
		return self._db.query("SELECT * from video WHERE hd=?;", StringList(["1"]))

class VideoSD(VideoContainer):
	def _get_res(self):
		return self._db.query("SELECT * from video WHERE hd=?;", StringList(["0"]))

class VideoAll(VideoContainer):
	def _get_res(self):
		return self._db.getAllVideos()

class Video(DBContainer):
	schemaVersion = 1

	def __init__(self, db, item, parent):
		self._db_item = item
		name, size = item[eMediaDatabase.FIELD_TITLE], item[eMediaDatabase.FIELD_SIZE]
		DBContainer.__init__(self, db, name, parent)
		self.location = "%s/%s" %(item[eMediaDatabase.FIELD_PATH], item[eMediaDatabase.FIELD_FILENAME])
		self.size = size

	def get_children(self,start=0,request_count=0):
		return []

	def get_item(self):
		if self.item is None:
			self.item = DIDLLite.VideoItem(self.get_id(), self.parent.get_id(), self.name)
			self.item.childCount = 0
			self.item.title = self.name
			self._default_mime = "video/*"
			codec = self._db_item['codec']
			self._set_item_resources(codec, self.size)
		return self.item

class DVBServiceList(Container):
	def __init__(self, parent, title):
		Container.__init__(self, parent, title)
		self.service_number = 0
		self.item = None
		self.location = ""
		self.children = None

	def get_service_number(self):
		return self.service_number

	def get_item(self):
		if self.item == None:
			self.item = DIDLLite.Container(self.get_id(), self.parent.get_id(), self.name)
		return self.item

	def get_children(self, start=0, end=0):
		if self.children is None:
			self.children = []
			self._init_services(self.external_id)
		return self.children

	def _get_next_service_nr(self):
		self.service_number += 1
		return self.service_number

	def _gen_child(self, ref, name):
		return DVBServiceList(self, name)

	def _init_services(self, ref):
		self.warning(ref)
		servicelist = None
		def get_servicelist(ref):
			servicelist.root = ref
		if ref:
			ref = eServiceReference(ref)
			if not ref.valid():
				self.warning("Invalid ref %s" %ref)
				return []
		else:
			self.warning("Missing ref!")

		servicelist = ServiceList(ref, command_func=get_servicelist, validate_commands=False)
		services = servicelist.getServicesAsList()
		for ref, name in services:
			if ref.startswith("1:64"): #skip markers
				continue
			child = self._gen_child(ref, name)
			self.add_child(child, external_id=ref)

class DVBService(DVBServiceList):
	def __init__(self, parent, title, is_radio=False):
		DVBServiceList.__init__(self, parent, title)
		self.location = None
		self.streaminghost = None

	def get_service_number(self):
		return self.service_number

	def get_path(self):
		if self.streaminghost is None:
			self.streaminghost = self.store.server.coherence.hostname
		if self.location is None:
			self.location = 'http://' + self.streaminghost + ':8001/' + self.external_id
		return self.location

	def get_item(self):
		if self.item == None:
			self.item = DIDLLite.VideoBroadcast(self.get_id(), self.parent.get_id(), self.name)
			res = DIDLLite.Resource(self.get_path(), 'http-get:*:video/mpegts:*')
			res.size = None
			self.item.res.append(res)
		return self.item

	def get_children(self, start=0, end=0):
		return []

class Favorite(DVBServiceList):
	def _gen_child(self, ref, name):
		return DVBService(self, name)

class Favorites(DVBServiceList):
	def _gen_child(self, ref, name):
		return Favorite(self, name)

class Provider(DVBServiceList):
	def _gen_child(self, ref, name):
		return DVBService(self, name)

class ProviderList(DVBServiceList):
	def _gen_child(self, ref, name):
		return Provider(self, name)

class DreamboxMediaStore(AbstractBackendStore):
	implements = ['MediaServer']
	logCategory = 'dreambox_media_store'

	def __init__(self, server, *args, **kwargs):
		AbstractBackendStore.__init__(self, server, **kwargs)
		self._db = eMediaDatabase.getInstance()

		self.next_id = 1000
		self.name = kwargs.get('name','Dreambox Mediaserver')
		# streaminghost is the ip address of the dreambox machine, defaults to localhost
		self.streaminghost = kwargs.get('streaminghost', self.server.coherence.hostname)

		self.refresh = float(kwargs.get('refresh', 1)) * 60
		self.init_root()
		self.init_completed()

		#Samsung TVs are special...
		self._X_FeatureList = """&lt;Features xmlns=\"urn:schemas-upnp-org:av:avs\""
		" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\""
		" xsi:schemaLocation=\"urn:schemas-upnp-org:av:avs http://www.upnp.org/schemas/av/avs.xsd\"&gt;"
		" &lt;Feature name=\"samsung.com_BASICVIEW\" version=\"1\"&gt;"
		 "&lt;container id=\"1\" type=\"object.item.audioItem\"/&gt;"
		 "&lt;container id=\"2\" type=\"object.item.videoItem\"/&gt;"
		 "&lt;container id=\"3\" type=\"object.item.imageItem\"/&gt;&lt;/Features&gt;"""

	def init_root(self):
		root = Container(None, ROOT_CONTAINER_ID)
		self.set_root_item( root )
		#AUDIO
		if config.plugins.mediaserver.share_audio.value:
			audio = Container(root, "Audio")
			root.add_child(audio, AUDIO_CONTAINER_ID)
			audio.add_child(
					Artists(self._db, _("Artists"), audio), AUDIO_ARTIST_CONTAINER_ID, 
				)
			audio.add_child(
					Albums(self._db, _("Albums"), audio), AUDIO_ALBUM_CONTAINER_ID,
				)
		#VIDEO
		if config.plugins.mediaserver.share_video.value:
			video = Container(root, "Video")
			root.add_child(video, VIDEO_CONTAINER_ID)
			video.add_child(
					VideoRecordings(self._db, _("Recordings"), video), VIDEO_RECORDINGS_CONTAINER_ID,
				)
			video.add_child(
					VideoUnseen(self._db, _("Unseen"), video), VIDEO_UNSEEN_CONTAINER_ID,
				)
			video.add_child(
					VideoHD(self._db, _("HD"), video), VIDEO_HD_CONTAINER_ID,
				)
			video.add_child(
					VideoSD(self._db, _("SD"), video), VIDEO_SD_CONTAINER_ID,
				)
			video.add_child(
					VideoAll(self._db, _("All"), video), VIDEO_RECORDINGS_CONTAINER_ID,
				)
		#DVB LIVE
		if config.plugins.mediaserver.share_live.value:
			live = Container(root, "Livestreams (DVB)")
			root.add_child(live, LIVE_CONTAINER_ID)
			#TV
			live.add_child(
					Favorites(live, _("Favorites (TV)")),
						external_id="1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet",
				)
			live.add_child(
					ProviderList(live, _("Provider (TV)")),
						external_id="1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name",
				)
			#RADIO
			live.add_child(
					Favorites(live, _("Favorites (Radio)")),
						external_id="1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET \"bouquets.radio\" ORDER BY bouquet",
				)
			live.add_child(
					ProviderList(live, _("Provider (Radio)")),
						external_id="1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name",
				)

		root.sorted = True
		def childs_sort(x,y):
			return cmp(x.name,y.name)
		root.sorting_method = childs_sort

	def upnp_init(self):
		if self.server:
			self.server.connection_manager_server.set_variable(0, 'SourceProtocolInfo', [
					'http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_TN',
					'http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_SM',
					'http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_MED',
					'http-get:*:image/jpeg:DLNA.ORG_PN=JPEG_LRG',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_HD_50_AC3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_HD_60_AC3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_HP_HD_AC3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_MP_HD_AAC_MULT5_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_MP_HD_AC3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_MP_HD_MPEG1_L3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_MP_SD_AAC_MULT5_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_MP_SD_AC3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=AVC_TS_MP_SD_MPEG1_L3_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=MPEG_PS_NTSC',
					'http-get:*:video/mpeg:DLNA.ORG_PN=MPEG_PS_PAL',
					'http-get:*:video/mpeg:DLNA.ORG_PN=MPEG_TS_HD_NA_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=MPEG_TS_SD_NA_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=MPEG_TS_SD_EU_ISO',
					'http-get:*:video/mpeg:DLNA.ORG_PN=MPEG1',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_MP_SD_AAC_MULT5',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_MP_SD_AC3',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_BL_CIF15_AAC_520',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_BL_CIF30_AAC_940',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_BL_L31_HD_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_BL_L32_HD_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_BL_L3L_SD_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_MP_HD_1080i_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_MP_HD_720p_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=MPEG4_P2_MP4_ASP_AAC',
					'http-get:*:video/mp4:DLNA.ORG_PN=MPEG4_P2_MP4_SP_VGA_AAC',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_HD_50_AC3',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_HD_50_AC3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_HD_60_AC3',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_HD_60_AC3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_HP_HD_AC3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_HD_AAC_MULT5',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_HD_AAC_MULT5_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_HD_AC3',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_HD_AC3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_HD_MPEG1_L3',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_HD_MPEG1_L3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_SD_AAC_MULT5',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_SD_AAC_MULT5_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_SD_AC3',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_SD_AC3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_SD_MPEG1_L3',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=AVC_TS_MP_SD_MPEG1_L3_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=MPEG_TS_HD_NA',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=MPEG_TS_HD_NA_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=MPEG_TS_SD_EU',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=MPEG_TS_SD_EU_T',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=MPEG_TS_SD_NA',
					'http-get:*:video/vnd.dlna.mpeg-tts:DLNA.ORG_PN=MPEG_TS_SD_NA_T',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVSPLL_BASE',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVSPML_BASE',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVSPML_MP3',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVMED_BASE',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVMED_FULL',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVMED_PRO',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVHIGH_FULL',
					'http-get:*:video/x-ms-wmv:DLNA.ORG_PN=WMVHIGH_PRO',
					'http-get:*:video/3gpp:DLNA.ORG_PN=MPEG4_P2_3GPP_SP_L0B_AAC',
					'http-get:*:video/3gpp:DLNA.ORG_PN=MPEG4_P2_3GPP_SP_L0B_AMR',
					'http-get:*:audio/mpeg:DLNA.ORG_PN=MP3',
					'http-get:*:audio/x-ms-wma:DLNA.ORG_PN=WMABASE',
					'http-get:*:audio/x-ms-wma:DLNA.ORG_PN=WMAFULL',
					'http-get:*:audio/x-ms-wma:DLNA.ORG_PN=WMAPRO',
					'http-get:*:audio/x-ms-wma:DLNA.ORG_PN=WMALSL',
					'http-get:*:audio/x-ms-wma:DLNA.ORG_PN=WMALSL_MULT5',
					'http-get:*:audio/mp4:DLNA.ORG_PN=AAC_ISO_320',
					'http-get:*:audio/3gpp:DLNA.ORG_PN=AAC_ISO_320',
					'http-get:*:audio/mp4:DLNA.ORG_PN=AAC_ISO',
					'http-get:*:audio/mp4:DLNA.ORG_PN=AAC_MULT5_ISO',
					'http-get:*:audio/L16;rate=44100;channels=2:DLNA.ORG_PN=LPCM',
					'http-get:*:image/jpeg:*',
					'http-get:*:video/avi:*',
					'http-get:*:video/divx:*',
					'http-get:*:video/x-matroska:*',
					'http-get:*:video/mpeg:*',
					'http-get:*:video/mp4:*',
					'http-get:*:video/x-ms-wmv:*',
					'http-get:*:video/x-msvideo:*',
					'http-get:*:video/x-flv:*',
					'http-get:*:video/x-tivo-mpeg:*',
					'http-get:*:video/quicktime:*',
					'http-get:*:audio/mp4:*',
					'http-get:*:audio/x-wav:*',
					'http-get:*:audio/x-flac:*',
					'http-get:*:application/ogg:*'
				])

			#Samsung TVs are special...
			self.server.content_directory_server.register_vendor_variable(
				'X_FeatureList',
				evented='no',
				data_type='string',
				default_value=self._X_FeatureList)

			self.server.content_directory_server.register_vendor_action(
				'X_GetFeatureList', 'optional',
				(('FeatureList', 'out', 'X_FeatureList'),),
				needs_callback=False)

def restartMediaServer(name, uuid):
	cp = resourcemanager.getResource("UPnPControlPoint")
	if cp:
		removeUPnPDevice(uuid, cp)
		return cp.registerServer(DreamboxMediaStore, name=name, uuid=uuid)
	return None

