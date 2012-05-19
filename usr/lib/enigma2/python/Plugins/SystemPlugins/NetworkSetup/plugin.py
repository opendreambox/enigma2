from Plugins.Plugin import PluginDescriptor

def autostart(reason, **kwargs):
	if "session" in kwargs:
		from Components.ResourceManager import resourcemanager
		from NetworkSetup import NetworkAdapterSelection, AdapterSetup
		resourcemanager.addResource("NetworkAdapterSelection", NetworkAdapterSelection)
		resourcemanager.addResource("AdapterSetup", AdapterSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, needsRestart = False, fnc = autostart)]

