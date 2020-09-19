from enigma import eDVBResourceManager
from Tools.Directories import fileExists
from Tools.HardwareInfo import HardwareInfo

SystemInfo = { }

#FIXMEE...
def getNumVideoDecoders():
	idx = 0
	while fileExists("/dev/dvb/adapter0/video%d"%(idx), 'f'):
		idx += 1
	return idx

SystemInfo["NumVideoDecoders"] = getNumVideoDecoders()
SystemInfo["CanMeasureFrontendInputPower"] = eDVBResourceManager.getInstance().canMeasureFrontendInputPower()

def countFrontpanelLEDs():
	leds = 0
	if fileExists("/proc/stb/fp/led_set_pattern"):
		leds += 1

	while fileExists("/proc/stb/fp/led%d_pattern" % leds):
		leds += 1

	return leds

SystemInfo["NumFrontpanelLEDs"] = countFrontpanelLEDs()
SystemInfo["FrontpanelDisplay"] = fileExists("/dev/dbox/oled0") or fileExists("/dev/dbox/lcd0")
SystemInfo["FrontpanelDisplayGrayscale"] = fileExists("/dev/dbox/oled0")
SystemInfo["DeepstandbySupport"] = True
try:
	from Plugins.SystemPlugins.NetworkManager import plugin
	SystemInfo["NetworkManager"] = True
except:
	SystemInfo["NetworkManager"] = False

device_name = HardwareInfo().device_name
SystemInfo["HaveTouchSensor"] = device_name in ('dm520', 'dm525', 'dm900', 'dm920')
brightnessLut = {
	'dm900' : 8,
	'dm920' : 8,
	'two' : 6,
}
SystemInfo["DefaultDisplayBrightness"] = brightnessLut.get(device_name, 5)
