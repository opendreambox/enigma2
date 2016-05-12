from Components.StreamServerControl import streamServerControl
from Plugins.Plugin import PluginDescriptor
from StreamServerConfig import StreamServerConfig, applyConfig as applyStreamServerConfig
from Tools.Log import Log

from WatchDog import WatchDog
def main(session, **kwargs):
	session.open(StreamServerConfig)

external_start = []
external_shutdown = []

def menu(menuid, **kwargs):
	if menuid == "network":
		return [(_("Streaming Server"), main, "streamserversetup", 47)]
	return []

def availabilityChanged(available):
	Log.w("available=%s" %available)
	if available:
		applyStreamServerConfig(streamServerControl)
	else:
		streamServerControl.stopEncoderService()

def autostart(reason, session=None, **kwargs):
	if reason == 0:
		if session:
			WatchDog()
			streamServerControl.start()
			streamServerControl.onAvailabilityChanged.append(availabilityChanged)
			if streamServerControl.isConnected():
				applyStreamServerConfig(streamServerControl, initial=True)
			for fnc in external_start:
				fnc()
	else:
		for fnc in external_shutdown:
			fnc()

def Plugins(**kwargs):
	return [ PluginDescriptor(name=_("Streaming Server Setup"), description=_("Streaming Server Setup"), where=PluginDescriptor.WHERE_MENU, fnc=menu),
			 PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
		 ]
