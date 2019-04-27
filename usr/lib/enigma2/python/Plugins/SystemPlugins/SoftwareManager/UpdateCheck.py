from enigma import eNetworkManager, eTimer
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigSelection, ConfigDateTime, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from Tools.Log import Log
from Tools import Notifications

from SoftwareTools import iSoftwareTools
from UpdatePlugin import UpdatePlugin

from time import time, strftime, localtime
from twisted.internet import reactor

UPDATE_CHECK_NEVER = "0"
UPDATE_CHECK_DAILY = "1"
UPDATE_CHECK_WEEKLY = "7"
UPDATE_CHECK_MONTHLY = "30"

config.plugins.updatechecker = ConfigSubsection()
config.plugins.updatechecker.checkonboot = ConfigEnableDisable(default=False)
config.plugins.updatechecker.lastcheck = ConfigDateTime(0, "%Y-%m-%d %H:%M:%S")
config.plugins.updatechecker.interval = ConfigSelection(choices= [
											(UPDATE_CHECK_NEVER, _("never")),
											(UPDATE_CHECK_DAILY, _("daily")),
											(UPDATE_CHECK_WEEKLY, _("weekly")),
											(UPDATE_CHECK_MONTHLY, _("monthly")),
										], default=UPDATE_CHECK_WEEKLY)

class UpdateCheck(object):
	def __init__(self):
		self.onUpdatesAvailable = []
		self._session = None
		self._onlineChangedConn = None
		self._checkTimer = eTimer()
		self._nextCheck = 0
		self.__checkTimerConn = self._checkTimer.timeout.connect(self.check)
		config.plugins.updatechecker.interval.addNotifier(self.onConfigChanged, initial_call=False)

	def getNextCheck(self):
		return self._nextCheck
	nextCheck = property(getNextCheck)

	def onConfigChanged(self, *args):
		self.recalcNext()

	def onOnlineStateChanged(self, state):
		if state:
			self.check()

	def recalcNext(self, last=None):
		if last:
			config.plugins.updatechecker.lastcheck.value = int(last)
			config.plugins.updatechecker.save()
		self._checkTimer.stop()
		if config.plugins.updatechecker.interval.value == UPDATE_CHECK_NEVER:
			Log.w("Periodical update checks disabled")
			return
		days = float(config.plugins.updatechecker.interval.value)
		distance = days * 24 * 60 * 60
		now = time()
		self._nextCheck = config.plugins.updatechecker.lastcheck.value + distance
		if self._nextCheck < now: #next check would be in the past?
			self._nextCheck = now + 300 #5 Minutes from now
		nextDistance = int(self._nextCheck - now)
		Log.w("Next update check on %s (%s seconds)" %(strftime("%a, %d %b %Y %H:%M:%S", localtime(self._nextCheck)), nextDistance))
		if nextDistance < 0:
			nextDistance = 0
		self._checkTimer.startLongTimer(nextDistance)

	def start(self, session):
		self._session = session
		self._onlineChangedConn = None
		if config.plugins.updatechecker.checkonboot.value:
			self.check()
		else:
			self.recalcNext()

	def check(self):
		if config.plugins.updatechecker.interval.value != UPDATE_CHECK_NEVER or config.plugins.updatechecker.checkonboot.value:
			iSoftwareTools.startSoftwareTools(self._onSoftwareToolsReady)

	def _onSoftwareToolsReady(self, retval = None):
		if retval is None:
			return
		if retval:
			self.recalcNext(iSoftwareTools.lastDownloadDate)
			if iSoftwareTools.available_updates is not 0:
				title = _("There are %s updates available.") %(iSoftwareTools.available_updates,)
				Log.w(title)
				Log.i(iSoftwareTools.available_updatelist)
				Notifications.AddNotificationWithCallback(self._onUpdateAnswer, MessageBox, text=_("Do you want to update now?"), windowTitle=title)
				for fnc in self.onUpdatesAvailable:
					fnc(iSoftwareTools.available_updates)
			else:
				self._session.toastManager.showToast(_("Your Dreambox software is up to date!"))
				Log.i("There are no updates available.")
		else:
			if iSoftwareTools.NetworkConnectionAvailable:
				Log.w("Package-Feed not available.")
			else:
				Log.w("No network connection available.")
				self._onlineChangedConn = eNetworkManager.getInstance().onlineChanged.connect(self.onOnlineStateChanged)

	def _onUpdateAnswer(self, answer):
		if answer:
			self._session.open(UpdatePlugin)

class UpdateCheckConfig(Screen, ConfigListScreen):
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		self.skinName = "Setup"
		self.setTitle(_("Update Check Setup"))

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyCancel,
			"green": self.keySave,
			"save": self.close,
			"cancel": self.close,
		}, -2)

		self._createSetup()
		config.plugins.updatechecker.interval.addNotifier(self._onChange, initial_call=False)

		self.onClose.append(self._onClose)

	def _onClose(self):
		config.plugins.updatechecker.save()
		config.plugins.updatechecker.interval.removeNotifier(self._onChange)

	def _onChange(self, *args):
		#use reactor so other notifiers can finish before we act
		reactor.callLater(0,self._createSetup)

	def _createSetup(self):
		configNextCheck = ConfigDateTime(updateCheck.nextCheck, "%Y-%m-%d %H:%M:%S")
		configNextCheck.enabled = False
		config.plugins.updatechecker.lastcheck.enabled = False
		l = [
				getConfigListEntry(_("Check on every boot"), config.plugins.updatechecker.checkonboot),
				getConfigListEntry(_("Automatically check for new updates"), config.plugins.updatechecker.interval),
			]
		if config.plugins.updatechecker.interval.value != UPDATE_CHECK_NEVER:
			l.extend([
				getConfigListEntry(_("Last check"), config.plugins.updatechecker.lastcheck),
				getConfigListEntry(_("Next check"), configNextCheck),
			])
		self["config"].list = l
		self["config"].l.setList(l)

updateCheck = UpdateCheck()
