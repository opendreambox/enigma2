from enigma import eServiceReference, ePicLoad
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.ResourceManager import resourcemanager
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap

import bludiscmenu

bd_paths = ["/media/bludisc/","/autofs/sr0"]

class BludiscMenu(Screen):
	skin = """
	<screen name="BludiscMenu" position="90,55" size="560,480" title="Bludisc Player">
			<widget name="pixmap" position="8,8" size="544,306" />
			<widget name="menu" position="8,320" size="544,150" scrollbarMode="showOnDemand" />
	</screen>"""
	def __init__(self, session, bd_mountpoint = None):
		
		Screen.__init__(self, session)
		self.tried_bdpath = 0
		self.bd_mountpoint = bd_mountpoint or bd_paths[self.tried_bdpath]
		self.list = []
		self["menu"] = MenuList(self.list)
		self.session = session
		self.onFirstExecBegin.append(self.opened)
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.picdecodedCB)
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((544, 306, sc[0], sc[1], False, 1, '#ff000000'))
		self["pixmap"] = Pixmap()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.ok,
			"cancel": self.exit,
			"red": self.exit,
			"green": self.ok,
			"yellow": self.settings,
		}, -1)

	def opened(self):
		bd_titles = bludiscmenu.getTitles(self.bd_mountpoint)
		print 'bludiscmenu.getTitles("%s") returns', self.bd_mountpoint, bd_titles
		if bd_titles:
		  	(di_name, country, thumbs, titles) = bd_titles
			for idx, duration, chapters, angels, clips, title_no, title_name in titles:
				titlestring = "%d. %s (%02d:%02d:%02d), %d %s" % (title_no or idx, title_name or _("Title"), (duration / 3600), ((duration % 3600) / 60), (duration % 60), chapters, _("chapters"))
				self.list.append((titlestring, idx))
			self["menu"].l.setList(self.list)
			if thumbs and thumbs[0][0]:
				max_x = 0
				thumb_filename = thumbs[0][0]
				for filename, x, y in thumbs:
					print filename, x, y
					if x > max_x or ( x == -1 and filename.find("lg") > 0 ):
						thumb_filename = filename
			        thumb_path = self.bd_mountpoint+"/BDMV/META/DL/"+thumb_filename
			        print "decoding thumbnail:", thumb_path
				self.picload.startDecode(thumb_path)
			if di_name:
				self.setTitle(_("Bludisc Player") + ": " + di_name)
		elif self.tried_bdpath < len(bd_paths)-1:
				self.tried_bdpath += 1
				self.bd_mountpoint = bd_paths[self.tried_bdpath]
				self.opened()

	def picdecodedCB(self, picInfo = None):
		ptr = self.picload.getData()
		if ptr is not None:
			self["pixmap"].instance.setPixmap(ptr.__deref__())

	def ok(self):
		if type(self["menu"].getCurrent()) is type(None):
			self.exit()
			return
		name = self["menu"].getCurrent()[0]
		idx = self["menu"].getCurrent()[1]
		newref = eServiceReference(0x04, 0, "%s:%03d" % (self.bd_mountpoint, idx))
		newref.setData(1,1)
		newref.setName("Bludisc title %d" % idx)
		print "[Bludisc] play: ", name, newref.toString()		
		self.session.openWithCallback(self.moviefinished, BludiscPlayer, newref)

	def settings(self):
		pass

	def moviefinished(self):
		print "Bludisc playback finished"

	def exit(self):
		self.close()

class BludiscPlayer(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			list = (
				(_("Yes"), "quit"),
				(_("No"), "continue")
			)
			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def showMovies(self):
		pass

	def movieSelected(self, service):
		pass

def main(session, **kwargs):
	session.open(BludiscMenu)

def autostart(reason, **kwargs):
	resourcemanager.addResource("Bludisc", main)

from Plugins.Plugin import PluginDescriptor

def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath
	return [
		Scanner(mimetypes = ["video/x-bluray"],
			paths_to_scan =
				[
					ScanPath(path = "BDMV", with_subdirs = False),
				],
			name = "Bludisc",
			description = _("Play Bludisc"),
			openfnc = filescan_open,
		)]

def filescan_open(list, session, **kwargs):
	print "filescan_open", list, list[0].mimetype, list[0].path
	if len(list) >= 1 and list[0].mimetype == "video/x-bluray":
		pos = list[0].path.find("BDMV")
		path = None
		if pos > 0:
			path = list[0].path[:pos]
		session.open(BludiscMenu, bd_mountpoint=path)
		return

def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [("Bludisc Player", main, "bludiscplayer", 47)]
	return []

def Plugins(**kwargs):
	return [ PluginDescriptor(name = "BludiscPlayer", description = _("Play Bludisc"), where = PluginDescriptor.WHERE_MENU, fnc = menu),
		PluginDescriptor(where = PluginDescriptor.WHERE_FILESCAN, fnc = filescan)]
		#PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart) ]
