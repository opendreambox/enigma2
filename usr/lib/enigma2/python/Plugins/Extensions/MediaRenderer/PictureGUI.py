from enigma import eTimer
from Tools.Log import Log

try:
	from Plugins.Extensions.PicturePlayer.plugin import Pic_Full_View
	class PictureGUI(Pic_Full_View):
		def __init__(self, session, filelist, index, path):
			Pic_Full_View.__init__(self, session, filelist, index, path)
			self.__delayed_close_timer = eTimer()
			self.__delayed_close_timer_conn = self.__delayed_close_timer.timeout.connect(self.close)

		def delayedClose(self):
			Log.i()
			self.__delayed_close_timer.stop()
			self.__delayed_close_timer.startLongTimer(4)
except:
	Log.w("The UPnP/DLNA PictureGUI won't be available")
