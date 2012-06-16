from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Components.HdmiCec import hdmi_cec
from Plugins.Plugin import PluginDescriptor

from CecConfig import CecConfig

config.plugins.cec = ConfigSubsection()
config.plugins.cec.sendpower = ConfigEnableDisable(default=True)
config.plugins.cec.receivepower = ConfigEnableDisable(default=False)

class Cec(object):
	session = None

	def __receivedStandby(self):
		if config.plugins.cec.receivepower.value:
			from Screens.Standby import Standby, inStandby
			if not inStandby and self.session.current_dialog and self.session.current_dialog.ALLOW_SUSPEND and self.session.in_exec:
				self.session.open(Standby)

	def __receivedNowActive(self):
		if config.plugins.cec.receivepower.value:
			from Screens.Standby import inStandby
			if inStandby != None:
				inStandby.Power()

	def __init__(self):
		config.misc.standbyCounter.addNotifier(self._onStandby, initial_call = False)
		hdmi_cec.instance.receivedStandby.get().append(self.__receivedStandby)
		hdmi_cec.instance.isNowActive.get().append(self.__receivedNowActive)

	def powerOn(self):
		if config.plugins.cec.sendpower.value:
			print "[Cec] power on"
			hdmi_cec.otp_source_enable()

	def powerOff(self):
		if config.plugins.cec.sendpower.value:
			print "[Cec] power off"
			hdmi_cec.ss_standby()

	def _onStandby(self, element):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.powerOn)
		self.powerOff()

cec = Cec()

def autostart(reason, **kwargs):
	session = kwargs.get('session', None)
	if session is not None:
		cec.session = session
	if reason == 0:
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