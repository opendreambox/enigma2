from Components.StreamServerControl import streamServerControl
from Plugins.Plugin import PluginDescriptor
from Screens.MoviePlayer import MoviePlayer
from StreamServerConfig import StreamServerConfig, applyConfig as applyStreamServerConfig

from Tools.Log import Log

def main(session, **kwargs):
	session.open(StreamServerConfig)

def menu(menuid, **kwargs):
	if menuid == "network":
		return [(_("Streaming Server Setup"), main, "streamserversetup", 47)]
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
			if streamServerControl.isConnected():
				applyStreamServerConfig(streamServerControl, initial=True)
				streamServerControl.onAvailabilityChanged.append(availabilityChanged)

def doPlay(session, ref):
	if session and ref:
		session.open(MoviePlayer, ref, streamMode=True)

def Plugins(**kwargs):
	return [ PluginDescriptor(name=_("Streaming Server Setup"), description=_("Streaming Server Setup"), where=PluginDescriptor.WHERE_MENU, fnc=menu),
			 PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
		 ]
