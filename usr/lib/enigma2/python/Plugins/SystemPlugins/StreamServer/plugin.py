from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor
from .StreamServerConfig import StreamServerConfig

def main(session, **kwargs):
	session.open(StreamServerConfig)

external_start = []
external_shutdown = []

def menu(menuid, **kwargs):
	if menuid == "network":
		return [(_("Streaming Server"), main, "streamserversetup", 47)]
	return []

def Plugins(**kwargs):
	return [ PluginDescriptor(name=_("Streaming Server Setup"), description=_("Streaming Server Setup"), where=PluginDescriptor.WHERE_MENU, fnc=menu) ]
