from Plugins.Plugin import PluginDescriptor

def autostart(reason, **kwargs):
	if "session" in kwargs:
		from Components.ResourceManager import resourcemanager
		from NetworkSetup import NetworkAdapterSelection, NameserverSetup, AdapterSetup
		resourcemanager.addResource("NetworkAdapterSelection", NetworkAdapterSelection)
		resourcemanager.addResource("NameserverSetup", NameserverSetup)
		resourcemanager.addResource("AdapterSetup", AdapterSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, needsRestart = False, fnc = autostart)]

