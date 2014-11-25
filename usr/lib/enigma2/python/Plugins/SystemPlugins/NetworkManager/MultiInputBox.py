from enigma import getPrevAsciiCode

from Components.ActionMap import ActionMap, NumberActionMap
from Components.Input import Input
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction


class MultiInputBox(Screen):
	skin = """
		<screen position="center,center" size="700,120"  title="Input">
			<widget source="title" render="Label" position="5,0" zPosition="1" size="690,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="background" transparent="1" />
			<widget source="firstTitle" render="Label" position="5,30" zPosition="1" size="220,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="background" transparent="1" />
			<widget source="secondTitle" render="Label" position="5,70" zPosition="1" size="220,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="background" transparent="1" />
			<widget name="first" position="230,30" size="420,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="background" transparent="1"/>
			<widget name="second" position="230,70" size="420,25" font="Regular;22" halign="left" valign="bottom" backgroundColor="background" transparent="1"/>
			<widget name="firstActive" position="660,30" zPosition="1" size="40,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="background" transparent="1" />
			<widget name="secondActive" position="660,70" zPosition="1" size="40,25" font="Regular;22" halign="right" valign="bottom" backgroundColor="background" transparent="1" />
		</screen>"""

	default_config = {
		"first" : {
			"key" : "User",
			"value" : "",
			"title" : _("User"),
			"required" : True,
			"type" : Input.TEXT,
			"alternative" : None
			},
		"second" : {
			"key" : "Password",
			"value" : "",
			"title" : _("Password"),
			"required" : True,
			"type" : Input.PIN,
			"alternatives" : None
			},
	}

	def __init__(self, session, title="", windowTitle=_("Input"), config=default_config):
		Screen.__init__(self, session)
		self.onShown.append(boundFunction(self.setTitle, windowTitle))

		self._config = config
		first = config["first"]
		second = config["second"]
		self._title = title

		self._first = first["value"]
		self._second = second["value"]

		self["title"] = StaticText(self._title)
		self["firstTitle"] = StaticText(first["title"])
		self["secondTitle"] = StaticText(second["title"])

		self["firstActive"] = Label("<")
		self["secondActive"] = Label("<")

		self._inputFirst = Input( self._first, type=first["type"] )
		self["first"] = self._inputFirst
		self._inputSecond = Input( self._second, type=second["type"] )
		self["second"] = self._inputSecond

		self["actions"] = ActionMap(["NetworkManagerInputActions"],
		{
			"ok" : self._ok,
			"exit" : self._cancel,
			"up" : self._up,
			"down" : self._down,
			"left" : self._left,
			"right" : self._right,
			"ascii" : self._ascii,
			"delete" : self._delete,
			"backspace" : self._backspace
		})
		self["numberactions"] = NumberActionMap(["NumberActions"],
		{
			"1": self._keyNumberGlobal,
			"2": self._keyNumberGlobal,
			"3": self._keyNumberGlobal,
			"4": self._keyNumberGlobal,
			"5": self._keyNumberGlobal,
			"6": self._keyNumberGlobal,
			"7": self._keyNumberGlobal,
			"8": self._keyNumberGlobal,
			"9": self._keyNumberGlobal,
			"0": self._keyNumberGlobal
		})

		self._firstFocus = False
		self.onShow.append(self._toggleInput)
		self.onExecBegin.append(self.setKeyboardModeAscii)

	def _ok(self):
		first = self._inputFirst.getText()
		second = self._inputSecond.getText()

		if self._checkInput():
			ret = {}
			if first:
				ret[ self._config["first"]["key"] ] = first
			if second:
				ret[ self._config["second"]["key"] ] = second
			self.close( ret )
		else:
			self.close(None)

	def _checkInput(self):
		_first = self._config["first"]
		_second = self._config["second"]
		first = self._inputFirst.getText()
		second = self._inputSecond.getText()

		firstok = self._checkSingleInput(first, _first)
		secondok = self._checkSingleInput(second, _second)
		if not ( _first["required"] and _second["required"] ):
			return firstok or secondok

		return firstok and secondok

	def _checkSingleInput(self, value, config):
		return value != None and value != ""

	def _cancel(self):
		self.close(None)

	def _up(self):
		self._toggleInput()

	def _down(self):
		self._toggleInput()

	def _toggleInput(self):
		self._firstFocus = not self._firstFocus
		if self._firstFocus:
			self["firstActive"].show()
			self._inputFirst.end()
			self["secondActive"].hide()
			self._inputSecond.markNone()
		else:
			self["firstActive"].hide()
			self._inputFirst.markNone()
			self["secondActive"].show()
			self._inputSecond.end()

	def _left(self):
		if self._firstFocus:
			self._inputFirst.left()
		else:
			self._inputSecond.left()

	def _right(self):
		if self._firstFocus:
			self._inputFirst.right()
		else:
			self._inputSecond.right()

	def _delete(self):
		if self._firstFocus:
			self._inputFirst.delete()
		else:
			self._inputSecond.delete()

	def _backspace(self):
		if self._firstFocus:
			self._inputFirst.deleteBackward()
		else:
			self._inputSecond.deleteBackward()

	def _keyNumberGlobal(self, number):
		if self._firstFocus:
			self._inputFirst.number(number)
		else:
			self._inputSecond.number(number)

	def _ascii(self):
		if self._firstFocus:
			self._inputFirst.handleAscii(getPrevAsciiCode())
		else:
			self._inputSecond.handleAscii(getPrevAsciiCode())
