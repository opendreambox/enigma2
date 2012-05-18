from datetime import datetime
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigYesNo
from Components.ActionMap import NumberActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.MultiContent import MultiContentEntryText
from Components.ResourceManager import resourcemanager
from Tools.BoundFunction import boundFunction
from Tools import Notifications
from enigma import gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_WRAP
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

ICON_PENDING = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/buttons/button_green.png'))
ICON_SEEN = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/buttons/button_green_off.png'))

class NotificationQueueViewer(Screen):
  	skin = """
		<screen position="100,100" size="550,416" title="Notification Queue Viewer" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;19" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;19" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="label_results" render="Label" position="290,0" size="250,40" font="Regular;19" halign="center" valign="center" transparent="1" />
			<widget source="labels" render="Listbox" scrollbarMode="showOnDemand" position="10,48" size="530,16" zPosition="3" transparent="1" >
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos = (0, 0), size = (74, 16), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 Time,
							MultiContentEntryText(pos = (76, 0), size = (0, 0), font = 0, flags = RT_HALIGN_LEFT, text = 2), # domain icon
							MultiContentEntryText(pos = (76, 0), size = (98, 16), font = 0, flags = RT_HALIGN_CENTER, text = 3), # index 3 Domain,
							MultiContentEntryText(pos = (176, 0), size = (310, 16), font = 0, flags = RT_HALIGN_LEFT, text = 4), # index 4 Text,
							MultiContentEntryText(pos = (466, 0), size = (55, 16), font = 0, flags = RT_HALIGN_CENTER, text = 5), # index 5 is the pending pixmap
						],
					"fonts": [gFont("Regular", 14)],
					"itemHeight": 14
					}
				</convert>
			</widget>
			<widget source="notifications" render="Listbox" scrollbarMode="showOnDemand" position="10,68" size="530,320" zPosition="3" transparent="1" >
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos = (0, 2), size = (74, 30), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 Time,
							MultiContentEntryPixmapAlphaTest(pos = (76, 2), size = (22, 22), png = 2), # domain icon
							MultiContentEntryText(pos = (100, 2), size = (74, 30), font = 0, flags = RT_HALIGN_LEFT|RT_WRAP, text = 3), # index 3 Domain,
							MultiContentEntryText(pos = (176, 2), size = (310, 30), font = 0, flags = RT_HALIGN_LEFT|RT_WRAP, text = 4), # index 4 Text,
							MultiContentEntryPixmapAlphaTest(pos = (486, 8), size = (15, 16), png = 5), # index 5 is the pending pixmap
						],
					"fonts": [gFont("Regular", 14)],
					"itemHeight": 32
					}
				</convert>
			</widget>
			<widget source="statusbar" render="Label" position="10,392" size="530,20" halign="left" valign="center" font="Regular;14" backgroundColor="#254f7497" foregroundColor="#272F97" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Select"))
		
		self["label_results"] = StaticText(_("Results"))
		self["statusbar"] = StaticText()

		self["labels"] =  List([(None, _("Time"), "icon", _("Domain"), _("Text"), (_("New")+'?'))])
		self["notifications"] = List([])
	
		self["setupActions"] = NumberActionMap(["ColorActions", "WizardActions"],
		{
			"red": self.keyRed,
			"green": self.keyGreen,
			"back": self.keyRed,
			"ok": self.keyGreen,
			"up": self.keyUp,
			"down": self.keyDown,
		}, -3)
		
		if not self.selectionChanged in self["notifications"].onSelectionChanged:
			self["notifications"].onSelectionChanged.append(self.selectionChanged)
		Notifications.notificationQueue.addedCB.append(self.checkNotifications)
		self.onClose.append(self.__removeNotification)
		self.onLayoutFinish.append(self.refreshList)

	def __removeNotification(self):
		Notifications.notificationQueue.addedCB.remove(self.checkNotifications)

	def checkNotifications(self):
		print "[NotificationQueueViewer::checkNotifications]"
		self.refreshList()
		Notifications.notificationQueue.popNotification(self)

	def keyUp(self):
		self["notifications"].selectPrevious()

	def keyDown(self):
		self["notifications"].selectNext()
		
	def selectionChanged(self):
		current = self["notifications"].getCurrent()
		if isinstance(current, tuple):
			entry = current[0]
			self["statusbar"].text = _("Press OK to get further details for %s") % (Notifications.notificationQueue.domains[entry.domain]["name"] + ' ' +_("Notification"))

	def refreshList(self):
		entries = []
		for entry in reversed(Notifications.notificationQueue.queue):
			timetext = entry.timestamp.strftime("%Y-%m-%d\n%H:%M:%S")
			domain = Notifications.notificationQueue.domains[entry.domain]
			entries.append((entry, timetext, domain["icon"], domain["name"], entry.text, ICON_PENDING if entry.pending else ICON_SEEN))
		num_pending = len(Notifications.notificationQueue.getPending())
		self["notifications"].list = entries
		self["label_results"].text = _("%i entries (%i pending)") % (len(entries), num_pending)
		self.selectionChanged()

	def keyGreen(self):
		current = self["notifications"].getCurrent()
		print "keyGreen", current
		if isinstance(current, tuple):
			entry = current[0]
			Notifications.notificationQueue.popNotification(self, entry)
			if not entry.deferred_callable and entry.fnc is not None:
				self["statusbar"].text = _("This notification does not allow deferred execution!")

	def keyRed(self):
		self.close()
		if self.selectionChanged in self["notifications"].onSelectionChanged:
			self["notifications"].onSelectionChanged.remove(self.selectionChanged)

