from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigBoolean
import NetworkWizard

config.misc.firstrun = ConfigBoolean(default = True)

def runNetworkWizard(*args, **kwargs):
	return NetworkWizard.NetworkWizard(*args, **kwargs)

def Plugins(**kwargs):
	list = []
	if config.misc.firstrun.value:
		NetworkWizard.firstRun = True
		NetworkWizard.checkNetwork = True
		list.append(PluginDescriptor(name=_("Network Wizard"), where = PluginDescriptor.WHERE_WIZARD, needsRestart = False, fnc=(25, runNetworkWizard)))
	return list

