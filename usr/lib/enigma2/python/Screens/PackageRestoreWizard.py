from Components.config import ConfigYesNo, getConfigListEntry
from Components.DreamInfoHandler import DreamInfoHandler, IpkgComponent
from Components.Pixmap import Pixmap, MovingPixmap
from Screens.Ipkg import Ipkg
from Screens.WizardLanguage import WizardLanguage
from Tools.Directories import fileExists, resolveFilename, SCOPE_CONFIG
from Tools.Log import Log

from os import remove as os_remove, rename as os_rename

class PackageRestoreCheck(DreamInfoHandler):
	def __init__(self, session):
		DreamInfoHandler.__init__(self, self.statusCallback, blocking = True)
		self._session = session
		self._backupFile = resolveFilename(SCOPE_CONFIG, "packages.bak")
		self._checkPackageRestore()

	def _checkPackageRestore(self):
		from Plugins.SystemPlugins.SoftwareManager.SoftwareTools import iSoftwareTools
		bak = self._backupFile
		if not fileExists(bak):
			Log.i("Package backup does not exist... (%s)" %(bak,))
			return

		def doRestore(unused):
			available = []
			for p in iSoftwareTools.available_packetlist:
				available.append(p[0])

			with open(bak) as f:
				packagesAvailable = []
				packagesMissing = []
				for packagename in f:
					packagename = packagename.strip()
					if packagename in available:
						if packagename not in iSoftwareTools.installed_packetlist:
							packagesAvailable.append(packagename)
							Log.w("%s is NOT installed!" %packagename)
					else:
						packagesMissing.append(packagename)
				if packagesAvailable:
					self._session.open(PackageRestoreWizard, packagesAvailable, packagesMissing)
			self._moveBackupList()
		if iSoftwareTools.installed_packetlist and iSoftwareTools.available_packetlist:
			doRestore(None)
		else:
			def loadInstalled(unused):
				iSoftwareTools.startIpkgListInstalled(callback=doRestore)
			iSoftwareTools.startIpkgListAvailable(loadInstalled)

	def _moveBackupList(self):
		try:
			fname = "%s.old" %(self._backupFile,)
			if fileExists(fname):
				os_remove(fname)
			os_rename(self._backupFile, "%s.old" %(self._backupFile,))
		except Exception as e:
			self._onRestoreRenameFailed(e)

	def _onRestoreFinished(self):
		self._session.toastManager.showToast(_("%s previously installed package(s) have been restored!") %(len(self._commands,)))

	def _onRestoreRenameFailed(self, e):
		Log.w(e)
		self._session.toastManager.showToast(_("An error occured while renaming the package list backup!\n%s") %(e,))

	def statusCallback(self, status, progress):
		pass

class PackageRestoreWizard(WizardLanguage):
	def __init__(self, session, packagesAvailable, packagesMissing):
		self.xmlfile = "restorewizard.xml"
		WizardLanguage.__init__(self, session)
		self.skinName = "DefaultWizard"
		self._packagesAvailable = packagesAvailable
		self._packagesMissing = packagesMissing
		self._commands = []

		self["wizard"] = Pixmap()
		self["rc"] = MovingPixmap()
		self["arrowdown"] = MovingPixmap()
		self["arrowup"] = MovingPixmap()
		self["arrowup2"] = MovingPixmap()

		self._packages = []
		for p in self._packagesAvailable:
			self._packages.append(getConfigListEntry(p, ConfigYesNo(default=True)))

	def introduction(self, unused):
		text = "It looks like you have recently updated your Dreambox using the 'Settings Backup & Restore' feature of the Rescue Loader.\n\nThere is/are %s software package(s) available online.\n" %(len(self._packagesAvailable))

		if self._packagesMissing:
			text = "%sThere is/are  %s software package(s) which are available and can not be restored automatically." %(text, len(self._packagesMissing))
		text = "%s\nDo you want to restore available and previously installed software?""" %(text,)
		return text

	def packagesAvailable(self, unused=None):
		return len(self._packagesAvailable) > 0

	def packageList(self):
		return self._packages

	def buildCommands(self):
		commands = []
		for p in self._packages:
			if p[1].value: # ConfigYesNo
				commands.append((IpkgComponent.CMD_INSTALL, { "package": p[0] })) #packagename
		self._commands = commands

	def haveCommands(self, unused=True):
		if not self._commands:
			self.buildCommands()
		return len(self._commands)

	def restoreSelectedPackages(self):
		self._foreignScreenInstancePrepare()
		if self._commands:
			self.session.openWithCallback(self._foreignScreenInstanceFinished, Ipkg, self._commands)
		else:
			self._restoreFinished()

	def restorationSummary(self, unused=False):
		if self._commands:
			return "%s software package(s) restored!\n" \
					"%s couldn't be restored because they are" \
					"currently not available online." %(len(self._commands), len(self._packagesMissing))
		else:
			return "No software packages have been restored!"
