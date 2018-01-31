from Plugins.Plugin import PluginDescriptor

from twisted.conch.insults import insults
from twisted.conch.manhole import ColoredManhole
from twisted.conch.telnet import TelnetBootstrapProtocol, TelnetTransport
from twisted.internet import protocol, reactor

def main(*args, **kwargs):
	f = protocol.ServerFactory()
	f.protocol = lambda: TelnetTransport(TelnetBootstrapProtocol, insults.ServerProtocol, ColoredManhole)
	reactor.listenTCP(8007, f, interface='localhost')

def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=main),]
