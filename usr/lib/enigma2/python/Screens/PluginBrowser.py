from Screen import Screen
from enigma import eConsoleAppContainer

from Components.ActionMap import ActionMap
from Components.PluginComponent import plugins
from Components.PluginList import PluginEntryComponent, PluginList
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Tools.LoadPixmap import LoadPixmap

from time import time

class PluginBrowserSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">	
		<widget source="parent.pluginlist" render="Label" position="6,0" size="120,30" font="Regular;15">
			<convert type="StringListSelection">1</convert>
		</widget>
		<widget source="parent.pluginlist" render="Label" position="6,30" size="120,36" font="Regular;12">
			<convert type="StringListSelection">2</convert>
		</widget>
	</screen>"""

class PluginBrowser(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["red"] = Label(_("Manage extensions"))
		self["green"] = Label()
		
		self.list = []
		self["pluginlist"] = PluginList(self.list)
		self.pluginlist = []
		
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.save,
			"back": self.close,
		})
		self["SoftwareActions"] = ActionMap(["ColorActions"],
		{
			"red": self.openExtensionmanager
		})
		self["SoftwareActions"].setEnabled(True)
		self.updateList()
		self.onFirstExecBegin.append(self.checkWarnings)
	
	def checkWarnings(self):
		if len(plugins.warnings):
			text = _("Some plugins are not available:\n")
			for (pluginname, error) in plugins.warnings:
				text += _("%s (%s)\n") % (pluginname, error)
			plugins.resetWarnings()
			self.session.open(MessageBox, text = text, type = MessageBox.TYPE_WARNING)

	def save(self):
		self.run()
	
	def run(self):
		plugin = self["pluginlist"].current[0]
		plugin(session=self.session)
		
	def updateList(self):
		self.pluginlist = plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU)
		self.list = [PluginEntryComponent(plugin) for plugin in self.pluginlist]
		self["pluginlist"].setList(self.list)

	def PluginDownloadBrowserClosed(self):
		self.updateList()

	def openExtensionmanager(self):
		if fileExists(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/SoftwareManager/plugin.py")):
			from Plugins.SystemPlugins.SoftwareManager.plugin import PluginManager
			self.session.openWithCallback(self.PluginDownloadBrowserClosed, PluginManager)
		else:
			self.session.open(MessageBox, _("The Softwaremanagement extension is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 10 )

	def createSummary(self):
		return PluginBrowserSummary
