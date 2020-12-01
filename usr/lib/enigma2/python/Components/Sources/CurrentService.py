from __future__ import absolute_import
from Components.PerServiceDisplay import PerServiceBase
from enigma import iPlayableService
from Components.Sources.Source import Source
from Components.Element import cached

class CurrentService(PerServiceBase, Source):
	def __init__(self, navcore):
		Source.__init__(self)
		PerServiceBase.__init__(self, navcore, 
			{ 
				iPlayableService.evStart: self.serviceEvent,
				iPlayableService.evEnd: self.serviceEvent,
				# FIXME: we should check 'interesting_events'
				# which is not always provided.
				iPlayableService.evSubtitleListChanged : self.serviceEvent,
				iPlayableService.evUpdatedInfo: self.serviceEvent,
				iPlayableService.evUpdatedEventInfo: self.serviceEvent,
				iPlayableService.evCuesheetChanged: self.serviceEvent,
				iPlayableService.evVideoSizeChanged: self.serviceEvent,
				iPlayableService.evVideoTypeReady: self.serviceEvent,
				iPlayableService.evVideoProgressiveChanged: self.serviceEvent,
				iPlayableService.evVideoFramerateChanged: self.serviceEvent,
			}, with_event=True)
		self.navcore = navcore

	def serviceEvent(self, event):
		self.changed((self.CHANGED_SPECIFIC, event))

	@cached
	def getCurrentService(self):
		return self.navcore.getCurrentService()

	service = property(getCurrentService)

	def destroy(self):
		PerServiceBase.destroy(self)
		Source.destroy(self)

