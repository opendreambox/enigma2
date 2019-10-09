# coding: utf-8
from __future__ import print_function
from config import config, ConfigSlider, ConfigSubsection, ConfigYesNo, ConfigText

import struct
from ioctl import ioctl
from ioctl.linux import IOC
from os import listdir, open as os_open, close as os_close, write as os_write, O_RDONLY, O_RDWR
from Components.config import ConfigOnOff, ConfigSelection,	ConfigBoolean
from enigma import eInputDeviceManager
import six

O_CLOEXEC = 0o2000000

def EVIOCGNAME(length):
	return IOC('r', 'E', 0x06, length)

class inputDevices:
	BLACKLIST = ("dreambox front panel", "cec_input")
	def __init__(self):
		self.Devices = {}
		self.currentDevice = ""
		self.getInputDevices()
	
	def getInputDevices(self):
		for evdev in sorted(listdir("/dev/input")):
			try:
				fd = os_open("/dev/input/%s" % evdev, O_RDONLY | O_CLOEXEC)
			except:
				continue

			buf = "\0"*256
			try:
				size = ioctl(fd, EVIOCGNAME(len(buf)), buf)
			except:
				os_close(fd)
				continue

			os_close(fd)
			if size <= 0:
				continue

			name = buf[:size - 1]
			if name:
				if name == "aml_keypad":
					name = "dreambox advanced remote control (native)"
				if name == "dreambox advanced remote control (native)" and config.misc.rcused.value not in (0, 2):
					continue
				if name == "dreambox remote control (native)" and config.misc.rcused.value in (0, 2):
					continue
				if name in self.BLACKLIST:
					continue
				self.Devices[evdev] = {'name': name, 'type': self.getInputDeviceType(name),'enabled': False, 'configuredName': None }

	def getInputDeviceType(self,name):
		if name.find("remote control") != -1:
			return "remote"
		elif name.find("keyboard") != -1:
			return "keyboard"
		elif name.find("mouse") != -1:
			return "mouse"
		else:
			print("Unknown device type:",name)
			return None
			
	def getDeviceName(self, x):
		if x in list(self.Devices.keys()):
			return self.Devices[x].get("name", x)
		else:
			return "Unknown device name"

	def getDeviceList(self):
		return sorted(six.iterkeys(self.Devices))

	def getDefaultRCdeviceName(self):
		if config.misc.rcused.value == 1:
			for device in six.iterkeys(self.Devices):
				if self.Devices[device]["name"] == "dreambox remote control (native)":
					return device
		else:
			for device in six.iterkeys(self.Devices):
				if self.Devices[device]["name"] == "dreambox advanced remote control (native)":
					return device

	def setDeviceAttribute(self, device, attribute, value):
		#print "[iInputDevices] setting for device", device, "attribute", attribute, " to value", value
		if device in self.Devices:
			self.Devices[device][attribute] = value
			
	def getDeviceAttribute(self, device, attribute):
		if device in self.Devices:
			if attribute in self.Devices[device]:
				return self.Devices[device][attribute]
		return None
			
	def setEnabled(self, device, value):
		oldval = self.getDeviceAttribute(device, 'enabled')
		#print "[iInputDevices] setEnabled for device %s to %s from %s" % (device,value,oldval)
		self.setDeviceAttribute(device, 'enabled', value)
		if oldval is True and value is False:
			self.setDefaults(device)

	def setName(self, device, value):
		#print "[iInputDevices] setName for device %s to %s" % (device,value)
		self.setDeviceAttribute(device, 'configuredName', value)
		
	#struct input_event {
	#	struct timeval time;	-> ignored
	#	__u16 type;				-> EV_REP (0x14)
	#	__u16 code;				-> REP_DELAY (0x00) or REP_PERIOD (0x01)
	#	__s32 value;			-> DEFAULTS: 700(REP_DELAY) or 100(REP_PERIOD)
	#}; -> size = 16

	def setDefaults(self, device):
		print("[iInputDevices] setDefaults for device %s" % (device))
		self.setDeviceAttribute(device, 'configuredName', None)
		event_repeat = struct.pack('llHHi', 0, 0, 0x14, 0x01, 100)
		event_delay = struct.pack('llhhi', 0, 0, 0x14, 0x00, 700)
		fd = os_open("/dev/input/" + device, O_RDWR | O_CLOEXEC)
		os_write(fd, event_repeat)
		os_write(fd, event_delay)
		os_close(fd)

	def setRepeat(self, device, value): #REP_PERIOD
		if self.getDeviceAttribute(device, 'enabled') == True:
			print("[iInputDevices] setRepeat for device %s to %d ms" % (device,value))
			event = struct.pack('llHHi', 0, 0, 0x14, 0x01, int(value))
			fd = os_open("/dev/input/" + device, O_RDWR | O_CLOEXEC)
			os_write(fd, event)
			os_close(fd)

	def setDelay(self, device, value): #REP_DELAY
		if self.getDeviceAttribute(device, 'enabled') == True:
			print("[iInputDevices] setDelay for device %s to %d ms" % (device,value))
			event = struct.pack('llHHi', 0, 0, 0x14, 0x00, int(value))
			fd = os_open("/dev/input/" + device, O_RDWR | O_CLOEXEC)
			os_write(fd, event)
			os_close(fd)


