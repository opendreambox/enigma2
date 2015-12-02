from Screens.Wizard import WizardSummary
from Screens.WizardLanguage import WizardLanguage
from Screens.Rc import Rc
import VideoHardware

from Components.Pixmap import Pixmap
from Components.config import config, configfile

from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.HardwareInfo import HardwareInfo
from Components.SystemInfo import SystemInfo

class VideoWizardSummary(WizardSummary):
	skin = (
	"""<screen name="VideoWizardSummary" position="0,0" size="132,64" id="1">
		<widget source="text" render="Label" position="6,0" size="120,40" font="Regular;12" transparent="1" />
		<widget source="parent.list" render="Label" position="6,40" size="120,21" font="Regular;14">
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
		self.hw = VideoHardware.video_hw

		self.port = None
		self.mode = None
		self.rate = None

	def createSummary(self):
		return VideoWizardSummary

	def markDone(self):
		config.misc.videowizardenabled.value = 0
		config.misc.videowizardenabled.save()
		configfile.save()

	def listInputChannels(self):
		hw_type = HardwareInfo().get_device_name()
		list = []

		for port in self.hw.getPortList():
			if self.hw.isPortUsed(port):
				descr = port
				if descr == 'DVI' and hw_type != 'dm8000':
					descr = 'HDMI'
				if port != "DVI-PC":
					list.append((descr,port))
		list.sort(key = lambda x: x[0])
		print "listInputChannels:", list
		return list

	def selectDVI(self):
		self.selection = 'DVI'
		self.inputSelectionMade(self.selection)

	def inputSelectionMade(self, index):
		print "inputSelectionMade:", index
		self.port = index
		self.inputSelect(index)
		
	def inputSelectionMoved(self):
		print "input selection moved:", self.selection
		self.inputSelect(self.selection)
		if self["portpic"].instance is not None:
			picname = self.selection
			if picname == "DVI" and HardwareInfo().get_device_name() != "dm8000":
				picname = "HDMI"
			self["portpic"].instance.setPixmapFromFile(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/Videomode/" + picname + ".png"))
		
	def inputSelect(self, port):
		print "inputSelect:", port
		modeList = self.hw.getModeList(self.selection)
		print "modeList:", modeList
		self.port = port
		if (len(modeList) > 0):
			ratesList = self.listRates(modeList[0][0])
			self.hw.setMode(port = port, mode = modeList[0][0], rate = ratesList[0][0])
		
	def listModes(self):
		list = []
		print "modes for port", self.port
		for mode in self.hw.getModeList(self.port):
			#if mode[0] != "PC":
				list.append((mode[0], mode[0]))
		print "modeslist:", list
		return list
	
	def modeSelectionMade(self, index):
		print "modeSelectionMade:", index
		self.mode = index
		self.modeSelect(index)
		
	def modeSelectionMoved(self):
		print "mode selection moved:", self.selection
		self.modeSelect(self.selection)
		
	def modeSelect(self, mode):
		ratesList = self.listRates(mode)
		print "ratesList:", ratesList
		if self.port == "DVI" and mode in ("720p", "1080p", "1080i"):
			self.rate = "multi"
			self.hw.setMode(port = self.port, mode = mode, rate = "multi")
		else:
			self.hw.setMode(port = self.port, mode = mode, rate = ratesList[0][0])
	
	def listRates(self, querymode = None):
		if querymode is None:
			querymode = self.mode
		list = []
		print "modes for port", self.port, "and mode", querymode
		for mode in self.hw.getModeList(self.port):
			print mode
			if mode[0] == querymode:
				for rate in mode[1]:
					if self.port == "DVI-PC":
						print "rate:", rate
						if rate == "640x480":
							list.insert(0, (rate, rate))
							continue
					list.append((rate, rate))
		return list
	
	def rateSelectionMade(self, index):
		print "rateSelectionMade:", index
		self.rate = index
		self.rateSelect(index)
		
	def rateSelectionMoved(self):
		print "rate selection moved:", self.selection
		self.rateSelect(self.selection)

	def rateSelect(self, rate):
		self.hw.setMode(port = self.port, mode = self.mode, rate = rate)

	def keyNumberGlobal(self, number):
		if number in (1,2,3,4):
			if number == 1:
				self.hw.saveMode("DVI", "720p", "multi")
			elif number == 2:
				self.hw.saveMode("DVI", "1080i", "multi")
			elif SystemInfo["AnalogOutput"] and number == 3:
				self.hw.saveMode("Scart", "Multi", "multi")
			elif number == 4:
				self.hw.saveMode("DVI", "1080p", "multi")
			self.hw.setConfiguredMode()
			self.close()

		WizardLanguage.keyNumberGlobal(self, number)
