# -*- coding: utf-8 -*-
from __future__ import absolute_import

from enigma import eInputDeviceManager
from Screens.Screen import Screen
from Screens.Rc import Rc
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Sources.StaticText import StaticText
from Tools.Directories import pathExists, resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from Tools.Log import Log

from os import path as os_path

import six

from .CharJump import CharJump
from .InputDeviceIRDatabase import irdb
from .IrProtocols.ProtocolMaster import ProtocolMaster
from .KeyBindingList import KeyBindingList


class InputDeviceIRProg(Screen, CharJump):
	PLUGIN_IMAGES_PATH = "%s/images/" % (os_path.dirname(__file__))
	SKIN_IMAGES_PATH = resolveFilename(SCOPE_CURRENT_SKIN, config.skin.primary_skin.value.replace("/skin.xml", "/images/"))
	MAJOR_CODELIST_ITEMS = [ "amp", "tv", "vcr", "sat"]

	def __init__(self, session, remote):
		Screen.__init__(self, session)
		CharJump.__init__(self, session)
		self._remote = remote

		self["actions"] = ActionMap(["ListboxActions", "OkCancelActions", "EPGSelectActions"],
		{
			"ok": self._onKeyOK,
			"cancel": self._onKeyExit,
			"info" : self._onKeyInfo
		}, -1)

		self["list"] = List()
		self["list"].onSelectionChanged.append(self._onSelectionChanged)
		self._status = StaticText()
		self["status"] = self._status

		self._vendorPixmap = self._loadPixmap("vendor.svg")
		self._seperatorPixmap = self._loadPixmap("div-h.svg")
		self._level = 0
		self._lastLevel = 0
		self._lastVendor = ""
		self.__onIrKeycount = eInputDeviceManager.getInstance().irKeyCount.connect(self._onIrKeyCount)
		self.onLayoutFinish.append(self._reload)

	def _onIrKeyCount(self, address, count):
		if address == self._remote.address():
			self.session.toastManager.showToast(_("%s IR codes acknowledged!") %(count))

	def _loadPixmap(self, filename, desktop=None):
		picfile = None
		if filename[0] == "/" and pathExists(filename):
			picfile = filename
		else:
			for p in (self.SKIN_IMAGES_PATH, self.PLUGIN_IMAGES_PATH):
				imagepath = "%s%s" % (p, filename)
				if pathExists(imagepath):
					picfile = "%s%s" % (p, filename)
					break
		if picfile:
			return LoadPixmap(path=picfile, desktop=desktop, cached=False)
		return None

	def _onKeyExit(self):
		if self._level == 1:
			self._level = 0
			self._reload()
			return
		self.close()

	def _getFirstForChar(self, char):#CharJump
		idx = 0
		for x in self["list"].list:
			val = x[0][0]
			Log.w(val)
			if val and val[0].upper() == char and not val.lower() in self.MAJOR_VENDORS:
				self["list"].setIndex(idx)
				break
			idx += 1

	def _onKey0(self, unused):#CharJump
		if self["list"].count():
			self["list"].setIndex(0)

	def _reload(self, dlist={}):
		if self._level == 0:
			dlist = irdb.data
		mlist = []
		for x, y in dlist.items():
			x = six.ensure_str(x)
			title = ""
			subtitle = ""
			pic = self._seperatorPixmap
			if self._level == 0:
				title = x
				lendev = len(y)
				if lendev == 1:
					subtitle = "%s" % (six.ensure_str(y.keys()[0]))
				else:
					subtitle = _("%s devices") % (lendev,)
			else:
				title = x
				if title == "":
					title = _("Unknown")
				if not len(y["keys"]):
					Log.w("No known automap-keys for %s" % (title,))
				subtitle = _("%s mapped keys, %s unmapped keys") % (len(y["keys"]), len(y["keys_unknown"]))
			mlist.append(((x, y), self._vendorPixmap, subtitle, title, pic))
		if self._level != 0:

			def sortCodelist(x):
				x = x[0][0]
				val = "000000"
				items = self.MAJOR_CODELIST_ITEMS[:]
				items.reverse()
				for key in items:
					if x.lower().startswith(key):
						return val + x
					val += "000000"
				return x

			mlist = sorted(mlist, key=sortCodelist)
		self["list"].setList(mlist)
		if self._level == 0:
			self["list"].setIndex(self._lastLevel)
			self.setTitle(_("Vendors"))
			self["status"].setText("%s entries" % (len(mlist),))
		else:
			self.setTitle(self._lastVendor)
			self._onSelectionChanged()

	def _onKeyOK(self):
		sel = self["list"].getCurrent()
		entry = sel and sel[0]
		if not len(entry):
			return
		if self._level == 0:
			self._level = 1
			self._lastLevel = self["list"].getIndex()
			self._lastVendor = six.ensure_str(entry[0])
			self._reload(entry[1])
		else:
			self._send(entry[1])

	def _onKeyInfo(self):
		if self._level == 0:
			return
		sel = self["list"].getCurrent()
		entry = sel and sel[0]
		if not len(entry):
			return
		device, data = entry[0:2]
		title = six.ensure_str("%s - %s (%s - %s:%s)" %(self._lastVendor, device, data["protocol"], data["device"], data["subdevice"]))
		self.session.open(InputDeviceKeyInfo, title, data["keys"].keys())

	def _send(self, data):
		protocolData = ProtocolMaster.buildProtocol(data)
		self._remote.resetIr()
		for d in protocolData: #initial / repeat
			protocol, isRepeat, keys = d
			if protocol:
				self._remote.setIrProtocol(isRepeat, protocol)
			for irKey in keys:
				self._remote.setIrKey(irKey)
			self._remote.getIrKeyCount()
		self.session.toastManager.showToast(_("%s IR codes sent!") %(len(keys)), 3)

	def _onSelectionChanged(self):
		if self._level == 0:
			return
		entry = self["list"].getCurrent()
		entry = entry and entry[0]
		if not entry:
			return
		device, data = entry
		count = len(data["keys"])
		self["status"].setText(_("Press OK to apply assign %s keys of '%s'") %(count, device))

class InputDeviceKeyInfo(Screen, Rc):
	def __init__(self, session, title, boundKeys):
		Screen.__init__(self, session, windowTitle=title)
		Rc.__init__(self, 3)
		keys = sorted([six.ensure_str(x) for x in boundKeys])
		self["list"] = KeyBindingList(3, keys)
		self["list"].onSelectionChanged.append(self._onSelectionChanged)
		self["actions"] = ActionMap(["OkCancelActions"], 
		{
			"cancel": self.close,
		}, -1)
		self.onLayoutFinish.append(self._onSelectionChanged)

	def _onSelectionChanged(self):
		self.clearSelectedKeys()
		selection = self["list"].getCurrent()
		Log.w(selection)
		selection = selection and selection[0]
		if not selection:
			return
		self.selectKey(selection)

