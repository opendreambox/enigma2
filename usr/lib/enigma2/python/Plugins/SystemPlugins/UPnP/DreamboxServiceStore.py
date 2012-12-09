# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009, Jose Luis Garduno Garcia <deepsight[atsign]gmail.com>
# Based on the Lolcats Media backend from Benjamin Kampmann
# Copyright 2008, Benjamin Kampmann <ben.kampmann@googlemail.com>

#relicensed under the enigma2 license!
"""
This is a Media Backend that allows you to access video streams from
a Dreambox which uses the Enigma2 web interface. Based on the
Lolcats media backend.

"""
from enigma import eServiceReference
from Components.Sources.ServiceList import ServiceList

from coherence.backend import BackendStore
from coherence.backend import BackendItem
from coherence.upnp.core import DIDLLite

from twisted.internet import reactor
from coherence.extern.et import parse_xml

class DreamboxService(BackendItem):
	def __init__(self, parent_id, id, name, url):
		self.parentid = parent_id
		self.update_id = 0
		self.id = id
		self.location = url
		self.name = name
		self.item = DIDLLite.VideoItem(id, parent_id, self.name)
		res = DIDLLite.Resource(self.location, 'http-get:*:video/mpeg:DLNA_PN=MPEG_PS_PAL')
		res.size = None
		self.item.res.append(res)

class DreamboxServiceContainer(BackendItem):
	def __init__(self, parent_id, id, name="Dreambox", ref=None, children=None):
		self.parent_id = parent_id
		self.id = id
		self.name = name
		self.mimetype = 'directory'
		self.update_id = 0
		self.children = children or []
		self.item = DIDLLite.Container(id, parent_id, self.name)
		self.item.childCount = None
		self.ref = ref

	def get_children(self, start=0, end=0):
		if end != 0:
			return self.children[start:end]
		return self.children[start:]

	def get_child_count(self):
		return len(self.children)

	def get_item(self):
		return self.item

	def get_name(self):
		return self.name

	def get_id(self):
		return self.id

class DreamboxServiceStore(BackendStore):
	implements = ['MediaServer']
	logCategory = 'dreambox_service_store'

	ROOT_ID = 0
	def __init__(self, server, *args, **kwargs):

		self.server = server

		# streaminghost is the ip address of the dreambox machine, defaults to localhost
		self.streaminghost = kwargs.get('streaminghost', self.server.coherence.hostname)
		self.name = kwargs.get('name', 'Dreambox')
		# timeout between updates in minutes
		self.refresh = float(kwargs.get('refresh', 1)) * 60
		self.next_id = 1000
		self.update_id = 0
		self.last_updated = None
		self.container = None
		self.set_default_container()
		self.init_completed()

	def set_default_container(self):
		l = [
			DreamboxServiceContainer(
				self.ROOT_ID,
				self.get_next_id(self.ROOT_ID),
				name=_("Bouquets (TV)"),
				ref="1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet"),
			DreamboxServiceContainer(
				self.ROOT_ID,
				self.get_next_id(self.ROOT_ID),
				name=_("Provider (TV)"),
				ref="1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name"),
			# RADIO
			DreamboxServiceContainer(
				self.ROOT_ID,
				self.get_next_id(self.ROOT_ID),
				name=_("Bouquets (Radio)"),
				ref="1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET \"bouquets.radio\" ORDER BY bouquet"),
			DreamboxServiceContainer(
				self.ROOT_ID,
				self.get_next_id(self.ROOT_ID),
				name=_("Provider (Radio)"),
				ref="1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name"),
		]
		self.container = DreamboxServiceContainer(None, self.ROOT_ID, children=l)

	def get_next_id(self, parent):
		id = "%s:%s" % (parent, self.next_id)
		self.next_id += 1
		return id

	def get_by_id(self, id):
		self.info("get_by_id: %s" %id)
		if str(id) == "0":
			return self.container
		else:
			container = self.container
			id = str(id).split(":")
			upper = len(id) - 1

			i = 1
			while i <= upper:
				current_id = id if i == upper else id[:i+1]
				child_id = ":".join(current_id)
				found = False

				for child in container.get_children():
					if child.get_id() == child_id:
						container = child
						found = True
						break
				if not found:
					self.warning("Couldn't find container with id %s, returning closest existing parent", id)
					break
				i += 1

		if container.get_id() != self.ROOT_ID:
			if container.get_child_count() <= 0:
 				self.populate_container(container)

		return container

	def populate_container(self, container):
		if container.ref == None:
			self.warning("Invalid ref %s" %container.ref)
			return

		servicelist = None
		def get_servicelist(ref):
			servicelist.root = ref
		ref = eServiceReference(container.ref)
		if not ref.valid():
			self.warning("Invalid ref %s" %container.ref)
			return

		servicelist = ServiceList(ref, command_func=get_servicelist, validate_commands=False)
		services = servicelist.getServicesAsList()
		isContainerList = len(container.get_id().split(":")) < 3 #HACK ALERT

		cid = container.get_id()
		append = container.children.append

		for ref, name in services:
			name = unicode(name.replace('\xc2\x86', '').replace('\xc2\x87', ''), errors='ignore')
			if isContainerList:
				append(DreamboxServiceContainer(
						cid,
						self.get_next_id(cid),
						name=name,
						ref=ref))
			else:
				url = 'http://' + self.streaminghost + ':8001/' + ref
				append(DreamboxService(
						cid,
						self.get_next_id(cid),
						name,
						url))

		container.update_id += 1
		self.update_id += 1
		if self.server:
			self.server.content_directory_server.set_variable(0, 'SystemUpdateID', self.update_id)
			self.server.content_directory_server.set_variable(0, 'ContainerUpdateIDs', (cid, container.update_id))

	def upnp_init(self):
		if self.server:
			self.server.connection_manager_server.set_variable(\
				0, 'SourceProtocolInfo', ['http-get:*:video/mpeg:DLNA_PN=MPEG_PS_PAL',
				'http-get:*:video/mpeg:DLNA_PN=MPEG_TS_PAL', ])

