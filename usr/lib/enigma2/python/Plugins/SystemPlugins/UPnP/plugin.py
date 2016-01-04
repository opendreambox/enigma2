from enigma import eNetworkManager

from Components.config import config
from Components.ResourceManager import resourcemanager
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.UPnP.DreamboxMediaStore import restartMediaServer

from UPnPConfig import UPnPConfig, getUUID

def upnp_start(reason, **kwargs):
	if reason == 0 and config.plugins.mediaserver.enabled.value:
		restartMediaServer(
				config.plugins.mediaserver.name.value,
				getUUID(config.plugins.mediaserver.uuid),
				manufacturer='dreambox',
				manufacturer_url='http://www.dreambox.de',
				model_description='Dreambox MediaServer',
				model_name=config.plugins.mediaserver.name.value,
				model_number=config.plugins.mediaserver.name.value,
				model_url='http://www.dreambox.de'
			)

def session_start(reason, session=None, **kwargs):
	if reason == 0 and session != None:
		cp = resourcemanager.getResource("UPnPControlPoint")
		if cp:
			cp.setSession(session)

def upnp_setup(session, **kwargs):
	session.open(UPnPConfig)

def upnp_menu(menuid, **kwargs):
	if menuid == "network":
		return [(_("UPnP/DLNA"), upnp_setup, "upnp_setup", None)]
	else:
		return []

def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=session_start),
			PluginDescriptor(where=PluginDescriptor.WHERE_UPNP, fnc=upnp_start),
			PluginDescriptor(name=_("UPnP/DLNA Setup"), description=_("Setup UPnP/DLNA Services"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=upnp_menu)
		]