class InitInputDevices:
	
	def __init__(self):
		self.currentDevice = ""
		self.createConfig()
	
	def createConfig(self, *args):
		config.inputDevices = ConfigSubsection()
		config.inputDevices.settings = ConfigSubsection()
		config.inputDevices.settings.firstDevice = ConfigBoolean(default=True)
		config.inputDevices.settings.logBattery = ConfigBoolean(default=False)
		config.inputDevices.settings.listboxFeedback = ConfigOnOff(default=True)
		colors = [
			("0xFF0000",_("red")),
			("0xFF3333", _("rose")),
			("0xFF5500", _("orange")),
			("0xDD9900", _("yellow")),
			("0x99DD00", _("lime")),
			("0x00FF00", _("green")),
			("0x00FF99", _("aqua")),
			("0x00BBFF", _("olympic blue")),
			("0x0000FF", _("blue")),
			("0x6666FF", _("azure")),
			("0x9900FF", _("purple")),
			("0xFF0066", _("pink")),
		]
		config.inputDevices.settings.connectedColor = ConfigSelection(colors, default="0xFF0066")
		config.inputDevices.settings.connectedColor.addNotifier(self._onConnectedRcuColorChanged, initial_call=False)

		for device in sorted(six.iterkeys(iInputDevices.Devices)):
			self.currentDevice = device
			#print "[InitInputDevices] -> creating config entry for device: %s -> %s  " % (self.currentDevice, iInputDevices.Devices[device]["name"])
			self.setupConfigEntries(self.currentDevice)
			self.currentDevice = ""

	def _onConnectedRcuColorChanged(self, *args):
		eInputDeviceManager.getInstance().setLedColor(int(config.inputDevices.settings.connectedColor.value, 0))

	def inputDevicesEnabledChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setEnabled(self.currentDevice, configElement.value)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setEnabled(iInputDevices.currentDevice, configElement.value)

	def inputDevicesNameChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setName(self.currentDevice, configElement.value)
			if configElement.value != "":
				devname = iInputDevices.getDeviceAttribute(self.currentDevice, 'name')
				if devname != configElement.value:
					exec("config.inputDevices." + self.currentDevice + ".enabled.value = False")
					exec("config.inputDevices." + self.currentDevice + ".enabled.save()")
		elif iInputDevices.currentDevice != "":
			iInputDevices.setName(iInputDevices.currentDevice, configElement.value)

	def inputDevicesRepeatChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setRepeat(self.currentDevice, configElement.value)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setRepeat(iInputDevices.currentDevice, configElement.value)
		
	def inputDevicesDelayChanged(self,configElement):
		if self.currentDevice != "" and iInputDevices.currentDevice == "":
			iInputDevices.setDelay(self.currentDevice, configElement.value)
		elif iInputDevices.currentDevice != "":
			iInputDevices.setDelay(iInputDevices.currentDevice, configElement.value)

	def setupConfigEntries(self,device):
		cmds = [
			"config.inputDevices." + device + " = ConfigSubsection()",
			"config.inputDevices." + device + ".enabled = ConfigYesNo(default = False)",
			"config.inputDevices." + device + ".enabled.addNotifier(self.inputDevicesEnabledChanged,config.inputDevices." + device + ".enabled)",
			"config.inputDevices." + device + ".name = ConfigText(default=\"\")",
			"config.inputDevices." + device + ".name.addNotifier(self.inputDevicesNameChanged,config.inputDevices." + device + ".name)",
			"config.inputDevices." + device + ".repeat = ConfigSlider(default=100, increment = 10, limits=(0, 500))",
			"config.inputDevices." + device + ".repeat.addNotifier(self.inputDevicesRepeatChanged,config.inputDevices." + device + ".repeat)",
			"config.inputDevices." + device + ".delay = ConfigSlider(default=700, increment = 100, limits=(0, 5000))",
			"config.inputDevices." + device + ".delay.addNotifier(self.inputDevicesDelayChanged,config.inputDevices." + device + ".delay)",
		]
		for cmd in cmds:
			exec(cmd)

iInputDevices = inputDevices()
