from __future__ import absolute_import
from Components.config import config
from Plugins.Plugin import PluginDescriptor

from .Browser import Browser
from .BrowserMenu import BrowserMenu

def main_widget(session, **kwargs):
	url = kwargs.get("url", None)
	session.openWithCallback(main_widget_callback, Browser, config.plugins.WebBrowser.fullscreen.value, url, False)

def main_widget_callback(session = None, restart = False, url = None):
	if restart:
		main_widget(session, url=url)

def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("Web Browser"), main_widget, "web_browser", 30)]
	return []

def downloads(session, **kwargs):
	session.open(BrowserMenu, None, None, menulist = [(_("Downloads"), BrowserMenu.MENU_DOWNLOADS),])

def Plugins(**kwargs):
	return [
			PluginDescriptor(name = "Browser", description = _("Browse the web"), where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = "Downloads", description = _("Downloads"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = downloads),
		]
