from __future__ import print_function
from enigma import getPrevAsciiCode

from Components.ActionMap import ActionMap, NumberActionMap
from Components.Sources.StaticText import StaticText
from Components.Label import Label

from Screens.Screen import Screen

from EnhancedInput import EnhancedInput
from BrowserDB import Bookmark

class BookmarkEditor(Screen):
	skin = """
		<screen position="center,center" size="600,80"  title="Edit Bookmark">
			<widget source="nameTitle" render="Label" position="5,0" zPosition="1" size="90,30" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget source="urlTitle" render="Label" position="5,40" zPosition="1" size="90,30" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget name="name" position="100,0" size="450,30" font="Regular;22" halign="left" valign="bottom" backgroundColor="#000000" transparent="1"/>
			<widget name="url" position="100,40" size="450,30" font="Regular;22" halign="left" valign="bottom" backgroundColor="#000000" transparent="1"/>
			<widget name="nameActive" position="560,0" zPosition="1" size="40,30" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
			<widget name="urlActive" position="560,40" zPosition="1" size="40,30" font="Regular;22" halign="right" valign="bottom" backgroundColor="#000000" transparent="1" />
		</screen>"""
	
	def __init__(self, session, bookmark = None):
		Screen.__init__(self, session)
		
		self.bookmark = bookmark
		if self.bookmark == None:
			self.bookmark = Bookmark()
		
		self["nameTitle"] = StaticText(_("Name:"))
		self["urlTitle"] = StaticText(_("Url:"))
		
		self["nameActive"] = Label("<")
		self["urlActive"] = Label("<")
		
		self.inputName = EnhancedInput( self.bookmark.name )
		self["name"] = self.inputName
		self.inputUrl = EnhancedInput( self.bookmark.url )
		self["url"] = self.inputUrl
		self.onShow.append(self.setKeyboardModeAscii)
		
		self["actions"] = ActionMap(["SimpleEditorActions"],
		{
			"ok" : self.__ok,
			"exit" : self.__cancel,
			"up" : self.__up,
			"down" : self.__down,
			"left" : self.__left,
			"right" : self.__right,
			"ascii" : self.__ascii,
			"delete" : self.__delete,
			"backspace" : self.__backspace
		})
		self["numberactions"] = NumberActionMap(["NumberActions"],
		{
			"1": self.__keyNumberGlobal,
			"2": self.__keyNumberGlobal,
			"3": self.__keyNumberGlobal,
			"4": self.__keyNumberGlobal,
			"5": self.__keyNumberGlobal,
			"6": self.__keyNumberGlobal,
			"7": self.__keyNumberGlobal,
			"8": self.__keyNumberGlobal,
			"9": self.__keyNumberGlobal,
			"0": self.__keyNumberGlobal
		})
		
		self.nameFocus = False
		self.onShow.append(self.__toggleInput)
		
	def __ok(self):
		name = self.inputName.getText()
		url = self.inputUrl.getText() 
		if name != None and url != None and name != "" and url != "":
			self.bookmark.name = name
			self.bookmark.url = url
			self.close( self.bookmark )
		else:
			self.close(None)
	
	def __cancel(self):
		self.close(None)
	
	def __up(self):
		self.__toggleInput()
	
	def __down(self):
		self.__toggleInput()
	
	def __toggleInput(self):
		self.nameFocus = not self.nameFocus
		if self.nameFocus:
			self["nameActive"].show()
			self.inputName.end()
			self["urlActive"].hide()
			self.inputUrl.markNone()
		else:
			self["nameActive"].hide()
			self.inputName.markNone()
			self["urlActive"].show()
			self.inputUrl.end()
	
	def __left(self):
		if self.nameFocus:
			self.inputName.left()
		else:
			self.inputUrl.left()
	
	def __right(self):
		if self.nameFocus:
			self.inputName.right()
		else:
			self.inputUrl.right()
	
	def __delete(self):
		if self.nameFocus:
			self.inputName.delete()
		else:
			self.inputUrl.delete()
		
	def __backspace(self):
		if self.nameFocus:
			self.inputName.deleteBackward()
		else:
			self.inputUrl.deleteBackward()
	
	def __keyNumberGlobal(self, number):
		if self.nameFocus:
			self.inputName.number(number)
		else:
			self.inputUrl.number(number)
	
	def __ascii(self):
		print("ASCII!")
		if self.nameFocus:
			self.inputName.handleAscii(getPrevAsciiCode())
		else:
			self.inputUrl.handleAscii(getPrevAsciiCode())

