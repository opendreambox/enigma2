from Components.ResourceManager import resourcemanager
from Hotplug import Hotplug
from Plugins.Plugin import PluginDescriptor

class HotplugNotifier():
	def append(self, callback):
		hotplug = resourcemanager.getResource("Hotplug")
		if hotplug:
			hotplug.registerEventCallback(callback)
	def remove(self, callback):
		hotplug = resourcemanager.getResource("Hotplug")
		if hotplug:
			hotplug.unregisterEventCallback(callback)

# Used by Netlink and event listeners. Needs to stay here
# for backwards compatibility. New users should use the
# resourceManager and (un-)registerEventCallback directly.
hotplugNotifier = HotplugNotifier()

def autostart(reason, **kwargs):
	if reason == 0:
		resourcemanager.addResource("Hotplug", Hotplug())
	elif reason == 1:
		hotplug = resourcemanager.getResource("Hotplug")
		if hotplug:
			resourcemanager.removeResource("Hotplug")
			hotplug.release()

def Plugins(**kwargs):
	return PluginDescriptor(name = "Hotplug", description = "listens to hotplug events", where = PluginDescriptor.WHERE_AUTOSTART, needsRestart = True, fnc = autostart)
