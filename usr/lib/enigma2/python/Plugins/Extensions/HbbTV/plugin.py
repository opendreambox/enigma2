from Components.config import config

from Plugins.Plugin import PluginDescriptor
from HbbTV import HbbTV
from HbbTVSetup import HbbTVSetup

def hbbtv_browser(session, **kwargs):
	HbbTV.instance.startApplicationByUri("http://www.hbbig.com")

def menu_hbbtv_browser(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("HbbTV Browser"), hbbtv_browser, "hbbtv_browser", 46)]
	return []

def hbbtv_setup(session, **kwargs):
	session.open(HbbTVSetup)

def menu_setup(menuid, **kwargs):
	if menuid == "system":
		return [(_("HbbTV"), hbbtv_setup, "hbbtv_setup", None)]
	return []


def Plugins(**kwargs):
	list = [PluginDescriptor(name = "HbbTV", description = _("Setup HbbTV functionalities"), where = PluginDescriptor.WHERE_MENU, fnc = menu_setup)]

	if config.plugins.hbbtv.enabled.value:
		from HbbTV import start, autostart
		list.extend(
			[ PluginDescriptor(where=[PluginDescriptor.WHERE_INFOBAR,], fnc=start),
			PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART,], fnc=autostart) ]
		)

		#Testsuite availability
		if config.plugins.hbbtv.testsuite.value == "mainmenu":
			list.append(
				PluginDescriptor(name = "HbbTV Browser", description = _("HbbTV Browser"), where = PluginDescriptor.WHERE_MENU, fnc = menu_hbbtv_browser)
			)
		elif config.plugins.hbbtv.testsuite.value == "extensions":
			list.append(
				PluginDescriptor(name = "HbbTV Browser", description = _("HbbTV Browser"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = hbbtv_browser)
			)
		elif config.plugins.hbbtv.testsuite.value == "plugins":
			list.append(
				PluginDescriptor(name = "HbbTV Browser", description = _("HbbTV Browser"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = hbbtv_browser)
			)

	return list
