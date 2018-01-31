from Components.Label import Label
from Screens.Screen import Screen

class MediaRendererLCDScreen(Screen):
	skin = (
	"""<screen name="MediaRendererLCDScreen" position="0,0" size="132,64" id="1">
		<widget name="text1" position="4,0" size="132,18" font="Regular;14"/>
		<widget name="text2" position="4,20" size="132,14" font="Regular;11"/>
		<widget name="text3" position="4,36" size="132,14" font="Regular;11"/>
	</screen>""",
	"""<screen name="MediaRendererLCDScreen" position="0,0" size="96,64" id="2">
		<widget name="text1" position="0,0" size="96,18" font="Regular;13"/>
		<widget name="text2" position="0,20" size="96,14" font="Regular;10"/>
		<widget name="text3" position="0,36" size="96,14" font="Regular;10"/>
	</screen>""",
	"""<screen name="MediaRendererLCDScreen" position="0,0" size="400,240" id="3">
		<ePixmap position="0,0" size="400,240" pixmap="skin_default/display_bg.png" zPosition="-1"/>
		<widget name="text1" font="Display;48" halign="center" position="0,3" size="400,48" transparent="1"/>
		<eLabel backgroundColor="yellow" position="0,60" size="400,2" />
		<widget name="text2" font="Display;36" halign="center" valign="center" position="0,65" size="400,72" transparent="1"/>
		<widget name="text3" font="Display;36" halign="center" valign="center" position="0,150" size="400,72" transparent="1"/>
	</screen>"""
	)

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label("")
		self["text2"] = Label("")
		self["text3"] = Label("")

	def setText(self, text, line):
		if line == 1:
			if len(text) > 100:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 100:
					text = text[-100:]
		else:
			if len(text) > 100:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 100:
					text = text[-100:]
		empty = "	"
		text = text + empty * 10
		if line == 1:
			self["text1"].setText(text)
		elif line == 2:
			self["text2"].setText(text)
		elif line == 3:
			self["text3"].setText(text)
		else:
			print "SimpleLCDScreen line %s does not exist!"

	def clear(self):
		self["text1"].setText("")
		self["text2"].setText("")
		self["text3"].setText("")
