from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent
from config import KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_0, KEY_DELETE, KEY_BACKSPACE, KEY_OK, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT, KEY_NUMBERS, ConfigElement, ConfigText, ConfigPassword
from Components.ActionMap import NumberActionMap, ActionMap
from enigma import eListbox, eListboxPythonConfigContent, eTimer
from Screens.MessageBox import MessageBox
from skin import componentSizes

class ConfigList(HTMLComponent, GUIComponent, object):
	def __init__(self, list, session = None):
		GUIComponent.__init__(self)
		self.l = eListboxPythonConfigContent()
		sizes = componentSizes[componentSizes.CONFIG_LIST]
		self.l.setSeperation(sizes.get("seperation", 400))
		self.l.setDividerHeight(sizes.get("dividerHeight", 1))
		self.timer = eTimer()
		self._headers = []
		self.list = list
		self.onSelectionChanged = [ ]
		self.current = None
		self.session = session

	def execBegin(self):
		self.timer_conn = self.timer.timeout.connect(self.timeout)

	def execEnd(self):
		self.timer_conn = None

	def toggle(self):
		selection = self.getCurrent()
		selection[1].toggle()
		self.invalidateCurrent()

	def handleKey(self, key):
		selection = self.getCurrent()
		if selection and selection[1].enabled:
			selection[1].handleKey(key)
			self.invalidateCurrent()
			if key in KEY_NUMBERS:
				self.timer.start(1000, 1)

	def getCurrent(self):
		return self.l.getCurrentSelection()
	
	def getCurrentIndex(self):
		return self.l.getCurrentSelectionIndex()
	
	def setCurrentIndex(self, index):
		if self.instance is not None:
			self.instance.moveSelectionTo(index)
	
	def invalidateCurrent(self):
		self.l.invalidateEntry(self.l.getCurrentSelectionIndex())
		for x in self.onSelectionChanged:
			x()

	def invalidate(self, entry):
		# when the entry to invalidate does not exist, just ignore the request.
		# this eases up conditional setup screens a lot.
		if entry in self.__list:
			self.l.invalidateEntry(self.__list.index(entry))

	GUI_WIDGET = eListbox
	
	def selectionChanged(self):
		if isinstance(self.current,tuple) and len(self.current) > 1:
			self.current[1].onDeselect(self.session)
		self.current = self.getCurrent()
		if isinstance(self.current,tuple) and len(self.current) > 1:
			self.current[1].onSelect(self.session)
		else:
			return
		for x in self.onSelectionChanged:
			x()

	def postWidgetCreate(self, instance):
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		instance.setContent(self.l)
	
	def preWidgetRemove(self, instance):
		if isinstance(self.current,tuple) and len(self.current) > 1:
			self.current[1].onDeselect(self.session)
		self.selectionChanged_conn = None
		instance.setContent(None)

	def setList(self, l):
		self.timer.stop()
		self.__list = l
		self.l.setList(self.__list)
		self._headers = []
		if l is not None:
			index = 0
			for x in l:
				if len(x) < 2:
					self._headers.append(index)
				else:
					assert isinstance(x[1], ConfigElement), "entry in ConfigList " + str(x[1]) + " must be a ConfigElement"
				index += 1

	def pageUp(self):
		self.instance.moveSelection(eListbox.pageUp)

	def pageDown(self):
		self.instance.moveSelection(eListbox.pageDown)

	def jumpToNextSection(self):
		index = self.getCurrentIndex()
		maxlen = len(self.__list)
		while index < maxlen - 1:
			index += 1
			if index in self._headers:
				if index + 1 < maxlen:
					self.setCurrentIndex(index + 1)
					return
				else:
					self.setCurrentIndex(index - 1)
					return
		self.pageDown()

	def jumpToPreviousSection(self):
		index = self.getCurrentIndex() - 1
		maxlen = len(self.__list)
		while index >= 0 and maxlen > 0:
			index -= 1
			if index in self._headers:
				if index + 1 < maxlen:
					self.setCurrentIndex(index + 1)
					return
				else:
					self.setCurrentIndex(index - 1)
					return
		self.pageUp()

	def getList(self):
		return self.__list

	list = property(getList, setList)

	def timeout(self):
		self.handleKey(KEY_TIMEOUT)

	def isChanged(self):
		is_changed = False
		for x in self.list:
			if len(x) > 1:
				is_changed |= x[1].isChanged()

		return is_changed

