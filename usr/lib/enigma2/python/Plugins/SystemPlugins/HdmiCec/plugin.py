from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Components.HdmiCec import hdmi_cec
from Plugins.Plugin import PluginDescriptor
from Screens import Screen
from Tools.DreamboxHardware import getFPWasTimerWakeup

from CecConfig import CecConfig

config.plugins.cec = ConfigSubsection()
config.plugins.cec.power = ConfigEnableDisable(default=True)

class Cec(object):
	def __init__(self):
		config.misc.standbyCounter.addNotifier(self._onStandby, initial_call = False)

	def powerOn(self):
		if config.plugins.cec.power.value:
			print "[Cec] power on"
			hdmi_cec.otp_source_enable()

	def powerOff(self):
		if config.plugins.cec.power.value:
			print "[Cec] power off"
			hdmi_cec.ss_standby()

	def _onStandby(self, element):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.powerOn)
		self.powerOff()

cec = Cec()

def autostart(reason, **kwargs):
	if reason == 0:
		session = kwargs.get('session', None)
		if session is not None:
			#only send cec power on if it hasn been a record-timer issued poweron
			if not session.nav.wasTimerWakeup() or session.nav.RecordTimer.getNextRecordingTime() > session.nav.RecordTimer.getNextZapTime():
				cec.powerOn()
	else:
		cec.powerOff()

def conf(session, **kwargs):
	session.open(CecConfig)

def menu(menuid, **kwargs):
	if menuid == "system":
		return [(_("HDMI CEC"), conf, "hdmi_cec", None)]
	else:
		return []

def Plugins(**kwargs):
	return [
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART] , fnc = autostart),
		PluginDescriptor(name = "HDMI CEC", description = "Configure HDMI CEC", where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc = menu)
		]