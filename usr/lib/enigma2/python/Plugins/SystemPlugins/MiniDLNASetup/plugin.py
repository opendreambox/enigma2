from enigma import eEnv, eConsoleAppContainer, eTimer

from Components.config import config, ConfigYesNo, ConfigEnableDisable, ConfigText, ConfigInteger, ConfigSubList, ConfigSubsection, ConfigSelection, ConfigDirectory, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Harddisk import harddiskmanager
from Components.Sources.StaticText import StaticText
from Components.ResourceManager import resourcemanager
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.HardwareInfo import HardwareInfo

from os import path as os_path

iNetwork = resourcemanager.getResource("iNetwork")

def onUnMountNotifier(action, mountpoint):
	if action == harddiskmanager.EVENT_UNMOUNT:
		dlna_config.stopDaemon()
	else:
		if config.plugins.minidlna.enabled.value:
			dlna_config.startDaemon()
harddiskmanager.onUnMount_Notifier.append(onUnMountNotifier)

"""
This is a start-stop-script-like python-class
"""
class StartStopDaemon(object):
	TYPE_START = "start"
	TYPE_STOP = "stop"

	def __init__(self, daemon, title, bindir=eEnv.resolve('${bindir}'), pidfile=None):
		self._daemon = daemon
		self._title = title

		self._path_daemon = '%s/%s' %(bindir, daemon)
		self._path_killall = '%s/killall' %(eEnv.resolve('${bindir}'))
		self._path_pidfile = pidfile or '/var/run/%s.pid' %(self._daemon)

		self._console = eConsoleAppContainer()
		self._console.appClosed.append(self._consoleCmdFinished)

		self._cmd_kill = [self._path_killall, self._path_killall, "-HUP", self._daemon]
		self._cmd_start = [self._path_daemon, self._path_daemon]
		self._restart = False
		self.__checkTimer = eTimer()
		self.__checkTimer.callback.append(self._checkIfRunning)
		self.onCommandFinished = [] # function(TYPE_START/STOP, isSuccess, message)

	def _consoleCmdFinished(self, data):
		if self._restart and config.plugins.minidlna.enabled.value:
			self._restart = False
			self._console.execute(*self._cmd_start)
		elif self._restart:
			self._restart = False
			self._commandFinished(self.TYPE_STOP, True, _("Configuration saved. %s is disabled") %self._title)
		else:
			self.__checkTimer.start(1500, True)

	def _checkIfRunning(self):
		result = self.isRunning()
		message = _("%s started successfully with the new configuration") %self._title
		if not result:
			message = _("%s was NOT started due to an unexpected error") %self._title

		self._commandFinished(self.TYPE_START, result, message)

	def _commandFinished(self, type, result, message):
		for callback in self.onCommandFinished:
			callback(type, result, message)

	def _getPid(self):
		pid = -1
		if os_path.exists(self._path_pidfile):
			try:
				with open(self._path_pidfile, "r") as f:
					pid = int(f.readline())
			except:
				pass
		return pid

	def isRunning(self):
		pid = self._getPid()
		return os_path.exists("/proc/%s" %pid)

	def stop(self, restart = False):
		self._restart = restart
		self._console.execute(*self._cmd_kill)

	def start(self):
		self._restart = False
		if not self.isRunning():
			self._console.execute(*self._cmd_start)
		else:
			self._commandFinished(self.TYPE_START, True, _("%s was already running") %self._title)

	def restart(self):
		if self.isRunning():
			self.stop(True)
		else:
			self.start()

