from enigma import eNetworkManager, eTimer, quitMainloop
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Ipkg import IpkgComponent
from Components.Slider import Slider
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

from SoftwareTools import iSoftwareTools
from Screens.MessageBox import MessageBox


class UpdatePlugin(Screen):
	skin = """
		<screen name="UpdatePlugin" position="center,center" size="620,160" title="Software update">
			<widget name="activityslider" position="10,10" size="600,10"  borderWidth="2" borderColor="#cccccc"/>
			<widget source="package" render="Label" position="10,40" size="600,25" font="Regular;22" />
			<widget source="status" render="Label" position="10,70" size="600,45" font="Regular;22" />
			<widget name="slider" position="10,140" size="600,12" borderWidth="2" borderColor="#cccccc" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)

		self.sliderPackages = { "dreambox-dvb-modules": 1, "enigma2": 2, "tuxbox-image-info": 3 }

		self.slider = Slider(0, 4)
		self["slider"] = self.slider
		self.activityslider = Slider(0, 100)
		self["activityslider"] = self.activityslider
		self.status = StaticText(_("Please wait..."))
		self["status"] = self.status
		self.package = StaticText(_("Verifying your internet connection..."))
		self["package"] = self.package
		self.oktext = _("Press OK on your remote control to continue.")

		self.packages = 0
		self.error = 0
		self.processed_packages = []
		self.modified_packages = []

		self.activity = 0
		self.activityTimer = eTimer()
		self.activityTimer_conn = self.activityTimer.timeout.connect(self.doActivityTimer)

		self.ipkg = IpkgComponent()
		self.ipkg.addCallback(self.ipkgCallback)

		self.updating = False
		self.rebootRequired = False
		self.device_name = iSoftwareTools.hardware_info.device_name

		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.exit,
			"back": self.exit
		}, -1)

		self.checkNetwork()
		self.onClose.append(self.cleanup)

	def cleanup(self):
		iSoftwareTools.cleanupSoftwareTools()

	def checkNetwork(self):
		if eNetworkManager.getInstance().online():
			self.updating = True
			self.activityTimer.start(100, False)
			self.package.setText(_("Package list update"))
			self.status.setText(_("Upgrading Dreambox... Please wait"))
			self.ipkg.startCmd(IpkgComponent.CMD_UPDATE)
		else:
			self.package.setText(_("Your network is not working. Please try again."))
			self.status.setText(self.oktext)

	def doActivityTimer(self):
		self.activity += 1
		if self.activity == 100:
			self.activity = 0
		self.activityslider.setValue(self.activity)

	def ipkgCallback(self, event, param):
		if event == IpkgComponent.EVENT_DOWNLOAD:
			self.status.setText(_("Downloading"))
		elif event == IpkgComponent.EVENT_UPGRADE:
			if param in self.sliderPackages:
				self.slider.setValue(self.sliderPackages[param])
			self.package.setText(param)
			self.status.setText(_("Upgrading"))
			if not param in self.processed_packages:
				self.processed_packages.append(param)
				self.packages += 1
		elif event == IpkgComponent.EVENT_INSTALL:
			self.package.setText(param)
			self.status.setText(_("Installing"))
			if not param in self.processed_packages:
				self.processed_packages.append(param)
				self.packages += 1
		elif event == IpkgComponent.EVENT_REMOVE:
			self.package.setText(param)
			self.status.setText(_("Removing"))
			if not param in self.processed_packages:
				self.processed_packages.append(param)
				self.packages += 1
		elif event == IpkgComponent.EVENT_CONFIGURING:
			self.package.setText(param)
			self.status.setText(_("Configuring"))
		elif event == IpkgComponent.EVENT_ERROR:
			self.error += 1
		elif event == IpkgComponent.EVENT_DONE:
			if self.updating:
				iSoftwareTools.listUpgradable(self.listUpgradableCB)
			elif self.error == 0:
				self.slider.setValue(4)
				self.activityTimer.stop()
				self.activityslider.setValue(0)
				self.package.setText(_("Done - Installed or upgraded %d packages") % self.packages)
				self.status.setText(self.oktext)
			else:
				self.activityTimer.stop()
				self.activityslider.setValue(0)
				error = _("your dreambox might be unusable now. Please consult the manual for further assistance before rebooting your dreambox.")
				if self.packages == 0:
					error = _("No packages were upgraded yet. So you can check your network and try again.")
				if self.updating:
					error = _("Your dreambox isn't connected to the internet properly. Please check it and try again.")
				self.status.setText(_("Error") +  " - " + error)
		#print event, "-", param
		pass

	def listUpgradableCB(self, res):
		if iSoftwareTools.upgradeAvailable is False:
			self.updating = False
			self.slider.setValue(4)
			self.activityTimer.stop()
			self.activityslider.setValue(0)
			self.package.setText(_("Done - No updates available."))
			self.status.setText(self.oktext)
		else:
			self.updating = False
			upgrade_args = {'use_maintainer' : True, 'test_only': False}
			if config.plugins.softwaremanager.overwriteConfigFiles.value == 'N':
				upgrade_args = {'use_maintainer' : False, 'test_only': False}
			self.ipkg.startCmd(IpkgComponent.CMD_UPGRADE, args = upgrade_args)

	def exit(self):
		if not self.ipkg.isRunning():
			if self.packages != 0 and self.error == 0:
				self.session.openWithCallback(self.exitReboot, MessageBox, _("Upgrade finished.") +" "+_("Do you want to reboot your Dreambox?"))
			else:
				self.close()
		else:
			if not self.updating:
				self.close()

	def exitReboot(self, result):
		if result:
			quitMainloop(2)
		self.close()

	def exitRestart(self, result):
		if result:
			quitMainloop(3)
		self.close()
