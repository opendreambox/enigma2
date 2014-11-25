# -*- coding: utf-8 -*-

from enigma import eNetworkManager, StringMap
from Components.config import config, ConfigBoolean
from Components.Input import Input
from Plugins.Plugin import PluginDescriptor
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Tools.Log import Log

from MultiInputBox import MultiInputBox
from NetworkConfig import NetworkServiceConfig

from NetworkWizard import NetworkWizardNew

class NetworkAgent(object):
	def __init__(self, session):
		self._nm = eNetworkManager.getInstance()
		self.session = session

		self._userInputField = None
		self._connected_signals = []
		self._userInputScreen = None
		ap = self._connected_signals.append
		ap( self._nm.userInputRequested.connect(self._userInputRequested) )
		ap( self._nm.userInputCanceled.connect(self._userInputCanceled) )
		ap( self._nm.errorReported.connect(self._errorReported) )

	def _errorReported(self, svcpath, error):
		Log.w("Network service %s report an error: %s" %(svcpath, error))
		service = self._nm.getService(svcpath)
		svcname = svcpath
		if service:
			svcname = service.name()
		title = _("Network error on %s" %svcname)
		self.session.open(MessageBox, error, type=MessageBox.TYPE_ERROR, title=title)

	def _userInputRequested(self, svcpath):
		Log.i(svcpath)
		dialog_values = self._nm.getUserInputRequestFields()
		for key,value in dialog_values.iteritems():
			Log.i("%s => %s" %(key, value))

		windowTitle = _("Network")
		svc = self._nm.getService(svcpath)
		if svc:
			windowTitle = svc.name()

		prev = dialog_values.get("PreviousPassphrase", None)
		if prev:
			del dialog_values["PreviousPassphrase"]

		if len(dialog_values) == 1:
			request_part = dialog_values.values()[0]
			title = self._userInputField = dialog_values.keys()[0]
			if request_part["Requirement"] == "mandatory":
				title = "%s" %title
			title = "%s (%s)" %(title, request_part["Type"])
			self._userInputScreen = self.session.openWithCallback(self._onUserInput, InputBox, title=title, windowTitle=windowTitle)
		elif len(dialog_values) == 2:
			first, second = dialog_values.keys()
			input_config = {
				"first" : self._createInputConfig(first, dialog_values[first], prev),
				"second" : self._createInputConfig(second, dialog_values[second], prev),
			}
			self._userInputScreen = self.session.openWithCallback(self._onUserMultiInput, MultiInputBox, title=_("Input required"), windowTitle=windowTitle, config=input_config)
		else:
			self._nm.sendUserReply(StringMap()) #Cancel

	def _createInputConfig(self, key, request_part, previousPassphrase):
			requirement = request_part["Requirement"] == "mandatory"
			val_type = Input.TEXT
			if request_part["Type"] == "wpspin":
				val_type = Input.PIN

			value = ""
			if previousPassphrase and request_part["Type"] == previousPassphrase["Type"]:
				value = str(previousPassphrase["value"])

			alternatives = request_part.get("Alternates", [])
			return {
				"key" : key,
				"value" : value,
				"title" : key,
				"required" : requirement,
				"type" : val_type,
				"alternatives" : alternatives,
			}

	def _userInputCanceled(self):
		if self._userInputScreen:
			self._userInputScreen.close()
			self._userInputScreen = None
		self.session.open(MessageBox, _("There was no input for too long!"), type=MessageBox.TYPE_ERROR, title=_("Timeout!"))

	def _onUserMultiInput(self, values):
		Log.i(values)
		self._userInputScreen = None
		if values:
			self._nm.sendUserReply(StringMap(values))
		else:
			self._nm.sendUserReply(StringMap())

	def _onUserInput(self, value):
		Log.i(self._userInputField)
		self._userInputScreen = None
		if value and self._userInputField != None:
			answer = StringMap({self._userInputField : value})
			self._nm.sendUserReply(answer)
		else:
			self._nm.sendUserReply(StringMap()) #cancel

	def shutdown(self):
		Log.i("cancelling any pending request")
		if self._userInputScreen:
			self._nm.sendUserReply(StringMap()) #cancel request

global networkagent
networkagent = None
def main(reason, **kwargs):
	global networkagent
	if reason == 0:
		session = kwargs.get("session", None)
		if session:
			networkagent = NetworkAgent(session)
	elif reason == 1 and networkagent:
		networkagent.shutdown()

def nw_setup(session, **kwargs):
	session.open(NetworkServiceConfig)

def nw_menu(menuid, **kwargs):
	if menuid == "network":
		return [(_("Network Setup"), nw_setup, "nw_setup", 1)]
	else:
		return []

config.misc.firstrun = ConfigBoolean(default = True)
def runNetworkWizard(*args, **kwargs):
	return NetworkWizardNew(*args, **kwargs)

def Plugins(**kwargs):
	lst = [
		PluginDescriptor(name="Network Agent", where=[PluginDescriptor.WHERE_SESSIONSTART,PluginDescriptor.WHERE_AUTOSTART], needsRestart=False, fnc=main),
		PluginDescriptor(name=_("Network"), description=_("Set up your Network connections"), where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc=nw_menu)
	]
	if config.misc.firstrun.value:
		NetworkWizardNew.firstRun = True
		NetworkWizardNew.checkNetwork = True
		lst.append(PluginDescriptor(name=_("Network Wizard"), where = PluginDescriptor.WHERE_WIZARD, needsRestart = False, fnc=(25, runNetworkWizard)))
	return lst