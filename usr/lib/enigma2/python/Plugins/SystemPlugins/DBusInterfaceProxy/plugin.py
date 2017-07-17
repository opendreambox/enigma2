from enigma import eDBusInterface, eDBusInterfaceProxy, eServiceReference
from Components.VolumeControl import VolumeControl
from Plugins.Plugin import PluginDescriptor
from Screens.MoviePlayer import MoviePlayer
from Tools.Log import Log

from time import time

class DBusInterfaceProxy(eDBusInterfaceProxy):
	proxyInstance = None

	def __init__(self, session):
		assert not DBusInterfaceProxy.instance
		eDBusInterfaceProxy.__init__(self)
		DBusInterfaceProxy.proxyInstance = self
		self._session = session
		self._player = None

	def play(self, val, isUri):
		Log.w("%s %s" %(val, isUri))
		if isUri:
			val = val.split("#")
			uri = val[0]
			if len(val) > 1:
				name = val[1]
			else:
				name = uri.split("/")[-1]
			if uri.startswith("file://") or uri.startswith("/"): #Local File
				if uri.lower().endswith(".ts"):
					serviceType = eServiceReference.idDVB
				elif uri.lower().endswith(".m2ts"):
					serviceType = eServiceReference.idM2TS
				else:
					serviceType = eServiceReference.idGST
				uri = uri.replace("file://", "")
				ref = eServiceReference(serviceType, 0, uri)
			else:
				ref = eServiceReference(eServiceReference.idURI, 0, uri)
				ref.setName(name)
		else:
			ref = eServiceReference(val)
		if not ref.valid():
			return False
		if not self._player:
			self._player = self._session.openWithCallback(self._onPlayerClosed, MoviePlayer, ref)
		else:
			self._player.playService(ref)
		return True

	def isTimerPending(self):
		next_rec_time = self._session.nav.RecordTimer.getNextRecordingTime()
		return next_rec_time > 0 and (next_rec_time - time()) < 360

	def setVolume(self, to):
		if to < 0 or to > 100 or not VolumeControl.instance:
			return False
		VolumeControl.instance.setDiscreteVolume(to)
		return True

	def _onPlayerClosed(self):
		Log.i("Playback stopped!")
		self._player = None

def registerProxy(session, *args, **kwargs):
	eDBusInterface.setProxy(DBusInterfaceProxy(session))

def Plugins(**kwargs):
	return PluginDescriptor(name=_("DBus Interface Python Proxy"), description=_("Supplies DBus with some additional functionality"), where = PluginDescriptor.WHERE_SESSIONSTART, needsRestart = False, fnc=registerProxy)
