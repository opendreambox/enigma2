from __future__ import print_function
from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from enigma import ePoint
from Tools import Notifications

from glob import glob
from os import remove, rename
from os.path import basename
from twisted.mail import smtp, relaymanager
import MimeWriter, mimetools, StringIO
from .__init__ import decrypt_block, validate_cert, read_random

config.plugins.crashlogautosubmit = ConfigSubsection()
config.plugins.crashlogautosubmit.sendmail = ConfigSelection(default = "send", choices = [
	("send", _("Always ask before sending")), ("send_always", _("Don't ask, just send")), ("send_never", _("Disable crashlog reporting"))])
config.plugins.crashlogautosubmit.sendlog = ConfigSelection(default = "rename", choices = [
	("delete", _("Delete crashlogs")), ("rename", _("Rename crashlogs"))])
config.plugins.crashlogautosubmit.sendAnonCrashlog = ConfigYesNo(default = True)

class CrashlogAutoSubmitConfiguration(Screen, ConfigListScreen):

	oldMailEntryValue = config.plugins.crashlogautosubmit.sendmail.value

	skin = """
		<screen name="CrashlogAutoSubmitConfiguration" position="center,center" size="560,440" title="CrashlogAutoSubmit settings" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" zPosition="2" position="5,50" size="550,300" scrollbarMode="showOnDemand" transparent="1" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,390" zPosition="10" size="560,2" transparent="1" alphatest="on" />
			<widget source="status" render="Label" position="10,400" size="540,40" zPosition="10" font="Regular;20" halign="center" valign="center" backgroundColor="#25062748" transparent="1"/>
			<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="10,420" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="160,325" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.MailEntry = None
		self.LogEntry = None
		self.addEmailEntry = None
		self.EmailEntry = None
		self.NameEntry = None
		self.AnonCrashlogEntry = None
		self.msgCrashlogMailer = False

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.createSetup()

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["status"] = StaticText()
		self["VKeyIcon"] = Pixmap()
		self["HelpWindow"] = Pixmap()

		self["VKeyIcon"].hide()
		self.onShown.append(self.setWindowTitle)
		self.onClose.append(self.msgCrashlogNotifier)


	def setWindowTitle(self):
		self.setTitle(_("CrashlogAutoSubmit settings..."))

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def createSetup(self):
		self.list = []
		self.MailEntry = getConfigListEntry(_("How to handle found crashlogs?"), config.plugins.crashlogautosubmit.sendmail)
		self.LogEntry = getConfigListEntry(_("What to do with submitted crashlogs?"), config.plugins.crashlogautosubmit.sendlog)
		self.AnonCrashlogEntry = getConfigListEntry(_("Anonymize crashlog?"), config.plugins.crashlogautosubmit.sendAnonCrashlog)

		self.list.append( self.MailEntry )
		if config.plugins.crashlogautosubmit.sendmail.value is not "send_never":
			self.list.append( self.LogEntry )
			self.list.append( self.AnonCrashlogEntry )

		self["config"].list = self.list
		self["config"].l.setList(self.list)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

		if not self.sendmailChanged in config.plugins.crashlogautosubmit.sendmail.notifiers:
			config.plugins.crashlogautosubmit.sendmail.addNotifier(self.sendmailChanged)

	def sendmailChanged(self, configElement):
		if configElement.value != CrashlogAutoSubmitConfiguration.oldMailEntryValue:
			self.msgCrashlogMailer = True
		else:
			self.msgCrashlogMailer = False

	def newConfig(self):
		if self["config"].getCurrent() == self.MailEntry:
			self.createSetup()
		if self["config"].getCurrent() == self.addEmailEntry:
			self.createSetup()

	def selectionChanged(self):
		current = self["config"].getCurrent()
		if current == self.MailEntry:
			self["status"].setText(_("Decide what should be done when crashlogs are found."))
		elif current == self.LogEntry:
			self["status"].setText(_("Decide what should happen to the crashlogs after submission."))
		elif current == self.AnonCrashlogEntry:
			self["status"].setText(_("Adds enigma2 settings and dreambox model informations like SN, rev... if enabled."))

	def showKeypad(self):
		current = self["config"].getCurrent()
		helpwindowpos = self["HelpWindow"].getPosition()
		if hasattr(current[1], 'help_window'):
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.show()
				current[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))

	def hideKeypad(self):
		current = self["config"].getCurrent()
		if hasattr(current[1], 'help_window'):
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.hide()

	def cancelConfirm(self, result):
		if not result:
			self.showKeypad()
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		print("cancel")
		if self["config"].isChanged():
			self.hideKeypad()
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def keySave(self):
		print("saving")
		CrashlogAutoSubmitConfiguration.oldMailEntryValue = config.plugins.crashlogautosubmit.sendmail.value
		ConfigListScreen.keySave(self)

	def msgCrashlogNotifier(self):
		if self.msgCrashlogMailer is True:
			try:
				callCrashMailer(True, self.session)
			except AttributeError:
				print("error, not restarting crashlogmailer")


def mxServerFound(mxServer,session):
	print("[CrashlogAutoSubmit] - mxServerFound -->", mxServer)
	crashLogFilelist = []
	message = StringIO.StringIO()
	writer = MimeWriter.MimeWriter(message)
	mailFrom = "enigma2@crashlog.dream-multimedia-tv.de"
	mailTo = "enigma2@crashlog.dream-multimedia-tv.de"
	subject = "Automatically generated crashlogmail"
	# Define the main body headers.
	writer.addheader('To', "dream-multimedia-crashlogs <enigma2@crashlog.dream-multimedia-tv.de>")
	writer.addheader('From', "CrashlogAutoSubmitter <enigma2@crashlog.dream-multimedia-tv.de>")
	writer.addheader('Subject', str(subject))
	writer.addheader('Date', smtp.rfc822date())
	writer.addheader('MIME-Version', '1.0')
	writer.startmultipartbody('mixed')
	# start with a text/plain part
	part = writer.nextpart()
	body = part.startbody('text/plain')
	part.flushheaders()
	# Define the message body
	body_text1 = "\nHello\n\nHere are some crashlogs i found for you.\n"
	body_text2 = "\n\nThis is an automatically generated email from the CrashlogAutoSubmit plugin.\n\n\nHave a nice day.\n"
	body_text = body_text1 + body_text2
	body.write(body_text)

	list = (
		(_("Yes"), "send"),
		(_("Yes, and don't ask again"), "send_always"),
		(_("No, not now"), "send_not"),
		(_("No, send them never"), "send_never")
	)

	def handleError(error):
		print("[CrashlogAutoSubmit] - Message send Error -->", error.getErrorMessage())

	def handleSuccess(result):
		print("[CrashlogAutoSubmit] - Message sent successfully -->",result)
		for crashlog in crashLogFilelist:
			if config.plugins.crashlogautosubmit.sendlog.value == "delete":
				remove(crashlog)
			elif config.plugins.crashlogautosubmit.sendlog.value == "rename":
				currfilename = basename(crashlog)
				newfilename = "/media/hdd/" + currfilename + ".sent"
				rename(crashlog, newfilename)

	def send_mail():
		print("[CrashlogAutoSubmit] - send_mail")
		for crashlog in crashLogFilelist:
			filename = basename(crashlog)
			subpart = writer.nextpart()
			subpart.addheader("Content-Transfer-Encoding", 'base64')
			subpart.addheader("Content-Disposition",'attachment; filename="%s"' % filename)
			subpart.addheader('Content-Description', 'Enigma2 crashlog')
			body = subpart.startbody("%s; name=%s" % ('application/octet-stream', filename))
			mimetools.encode(open(crashlog, 'rb'), body, 'base64')
		writer.lastpart()
		sending = smtp.sendmail(str(mxServer), mailFrom, mailTo, message.getvalue())
		sending.addCallback(handleSuccess).addErrback(handleError)

	def handleAnswer(answer):
		answer = answer and answer[1]
		print("[CrashlogAutoSubmit] - handleAnswer --> ",answer)
		if answer == "send":
			send_mail()
		elif answer == "send_always":
			config.plugins.crashlogautosubmit.sendmail.value = "send_always"
			config.plugins.crashlogautosubmit.sendmail.save()
			config.plugins.crashlogautosubmit.save()
			config.plugins.save()
			send_mail()
		elif answer in ( None, "send_never"):
			config.plugins.crashlogautosubmit.sendmail.value = "send_never"
			config.plugins.crashlogautosubmit.sendmail.save()
			config.plugins.crashlogautosubmit.save()
			config.plugins.save()
		elif answer == "send_not":
			print("[CrashlogAutoSubmit] - not sending crashlogs for this time.")

	for crashlog in glob('/media/hdd/enigma2_crash_*.log'):
		print("[CrashlogAutoSubmit] - found crashlog: ", basename(crashlog))
		crashLogFilelist.append(crashlog)

	if len(crashLogFilelist):
		if config.plugins.crashlogautosubmit.sendmail.value == "send":
			Notifications.AddNotificationWithCallback(handleAnswer, ChoiceBox, title=_("Crashlogs found!\nSend them to Dream Multimedia?"), list = list)
		elif config.plugins.crashlogautosubmit.sendmail.value == "send_always":
			send_mail()
	else:
		print("[CrashlogAutoSubmit] - no crashlogs found.")


def startMailer(session):
	if config.plugins.crashlogautosubmit.sendmail.value == "send_never":
		print("[CrashlogAutoSubmit] - not starting CrashlogAutoSubmit")
		return False

	def gotMXServer(mx):
		print("[CrashlogAutoSubmit] gotMXServer: ", mx.name)
		mxServerFound(mx.name, session)

	def handleMXError(error):
		print("[CrashlogAutoSubmit] - MX resolve ERROR:", error.getErrorMessage())

	if not config.misc.firstrun.value:
		relaymanager.MXCalculator().getMX('crashlog.dream-multimedia-tv.de').addCallback(gotMXServer).addErrback(handleMXError)


def callCrashMailer(result,session):
	if result is True:
		print("[CrashlogAutoSubmit] - config changed")
		startMailer(session)
	else:
		print("[CrashlogAutoSubmit] - config not changed")


def autostart(reason, **kwargs):
	print("[CrashlogAutoSubmit] - autostart")
	if "session" in kwargs:
		try:
			startMailer(kwargs["session"])
		except ImportError as e:
			print("[CrashlogAutoSubmit] Twisted-mail not available, not starting CrashlogAutoSubmitter", e)


def openconfig(session, **kwargs):
	session.open(CrashlogAutoSubmitConfiguration)


def selSetup(menuid, **kwargs):
	if menuid != "system":
		return [ ]

	return [(_("Crashlog settings"), openconfig, "crashlog_config", 70)]


def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], needsRestart = False, fnc = autostart),
		PluginDescriptor(name=_("CrashlogAutoSubmit"), description=_("CrashlogAutoSubmit settings"),where=PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=selSetup)]

