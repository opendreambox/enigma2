from config import config, ConfigSlider, ConfigSelection, ConfigYesNo, \
	ConfigOnOff, ConfigSubsection, ConfigBoolean, ConfigSelectionNumber, ConfigNothing, NoSave
from enigma import eAVSwitch, getDesktop, eDVBServicePMTHandler
from SystemInfo import SystemInfo
from os import path as os_path

class AVSwitch:
	def setInput(self, input):
		INPUT = { "ENCODER": 0, "SCART": 1, "AUX": 2 }
		eAVSwitch.getInstance().setInput(INPUT[input])

	def setColorFormat(self, value):
		eAVSwitch.getInstance().setColorFormat(value)

	def setAspectRatio(self, value):
		eAVSwitch.getInstance().setAspectRatio(value)

	def setSystem(self, value):
		eAVSwitch.getInstance().setVideomode(value)

	def getOutputAspect(self):
		return (16,9) # this function is very old... for analog TVs with different pixel aspect ratio .. for modern digital TVs 16:9 is always okay...
		valstr = config.av.aspectratio.value
		if valstr in ("4_3_letterbox", "4_3_panscan"): # 4:3
			return (4,3)
		elif valstr == "16_9": # auto ... 4:3 or 16:9
			try:
				aspect_str = open("/proc/stb/vmpeg/0/aspect", "r").read()
				if aspect_str[0] == "2": # 4:3
					return (4,3)
			except IOError:
				pass
		elif valstr in ("16_9_always", "16_9_letterbox"): # 16:9
			pass
		elif valstr in ("16_10_letterbox", "16_10_panscan"): # 16:10
			return (16,10)
		return (16,9)

	def getFramebufferScale(self):
		aspect = self.getOutputAspect()
		fb_size = getDesktop(0).size()
		return (aspect[0] * fb_size.height(), aspect[1] * fb_size.width())

	def getAspectRatioSetting(self):
		valstr = config.av.aspectratio.value
		if valstr == "4_3_letterbox":
			val = 0
		elif valstr == "4_3_panscan":
			val = 1
		elif valstr == "16_9":
			val = 2
		elif valstr == "16_9_always":
			val = 3
		elif valstr == "16_10_letterbox":
			val = 4
		elif valstr == "16_10_panscan":
			val = 5
		elif valstr == "16_9_letterbox":
			val = 6
		return val

	def setAspectWSS(self, aspect=None):
		if not config.av.wss.value:
			value = 2 # auto(4:3_off)
		else:
			value = 1 # auto
		eAVSwitch.getInstance().setWSS(value)

def InitAVSwitch():
	try:
		x = config.av
	except KeyError:
		config.av = ConfigSubsection()
	config.av.yuvenabled = ConfigBoolean(default=False)
	colorformat_choices = {"cvbs": _("CVBS"), "rgb": _("RGB"), "svideo": _("S-Video")}

	try:
		have_analog_output = open("/proc/stb/video/mode_choices", "r").read()[:-1].find("PAL") != -1
	except:
		have_analog_output = False

	SystemInfo["AnalogOutput"] = have_analog_output

	# when YUV is not enabled, don't let the user select it
	if config.av.yuvenabled.value and have_analog_output:
		colorformat_choices["yuv"] = _("YPbPr")

	config.av.colorformat = ConfigSelection(choices=colorformat_choices, default="rgb")
	config.av.aspectratio = ConfigSelection(choices={
			"4_3_letterbox": _("4:3 Letterbox"),
			"4_3_panscan": _("4:3 PanScan"), 
			"16_9": _("16:9"), 
			"16_9_always": _("16:9 always"),
			"16_10_letterbox": _("16:10 Letterbox"),
			"16_10_panscan": _("16:10 PanScan"), 
			"16_9_letterbox": _("16:9 Letterbox")}, 
			default = "4_3_letterbox")

	config.av.tvsystem = ConfigSelection(choices = {"pal": _("PAL"), "ntsc": _("NTSC"), "multinorm": _("multinorm")}, default="pal")
	config.av.wss = ConfigOnOff(default = True)
	config.av.vcrswitch = ConfigOnOff(default = False)

	iAVSwitch = AVSwitch()

	def setColorFormat(configElement):
		map = {"cvbs": 0, "rgb": 1, "svideo": 2, "yuv": 3}
		iAVSwitch.setColorFormat(map[configElement.value])

	def setAspectRatio(configElement):
		map = {"4_3_letterbox": 0, "4_3_panscan": 1, "16_9": 2, "16_9_always": 3, "16_10_letterbox": 4, "16_10_panscan": 5, "16_9_letterbox" : 6}
		iAVSwitch.setAspectRatio(map[configElement.value])

	def setSystem(configElement):
		map = {"pal": 0, "ntsc": 1, "multinorm" : 2}
		iAVSwitch.setSystem(map[configElement.value])

	def setWSS(configElement):
		iAVSwitch.setAspectWSS()

	try:
		have_analog_output = open("/proc/stb/video/mode_choices", "r").read()[:-1].find("PAL") != -1
	except:
		have_analog_output = False

	SystemInfo["AnalogOutput"] = have_analog_output

	if have_analog_output:
		# this will call the "setup-val" initial
		config.av.colorformat.addNotifier(setColorFormat)
		config.av.aspectratio.addNotifier(setAspectRatio)
		config.av.tvsystem.addNotifier(setSystem)
		config.av.wss.addNotifier(setWSS)

	iAVSwitch.setInput("ENCODER") # init on startup
	SystemInfo["ScartSwitch"] = eAVSwitch.getInstance().haveScartSwitch()