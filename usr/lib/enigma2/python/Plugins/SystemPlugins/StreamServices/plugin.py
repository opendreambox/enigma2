from __future__ import absolute_import
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from .StreamServicesConfig import StreamServicesConfigScreen

def main(session, **kwargs):
	session.open(StreamServicesConfigScreen)

def menu(menuid, **kwargs):
	if menuid == "network" and config.usage.setup_level.index > 0:
		return [(_("Stream Services"), main, "streamservicessetup", 47)]
	return []

def Plugins(**kwargs):
	return [ PluginDescriptor(name=_("Stream Services Setup"), description=_("Stream Services Setup"), where=PluginDescriptor.WHERE_MENU, fnc=menu) ]
