from enigma import eConsoleAppContainer

class IpkgComponent:
	EVENT_INSTALL = 0
	EVENT_DOWNLOAD = 1
	EVENT_CONFIGURING = 3
	EVENT_REMOVE = 4
	EVENT_UPGRADE = 5
	EVENT_LISTITEM = 9
	EVENT_DONE = 10
	EVENT_ERROR = 11

	CMD_INSTALL = 0
	CMD_LIST = 1
	CMD_REMOVE = 2
	CMD_UPDATE = 3
	CMD_UPGRADE = 4

	def __init__(self, ipkg = 'opkg'):
		self.ipkg = ipkg
		self.cmd = eConsoleAppContainer()
		self.cmd_appClosed_conn = self.cmd.appClosed.connect(self.cmdFinished)
		self.cmd_dataAvail_conn = self.cmd.dataAvail.connect(self.cmdData)
		self.cache = None
		self.callbackList = []
		self.setCurrentCommand()
		self.update_done = False

	def setCurrentCommand(self, command = None):
		self.currentCommand = command

	def runCmd(self, cmd):
		print "executing", self.ipkg, cmd
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
			self.callCallbacks(self.EVENT_LISTITEM, item)
		else:
			tokens = data.split()
			# opkg
			if data.startswith('Downloading'):
				# Extract package name from URL.
				self.callCallbacks(self.EVENT_DOWNLOAD, tokens[1].split('/')[-1].split('_')[0])
			elif data.startswith('Upgrading'):
				self.callCallbacks(self.EVENT_UPGRADE, tokens[1])
			elif data.startswith('Installing'):
				self.callCallbacks(self.EVENT_INSTALL, tokens[1])
			elif data.startswith('Removing package'):
				self.callCallbacks(self.EVENT_REMOVE, tokens[2])
			elif data.startswith('Configuring'):
				# Remove trailing dot.
				self.callCallbacks(self.EVENT_CONFIGURING, tokens[1][:-1])
			elif data.startswith('Failed to download'):
				self.callCallbacks(self.EVENT_ERROR, None)
			# apt-get
			elif data.startswith('Get:'):
				if self.currentCommand == self.CMD_INSTALL:
					self.callCallbacks(self.EVENT_INSTALL, tokens[3])
				elif self.currentCommand == self.CMD_UPGRADE:
					self.callCallbacks(self.EVENT_UPGRADE, tokens[3])
				self.callCallbacks(self.EVENT_DOWNLOAD, tokens[3])
			# dpkg
			elif data.startswith('Setting up'):
				self.callCallbacks(self.EVENT_CONFIGURING, tokens[2])
			elif data.startswith('Removing'):
				self.callCallbacks(self.EVENT_REMOVE, tokens[1])

	def callCallbacks(self, event, param = None):
		for callback in self.callbackList:
			callback(event, param)

	def addCallback(self, callback):
		self.callbackList.append(callback)

	def stop(self):
		self.cmd.kill()

	def isRunning(self):
		return self.cmd.running()
