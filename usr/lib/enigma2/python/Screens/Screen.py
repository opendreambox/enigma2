from Tools.Profile import profile

profile("LOAD:GUISkin")
from Components.GUISkin import GUISkin
profile("LOAD:Source")
from Components.Sources.Source import Source
profile("LOAD:GUIComponent")
from Components.GUIComponent import GUIComponent
profile("LOAD:eRCInput")
from enigma import eRCInput

class Screen(dict, GUISkin):

	False, SUSPEND_STOPS, SUSPEND_PAUSES = range(3)
	ALLOW_SUSPEND = False

	def __init__(self, session, parent = None):
		dict.__init__(self)
		self.skinName = self.__class__.__name__
		self.session = session
		self.parent = parent

		GUISkin.__init__(self)

		self.onClose = [ ]
		self.onFirstExecBegin = [ ]
		self.onFirstExecBegin.append(self._initAnimations)
		self.onExecBegin = [ ]
		self.onShown = [ ]

		self.onShow = [ ]
		self.onHide = [ ]
		self.onHideFinished = [ ]

		self.execing = False
		
		self.shown = True
		# already shown is false until the screen is really shown (after creation)
		self.already_shown = False

		self.renderer = [ ]

		# in order to support screens *without* a help,
		# we need the list in every screen. how ironic.
		self.helpList = [ ]

		self.close_on_next_exec = None

		# stand alone screens (for example web screens)
		# don't care about having or not having focus.
		self.stand_alone = False
		self.keyboardMode = None

		self._hideAnimFinishedConnInternal = None
		self._hideAnimFinishedConn = None

	def saveKeyboardMode(self):
		self.keyboardMode = eRCInput.getInstance().getKeyboardMode()

	def setKeyboardModeAscii(self):
		eRCInput.getInstance().setKeyboardMode(eRCInput.kmAscii)

	def setKeyboardModeNone(self):
		eRCInput.getInstance().setKeyboardMode(eRCInput.kmNone)

	def restoreKeyboardMode(self):
		if self.keyboardMode is not None:
			eRCInput.getInstance().setKeyboardMode(self.keyboardMode)

	def execBegin(self):
		self.active_components = [ ]

		if self.close_on_next_exec is not None:
			tmp = self.close_on_next_exec
			self.close_on_next_exec = None
			self.execing = True
			self.close(*tmp)
		else:
			single = self.onFirstExecBegin
			self.onFirstExecBegin = []
			for x in self.onExecBegin + single:
				x()
				if not self.stand_alone and self.session.current_dialog != self:
					return

#			assert self.session == None, "a screen can only exec once per time"
#			self.session = session

			for val in self.values() + self.renderer:
				val.execBegin()
				if not self.stand_alone and self.session.current_dialog != self:
					return
				self.active_components.append(val)

			self.execing = True
	
			for x in self.onShown:
				x()
	
	def execEnd(self):
		active_components = self.active_components
#		for (name, val) in self.items():
		self.active_components = None
		for val in active_components:
			val.execEnd()
#		assert self.session != None, "execEnd on non-execing screen!"
#		self.session = None
		self.execing = False
	
	# never call this directly - it will be called from the session!
	def doClose(self, immediate=False):
		if not self.instance:
			immediate = True

		def __onHideAnimationFinishedInternal():
			del self._hideAnimFinishedConnInternal
			self.doCloseInternal()
		if not immediate:
			self._hideAnimFinishedConnInternal = self.instance.hideAnimationFinished.connect(__onHideAnimationFinishedInternal)

		self.hide()
		if immediate or not self.instance.isFading():
			self.doCloseInternal()

	def doCloseInternal(self):
		for x in self.onClose:
			x()
		del self._hideAnimFinishedConn
		# fixup circular references
		del self.helpList
		GUISkin.close(self)

		# first disconnect all render from their sources.
		# we might split this out into a "unskin"-call,
		# but currently we destroy the screen afterwards
		# anyway.
		for val in self.renderer:
			val.disconnectAll()  # disconnected converter/sources and probably destroy them. Sources will not be destroyed.

		if self in self.session.fading_dialogs:
			self.session.fading_dialogs.remove(self)
		del self.session

		# we can have multiple dict entries with different names but same Element
		# but we dont can call destroy multiple times
		for name in self.keys():
			val = self[name]
			del self[name] # remove from dict
			if val is not None: # is not a duplicate...
				val.destroy()
				for (n, v) in self.items():
					if v == val: # check if it is the same Element
						self[n] = None # mark as duplicate

		self.renderer = [ ]

		# really delete all elements now
		self.__dict__.clear()

	def close(self, *retval):
		if not self.execing:
			self.close_on_next_exec = retval
		else:
			self.session.close(self, *retval)

	def setFocus(self, o):
		self.instance.setFocus(o.instance)

	def show(self):
		if not self.instance or (self.shown and self.already_shown and self.instance.isVisible()):
			return

		self.shown = True
		self.already_shown = True
		self.instance.show()
		self.__onShow()

	def __onShow(self):
		for x in self.onShow:
			x()
		for val in self.values() + self.renderer:
			if isinstance(val, GUIComponent) or isinstance(val, Source):
				val.onShow()

	def hide(self):
		if not self.instance or not (self.shown and self.instance.isVisible()):
			self.__onHideFinished()
			return

		self.shown = False
		self.instance.hide()
		if not self.instance.isFading():
			self.__onHideFinished()
		if not self.isEnabled(): #already disabled, don't call the callbacks twice
			return
		self.__onHide()

	def __onHide(self):
		for x in self.onHide:
			x()
		for val in self.values() + self.renderer:
			if isinstance(val, GUIComponent) or isinstance(val, Source):
				val.onHide()

	def __onHideFinished(self):
		for fnc in self.onHideFinished:
			fnc()

	def enable(self):
		if self.isEnabled() or not self.instance:
			return

		self.instance.enable()
		if self.instance.isVisible():
			self.__onShow()
		else:
			self.show()

	def disable(self):
		if not self.isEnabled() or not self.instance:
			return
		self.instance.disable()
		if not self.instance.isVisible():
			return
		self.__onHide()

	def isEnabled(self):
		return self.instance.isEnabled()

	def __repr__(self):
		return str(type(self))

	def getRelatedScreen(self, name):
		if name == "session":
			return self.session.screen
		elif name == "parent":
			return self.parent
		elif name == "global":
			return self.session.screen
		else:
			return None

	def _initAnimations(self):
		if self.instance: #WebScreens (for example) never have an instance
			self._hideAnimFinishedConn = self.instance.hideAnimationFinished.connect(self.__onHideFinished)

	def setShowHideAnimation(self, animation_key):
		if self.instance:
			return self.instance.setShowHideAnimation(animation_key)
		return False

	def neverAnimate(self):
		if self.instance:
			self.instance.neverAnimate()
			return True
		return False

	def canAnimate(self):
		"""
		True = it can
		False = it can NOT
		None = we have no instance, we don't know (call in onFirstExecBegin to avoid this)
		"""
		if self.instance:
			return self.instance.canAnimate()
		return None #We do not know that without an instance
