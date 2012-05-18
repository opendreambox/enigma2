from enigma import eHbbtv, eServiceReference, ePoint, eSize, getDesktop
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.VideoWindow import VideoWindow

from MoviePlayer import MoviePlayer

class HbbtvVideoOverlay(Screen):
	skin = """
		<screen name="HbbtvVideoOverlay" flags="wfNoBorder" position="0,0" size="1280,720" title="HbbtvVideoOverlay" >
			<widget name="Video" position="0,0" zPosition="9999" size="0,0" backgroundColor="transparent"/>
		</screen>
	"""

	def __init__(self, session, point = ePoint(0,0), size = eSize(0,0) ):
		Screen.__init__(self, session)
		desktopSize = getDesktop(0).size()
		self.__video = VideoWindow(decoder = 0, fb_width=1280, fb_height=720)
		self["Video"] = self.__video
		self.__point = point
		self.__size = size
		self.onFirstExecBegin.append(self.__onFirstExecBegin)

	def __onFirstExecBegin(self):
		self.setRect(self.__point, self.__size)

	def setRect(self, point, size):
		self.__video.move(point)
		self.__video.resize(size)
		self.__point = point
		self.__size = size

class Hbbtv(object):
	instance = None

	def __init__(self, session):
		assert Hbbtv.instance is None, "Hbbtv is a singleton class and may only be initialized once!"
		Hbbtv.instance = self
		from Screens.InfoBar import InfoBar

		self.session = session
		self.eHbbtv = eHbbtv.getInstance()
		self.eHbbtv.playServiceRequest.get().append(self.zap)
		self.eHbbtv.playStreamRequest.get().append(self.stream)
		self.eHbbtv.nextServiceRequest.get().append(self.nextService)
		self.eHbbtv.prevServiceRequest.get().append(self.prevService)
		InfoBar.instance.onServiceListRootChanged.append(self.setCurrentBouquet)

		self.__overlay = None

	def zap(self, sref):
		self.session.nav.playService(eServiceReference(sref))

	def stream(self, sref):
		self.session.open(MoviePlayer, eServiceReference(sref))

	def nextService(self):
		ib = InfoBar.instance
		ib.zapDown()

	def prevService(self):
		ib = InfoBar.instance
		ib.zapUp()

	def setVideoWindow(self, x, y, w, h):
		print "[Hbbtv].setVideoWindow x=%s, y=%s, w=%s, h=%s" %(x, y, w, h)
		if w < 1280 and h < 720:
			p = ePoint(x, y)
			s = eSize(w, h)
			if not self.__overlay:
				self.__overlay = self.session.instantiateDialog(HbbtvVideoOverlay, point = p, size = s)
			else:
				self.__overlay.setRect(p, s)
			self.__overlay.show()
		else:
			if self.__overlay:
				self.__overlay.hide()

	def setCurrentBouquet(self, ref):
		self.eHbbtv.setServiceList(ref.toString())

def start(session, **kwargs):
	Hbbtv(session)