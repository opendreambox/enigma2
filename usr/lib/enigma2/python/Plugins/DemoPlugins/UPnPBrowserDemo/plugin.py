# -*- coding: UTF-8 -*-
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont, eServiceReference
from Components.ActionMap import ActionMap
from Screens.ChoiceBox import ChoiceBox
from Components.MenuList import MenuList
from Plugins.SystemPlugins.UPnP.UPnPBrowser import UPnPBrowser
from Plugins.SystemPlugins.UPnP.UPnPCore import Statics
from Plugins.SystemPlugins.UPnP.UPnPMediaRenderingControlClient import UPnPMediaRenderingControlClient
from Screens.Screen import Screen
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap

def UPnPEntryComponent(title, item = None, type = Statics.ITEM_TYPE_SERVER):
	res = [ (item, True) ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, title))
	if type == Statics.ITEM_TYPE_CONTAINER:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "extensions/directory.png"))
	else:
		png = None
	if png:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))

	return res

class SimpleUPnPBrowser(Screen):
	skin = """
		<screen position="center,center" size="600,475"  title="UPnP Demo-Browser" >
			<widget name="list" position="10,5" size="580,410" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, enableWrapAround = True):
		Screen.__init__(self, session)
		self.list = MenuList([], enableWrapAround, eListboxPythonMultiContent)
		self.list.l.setFont(0, gFont("Regular", 18))
		self.list.l.setItemHeight(23)

		self["list"] = self.list
		self.browser = UPnPBrowser()

		self["actions"] = ActionMap(["ListboxActions", "OkCancelActions", "ColorActions"],
		{
			"ok" : self.ok,
			"cancel" : self.close,
			"moveUp" : self.moveUp,
			"moveDown" : self.moveDown,
			"pageUp" : self.pageUp,
			"pageDown" : self.pageDown,
		});

		self.browser.onMediaServerDetected.append(self._onMediaServerDetected)
		self.browser.onListReady.append(self._onListReady)
		self.onShow.append( self.__onShow )
		self.onClose.append(self.__onClose)

	def __onShow(self):
		self.browser.browse()

	def __onClose(self):
		self.browser.onMediaServerDetected.remove(self._onMediaServerDetected)
		self.browser.onListReady.remove(self._onListReady)

	def ok(self):
		if self.list.getSelectedIndex() == 0 and self.browser.canAscend():
			print "[SimpleUPnPBrowser].ok can Ascend"
			return self.browser.ascend()

		else:
			item = self.getSelection()[0]
			if item != None:
				if self.browser.canDescend(item):
					self.browser.descend(item)
				else:
					clients = self.browser.controlPoint.getRenderingControlClientList()
					list = [(_("Local"), "local", None, item)] #( Name, UUID, instance )
					for client in clients:
						c = UPnPMediaRenderingControlClient(client)
						devicename = c.getDeviceName()
						list.append( (str(devicename), "remote", c, item) )
					if len(list) > 1:
						self.session.openWithCallback(self.__onRendererSelected, ChoiceBox, title=_("Where do you want to play this?"), list = list)
					else:
						self.__onRendererSelected(list[0])

	def __onRendererSelected(self, selection):
		if selection:
			client = selection[2]
			item = selection[3]
			meta = self.browser.getItemMetadata(item)

			if selection[1] == "local":
				service = eServiceReference(4097,0, meta[Statics.META_URI])
				service.setName(meta[Statics.META_TITLE])
				self.session.nav.playService(service)
			else:
				client.setMediaUri(uri = meta[Statics.META_URI])
				client.play()

	def getSelection(self):
		if self.list.l.getCurrentSelection() is None:
			return None
		return self.list.l.getCurrentSelection()[0]

	def moveUp(self):
		self.list.up()

	def moveDown(self):
		self.list.down()

	def pageUp(self):
		self.list.pageUp()

	def pageDown(self):
		self.list.pageDown()

	def _onMediaServerDetected(self, udn, client):
		#If we cannot ascend anymore we are showing the server list
		#that's the only point where we want to react immediately on server list updates
		if not self.browser.canAscend():
			self._onListReady(self.browser.getList())

	def _onListReady(self, list):
		print "[SimpleUPnPBrowser]._onListReady: got %s items" %(len(list))
		l = []
		if self.browser.canAscend():
			l.append(UPnPEntryComponent( _("[up]") ))
		for item in list:
			l.append(UPnPEntryComponent( self.browser.getItemTitle(item), item, self.browser.getItemType(item) ))

		self.list.l.setList(l)

def main(session, **kwargs):
	session.open(SimpleUPnPBrowser)

from Plugins.Plugin import PluginDescriptor
def Plugins(**kwargs):
		return PluginDescriptor(name = "UPnP Browser Demo",
								description = _("Demo for browsing and playing Media from DLNA and UPnP A/V MediaServers"),
								icon = "plugin.png",
								where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
								fnc=main)
