from __future__ import absolute_import
from Components.ResourceManager import resourcemanager
from .UPnPCore import ManagedControlPoint

from enigma import eNetworkManager

def EarlyPlugins(**kwargs):
	cp = ManagedControlPoint()
	resourcemanager.addResource("UPnPControlPoint", cp)
	if eNetworkManager.getInstance().online():
		cp.start()

def onOnlineChanged(isOnline):
	cp = resourcemanager.getResource("UPnPControlPoint")
	if not cp:
		return
	if isOnline:
		cp.start()
	else:
		cp.shutdown()

_upnpOnlineChangedConn = eNetworkManager.getInstance().onlineChanged.connect(onOnlineChanged)