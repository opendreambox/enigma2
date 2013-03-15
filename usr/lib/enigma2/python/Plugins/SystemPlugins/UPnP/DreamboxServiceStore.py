"""
This is a Media Backend that allows you to access video streams from
a Dreambox which uses the Enigma2 web interface.
"""

from enigma import eServiceReference
from Components.Sources.ServiceList import ServiceList

from coherence.backend import ROOT_CONTAINER_ID, AbstractBackendStore, Container, LazyContainer, BackendItem
from coherence.upnp.core import DIDLLite

from twisted.internet import defer
from coherence.extern.et import parse_xml

class DreamboxService(BackendItem):
	def __init__(self, title, url, service_number, storage):
		self.update_id = 0
		self.name = title
		self.location = url
		self.storage = storage
		self.item = None
		self.service_number = service_number

	def get_service_number(self):
		return self.service_number

	def get_children(self, start=0, end=0):
		[]

	def get_child_count(self):
		return 0

	def get_id(self):
		return self.storage_id

	def get_path(self):
		return self.location

	def get_item(self):
		if self.item == None:
			self.item = DIDLLite.VideoItem(self.get_id(), self.storage.get_id(), self.name)
			res = DIDLLite.Resource(self.location, 'http-get:*:video/mpeg:DLNA_PN=MPEG_PS_PAL')
			res.size = None
			self.item.res.append(res)

		return self.item

class DreamboxServiceStore(AbstractBackendStore):
	implements = ['MediaServer']
	logCategory = 'dreambox_service_store'

	def __init__(self, server, *args, **kwargs):
		AbstractBackendStore.__init__(self, server, **kwargs)

		self.name = kwargs.get('name','Dreambox (TV)')
		# streaminghost is the ip address of the dreambox machine, defaults to localhost
		self.streaminghost = kwargs.get('streaminghost', self.server.coherence.hostname)

		self.refresh = float(kwargs.get('refresh', 1)) * 60
		self.init_root()
		self.init_completed()

	def init_root(self):
		root = Container(None, ROOT_CONTAINER_ID)
		self.set_root_item( root )
		root.add_child(
			LazyContainer(
				root,
				_("Bouquets (TV)"),
				external_id="1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet",
				childrenRetriever=self.populate_container))
		root.add_child(
			LazyContainer(
				root,
				("Provider (TV)"),
				external_id="1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name",
				childrenRetriever=self.populate_container))
		root.add_child(
			LazyContainer(
				root,
				_("Bouquets (Radio)"),
				external_id="1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET \"bouquets.radio\" ORDER BY bouquet",
				childrenRetriever=self.populate_container))
		root.add_child(
			LazyContainer(
				root,
				_("Provider (Radio)"),
				external_id="1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name",
				childrenRetriever=self.populate_container))
		root.sorted = True

	def populate_container(self, parent=None):
		self.warning("ref %s" %parent.external_id)
		retriever = self.populate_container

		def do_populate(parent=None):
			if parent.external_id == None:
				self.warning("Invalid ref %s" %parent.external_id)
				return

			servicelist = None
			def get_servicelist(ref):
				servicelist.root = ref
			ref = eServiceReference(parent.external_id)
			if not ref.valid():
				self.warning("Invalid ref %s" %parent.external_id)
				return

			servicelist = ServiceList(ref, command_func=get_servicelist, validate_commands=False)
			services = servicelist.getServicesAsList()

			snum = 1
			isChannelList = False
			for sref, name in services:
				name = unicode(name.replace('\xc2\x86', '').replace('\xc2\x87', ''), errors='ignore')
				item = None
				if sref.startswith("1:7:"): #Bouquet
					item = LazyContainer(parent, name, childrenRetriever=retriever)
				else:
					isChannelList = True
					if not sref.startswith("1:64:"): # skip markers
						url = 'http://' + self.streaminghost + ':8001/' + sref
						item = DreamboxService(name, url, snum, parent)
						snum += 1

				if item is not None:
					parent.add_child(item, external_id=sref)

			if isChannelList:
				def sort(x, y):
					return cmp(x.get_service_number(), y.get_service_number())
				parent.sorting_method = sort

		d = defer.maybeDeferred(do_populate, parent=parent)
		return d

	def upnp_init(self):
		if self.server:
			self.server.connection_manager_server.set_variable(\
				0, 'SourceProtocolInfo', ['http-get:*:video/mpeg:DLNA_PN=MPEG_PS_PAL',
				'http-get:*:video/mpeg:DLNA_PN=MPEG_TS_PAL', ])

