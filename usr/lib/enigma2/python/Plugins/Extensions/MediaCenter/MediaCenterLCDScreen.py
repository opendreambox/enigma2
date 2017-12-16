# -*- coding: UTF-8 -*-

from Components.Label import Label
from Screens.Screen import Screen

class MediaCenterLCDScreen(Screen):
	skin = (
	"""<screen name="MediaCenterLCDScreen" position="0,0" size="132,64" id="1">
		<widget name="text1" font="Display;18" halign="center" position="1,0" size="130,20"/>
		<eLabel backgroundColor="white" position="0,22" size="132,1" />
		<widget name="text2" font="Display;16" halign="center" valign="center" position="6,25" size="120,36"/>
		<widget name="text3" font="Display;12" halign="center" valign="center" position="6,24" size="120,40" transparent="1"/>
	</screen>""",
	"""<screen name="MediaCenterLCDScreen" position="0,0" size="96,64" id="2">
		<widget name="text1" font="Display;19" halign="center" position="0,0" size="96,18"/>
		<eLabel backgroundColor="white" position="0,24" size="96,1" />
		<widget name="text2" font="Display;15" halign="center" valign="center" position="0,28" size="96,34"/>
		<widget name="text3" font="Display;15" halign="center" valign="center" position="0,28" size="96,34" transparent="1"/>
	</screen>""",
	"""<screen name="MediaCenterLCDScreen" position="0,0" size="400,240" id="3">
		<ePixmap position="0,0" size="400,240" pixmap="skin_default/display_bg.png" zPosition="-1"/>
		<widget name="text1" font="Display;48" halign="center" position="0,5" size="400,48" transparent="1"/>
		<eLabel backgroundColor="yellow" position="0,52" size="400,2" />
		<widget name="text2" font="Display;36" halign="center" valign="center" position="0,56" size="400,72" transparent="1"/>
		<widget name="text3" font="Display;36" halign="center" valign="center" position="0,130" size="400,112" transparent="1"/>
	</screen>""")

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label("MediaCenter")
		self["text2"] = Label("")
		self["text3"] = Label("")

	def setText(self, text, line):
		if line == 1:
			if len(text) > 15:
				#TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 15:
					text = text[-15:]
		else:
			if len(text) > 60:
				#TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 60:
					text = text[-60:]
		textleer = "	"
		text = text + textleer * 10
		if line == 1:
			self["text1"].setText(text)
		elif line == 2:
			self["text2"].setText(text)
		elif line == 3:
			self["text3"].setText(text)
