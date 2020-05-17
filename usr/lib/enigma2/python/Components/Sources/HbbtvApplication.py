from __future__ import absolute_import
from enigma import eHbbtv
from Components.Sources.Source import Source
from Components.Element import cached

class HbbtvApplication(Source):
	def __init__(self):
		Source.__init__(self)
		self.disabled = False
		self._available = False
		self._appname = ""
		self.redButtonAppplicationReady_conn = eHbbtv.getInstance().redButtonAppplicationReady.connect(self._redButtonApplicationReady)
		self.aitInvalidated_conn = eHbbtv.getInstance().aitInvalidated.connect(self._aitInvalidated)
	
	def _redButtonApplicationReady(self, appid):
		app = eHbbtv.getInstance().getApplication(appid)
		if app.isValid():
			self._available = True
			self._appname = app.getName()
			self.changed((self.CHANGED_ALL,))
		else:
			self._aitInvalidated()

	def _aitInvalidated(self):
		self._available = False
		self._appname = ""
		self.changed((self.CHANGED_ALL,))
	
	def destroy(self):
		self.redButtonAppplicationReady_conn = None
		self.aitInvalidated_conn = None
		Source.destroy(self)

	@cached
	def getBoolean(self):
		return False if self.disabled else self._available

	boolean = property(getBoolean)

	@cached
	def getName(self):
		return "" if self.disabled else self._appname

	name = property(getName) 