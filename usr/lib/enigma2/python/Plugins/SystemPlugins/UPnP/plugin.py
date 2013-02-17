from Plugins.Plugin import PluginDescriptor
from Components.ResourceManager import resourcemanager

#shut down the controlpoint with all devices we registered until now so they disappear from all clients
def autostart(reason, **kwargs):
	if reason == 1:
		cp = resourcemanager.getResource("UPnPControlPoint")
		if cp:
			cp.shutdown()

def Plugins(**kwargs):
	return PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart)