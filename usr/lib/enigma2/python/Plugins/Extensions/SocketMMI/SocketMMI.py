from Screens.Ci import MMIDialog
from socketmmi import eSocket_UI

class SocketMMIMessageHandler:
	def __init__(self):
		self.session = None
		self.dlgs = { }
		self.socket_ui = eSocket_UI.getInstance()
		self.socketStateChanged_conn = self.socket_ui.socketStateChanged.connect(self.socketStateChanged)

	def setSession(self, session):
		self.session = session

	def numConnections(self):
		return self.socket_ui.numConnections()

	def getState(self, slot):
		return self.socket_ui.getState(slot)

	def getName(self, slot):
		return self.socket_ui.getName(slot)

	def startMMI(self, slot):
		self.dlgs[slot] = self.session.openWithCallback(self.dlgClosed, MMIDialog, slot, 2, self.socket_ui, _("wait for mmi..."))

	def socketStateChanged(self, slot):
		if slot in self.dlgs:
			self.dlgs[slot].ciStateChanged()
		elif self.socket_ui.availableMMI(slot) == 1:
			if self.session:
				self.dlgs[slot] = self.session.openWithCallback(self.dlgClosed, MMIDialog, slot, 3, self.socket_ui, _("wait for mmi..."))

	def dlgClosed(self, slot):
		if slot in self.dlgs:
			del self.dlgs[slot]

