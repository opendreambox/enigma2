from Components.ResourceManager import resourcemanager
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.UPnP.DreamboxServiceStore import DreamboxServiceStore
from Tools.HardwareInfo import HardwareInfo

global instance
instance = None

def start(reason, **kwargs):
	global instance
	session = kwargs.get('session', None)
	if session and reason == 0:
		cp = resourcemanager.getResource("UPnPControlPoint")
		if cp:
			instance = cp.registerServer(DreamboxServiceStore, name=_("%s (TV & Radio)" %(HardwareInfo().get_device_name())))
	else:
		if instance != None:
			instance.unregister()

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=start) ]
