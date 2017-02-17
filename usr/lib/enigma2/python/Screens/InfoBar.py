from Tools.Profile import profile

# workaround for required config entry dependencies.
from Screens.MovieSelection import MovieSelection

from Screen import Screen

profile("LOAD:enigma")
from enigma import iPlayableService

profile("LOAD:InfoBarGenerics")
from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarRdsDecoder, \
	InfoBarEPG, InfoBarSeek, InfoBarInstantRecord, \
	InfoBarAudioSelection, InfoBarAdditionalInfo, InfoBarDish, InfoBarUnhandledKey, \
	InfoBarSubserviceSelection, InfoBarShowMovies, InfoBarTimeshift,  \
	InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSimpleEventView, \
	InfoBarSummarySupport, InfoBarMoviePlayerSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfobarHbbtvPlugin, InfoBarExtensions, InfoBarNotifications, \
	InfoBarSubtitleSupport, InfoBarPiP, InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarAutoSleepTimer, InfoBarGstreamerErrorPopupSupport

from Screens.InfoBarPrivate import InfoBarPrivateExtensions
profile("LOAD:InitBar_Components")
from Components.ActionMap import HelpableActionMap
from Components.config import config, ConfigBoolean
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

profile("LOAD:HelpableScreen")
from Screens.HelpMenu import HelpableScreen

config.misc.initialharddisknotification = ConfigBoolean(True)
config.misc.missingdefaultstoragenotification = ConfigBoolean(False)

from Tools import Notifications
Notifications.notificationQueue.registerDomain("InfoBar", _("InfoBar"), Notifications.ICON_DEFAULT)