class MiniDLNAConfig:
	DAEMON = "minidlna"
	DAEMON_TITLE = "Mediaserver"
	CONFIG_FILE_PATH = "%s/minidlna.conf" %(eEnv.resolve('${sysconfdir}'))

	MEDIA_TYPE_AUDIO = "A"
	MEDIA_TYPE_VIDEO = "V"
	MEDIA_TYPE_PICTURE = "P"

	ROOT_TREE_DEFAULT = "."
	ROOT_TREE_DIRECTORY = "B"
	ROOT_TREE_MUSIC = "M"
	ROOT_TREE_VIDEO = "V"
	ROOT_TREE_PICTURES = "P"

	BOOL_TEXT = { True : "yes", False : "no" }
	TEXT_BOOL = { "yes" : True, "no" : False }

	def __init__(self, args = None):
		iNetwork = resourcemanager.getResource("iNetwork")
		self.adapters = iNetwork.getAdapterList()

		self.bool_options = ("inotify", "enable_tivo", "strict_dlna")
		self.hostname = HardwareInfo().get_device_name()
		if len(config.plugins.minidlna.media_dirs) == 0 and config.plugins.minidlna.share_videodirs.value:
			for dir in config.movielist.videodirs.value:
				config.plugins.minidlna.media_dirs.append(ConfigText(default=dir, fixed_size = False))

		self._config = {
			"port" : config.plugins.minidlna.port,
			"network_interface" : config.plugins.minidlna.network_interface,
			"media_dir" : config.plugins.minidlna.media_dirs,
			"friendly_name" : config.plugins.minidlna.friendly_name,
			"db_dir" : config.plugins.minidlna.db_dir,
			"log_dir" : config.plugins.minidlna.log_dir,
			"album_art_names" : config.plugins.minidlna.album_art_names,
			"inotify" : config.plugins.minidlna.inotify,
			"enable_tivo" : config.plugins.minidlna.enable_tivo,
			"strict_dlna" : config.plugins.minidlna.strict_dlna,
			"serial" : config.plugins.minidlna.serial,
			"model_number" : config.plugins.minidlna.model_number,
			"root_container" : config.plugins.minidlna.root_container,
		}

		self._init = StartStopDaemon(self.DAEMON, self.DAEMON_TITLE)
		self._init.onCommandFinished.append(self._onStartStopCommandFinished)
		self.onActionFinished = []

		harddiskmanager.delayed_device_Notifier.append(self._onDeviceNotifier)

	def get(self):
		return self._config

	def _actionFinished(self, result, message):
		for callback in self.onActionFinished:
			callback(result, message)

	def _onStartStopCommandFinished(self, type, result, message):
		self._actionFinished(result, message)

	def _onDeviceNotifier(self, device, action):
		self._writeConfig()

	def startDaemon(self):
		if harddiskmanager.isMount(config.plugins.minidlna.db_dir.value):
			self.apply()
		else:
			print "[MiniDLNAConfig].startDaemon :: Refusing to start with database in a non-mounted path"
			self._actionFinished(False, _("Error! The configured directory is not a mountpoint! Refusing to start!"))

	def stopDaemon(self):
		self._init.stop()

	def restartDaemon(self):
		self._init.restart()

	def apply(self):
		print "[MiniDLNAConfig].apply"
		for x in self._config.values():
			x.save()

		if self._writeConfig():
			self.restartDaemon()
		else:
			self._actionFinished(False, _("Error! Couldn't write the configuration file!\nSettings will NOT be lost on exit!"))

	def _writeConfig(self):
		lines = []
		for key, item in self._config.iteritems():
			if key == "media_dir":
				locations = []
				if config.plugins.minidlna.share_videodirs.value:
					locations = config.movielist.videodirs.value or []
				for cfgtxt in item:
					locations.append(cfgtxt.value)

				locations = self._unifyLocations( locations )
				config.plugins.minidlna.media_dirs = ConfigSubList()
				for loc in locations:
					lines.append("%s=%s\n" %(key, loc))
					config.plugins.minidlna.media_dirs.append(ConfigText(default=loc, fixed_size = False))
				self._config[key] = config.plugins.minidlna.media_dirs
			else:
				value = item.value
				if key in self.bool_options:
					value = self.BOOL_TEXT[value]
				elif key == "db_dir":
					value = "%s/minidlna" %value
				lines.append("%s=%s\n" %(key, value))

		try:
			with open(self.CONFIG_FILE_PATH, "w+") as f:
				f.writelines(lines)
			return True
		except IOError, e:
			print e
			return False

	def _unifyLocations(self, locations):
		lst = []
		for loc in locations:
			lst.append( harddiskmanager.getRealPath(loc) )
		lst.sort()
		lst.reverse()
		last = lst[-1]
		for i in range(len(lst)-2, -1, -1):
			item = lst[i]
			if last == item or item.startswith(last):
				del lst[i]
			else:
				last = item
		return lst

