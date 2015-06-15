from Screens.Ci import MMIDialog
import socketmmi

class SocketMMIMessageHandler:
	def __init__(self):
		self.session = None
		self.dlgs = { }
		socketmmi.getSocketStateChangedCallbackList().append(self.socketStateChanged)

	def setSession(self, session):
		self.session = session

	def numConnections(self):
		return socketmmi.numConnections()

	def getState(self, slot):
		return socketmmi.getState(slot)

	def getName(self, slot):
		return socketmmi.getName(slot)

	def startMMI(self, slot):
		self.dlgs[slot] = self.session.openWithCallback(self.dlgClosed, MMIDialog, slot, 2, socketmmi, _("wait for mmi..."))

	def socketStateChanged(self, slot):
		if slot in self.dlgs:
			self.dlgs[slot].ciStateChanged()
		elif socketmmi.availableMMI(slot) == 1:
			if self.session:
				self.dlgs[slot] = self.session.openWithCallback(self.dlgClosed, MMIDialog, slot, 3, socketmmi, _("wait for mmi..."))

	def dlgClosed(self, slot):
		if slot in self.dlgs:
			del self.dlgs[slot]

