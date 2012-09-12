from enigma import eConsoleAppContainer
from glob import glob
from os import unlink

def erase(name):
	try:
		unlink(name)
		return True
	except:
		pass
	return False

class IpkgComponent:
	EVENT_INSTALL = 0
	EVENT_DOWNLOAD = 1
	EVENT_INFLATING = 2
	EVENT_CONFIGURING = 3
	EVENT_REMOVE = 4
	EVENT_UPGRADE = 5
	EVENT_LISTITEM = 9
	EVENT_DONE = 10
	EVENT_ERROR = 11
	EVENT_MODIFIED = 12

	CMD_INSTALL = 0
	CMD_LIST = 1
	CMD_REMOVE = 2
	CMD_UPDATE = 3
	CMD_UPGRADE = 4

	def __init__(self, ipkg = 'opkg'):
		self.ipkg = ipkg
		self.cmd = eConsoleAppContainer()
		self.cache = None
		self.callbackList = []
		self.setCurrentCommand()
		self.update_done = False

	def __del__(self):
		if self.update_done:
			self.cleanupPackageData()

	def cleanupPackageData(self):
		list_dirs = [ ]
		feed_names = [ ]
		for name in glob("/etc/opkg/*.conf"):
			f = open(name)
			for line in f.readlines():
				try:
					if line.startswith('lists_dir'):
						lists_dir = line.split(' ')[2].rstrip('\n\t ')
						if not lists_dir in list_dirs:
							list_dirs.append(lists_dir)
					elif line.startswith('src'):
						feed_name = line.split(' ')[1]
						if not feed_name in feed_names:
							feed_names.append(feed_name)
				except:
					print 'IpkgComponent error parsing', name, 'line', line.rstrip('\n\t ')
			f.close()
		if not '/var/lib/opkg' in list_dirs:
			list_dirs.append('/var/lib/opkg')
		for feed in feed_names:
			for list_dir in list_dirs:
				path = list_dir + '/' + feed
				if erase(path):
					print 'IpkgComponent erased', path
		self.update_done = False

	def setCurrentCommand(self, command = None):
		self.currentCommand = command

	def runCmd(self, cmd):
		print "executing", self.ipkg, cmd
		self.cmd.appClosed.append(self.cmdFinished)
		self.cmd.dataAvail.append(self.cmdData)
		if self.cmd.execute(self.ipkg + " " + cmd):
			self.cmdFinished(-1)

	def startCmd(self, cmd, args = None):
		if cmd == self.CMD_UPDATE:
			self.runCmd("update")
			self.update_done = True
		elif cmd == self.CMD_UPGRADE:
			append = ""
			if args["use_maintainer"]:
				append += " --force-maintainer"
			if args["test_only"]:
				append += " -test"
			self.runCmd("upgrade" + append)
		elif cmd == self.CMD_LIST:
			self.fetchedList = []
			if args['installed_only']:
				self.runCmd("list-installed")
			else:
				self.runCmd("list")
		elif cmd == self.CMD_INSTALL:
			self.runCmd("install " + args['package'])
		elif cmd == self.CMD_REMOVE:
			append = ""
			if args["autoremove"]:
				append = "--autoremove "
			self.runCmd("remove " + append + args['package'])
		self.setCurrentCommand(cmd)

	def cmdFinished(self, retval):
		self.callCallbacks(self.EVENT_DONE)
		self.cmd.appClosed.remove(self.cmdFinished)
		self.cmd.dataAvail.remove(self.cmdData)

	def cmdData(self, data):
		print "data:", data
		if self.cache is None:
			self.cache = data
		else:
			self.cache += data

		if '\n' in data:
			splitcache = self.cache.split('\n')
			if self.cache[-1] == '\n':
				iteration = splitcache
				self.cache = None
			else:
				iteration = splitcache[:-1]
				self.cache = splitcache[-1]
			for mydata in iteration:
				if mydata != '':
					self.parseLine(mydata)
		
	def parseLine(self, data):
		if self.currentCommand == self.CMD_LIST:
			item = data.split(' - ', 2)
			self.fetchedList.append(item)
			self.callCallbacks(self.EVENT_LISTITEM, item)
		else:
			if data.find('Downloading') == 0:
				self.callCallbacks(self.EVENT_DOWNLOAD, data.split(' ', 5)[1].strip())
			elif data.find('Upgrading') == 0:
				self.callCallbacks(self.EVENT_UPGRADE, data.split(' ', 1)[1].split(' ')[0])
			elif data.find('Installing') == 0:
				self.callCallbacks(self.EVENT_INSTALL, data.split(' ', 1)[1].split(' ')[0])
			elif data.find('Removing') == 0:
				self.callCallbacks(self.EVENT_REMOVE, data.split(' ', 1)[1].split(' ')[1])
			elif data.find('Configuring') == 0:
				self.callCallbacks(self.EVENT_CONFIGURING, data.split(' ', 1)[1].split(' ')[0])
			elif data.find('An error occurred') == 0:
				self.callCallbacks(self.EVENT_ERROR, None)
			elif data.find('Failed to download') == 0:
				self.callCallbacks(self.EVENT_ERROR, None)
			elif data.find('ipkg_download: ERROR:') == 0:
				self.callCallbacks(self.EVENT_ERROR, None)
			elif data.find('    Configuration file \'') >= 0:
				# Note: the config file update question doesn't end with a newline, so
				# if we get multiple config file update questions, the next ones
				# don't necessarily start at the beginning of a line
				self.callCallbacks(self.EVENT_MODIFIED, data.split(' \'', 1)[1][:-1])

	def callCallbacks(self, event, param = None):
		for callback in self.callbackList:
			callback(event, param)

	def addCallback(self, callback):
		self.callbackList.append(callback)

	def getFetchedList(self):
		return self.fetchedList

	def stop(self):
		self.cmd.kill()

	def isRunning(self):
		return self.cmd.running()

	def write(self, what):
		if what:
			# We except unterminated commands
			what += "\n"
			self.cmd.write(what, len(what))