config.plugins.minidlna = ConfigSubsection()
config.plugins.minidlna.enabled = ConfigEnableDisable(default=False)
config.plugins.minidlna.share_videodirs = ConfigYesNo(default=True)
config.plugins.minidlna.port = ConfigInteger(default=8200, limits = (1, 65535))
config.plugins.minidlna.network_interface = ConfigText(default=",".join(iNetwork.getAdapterList()) or "eth0", fixed_size = False)
config.plugins.minidlna.media_dirs = ConfigSubList()
config.plugins.minidlna.friendly_name = ConfigText(default="%s Mediaserver" %(HardwareInfo().get_device_name()), fixed_size = False)
config.plugins.minidlna.db_dir = ConfigDirectory(default="/media/hdd")
config.plugins.minidlna.log_dir = ConfigText(default="/tmp/log", fixed_size = False)
config.plugins.minidlna.album_art_names = ConfigText("Cover.jpg/cover.jpg/AlbumArtSmall.jpg/albumartsmall.jpg/AlbumArt.jpg/albumart.jpg/Album.jpg/album.jpg/Folder.jpg/folder.jpg/Thumb.jpg/thumb.jpg", fixed_size = False)
config.plugins.minidlna.inotify = ConfigYesNo(default=True)
config.plugins.minidlna.enable_tivo = ConfigYesNo(default=False)
config.plugins.minidlna.strict_dlna = ConfigYesNo(default=False)
config.plugins.minidlna.serial = ConfigInteger(default=12345678)
config.plugins.minidlna.model_number = ConfigInteger(default=1)
config.plugins.minidlna.root_container = ConfigSelection([
				(MiniDLNAConfig.ROOT_TREE_DEFAULT, _("Default")),
				(MiniDLNAConfig.ROOT_TREE_DIRECTORY, _("Directories")),
				(MiniDLNAConfig.ROOT_TREE_MUSIC, _("Music")),
				(MiniDLNAConfig.ROOT_TREE_VIDEO, _("Video")),
				(MiniDLNAConfig.ROOT_TREE_PICTURES, _("Pictures")),
			], default = MiniDLNAConfig.ROOT_TREE_DEFAULT)

dlna_config = MiniDLNAConfig()