class InfoBar(InfoBarBase, InfoBarShowHide,
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder,
	InfoBarInstantRecord, InfoBarAudioSelection,
	HelpableScreen, InfoBarAdditionalInfo, InfoBarDish, InfoBarUnhandledKey,
	InfoBarSubserviceSelection, InfoBarTimeshift, InfoBarSeek,
	InfoBarSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfobarHbbtvPlugin, InfoBarExtensions, InfoBarNotifications,
	InfoBarPiP, InfoBarPlugins, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarAutoSleepTimer,
	InfoBarPrivateExtensions, InfoBarGstreamerErrorPopupSupport,
	Screen):

	ALLOW_SUSPEND = True
	instance = None

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(self, "InfobarActions",
			{
				"showMovies": (self.showMovies, _("Play recorded movies...")),
				"showRadio": (self.showRadio, _("Show the radio player...")),
				"showTv": (self.showTv, _("Show the tv player...")),
			}, prio=2)

		self.allowPiP = True

		for x in HelpableScreen, \
				InfoBarBase, InfoBarShowHide, \
				InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder, \
				InfoBarInstantRecord, InfoBarAudioSelection, InfoBarUnhandledKey, \
				InfoBarAdditionalInfo, InfoBarDish, InfoBarSubserviceSelection, \
				InfoBarTimeshift, InfoBarSeek, InfoBarSummarySupport, InfoBarTimeshiftState, \
				InfoBarTeletextPlugin, InfobarHbbtvPlugin, InfoBarExtensions, InfoBarNotifications, InfoBarPiP, InfoBarSubtitleSupport, InfoBarJobman, \
				InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarAutoSleepTimer, InfoBarPrivateExtensions, InfoBarGstreamerErrorPopupSupport:
			x.__init__(self)

		self.helpList.append((self["actions"], "InfobarActions", [("showMovies", _("view recordings..."))]))
		self.helpList.append((self["actions"], "InfobarActions", [("showRadio", _("hear radio..."))]))

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
			})

		self.current_begin_time=0
		assert InfoBar.instance is None, "class InfoBar is a singleton class and just one instance of this class is allowed!"
		InfoBar.instance = self
		for fnc in plugins.getPlugins(PluginDescriptor.WHERE_INFOBAR):
			fnc(session)

		self.showHarddiskPopup()

		self.onClose.append(self.__onClose)

	def showHarddiskPopup(self, dev = None, media_state = None):
		from Components.Harddisk import harddiskmanager
		if not self.HDDDetectedCB in harddiskmanager.delayed_device_Notifier:
			harddiskmanager.delayed_device_Notifier.append(self.HDDDetectedCB)
		if config.misc.initialharddisknotification.value:
			from Screens.MessageBox import MessageBox
			if harddiskmanager.HDDCount() and not harddiskmanager.HDDEnabledCount():
				Notifications.AddNotificationWithCallback(self.HDDDetectedAnswer, MessageBox, _("Unconfigured storage devices found!")  + "\n" \
					+ _("Please make sure to set up your storage devices with the storage management in menu -> setup -> system -> storage devices.") + "\n\n" \
					+ _("Set up your storage device now?"), type = MessageBox.TYPE_YESNO, timeout = 15, default = False, domain = "InfoBar")
				config.misc.initialharddisknotification.value = False
				config.misc.initialharddisknotification.save()
		elif config.misc.missingdefaultstoragenotification.value and not config.misc.initialharddisknotification.value:
			from Screens.ChoiceBox import ChoiceBox
			from Components.UsageConfig import defaultStorageDevice
			choices = [
				(_("OK, do nothing"), "ok"),
				(_("OK, and don't ask again"), "ok_always")
			]
			if harddiskmanager.HDDCount():
				choices.append((_("OK, and set up a new default storage device"), "ok_setup"))
			titletxt = _("Default storage device is not available!") + "\n"
			if dev is None and defaultStorageDevice() != "<undefined>" and harddiskmanager.isDefaultStorageDeviceActivebyUUID(defaultStorageDevice()) is False:
				Notifications.AddNotificationWithCallback(self.missingDefaultHDDAnswer, ChoiceBox, title = titletxt \
					+ _("Please verify if your default storage device is attached or set up your default storage device in menu -> setup -> system -> storage devices.") + "\n", list = choices, domain = "InfoBar")
			elif dev is not None and defaultStorageDevice() != "<undefined>" and harddiskmanager.isDefaultStorageDeviceActivebyUUID(defaultStorageDevice()) is False:
				part = harddiskmanager.getPartitionbyDevice(dev)
				if part is not None and part.uuid is not None and media_state is not None and media_state == "remove_default":
					titletxt = _("Default storage device was removed!") + "\n"
					Notifications.AddNotificationWithCallback(self.missingDefaultHDDAnswer, ChoiceBox, title = titletxt \
						+ _("Please verify if your default storage device is attached or set up your default storage device in menu -> setup -> system -> storage devices.") + "\n", list = choices, domain = "InfoBar")

	def missingDefaultHDDAnswer(self, answer):
		answer = answer and answer[1]
		if answer is not None:
			if answer == "ok_always":
				print answer
				config.misc.missingdefaultstoragenotification.value = False
				config.misc.missingdefaultstoragenotification.save()
			elif answer == "ok_setup":
				print answer
				from Screens.HarddiskSetup import HarddiskDriveSelection
				self.session.open(HarddiskDriveSelection)

	def HDDDetectedAnswer(self, answer):
		if answer is not None:
			if answer:
				from Screens.HarddiskSetup import HarddiskDriveSelection
				self.session.open(HarddiskDriveSelection)

	def HDDDetectedCB(self, dev, media_state):
		if InfoBar.instance:
			if InfoBar.instance.execing:
				self.showHarddiskPopup(dev, media_state)
			else:
				print "HDDDetectedCB: main infobar is not execing... so we ignore hotplug event!"
		else:
				print "HDDDetectedCB: hotplug event.. but no infobar"

	def __onClose(self):
		InfoBar.instance = None

	def __eventInfoChanged(self):
		if self.execing:
			service = self.session.nav.getCurrentService()
			old_begin_time = self.current_begin_time
			info = service and service.info()
			ptr = info and info.getEvent(0)
			self.current_begin_time = ptr and ptr.getBeginTime() or 0
			if config.usage.show_infobar_on_event_change.value:
				if old_begin_time and old_begin_time != self.current_begin_time:
					self.doShow()

	def serviceStarted(self):  #override from InfoBarShowHide
		new = self.servicelist.newServicePlayed()
		if self.execing:
			InfoBarShowHide.serviceStarted(self)
			self.current_begin_time=0
		elif not self.__checkServiceStarted in self.onShown and new:
			self.onShown.append(self.__checkServiceStarted)

	def __checkServiceStarted(self):
		self.serviceStarted()
		self.onShown.remove(self.__checkServiceStarted)

	def showTv(self):
		self.showTvChannelList(True)

	def showRadio(self):
		if config.usage.e1like_radio_mode.value:
			self.showRadioChannelList(True)
		else:
			self.rds_display.hide() # in InfoBarRdsDecoder
			from Screens.ChannelSelection import ChannelSelectionRadio
			self.session.openWithCallback(self.ChannelSelectionRadioClosed, ChannelSelectionRadio, self)

	def ChannelSelectionRadioClosed(self, *arg):
		self.rds_display.show()  # in InfoBarRdsDecoder

	def showMovies(self):
		self.session.openWithCallback(self.movieSelected, MovieSelection)

	def movieSelected(self, service):
		if service is not None:
			self.session.open(MoviePlayer, service)

