from enigma import eMediaDatabase, StringList
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from FileBrowser import FileBrowser

class MediaDatabaseManager(Screen):
	skin = """
		<screen name="MediaDatabaseManager" position="center,120" size="820,520" title="Database Manager">
			<widget name="red" position="10,5" size="200,40" pixmap="skin_default/buttons/red.png" />
			<widget name="green" position="210,5" size="200,40" pixmap="skin_default/buttons/green.png" />
			<widget name="yellow" position="410,5" size="200,40" pixmap="skin_default/buttons/yellow.png" />
			<widget name="blue" position="610,5" size="200,40" pixmap="skin_default/buttons/blue.png" />
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget source="list" render="Listbox" position="10,60" size="800,390">
				<convert type="StringList" />
			</widget>
			<widget name="status" position="10,465" size="800,45" zPosition="2" font="Regular;20" halign="center" valign="top" backgroundColor="background" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["list"] = List([], enableWrapAround=True)
		self["key_red"] = Button(_("Remove"))
		self["key_green"] = Button(_("Add"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Rescan"))
		self["status"] = Label(_("waiting for statistics..."))

		# Background for Buttons
		self["red"] = Pixmap()
		self["green"] = Pixmap()
		self["yellow"] = Pixmap()
		self["blue"] = Pixmap()

		self._db = eMediaDatabase.getInstance()
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok" : self._ok,
			"cancel" : self.close,
			"red" : self._red,
			"green" : self._green,
			"yellow" : self._yellow,
			"blue" : self._blue
		}, -2)

		self._db_scanStatistics_conn = self._db.scanStatistics.connect(self._onScanStatistics)
		self._db_scanFinished_conn = self._db.scanFinished.connect(self._onScanFinished)
		self._db_insertFinished_conn = self._db.insertFinished.connect(self._onInsertFinished)
		self.onLayoutFinish.append(self._onLayoutFinish)
		self.onClose.append(self._onClose)

	def _onClose(self):
		self._db_scanStatistics_conn = self._db_scanFinished_conn = self._db_insertFinished_conn = None

	def _onLayoutFinish(self):
		self._db.requestScanStatistics()
		self._reload()

	def _onScanStatistics(self, directory, total, successful, skipped, reload=True):
		self["status"].setText(_("Scanning '%s' for media files. Scanned %s files.\n%s of them contain audio or video.") %(directory, total, successful))
		if reload:
			self._reload()

	def _onScanFinished(self, directory, total, successful, skipped):
		self["status"].setText(_("'%s' contained a total of %s files.\n%s of them contain audio or video.") %(directory, total, successful))

	def _onInsertFinished(self, *args):
		self._reload()

	def _reload(self):
		result = self._db.getParentDirectories();
		currentDir = self._db.getCurrentScanPath()
		enqueued = StringList()
		self._db.getEnqueuedPaths(enqueued)
		l = []

		for dir in result.data():
			path = str(dir["path"])
			if path == currentDir:
				count = _("scanning...")
			else:
				if path in enqueued:
					count = _("enqueued for future scan...")
				else:
					dir_id = str(dir["id"])
					params = StringList((dir_id,dir_id))
					count = self._db.query(
								"""SELECT COUNT(t_files.id) as count
									 FROM t_files
									  INNER JOIN t_directories
									   ON ( t_directories.id = t_files.dir_id AND parent_id = ? )
									   OR ( t_directories.id =  t_files.dir_id and t_directories.id = ? );""", params)
					try:
						count = count.data()[0]["count"]
					except:
						count = _("n/a")
			item = "%s (%s)" %(path, count)

			l.append( (item, dir) )
		index = self["list"].index
		if index > len(l)-1:
			index = len(l)-1

		self["list"].list = l
		self["list"].index = index


	def _ok(self):
		pass

	def _red(self):
		dir = self._getSelectedDir()
		if dir:
			self.session.openWithCallback(self._onDeleteConfirmed, MessageBox, _("Do you really want to remove the directory %s and all of it's content from the database?") % dir, type=MessageBox.TYPE_YESNO)

	def _green(self):
		self.session.openWithCallback(self._onDirectorySelected, FileBrowser, showFiles=False, closeOnSelection=True)

	def _yellow(self):
		pass

	def _blue(self):
		dir = self._getSelectedDir()
		if dir:
			self._db.rescanPath(dir)
			#self.session.toaster.toast(Toast, _("Rescanning %s") % (dir))
			self._reload()

	def _getSelectedDir(self):
		dir = self["list"].getCurrent()
		print dir
		if dir:
			dir = dir[1]["path"]
		return dir

	def _onDirectorySelected(self, path=None):
		if path:
			known = self._db.getParentDirectories()
			if not known.error():
				for dir in known.data():
					if path.startswith(dir["path"]):
						return
			if path[-1:] == '/':
				path = path[:-1]
			self._db.addPath(path)
			self._reload()

	def _onDeleteConfirmed(self, confirmed):
		if confirmed:
			dir = self["list"].getCurrent()
			if dir:
				path = dir[1]["path"]
				id = int(dir[1]["id"])
				res = self._db.deleteParentDirectory(id)
				if res.error():
					self.session.open(MessageBox, _("Removing %s from the database failed with\n %s") %(path, res.errorDatabaseText()), type=MessageBox.TYPE_ERROR)
				else:
					self.session.open(MessageBox, _("Directory %s has been removed from the database!") %path, type=MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox,  _("Removing a directory from the database failed!"), type=MessageBox.TYPE_ERROR)
		self._reload()