class MiniDLNASetup(ConfigListScreen, Screen):
	skin = """
		<screen name="MiniDLNASetup" position="center,center" size="560,400" title="Mediaserver (DLNA) Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Shares"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.close,
			"green": self.save,
			"yellow": self._editShares,
			"save": self.save,
			"cancel": self.close,
		}, -2)

		self.conf = dlna_config.get()
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		config.plugins.minidlna.enabled.addNotifier(self._enabledChanged, initial_call = False)
		self.onClose.append(self._onClose)
		dlna_config.onActionFinished.append( self._actionFinished )

	def _onClose(self):
		dlna_config.onActionFinished.remove( self._actionFinished )
		config.plugins.minidlna.enabled.removeNotifier(self._enabledChanged)
		for x in self["config"].list:
			x[1].save()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def createSetup(self):
		list = [getConfigListEntry(_("Mediaserver"), config.plugins.minidlna.enabled)]
		if config.plugins.minidlna.enabled.value:
			list.extend( [
				getConfigListEntry(_("Always share movies"), config.plugins.minidlna.share_videodirs),
				getConfigListEntry(_("Server Name"), config.plugins.minidlna.friendly_name),
				getConfigListEntry(_("Watch Local Folders"), config.plugins.minidlna.inotify),
				getConfigListEntry(_("Enable TIVO Compatibility"), config.plugins.minidlna.enable_tivo),
				getConfigListEntry(_("Strict DLNA Mode"), config.plugins.minidlna.strict_dlna),
				getConfigListEntry(_("Root Container"), config.plugins.minidlna.root_container),
			])
			if config.usage.setup_level.index >= 2: # expert
				list.extend([
					getConfigListEntry(_("Port"), config.plugins.minidlna.port),
					getConfigListEntry(_("Base path for Database"), config.plugins.minidlna.db_dir),
					getConfigListEntry(_("Log Directory"), config.plugins.minidlna.log_dir),
					getConfigListEntry(_("Album Art Names"), config.plugins.minidlna.album_art_names),
					getConfigListEntry(_("Serial Number"), config.plugins.minidlna.serial),
					getConfigListEntry(_("Model Number"), config.plugins.minidlna.model_number),
				])

		self["config"].list = list
		self["config"].l.setList(list)

	def _enabledChanged(self, enabled):
		self.createSetup()

	def layoutFinished(self):
		self.setTitle(_("Mediaserver (DLNA) Setup"))

	def save(self):
		dlna_config.apply()

	def _actionFinished(self, result, text):
		if result:
			self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=3)
			self.close()
		else:
			self.session.open(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=15)

	def _editShares(self):
		self.session.open(MiniDLNAShareSetup)

class MiniDLNAShareSetup(ConfigListScreen, Screen):
	skin = """
		<screen name="MiniDLNAShareSetup" position="center,center" size="560,400" title="Mediaserver (DLNA) Shares">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])

		self["key_red"] = StaticText(_("Remove"))
		self["key_green"] = StaticText(_("Add"))
		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self._removeDirectory,
			"green" : self._addDirectory,
			"cancel": self.save,
			"ok" : self.save,
		}, -2)

		self._shares = dlna_config.get()['media_dir']
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def _addDirectory(self):
		self._shares.append(ConfigText(default="/media/", fixed_size = False))
		self.createSetup()

	def _removeDirectory(self):
		index = self["config"].getCurrentIndex()
		if index >= 0 and index < len(self._shares):
			self._shares.pop(index)
			self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def createSetup(self):
		list = []
		i = 1
		for x in self._shares:
			list.append(getConfigListEntry(_("Share %s") %(i), x))
			i += 1
		self["config"].list = list
		self["config"].l.setList(list)

	def layoutFinished(self):
		self.setTitle(_("Mediaserver (DLNA) Shares"))

	def save(self):
		nep = []
		hasError = False
		for item in self._shares:
			if not os_path.exists(item.value):
				nep.append(item.value)
				hasError = True
		if hasError:
			text = _("""The following configured paths do not exist:\n%s
						\nProceed anyways?""") %("\n".join(nep))
			self.session.openWithCallback(self._onSaveErrorDecision, MessageBox, text, type=MessageBox.TYPE_YESNO)
		else:
			self._save()

	def _save(self):
		self._shares.save()
		self.close()

	def _onSaveErrorDecision(self, decision):
		if decision:
			self._save()

def main(session, **kwargs):
	session.open(MiniDLNASetup)

def autostart(reason, **kwargs):
	if reason == 0 and config.plugins.minidlna.enabled.value:
		dlna_config.startDaemon()

def menu(menuid, **kwargs):
	if menuid == "system":
		return [(_("Mediaserver (DLNA)"), main, "media_server_setup", None)]
	else:
		return []

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Mediaserver (DLNA) Setup"), description=_("Setup the DLNA Mediaserver"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=menu),
			PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)
		]
