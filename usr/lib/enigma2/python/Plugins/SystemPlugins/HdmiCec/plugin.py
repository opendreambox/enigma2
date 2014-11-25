from enigma import eActionMap

from Components.config import config
from Components.HdmiCec import hdmi_cec
from Plugins.Plugin import PluginDescriptor

from CecConfig import CecConfig

from enigma import getExitCode
from Tools.Notifications import isPendingOrVisibleNotificationID

class Cec(object):
	session = None

	def __init__(self):
		config.misc.standbyCounter.addNotifier(self._onStandby, initial_call = False)
		self.cec_recvStandby_conn = hdmi_cec.instance.receivedStandby.connect(self.__receivedStandby)
		self.cec_isNowActive_conn = hdmi_cec.instance.isNowActive.connect(self.__receivedNowActive)
		self.actionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.keypress) #highest prio
		self._idle_to_standby = False
		self._skip_next_poweroff_message = False
		self._skip_next_poweron_message = False

	def __receivedStandby(self):
		if config.cec.receivepower.value:
			self._skip_next_poweroff_message = True
			from Screens.Standby import Standby, inStandby
			if not inStandby and self.session.current_dialog and self.session.current_dialog.ALLOW_SUSPEND and self.session.in_exec:
				self.session.open(Standby)

	def __receivedNowActive(self):
		if config.cec.receivepower.value:
			self.powerOn(forceOtp=True)
			self._skip_next_poweron_message = True
			from Screens.Standby import inStandby
			if inStandby != None:
				inStandby.Power()

	def powerOn(self, forceOtp=False):
		if self._skip_next_poweron_message:
			self._skip_next_poweron_message = False
			return
		if self.session.shutdown:
			self._idle_to_standby = True
			return
		hdmi_cec.setPowerState(hdmi_cec.POWER_STATE_ON)
		if config.cec.sendpower.value or forceOtp:
			print "[Cec] power on"
			hdmi_cec.otp_source_enable()

	def powerOff(self):
		if self._idle_to_standby:
			return
		hdmi_cec.setPowerState(hdmi_cec.POWER_STATE_STANDBY)
		if config.cec.sendpower.value:
			print "[Cec] power off"
			if self._skip_next_poweroff_message:
				self._skip_next_poweroff_message = False
			else:
				hdmi_cec.ss_standby()

	def _onStandby(self, element):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.powerOn)
		self.powerOff()

	def keypress(self, key, flag):
		if config.cec.volume_forward.value:
			if flag == 0 or flag == 2:
				hdmi_cec.sendSystemAudioKey(key)
		return 0

cec = Cec()

def autostart(reason, **kwargs):
	session = kwargs.get('session', None)
	if session is not None:
		cec.session = session
	if reason == 0:
		if session is not None:
			if not isPendingOrVisibleNotificationID("Standby"):
				cec.powerOn()
	elif getExitCode() == 1: # send CEC poweroff only on complete box shutdown
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