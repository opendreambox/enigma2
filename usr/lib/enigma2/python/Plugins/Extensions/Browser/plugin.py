from Components.config import config

from Plugins.Plugin import PluginDescriptor
from Browser import Browser

def main_widget(session, **kwargs):
	url = kwargs.get("url", None)
	hbbtv = kwargs.get("hbbtv", False)
	if hbbtv:
		url = "http://www.hbbig.com"
	session.openWithCallback(main_widget_callback, Browser, config.plugins.WebBrowser.fullscreen.value, url, hbbtv)

def main_widget_hbbtv(session, **kwargs):
	kwargs["hbbtv"] = True
	main_widget(session, **kwargs)

def main_widget_callback(session = None, restart = False, url = None):
	if restart:
		main_widget(session, url=url)

def menu(menuid, **kwargs):
	widgetfnc = kwargs.get("widgetfnc", main_widget)
	name = kwargs.get("name", _("Web Browser"))
	id = kwargs.get("id", "web_browser")
	if menuid == "mainmenu":
		plugins = []
		plugins.append([(name, widgetfnc, id, 46)])
		return plugins[0]
	return []

def menu_hbbtv(menuid, **kwargs):
	kwargs["widgetfnc"] = main_widget_hbbtv
	kwargs["name"] = _("HbbTV (Testsuite)")
	kwargs["id"] = "hbbtv_browser"

	return menu(menuid, **kwargs)

from Hbbtv import start as start_hbbtv
def Plugins(**kwargs):
	return [
			PluginDescriptor(name = "Browser", description = _("Browse the web"), where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = "HbbTV (Testsuite)", description = _("Test HbbTV Functionality"), where = PluginDescriptor.WHERE_MENU, fnc = menu_hbbtv),
			PluginDescriptor(where=[PluginDescriptor.WHERE_INFOBAR,], fnc=start_hbbtv),
		]
