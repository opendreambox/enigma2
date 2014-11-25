from Components.Label import Label
from Screens.Screen import Screen

class SimpleLCDScreen(Screen):
	skin = (
	"""<screen name="MediaPlayerLCDScreen" position="0,0" size="132,64" id="1">
		<widget name="text1" position="4,0" size="132,18" font="Regular;14"/>
		<widget name="text2" position="4,20" size="132,14" font="Regular;11"/>
		<widget name="text3" position="4,36" size="132,14" font="Regular;11"/>
	</screen>""",
	"""<screen name="MediaPlayerLCDScreen" position="0,0" size="96,64" id="2">
		<widget name="text1" position="0,0" size="96,18" font="Regular;13"/>
		<widget name="text2" position="0,20" size="96,14" font="Regular;10"/>
		<widget name="text3" position="0,36" size="96,14" font="Regular;10"/>
	</screen>""")

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label("")
		self["text2"] = Label("")
		self["text3"] = Label("")

	def setText(self, text, line):
		if line == 1:
			if len(text) > 18:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 15:
					text = text[-15:]
		else:
			if len(text) > 20:
				# TODO remove this hack
				if text[-4:-3] == ".":
					text = text[:-4]
				if len(text) > 20:
					text = text[-20:]
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