class MoviePlayer(InfoBarBase, InfoBarShowHide, \
		InfoBarMenu, \
		InfoBarSeek, InfoBarShowMovies, InfoBarAudioSelection, HelpableScreen,
		InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSimpleEventView,
		InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin,
		InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications, InfoBarPlugins, InfoBarPiP, InfoBarGstreamerErrorPopupSupport):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service):
		Screen.__init__(self, session)

		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, _("leave movie player..."))
			})

		self.allowPiP = False

		for x in HelpableScreen, InfoBarShowHide, InfoBarMenu, \
				InfoBarBase, InfoBarSeek, InfoBarShowMovies, \
				InfoBarAudioSelection, InfoBarSimpleEventView, \
				InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, \
				InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, \
				InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications, \
				InfoBarPlugins, InfoBarPiP, InfoBarGstreamerErrorPopupSupport:
			x.__init__(self)

		session.nav.playService(service)
		self.returning = False

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			if config.usage.setup_level.index < 2: # -expert
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue")
				)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("Yes, returning to movie list"), "movielist"),
					(_("Yes, and delete this movie"), "quitanddelete"),
					(_("No"), "continue"),
					(_("No, but restart from begin"), "restart")
				)

			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		self.handleLeave(config.usage.on_movie_stop.value)

	def deleteConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "quitanddeleteconfirmed"))

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]

		if answer in ("quitanddelete", "quitanddeleteconfirmed"):
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			from enigma import eServiceCenter
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(ref)
			name = info and info.getName(ref) or _("this recording")

			if answer == "quitanddelete":
				from Screens.MessageBox import MessageBox
				self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do you really want to delete %s?") % name)
				return

			elif answer == "quitanddeleteconfirmed":
				offline = serviceHandler.offlineOperations(ref)
				if offline.deleteFromDisk(0):
					from Screens.MessageBox import MessageBox
					self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)
					return

		if answer in ("quit", "quitanddeleteconfirmed"):
			self.close()
		elif answer == "movielist":
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			self.returning = True
			self.session.openWithCallback(self.movieSelected, MovieSelection, ref)
			self.session.nav.stopService()
		elif answer == "restart":
			self.doSeek(0)
			self.setSeekState(self.SEEK_STATE_PLAY)

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.handleLeave(config.usage.on_movie_eof.value)

	def showMovies(self):
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.openWithCallback(self.movieSelected, MovieSelection, ref)

	def movieSelected(self, service):
		if service is not None:
			self.is_closing = False
			self.session.nav.playService(service)
			self.returning = False
		elif self.returning:
			self.close()
