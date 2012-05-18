# -*- coding: UTF-8 -*-
from Components.ResourceManager import resourcemanager

from Plugins.SystemPlugins.UPnP.UPnPMediaRenderer import UPnPMediaRenderer
from Plugins.Plugin import PluginDescriptor

global instance
instance = None
def start(reason, **kwargs):
	global instance
	session = kwargs.get('session', None)
	if session and reason == 0:
		cp = resourcemanager.getResource("UPnPControlPoint")
		if cp:
			instance = cp.registerRenderer(UPnPMediaRenderer, session=session)
	else:
		if instance != None:
			instance.unregister()

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=start) ]