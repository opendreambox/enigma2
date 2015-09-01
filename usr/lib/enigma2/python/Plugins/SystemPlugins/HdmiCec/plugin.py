from enigma import eActionMap, eCec

from Components.HdmiCec import hdmi_cec
from Components.config import config

from Plugins.Plugin import PluginDescriptor

from CecConfig import CecConfig

from enigma import getExitCode
from Tools.Notifications import isPendingOrVisibleNotificationID

from CecRemoteHandler import CecRemoteHandler

class Cec(object):
	def __init__(self):
		self.session = None
		self.cec_recvStandby_conn = None
		self.cec_isNowActive_conn = None
		self._remoteHandler = None
		self.actionSlot = None
		self._idle_to_standby = False
		self._skip_next_poweroff_message = False
		self._skip_next_poweron_message = False
		self._started = False

	def start(self, session):
		if self._started:
			return
		self.session = session
		config.misc.standbyCounter.addNotifier(self._onStandby, initial_call = False)
		self.cec_recvStandby_conn = hdmi_cec.instance.receivedStandby.connect(self.__receivedStandby)
		self.cec_isNowActive_conn = hdmi_cec.instance.isNowActive.connect(self.__receivedNowActive)
		self.actionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self._onKeyPress) #highest prio
		self._remoteHandler = CecRemoteHandler() #the handler registeres all cec stuff itself, so no need to do anything else here
		self._started = True

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
			hdmi_cec.otpEnable()
			if config.cec.avr_power_explicit.value:
				self._remoteHandler.sendKey(5, eCec.RC_POWER_ON)
			hdmi_cec.systemAudioRequest()

	def powerOff(self):
		if self._idle_to_standby:
			return
		hdmi_cec.setPowerState(hdmi_cec.POWER_STATE_STANDBY)
		if config.cec.sendpower.value:
			print "[Cec] power off"
			if self._skip_next_poweroff_message:
				self._skip_next_poweroff_message = False
			else:
				hdmi_cec.systemStandby()
				if config.cec.avr_power_explicit.value:
					self._remoteHandler.sendKey(5, eCec.RC_POWER_OFF)
					hdmi_cec.systemStandby(target=5)

	def _onStandby(self, element):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.powerOn)
		self.powerOff()

	def _onKeyPress(self, keyid, flag):
		if config.cec.volume_forward.value:
			if flag == 0 or flag == 2:
				self._remoteHandler.sendSystemAudioKey(keyid)
		return 0

cec = Cec()

def autostart(reason, **kwargs):
	session = kwargs.get('session', None)
	if session is not None:
		cec.start(session)
	if reason == 0:
		if session is not None:
			if not isPendingOrVisibleNotificationID("Standby"):
				cec.powerOn()
	elif getExitCode() == 1: # send CEC poweroff only on complete box shutdown
		cec.powerOff()

def conf(session, **kwargs):
	session.open(CecConfig)

def menu(menuid, **kwargs):
	if menuid == "devices":
		return [(_("HDMI CEC"), conf, "hdmi_cec", 40)]
	else:
		return []

def Plugins(**kwargs):
	return [
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART] , fnc = autostart, weight=100),
		PluginDescriptor(name = "HDMI CEC", description = "Configure HDMI CEC", where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc = menu)
		]