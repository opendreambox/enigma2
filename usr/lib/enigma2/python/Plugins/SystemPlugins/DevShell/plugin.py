from Plugins.Plugin import PluginDescriptor

from Tools.Log import Log

from twisted.conch.insults import insults
from twisted.conch.manhole import ColoredManhole
from twisted.conch.telnet import TelnetBootstrapProtocol, TelnetTransport
from twisted.internet import protocol, reactor

def main(reason, *args):
	Log.w(main.listeningPort)
	if main.listeningPort:
		return
	f = protocol.ServerFactory()
	f.protocol = lambda: TelnetTransport(TelnetBootstrapProtocol, insults.ServerProtocol, ColoredManhole)
	main.listeningPort = reactor.listenTCP(8007, f, interface='localhost')

main.listeningPort = None

def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=main),]
