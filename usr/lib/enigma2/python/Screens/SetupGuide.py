from Screens.Screen import Screen
from Components.config import KEY_LEFT, KEY_RIGHT, KEY_0, KEY_BACKSPACE, KEY_DELETE, config, ConfigBoolean
from Components.ActionMap import NumberActionMap
from Components.ConfigList import ConfigList
from Components.Label import Label
from Components.SetupGuide.BaseStep import SetupListStep, SetupConfigStep
from Components.SetupGuide.InitialSetupSteps import initialSetupSteps
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.PrioritizedStepper import PrioritizedStepper
from Tools.Log import Log
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
import six
from six.moves import range

config.misc.firstrun = ConfigBoolean(default = True)

class SetupGuideSummary(Screen):
	skin = """<screen id="3" name="SetupGuideSummary" position="0,0" size="400,240">
		<ePixmap pixmap="skin_default/display_bg.png" position="0,0" size="400,240" zPosition="-1"/>
		<widget font="Display;48" halign="center" position="10,5" render="Label" size="380,240" source="title" transparent="1" valign="top"/>
		<widget font="Display;42" halign="center" position="10,55" render="Label" size="380,180" source="text" transparent="1" valign="bottom" />
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self._title = StaticText("")
		self["title"] = self._title
		self._text = StaticText("")
		self["text"] = self._text
		self.onShow.append(self.parent.updateSummary)

	def setText(self, text):
		self._text.text = text

	def setTitle(self, title):
		self._title.text = title

class SetupGuide(Screen):
	MENU_CHOICE_LEAVE = "leave"

	skin="""<screen name="SetupGuide" position="0,0" size="1280,720" title="Welcome" flags="wfNoBorder">
		<widget name="banner" position="0,0" size="240,720" pixmap="skin_default/wizard.png" scale="fill" />
		<widget source="green" render="Pixmap" pixmap="skin_default/buttons/green.png" position="475,15" size="200,40" >
			<convert type="ConditionalShowHide"/>
		</widget>
		<widget name="green_text" position="475,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="yellow" render="Pixmap" pixmap="skin_default/buttons/yellow.png" position="685,15" size="200,40" >
			<convert type="ConditionalShowHide"/>
		</widget>
		<widget name="yellow_text" position="685,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="blue" render="Pixmap" pixmap="skin_default/buttons/blue.png" position="895,15" size="200,40" >
			<convert type="ConditionalShowHide"/>
		</widget>
		<widget name="blue_text" position="895,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="Title" render="Label" position="250,70" size="950,40" font="Regular;36" halign="center" valign="center" />
		<widget name="text" position="250,120" size="950,240" font="Regular;24" halign="center" valign="center" />
		<widget source="list" render="Listbox" position="250,370" size="950,300" zPosition="1" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
			<convert type="TemplatedMultiContent">
				{"templates":
					{	"default" :  (28,[ MultiContentEntryText(pos=(10,4),size=(580,22),flags=RT_HALIGN_LEFT,text=0) ]),
						"iconized" :  (50,[
							MultiContentEntryText(pos=(75,0),size=(310,50),flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=0),# index 0 is the text,
							MultiContentEntryPixmap(pos=(5,5),size=(60,40),png=1),# index 1 is the pixmap
						]),
						"networkservice" : (50,[
							MultiContentEntryPixmapAlphaTest(pos=(0,0),size=(50,50),png=1),#type icon
							MultiContentEntryText(pos=(55,0),size=(400,24),font=0,flags=RT_HALIGN_LEFT,text=3),#service name
							MultiContentEntryText(pos=(780,0),size=(100,24),font=1,flags=RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM,text=7),#security
							MultiContentEntryText(pos=(780,30),size=(100,18),font=1,flags=RT_HALIGN_RIGHT|RT_VALIGN_TOP,text=2),#signal strength
							MultiContentEntryText(pos=(55,30),size=(220,18),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=4),#ip
							MultiContentEntryText(pos=(605,30),size=(150,18),font=1,flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER,text=5),#state
							MultiContentEntryText(pos=(5,0),size=(490,50),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=6),#technology name
						]),
						"inputdevice":(50, [
							MultiContentEntryText(pos = (5, 0), size = (200, 24), font=0, flags = RT_HALIGN_LEFT, text = 0), #device name
							MultiContentEntryText(pos = (210, 0), size = (310, 50), font=0, flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER, text = 3), #pairing state
							MultiContentEntryText(pos = (670, 0), size = (200, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 4), #connection state
							MultiContentEntryText(pos = (5, 30), size = (200, 18), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 2), #device address
							MultiContentEntryText(pos = (670, 30), size = (200, 18), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_TOP, text = 1), #rssi
						]),
					},
					"fonts": [gFont("Regular",20),gFont("Regular",18)],
					"itemHeight": 30
				}
			</convert>
		</widget>
		<widget name="config" position="250,370" size="950,300" zPosition="1" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1" />
	</screen>
	"""

	def __init__(self, session, steps={}):
		Screen.__init__(self, session, windowTitle=_("Welcome"))
		self["Title"] = StaticText()
		self["banner"] = Pixmap()

		self._text = Label()
		self["text"] = self._text
		#buttons
		self["green"] = Boolean(False)
		self["green_text"] = Label()
		self["green_text"].hide()
		self["yellow"] = Boolean(False)
		self["yellow_text"] = Label()
		self["yellow_text"].hide()
		self["blue"] = Boolean(False)
		self["blue_text"] = Label()
		self["blue_text"].hide()
		#list
		self.listContent = []
		self.list = List(self.listContent)
		self.list.hide()
		self["list"] = self.list
		#config
		self.configContent = []
		self.configList = ConfigList(self.configContent, session=session)
		self.configList.hide()
		self["config"] = self.configList

		self._movingBack = False
		self._currentStep = None

		self._stepper = PrioritizedStepper()
		if not steps:
			initialSetupSteps.prepare()
			for s in initialSetupSteps.steps:
				self.addSteps(s)
		else:
			for s in steps:
				self.addSteps(s)
		self["actions"] = NumberActionMap(["MenuActions", "SetupActions", "ColorActions"],
		{
			"ok": self._ok,
			"cancel": self._cancelAndBack,
			"menu" : self._menu,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"red": self.red,
			"green": self.green,
			"yellow": self.yellow,
			"blue":self.blue,
			"deleteForward": self.keyDelete, # >
			"deleteBackward": self.keyBackspace, # <
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
		}, -1)
		self.onFirstExecBegin.append(self._nextStep)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self._stepper.cleanup()
		self._currentStep = None

	def _menu(self):
		choices = [
			(_("Cancel guided setup"), self.MENU_CHOICE_LEAVE),
		]
		self.session.openWithCallback(self._onMenuChoice, ChoiceBox, title=_("Menu"), list=choices)

	def _onMenuChoice(self, choice):
		choice = choice and choice[1]
		if not choice:
			return
		if choice == self.MENU_CHOICE_LEAVE:
			self._cancel()

	def createSummary(self):
		return SetupGuideSummary

	def updateSummary(self):
		if not self._currentStep:
			return
		self.summaries.setTitle(self._currentStep.title)
		summaryText = self._currentStep.text
		if isinstance(self._currentStep, SetupListStep):
			current = self.list.current
			if current:
				style = self.list.style
				Log.d("%s - %s" %(current, style))
				if style in ("default", "iconized"):
					summaryText = current[1]
				elif style == "networkservice":
					summaryText = current[1].name()
				elif style == "inputdevice":
					deviceName = current[1].name() or current[1].shortName() or _("DM Remote")
					summaryText = "%s (%s)" %(deviceName, current[1].address())
			else:
				summaryText =  _("n/A")
		elif isinstance(self._currentStep, SetupConfigStep):
			current = self.configList.current
			summaryText = (current and "%s\n%s" %(current[0], _(current[1].getText()))) or _("n/A")
		Log.d("%s" %(summaryText,))
		self.summaries.setText(summaryText)

	def getText(self):
		return self._text.getText()
	def setText(self, text):
		self._text.setText(text)
	text = property(getText, setText)

	def getTitle(self):
		return Screen.getTitle(self)
	def setTitle(self, title):
		Screen.setTitle(self, title)
	title = property(getTitle, setTitle)

	def checkButtons(self):
		keys = ["red", "green", "yellow", "blue"]
		texts = self._currentStep.buttons()
		for i in range(1,4):
			buttonText = texts[i]
			key = keys[i]
			key_text = "%s_text" %(key,)
			if buttonText:
				self[key].boolean = True
				self[key_text].text = buttonText
				self[key_text].show()
			else:
				self[key].boolean = False
				self[key_text].text = ""
				self[key_text].show()

	def addSteps(self, steps):
		for prio, step in six.iteritems(steps):
			self._stepper.add(self, prio, step)

	def left(self):
		if isinstance(self._currentStep, SetupConfigStep):
			self.configList.handleKey(KEY_LEFT)
			self._currentStep.left()

	def right(self):
		if isinstance(self._currentStep, SetupConfigStep):
			self.configList.handleKey(KEY_RIGHT)
			self._currentStep.right()

	def keyNumberGlobal(self, number):
		if isinstance(self._currentStep, SetupConfigStep):
			self.configList.handleKey(KEY_0 + number)

	def keyDelete(self):
		if isinstance(self._currentStep, SetupConfigStep):
			self.configList.handleKey(KEY_DELETE)

	def keyBackspace(self):
		if isinstance(self._currentStep, SetupConfigStep):
			self.configList.handleKey(KEY_BACKSPACE)

	def up(self):
		pass

	def down(self):
		pass

	def red(self):
		pass

	def green(self):
		if self._currentStep:
			self._currentStep.green()

	def yellow(self):
		if self._currentStep:
			self._currentStep.yellow()

	def blue(self):
		if self._currentStep:
			self._currentStep.blue()

	def nextStep(self):
		self._nextStep()

	def _nextStep(self):
		self.list.buildfunc = None
		self._movingBack = False
		step = self._stepper.next()
		if step:
			self._runStep(step)
			return
		Log.w("No next step available!")
		self.close()

	def _cancelAndBack(self):
		if self._currentStep:
			self._currentStep.cancel()
		self._previousStep()

	def _previousStep(self):
		self.list.buildfunc = None
		self._movingBack = True
		step = self._stepper.previous()
		if step:
			self._runStep(step)
		else:
			Log.w("No previous step available!")
			self._cancel()

	def _cancel(self):
		self.session.openWithCallback(
				self._onCancelAnswered, MessageBox,
				_("Do you want to cancel the guided setup?"),
				type=MessageBox.TYPE_YESNO,
				windowTitle=_("Cancel guided setup?"),
			)

	def _onCancelAnswered(self, answer):
		if answer:
			if self._currentStep:
				self._currentStep.cancel()
			self.close()

	def _ok(self):
		if self._currentStep.onOk():
			self._nextStep()

	def onSelectionChanged(self):
		self.updateSummary()

	def _runStep(self, step):
		self._currentStep = step
		self.listContent = []
		self.configList.onSelectionChanged = []
		self.list.onSelectionChanged = []
		if not step.prepare():
			if self._movingBack:
				self._previousStep()
			else:
				self.nextStep()
			return
		if isinstance(step, SetupListStep):
			self.configList.hide()
			self.listContent = step.listContent
			self.list.list = self.listContent
			self.list.style = step.listStyle
			self.list.buildfunc = step.buildfunc
			self.list.onSelectionChanged = [step.onSelectionChanged,self.onSelectionChanged]
			self.list.index = step.selectedIndex
			self.list.show()
		elif isinstance(step, SetupConfigStep):
			self.list.hide()
			self.configContent = step.configContent
			self.configList.list = self.configContent
			self.configList.onSelectionChanged = [step.onSelectionChanged,self.onSelectionChanged]
			self.configList.show()
		else:
			self.configList.hide()
			self.list.hide()
		self.setTitle(step.title)
		self._text.text = step.text
		self.checkButtons()
		self.updateSummary()

