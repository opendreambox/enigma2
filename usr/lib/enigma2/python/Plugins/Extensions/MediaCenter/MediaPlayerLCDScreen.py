# -*- coding: UTF-8 -*-

from Components.Label import Label
from Screens.Screen import Screen

class MediaPlayerLCDScreen(Screen):
	skin = (
	"""<screen name="MediaPlayerLCDScreen" position="0,0" size="132,64" id="1">
		<widget name="text1" position="4,0" size="132,18" font="Regular;16"/>
		<widget name="text2" position="4,19" size="132,14" font="Regular;10"/>
		<widget name="text3" position="4,34" size="132,14" font="Regular;10"/>
		<widget name="text4" position="4,49" size="132,14" font="Regular;10"/>
	</screen>""",
	"""<screen name="MediaPlayerLCDScreen" position="0,0" size="96,64" id="2">
		<widget name="text1" position="0,0" size="96,18" font="Regular;16"/>
		<widget name="text2" position="0,19" size="96,14" font="Regular;10"/>
		<widget name="text3" position="0,34" size="96,14" font="Regular;10"/>
		<widget name="text4" position="0,49" size="96,14" font="Regular;10"/>
	</screen>""")

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label("MediaCenter")
		self["text2"] = Label("")
		self["text3"] = Label("")
		self["text4"] = Label("")

	def setText(self, text, line):
		if line == 1:
			if len(text) > 15:
				#TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 15:
					text = text[-15:]
		else:
			if len(text) > 20:
				#TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 20:
					text = text[-20:]
		textleer = "	"
		text = text + textleer * 10
		if line == 1:
			self["text1"].setText(text)
		elif line == 2:
			self["text2"].setText(text)
		elif line == 3:
			self["text3"].setText(text)
		elif line == 4:
			self["text4"].setText(text)
