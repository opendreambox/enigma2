from Screens.WizardLanguage import WizardLanguage
from Screens.Wizard import wizardManager
from Screens.Rc import Rc
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Components.Pixmap import Pixmap
from os import access, W_OK, R_OK
from enigma import eEnv

from Components.config import config, ConfigSubsection, ConfigText, ConfigLocations, ConfigBoolean
from Components.Harddisk import harddiskmanager
from Tools.Log import Log

config.misc.firstrun = ConfigBoolean(default = True)
config.plugins.configurationbackup = ConfigSubsection()
config.plugins.configurationbackup.backuplocation = ConfigText(default = '/media/hdd/', visible_width = 50, fixed_size = False)
config.plugins.configurationbackup.backupdirs = ConfigLocations(default=[eEnv.resolve('${sysconfdir}/enigma2/'), '/etc/hostname'])


backupfile = "enigma2settingsbackup.tar.gz"

def checkConfigBackup():
	parts = [ (p.description, p.mountpoint) for p in harddiskmanager.getMountedPartitions() if p.mountpoint != "/"]
	parts.extend([ ( hd.model(), harddiskmanager.getAutofsMountpoint(hd.device + str(hd.numPartitions())) ) for hd in harddiskmanager.hdd if harddiskmanager.getAutofsMountpoint(hd.device + str(hd.numPartitions())) not in parts ])

	for x in parts:
		path = x[1]
		path = path[:-1] if path.endswith('/') else path
		fullbackupfile =  "%s/backup/%s" %(path,backupfile)
		if fileExists(fullbackupfile):
			Log.i("Found backup at '%s'" %(fullbackupfile,))
			config.plugins.configurationbackup.backuplocation.value = str(x[1])
			config.plugins.configurationbackup.backuplocation.save()
			config.plugins.configurationbackup.save()
			return x
	return None

def checkBackupFile():
	backuplocation = config.plugins.configurationbackup.backuplocation.value
	backuplocation = backuplocation[:-1] if backuplocation.endswith('/') else backuplocation
	fullbackupfile =  backuplocation + 'backup/' + backupfile
	if fileExists(fullbackupfile):
		Log.i("Found backup at '%s'" %(fullbackupfile,))
		return True
	return False

class ImageWizard(WizardLanguage, Rc):
	skin = """
		<screen name="ImageWizard" position="center,80" size="1200,610" title="Welcome...">
			<ePixmap pixmap="skin_default/buttons/red.png" position="270,15" size="200,40"  />
			<widget name="languagetext" position="270,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="wizard" position="0,3" size="240,605" pixmap="skin_default/wizard.png" />
			<widget name="rc" position="40,60" size="160,500" zPosition="1" pixmaps="skin_default/rc0.png,skin_default/rc1.png,skin_default/rc2.png"  />
			<widget name="arrowdown" position="-100,-100" size="37,70" pixmap="skin_default/arrowdown.png" zPosition="2"  />
			<widget name="arrowdown2" position="-100,-100" size="37,70" pixmap="skin_default/arrowdown.png" zPosition="2"  />
			<widget name="arrowup" position="-100,-100" size="37,70" pixmap="skin_default/arrowup.png" zPosition="2"  />
			<widget name="arrowup2" position="-100,-100" size="37,70" pixmap="skin_default/arrowup.png" zPosition="2"  />
			<widget name="text" position="280,70" size="880,240" font="Regular;23"  />
			<widget source="list" render="Listbox" position="280,330" size="880,270" zPosition="1" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
				<convert type="TemplatedMultiContent">
					{"template": [ MultiContentEntryText(pos=(10,4),size=(580,22),flags=RT_HALIGN_LEFT,text=0) ],
					"fonts": [gFont("Regular",20)],
					"itemHeight": 30
					}
				</convert>
			</widget>
			<widget name="config" position="280,330" size="880,270" zPosition="2" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1"/>
		</screen>"""
	def __init__(self, session):
		self.xmlfile = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/SoftwareManager/imagewizard.xml")
		WizardLanguage.__init__(self, session, showSteps = False, showStepSlider = False)
		Rc.__init__(self)
		self.session = session
		self["wizard"] = Pixmap()
		self.selectedDevice = None
		
	def markDone(self):
		pass

	def listDevices(self):
		list = [ (r.description, r.mountpoint) for r in harddiskmanager.getMountedPartitions(onlyhotplug = False)]
		for x in list:
			result = access(x[1], W_OK) and access(x[1], R_OK)
			if result is False or x[1] == '/':
				list.remove(x)
		for x in list:
			if x[1].startswith('/autofs/'):
				list.remove(x)	
		return list

	def deviceSelectionMade(self, index):
		self.deviceSelect(index)
		
	def deviceSelectionMoved(self):
		self.deviceSelect(self.selection)
		
	def deviceSelect(self, device):
		self.selectedDevice = device
		config.plugins.configurationbackup.backuplocation.value = self.selectedDevice
		config.plugins.configurationbackup.backuplocation.save()
		config.plugins.configurationbackup.save()

wizardManager.registerWizard(ImageWizard, config.misc.firstrun.value, priority = 10)

