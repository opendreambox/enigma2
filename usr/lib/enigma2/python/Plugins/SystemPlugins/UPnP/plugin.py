from Components.config import config
from Components.ResourceManager import resourcemanager
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.UPnP.DreamboxMediaStore import restartMediaServer

from UPnPConfig import UPnPConfig, getUUID

def session_start(reason, **kwargs):
	session = kwargs.get('session', None)
	if session and reason == 0 and config.plugins.mediaserver.enabled.value:
		restartMediaServer(config.plugins.mediaserver.name.value, getUUID(config.plugins.mediaserver.uuid))

#shut down the controlpoint with all devices we registered until now so they disappear from all clients
def autostart(reason, **kwargs):
	if reason == 1:
		cp = resourcemanager.getResource("UPnPControlPoint")
		if cp:
			cp.shutdown()

def upnp_setup(session, **kwargs):
	session.open(UPnPConfig)

def upnp_menu(menuid, **kwargs):
	if menuid == "system":
		return [(_("UPnP/DLNA"), upnp_setup, "upnp_setup", None)]
	else:
		return []

def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
			PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=session_start),
			PluginDescriptor(name=_("UPnP/DLNA Setup"), description=_("Setup UPnP/DLNA Services"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=upnp_menu)
		]