class ConfigListScreen(object):
	def __init__(self, list, session = None, on_change = None):
		self["config_actions"] = NumberActionMap(["SetupActions", "InputAsciiActions", "KeyboardInputActions"],
		{
			"gotAsciiCode": self.keyGotAscii,
			"ok": self.keyOK,
			"left": self.keyLeft,
			"right": self.keyRight,
			"home": self.keyHome,
			"end": self.keyEnd,
			"deleteForward": self.keyDelete,
			"deleteBackward": self.keyBackspace,
			"toggleOverwrite": self.keyToggleOW,
			"previousSection" : self.keyPreviousSection,
			"nextSection" : self.keyNextSection,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal
		}, -1) # to prevent left/right overriding the listbox

		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
		{
			"showVirtualKeyboard": self.KeyText,
		}, -2)
		self["VirtualKB"].setEnabled(False)
		
		self["config"] = ConfigList(list, session = session)
		if not hasattr(self, "setup_title"):
			self.setup_title = ""

		self.onConfigEntryChanged = []
		if on_change:
			self.onConfigEntryChanged.append(on_change)

		if not self.handleInputHelpers in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.handleInputHelpers)

	def _changedEntry(self):
		for fnc in self.onConfigEntryChanged:
			fnc()

	def handleInputHelpers(self):
		if self["config"].getCurrent() is not None:
			if isinstance(self["config"].getCurrent()[1], ConfigText) or isinstance(self["config"].getCurrent()[1], ConfigPassword):
				if self.has_key("VKeyIcon"):
					self["VirtualKB"].setEnabled(True)
					self["VKeyIcon"].boolean = True
				if self.has_key("HelpWindow"):
					if self["config"].getCurrent()[1].help_window.instance is not None:
						helpwindowpos = self["HelpWindow"].getPosition()
						from enigma import ePoint
						self["config"].getCurrent()[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))
			else:
				if self.has_key("VKeyIcon"):
					self["VirtualKB"].setEnabled(False)
					self["VKeyIcon"].boolean = False
		else:
			if self.has_key("VKeyIcon"):
				self["VirtualKB"].setEnabled(False)
				self["VKeyIcon"].boolean = False

	def KeyText(self):
		from Screens.VirtualKeyBoard import VirtualKeyBoard
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title = self["config"].getCurrent()[0], text = self["config"].getCurrent()[1].getValue())

	def VirtualKeyBoardCallback(self, callback = None):
		if callback is not None and len(callback):
			self["config"].getCurrent()[1].setValue(callback)
			self["config"].invalidate(self["config"].getCurrent())
			
	def keyOK(self):
		self["config"].handleKey(KEY_OK)

	def keyLeft(self):
		self["config"].handleKey(KEY_LEFT)
		self._changedEntry()

	def keyRight(self):
		self["config"].handleKey(KEY_RIGHT)
		self._changedEntry()

	def keyHome(self):
		self["config"].handleKey(KEY_HOME)
		self._changedEntry()

	def keyEnd(self):
		self["config"].handleKey(KEY_END)
		self._changedEntry()

	def keyDelete(self):
		self["config"].handleKey(KEY_DELETE)
		self._changedEntry()

	def keyBackspace(self):
		self["config"].handleKey(KEY_BACKSPACE)
		self._changedEntry()

	def keyToggleOW(self):
		self["config"].handleKey(KEY_TOGGLEOW)
		self._changedEntry()

	def keyGotAscii(self):
		self["config"].handleKey(KEY_ASCII)
		self._changedEntry()

	def keyNumberGlobal(self, number):
		self["config"].handleKey(KEY_0 + number)
		self._changedEntry()

	def keyPreviousSection(self):
		self["config"].jumpToPreviousSection()

	def keyNextSection(self):
		self["config"].jumpToNextSection()

	def saveAll(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()

	# keySave and keyCancel are just provided in case you need them.
	# you have to call them by yourself.
	def keySave(self):
		self.saveAll()
		self.close()
	
	def cancelConfirm(self, result):
		if not result:
			return

		for x in self["config"].list:
			if len(x) > 1:
				x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def getCurrentEntry(self):
		current = self["config"].getCurrent()
		return current and current[0] or ""

	def getCurrentValue(self):
		current = self["config"].getCurrent()
		return current and str(current[1].getText()) or ""

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary
