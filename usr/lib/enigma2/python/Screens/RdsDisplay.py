from enigma import iPlayableService, iRdsDecoder
from Screens.Screen import Screen
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Pixmap import Pixmap
from Components.Label import Label

class RdsInfoDisplay(Screen):
	ALLOW_SUSPEND = True
	
	def __init__(self, session):
		Screen.__init__(self, session)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEnd: self.__serviceStopped,
				iPlayableService.evUpdatedRadioText: self.RadioTextChanged,
				iPlayableService.evUpdatedRtpText: self.RtpTextChanged,
			})

		self["RadioText"] = Label()
		self["RtpText"] = Label()
		self["RassLogo"] = Pixmap()

		self.onLayoutFinish.append(self.hideWidgets)
		self.onHide.append(self.hideWidgets)
		self.onRassInteractivePossibilityChanged = [ ]

	def hideWidgets(self):
		for x in (self["RadioText"],self["RtpText"],self["RassLogo"]):
			x.hide()

	def RadioTextChanged(self):
		service = self.session.nav.getCurrentService()
		decoder = service and service.rdsDecoder()
		rdsText = decoder and decoder.getText(iRdsDecoder.RadioText)
		if rdsText:
			self.show()
			self["RadioText"].setText(rdsText)
			self["RadioText"].show()
		else:
			if not self["RtpText"].text:
				self.hide()
			self["RadioText"].hide()

	def RtpTextChanged(self):
		service = self.session.nav.getCurrentService()
		decoder = service and service.rdsDecoder()
		rtpText = decoder and decoder.getText(iRdsDecoder.RtpText)
		if rtpText:
			self.show()
			self["RtpText"].setText(rtpText)
			self["RtpText"].show()
		else:
			if not self["RadioText"].text:
				self.hide()
			self["RtpText"].hide()

	def __serviceStopped(self):
		self.hide()
