from Components.config import ConfigYesNo, getConfigListEntry
from Components.DreamInfoHandler import DreamInfoHandler
from Components.SetupGuide.BaseStep import SetupConfigStep

from Tools.Log import Log
from Tools.Directories import resolveFilename, SCOPE_DEFAULTDIR,\
	SCOPE_DEFAULTPARTITION, SCOPE_DEFAULTPARTITIONMOUNTDIR
from Components.NimManager import nimmanager
from six.moves import range

class DefaultServicelistStep(DreamInfoHandler, SetupConfigStep):
	def __init__(self, parent):
		SetupConfigStep.__init__(self, parent)
		DreamInfoHandler.__init__(self, statusCallback=self._onDreamInfoHandlerStatus, neededTag="services")

	def prepare(self):
		self.title = _("Choose Servicelist")
		self.text = _("Please choose the default service list you want to install.")
		self._setDirectory()
		Log.w("configuredSats: %s" %(nimmanager.getConfiguredSats()))
		packages = self.fillPackagesList()
		Log.w(str(packages))
		if not packages:
			return False
		return True

	def _setDirectory(self):
		self.directory = []
		self.directory.append(resolveFilename(SCOPE_DEFAULTDIR))
		import os
		os.system("mount %s %s" % (resolveFilename(SCOPE_DEFAULTPARTITION), resolveFilename(SCOPE_DEFAULTPARTITIONMOUNTDIR)))
		self.directory.append(resolveFilename(SCOPE_DEFAULTPARTITIONMOUNTDIR))

	def _onDreamInfoHandlerStatus(self, status, progress):
		Log.i("%s - %s" %(status, progress))
		if status == DreamInfoHandler.STATUS_DONE:
			self.parent.session.toastManager.showToast(_("The installation of the default services lists is finished."))
			self.parent.nextStep()

	@property
	def configContent(self):
		self.packageslist = []
		configList = []
		self.fillPackagesList()
		self.packagesConfig = []
		for x in range(len(self.packageslist)):
			entry = ConfigYesNo(default = False)
			self.packagesConfig.append(entry)
			configList.append(getConfigListEntry(self.packageslist[x][0]["attributes"]["name"], entry))
		return configList

	def onOk(self):
		self._installlSelected()
		return False

	def _installlSelected(self):
		indexes = []
		for x in range(len(self.packagesConfig)):
			if self.packagesConfig[x].value:
				indexes.append(x)
		self.parent.title = _("Installing...")
		self.parent.text = _("Installing default service lists... Please wait...")
		if indexes:
			self.installPackages(indexes)
		else:
			self.parent.nextStep()

