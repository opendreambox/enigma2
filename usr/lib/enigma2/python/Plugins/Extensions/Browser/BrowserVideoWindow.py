from enigma import ePoint, eSize, getDesktop
from Components.VideoWindow import VideoWindow
from Screens.Screen import Screen

from Tools.Log import Log

class BrowserVideoWindow(Screen):
	skin = """
		<screen name="HbbTVVideoWindow" flags="wfNoBorder" zPosition="-1" position="0,0" size="1280,720" title="HbbTVVideoWindow" transparent="1">
			<widget name="video" position="0,0" zPosition="0" size="0,0" backgroundColor="transparent" transparent="1"/>
			<eLabel text="VIDEO HERE!" position="0,0" zPosition="1" size="200,30" font="Regular;18" foregroundColor="#7f848d" backgroundColor="#182946" />
		</screen>
	"""

	def __init__(self, session, point=ePoint(0, 0), size=eSize(0, 0)):
		Screen.__init__(self, session)
		desktopSize = getDesktop(0).size()
		self["video"] = VideoWindow(decoder=0, fb_width=desktopSize.width(), fb_height=desktopSize.height())

		self.__point = point
		self.__size = size
		self.__retainedPoint = point
		self.__retainedSize = size

		self.__isFullscreen = False
		self.onLayoutFinish.append(self._onLayoutFinished)

	def _onLayoutFinished(self):
		self.setRect(self.__point, self.__size, force=True)

	def setRect(self, point, size, retain=True, force=False):
		Log.w("%s,%s %s x %s" %(point.x(), point.y(), size.width(), size.height()))
		if point.x() != self.__point.x() or point.y() != self.__point.y() or force:
			self.instance.move(point)
			self.__point = point
		if size.width() != self.__size.width() or size.height() != self.__size.height() or force:
			self.instance.resize(size)
			self.__size = size
			self["video"].instance.resize(size)

		if retain:
			self.__retainedPoint = point
			self.__retainedSize = size

	def toggleFullscreen(self):
		if self.__isFullscreen:
			self.setRect(self.__retainedPoint, self.__retainedSize)
			self.__isFullscreen = False
		else:
			point = ePoint(0, 0)
			size = getDesktop(0).size()
			self.setRect(point, size, retain=False)
			self.__isFullscreen = True
		return self.__isFullscreen
