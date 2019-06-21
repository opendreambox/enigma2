class SetupBaseStep(object):
	NXT = None # Next Step - DO NOT set this manually!! => PrioritizedStepper
	PRV = None # Previous Step - DO NOT set this manually!! => PrioritizedStepper
	def __init__(self, parent):
		self.parent = parent
		self.title = ""
		self.text = ""

	def prepare(self):
		return True

	def buttons(self):
		return [None, None, None, None] #red, green, yellow, blue - Set to string when used

	def green(self):
		pass

	def yellow(self):
		pass

	def blue(self):
		pass

	#==============================================================================
	# onOk
	# return True when step is done - parent will continue to the next step
	# return False when step is not done - parent will NOT continue to the next step
	#              but you will have to call self.parent.nextStep()
	#==============================================================================
	def onOk(self):
		return True

	def cancel(self):
		pass

class SetupTextStep(SetupBaseStep):
	def __init__(self, parent):
		SetupBaseStep.__init__(self, parent)

class SetupListStep(SetupBaseStep):
	def __init__(self, parent, listStyle="default"):
		SetupBaseStep.__init__(self, parent)
		self._list = parent.list
		self.listStyle=listStyle

	@property
	def listContent(self):
		raise NotImplementedError

	@property
	def selectedIndex(self):
		return 0

	def buildfunc(self, entry, *args):
		raise NotImplementedError

	def onSelectionChanged(self):
		pass

class SetupListStepConfigSelection(SetupListStep):
	def __init__(self, parent):
		SetupListStep.__init__(self, parent)
		self._configSelection = None

	@property
	def listContent(self):
		return [ (choice[0] , choice[1]) for choice in self._configSelection.choices.choices ]

	@property
	def selectedIndex(self):
		i = 0
		for key, text in self.listContent:
			if key ==  self._configSelection.value:
				break
			i += 1
		return i

	def buildfunc(self, choice, text):
		return text, choice

	def onOk(self):
		current = self.parent.list.current
		value = current and current[0]
		if not value:
			return True
		self._configSelection.value = value
		self._configSelection.save()
		return True

class SetupConfigStep(SetupBaseStep):
	def __init__(self, parent):
		SetupBaseStep.__init__(self, parent)
		self._configList = parent.configList

	@property
	def configContent(self):
		raise NotImplementedError

	@property
	def selectedIndex(self):
		raise NotImplementedError

	def onSelectionChanged(self):
		pass

	def left(self):
		pass

	def right(self):
		pass
