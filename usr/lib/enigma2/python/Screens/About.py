from enigma import eNetworkManager

from Screen import Screen
from Components.config import config
from API import api
from Components.About import about
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Harddisk import harddiskmanager
from Components.NimManager import nimmanager
from Tools.DreamboxHardware import getFPVersion
from Tools.Log import Log

class About(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self["Model"] = StaticText(api.enigma2.systeminfo.modelname())
		self["EnigmaVersion"] = StaticText("Dreambox OS: " + about.getEnigmaVersionString())
		self["ImageVersion"] = StaticText("Image: " + about.getImageVersionString())

		self["TunerHeader"] = StaticText(_("Detected NIMs:"))

		fp_version = getFPVersion()
		if fp_version is None:
			fp_version = ""
		else:
			fp_version = _("Frontprocessor version: %d") % fp_version

		self["FPVersion"] = StaticText(fp_version)

		nims = nimmanager.nimList()
		for count in (0, 1, 2, 3, 4):
			if count < len(nims):
				self["Tuner" + str(count)] = StaticText(nims[count])
			else:
				self["Tuner" + str(count)] = StaticText("")

		self["HDDHeader"] = StaticText(_("Detected HDD:"))
		hdd = None
		hddlist = harddiskmanager.HDDList()
		defaultDisk = harddiskmanager.getDefaultStorageDevicebyUUID(config.storage_options.default_device.value)
		if defaultDisk:
			default_hdd = "/dev/%s" %(defaultDisk.device,)
			for hd in hddlist:
				hd = hd[1]
				if default_hdd.startswith(hd.getDeviceDir()):
					Log.i("Default HDD matched! (%s -> %s)" %(default_hdd,hd.getDeviceDir()))
					hdd = hd
					break
		if not hdd:
			hdd = hddlist and hddlist[0][1] or None
			Log.w("No default Harddisk found. Falling back to first in list -> %s" %(hdd,))

		if hdd is not None and hdd.model() != "":
			self["hddA"] = StaticText(_("%s\n(%s, %d MB free)") % (hdd.model(), hdd.capacity(),hdd.free()))
		else:
			self["hddA"] = StaticText(_("none"))

		self["IPHeader"] = StaticText(_("Current IP Address:"))

		ipA = _("none")
		services = eNetworkManager.getInstance().getServices()
		for service in services:
			ip = self.getServiceIP(service)
			name = service.name()
			if ip != None:
				ipA = "%s (%s)" %(ip, name)
		self["ipA"] = StaticText(ipA)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.close,
				"ok": self.close,
				"green": self.showTranslationInfo
			})

	def getServiceIP(self, service):
		ip = None
		if service.state() == eNetworkManager.STATE_ONLINE:
			ipv4 = service.ipv4()
			ip = ipv4.get("Address", "0.0.0.0")
			if ip == "0.0.0.0":
				ipv6 = self._service.ipv6()
				ip6 = ipv6.get("Address", "::")
				if ip6 != "::":
					ip = ip6
		return ip

	def showTranslationInfo(self):
		self.session.open(TranslationInfo)

class TranslationInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		# don't remove the string out of the _(), or it can't be "translated" anymore.

		# TRANSLATORS: Add here whatever should be shown in the "translator" about screen, up to 6 lines (use \n for newline)
		info = _("TRANSLATOR_INFO")

		if info == "TRANSLATOR_INFO":
			info = "(N/A)"

		infolines = _("").split("\n")
		infomap = {}
		for x in infolines:
			l = x.split(': ')
			if len(l) != 2:
				continue
			(type, value) = l
			infomap[type] = value
		print infomap

		self["TranslationInfo"] = StaticText(info)

		translator_name = infomap.get("Language-Team", "none")
		if translator_name == "none":
			translator_name = infomap.get("Last-Translator", "")

		self["TranslatorName"] = StaticText(translator_name)

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.close,
				"ok": self.close,
			})
