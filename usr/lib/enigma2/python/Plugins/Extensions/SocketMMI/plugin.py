from Tools.BoundFunction import boundFunction
from Plugins.Plugin import PluginDescriptor
from SocketMMI import SocketMMIMessageHandler

socketHandler = None

def menuCallback(slot, session, **kwargs):
	socketHandler.startMMI(slot)

def menu(menuid, **kwargs):
	ret = [ ]
	if menuid == "setup" and socketHandler:
		connections = socketHandler.numConnections()
		slot = 0;
		valid = 0;
		while valid < connections and slot < 256:
			if socketHandler.getState(slot):
				ret.append((socketHandler.getName(slot), boundFunction(menuCallback, slot), "socket_mmi_%d" %valid, 0))
				valid += 1
			slot += 1
	return ret

def sessionstart(reason, session):
	socketHandler.setSession(session)

def autostart(reason, **kwargs):
	global socketHandler
	if reason == 1:
		socketHandler = None
	else:
		if socketHandler is None:
			socketHandler = SocketMMIMessageHandler()
		else:
			print "[SocketMMI] - socketHandler already connected."

def Plugins(**kwargs):
	return [ PluginDescriptor(name = "SocketMMI", description = _("Python frontend for /tmp/mmi.socket"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc = menu),
		PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, needsRestart = True, fnc = sessionstart),
		PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, needsRestart = True, fnc = autostart) ]

