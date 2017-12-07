from enigma import eWebMediaPlayer, eWebMediaPlayerProxy, eServiceReference
from Components.VolumeControl import VolumeControl

from Tools.Log import Log

class WebMediaPlayerProxy(eWebMediaPlayerProxy):
	proxyInstance = None

	def __init__(self, session, player):
		assert not WebMediaPlayerProxy.proxyInstance
		eWebMediaPlayerProxy.__init__(self)
		WebMediaPlayerProxy.proxyInstance = self
		self._session = session
		self.player = player

	def setVideoWindow(self, x, y, width, height):
		if self.player:
			if width > 0 and height > 0:
				self.player.setVideoWindow(x, y, width, height)
			else:
				self.player.resetVideoWindow()

	@staticmethod
	def register(player):
		proxy = WebMediaPlayerProxy(player.session, player)
		eWebMediaPlayer.setProxy(proxy)
		return proxy
	
	@staticmethod
	def unregister(player):
		if player == WebMediaPlayerProxy.proxyInstance.player:
			WebMediaPlayerProxy.proxyInstance = None
			eWebMediaPlayer.resetProxy()

	def play(self, val, isUri):
		Log.w("%s %s" %(val, isUri))
		if not self.player:
			return
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
		self.stop()
		self.player.playStream(ref);
		return True

	def stop(self):
		Log.w()
		if self.player:
			self.player.stopStream()
			return True
		return False

	def setVolume(self, to):
		if to < 0 or to > 100 or not VolumeControl.instance:
			return False
		VolumeControl.instance.setDiscreteVolume(to)
		return True



