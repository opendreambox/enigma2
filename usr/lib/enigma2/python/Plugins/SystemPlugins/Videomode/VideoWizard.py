from __future__ import print_function
from enigma import eDisplayManager
from Screens.Wizard import WizardSummary
from Components.DisplayHardware import DisplayHardware

from Components.config import config, configfile

from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.HardwareInfo import HardwareInfo


class VideoWizardSummary(WizardSummary):
	skin = (
	"""<screen name="VideoWizardSummary" position="0,0" size="132,64" id="1">
		<widget source="text" render="Label" position="6,0" size="120,64" font="Display;15" halign="left" valign="top"/>
		<widget source="parent.list" render="Label" position="6,34" size="120,46" font="Display;12" valign="center" halign="center" transparent="1">
			<convert type="StringListSelection" />
		</widget>
		<!--widget name="pic" pixmap="%s" position="6,22" zPosition="10" size="64,64" transparent="1" alphatest="on"/-->
	</screen>""",
	"""<screen name="VideoWizardSummary" position="0,0" size="96,64" id="2">
		<widget source="text" render="Label" position="6,0" size="120,40" font="Regular;12" transparent="1" />
		<widget source="parent.list" render="Label" position="0,40" size="96,21" font="Regular;14">
			<convert type="StringListSelection" />
		</widget>
		<!--widget name="pic" pixmap="%s" position="0,22" zPosition="10" size="64,64" transparent="1" alphatest="on"/-->
	</screen>""")
	
	def __init__(self, session, parent):
		WizardSummary.__init__(self, session, parent)

	def setLCDPicCallback(self):
		self.parent.setLCDTextCallback(self.setText)

	def setLCDPic(self, file):
		self["pic"].instance.setPixmapFromFile(file)

class VideoWizard():
	def __init__(self):
		self.hw = DisplayHardware.instance

		self.port = None
		self.mode = None
		self.rate = None

	def createSummary(self):
		return VideoWizardSummary

	def markDone(self):
		config.misc.videowizardenabled.value = 0
		config.misc.videowizardenabled.save()
		configfile.save()

	def listPorts(self):
		hw_type = HardwareInfo().get_device_name()
		list_ports = list(config.av.videoport.getChoices())
		print("listPorts:", list_ports)

		try:
			list_ports.remove(("HDMI-PC", "HDMI-PC"))
		except ValueError:
			pass
		
		list_ports.sort(key = lambda x: x[0])

		return list_ports

	def selectHDMI(self):
		self.selection = "HDMI"
		self.portSelectionMade(self.selection)

	def portSelectionMade(self, index):
		print("portSelectionMade:", index)
		self.port = index
		self.portSelect(index)
		
	def portSelectionMoved(self):
		print("portSelectionMoved:", self.selection)
		self.portSelect(self.selection)
		if self["portpic"].instance is not None:
			picname = self.selection
			if picname == "DVI" and HardwareInfo().get_device_name() != "dm8000":
				picname = "HDMI"
			self["portpic"].instance.setPixmapFromFile(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/Videomode/" + picname + ".png"))
		
	def portSelect(self, port):
		print("inputSelect:", port)
		self.port = port

		modeList = self.listModes()
		if(len(modeList) > 0):
			mode = modeList[0][0]
			rateList = config.av.videorate[mode].getChoices()
			self.mode = mode
			self.rate = rateList[0][0]
			self.hw.setMode(self.port, self.mode, self.rate)
		
	def listModes(self):
		print("modes for port", self.port)

		try:
			list = config.av.videomode[self.port].getChoices()
			print("modeslist:", list)
			return list
		except AttributeError:
			print("modeslist: empty")
			return []
	
	def modeSelectionMade(self, index):
		print("modeSelectionMade:", index)
		self.mode = index
		self.modeSelect(index)
		
	def modeSelectionMoved(self):
		print("mode selection moved:", self.selection)
		self.modeSelect(self.selection)
		
	def modeSelect(self, mode):
		print("modeSelect")
		print("Mode: ", mode)
		self.mode = mode
		ratesList = self.listRates()

		self.rate = ratesList[0][0]

		self.hw.setMode(self.port, mode, self.rate)

	def listRates(self):
		list = sorted(config.av.videorate[self.mode].getChoices(), key=lambda rate: rate[0], reverse=True)
		print(list)
		return list

	def rateSelectionMade(self, index):
		print("rateSelectionMade:", index)
		self.rate = index
		self.rateSelect(index)

	def rateSelectionMoved(self):
		print("rate selection moved:", self.selection)
		self.rateSelect(self.selection)

	def rateSelect(self, rate):
		self.hw.setMode(self.port,self.mode, self.rate)
