from Components.StreamServerControl import StreamServerControl
from Plugins.Plugin import PluginDescriptor
from StreamServerConfig import StreamServerConfig, applyConfig as applyStreamServerConfig


def main(session, **kwargs):
	session.open(StreamServerConfig)

def menu(menuid, **kwargs):
	if menuid == "network":
		return [(_("Streaming Server Setup"), main, "streamserversetup", 47)]
	return []

def autostart(reason, session=None, **kwargs):
	if reason == 0:
		ssc = StreamServerControl()
		if ssc.isConnected():
			applyStreamServerConfig(ssc)

def Plugins(**kwargs):
	return [ PluginDescriptor(name=_("Streaming Server Setup"), description=_("Streaming Server Setup"), where=PluginDescriptor.WHERE_MENU, fnc=menu),
			 PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
		 ]
