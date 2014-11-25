from Plugins.Plugin import PluginDescriptor
from MediaDatabaseManager import MediaDatabaseManager

def manager_menu(menuid, **kwargs):
	if menuid == "system":
		return [(_("Media Database"), manager_setup, "media_database_manager", None)]
	return []

def manager_setup(session, **kwargs):
	session.open(MediaDatabaseManager)

def Plugins(**kwargs):
	return PluginDescriptor(
						name="Media Database Setup",
						description=_("Setup Folders of your Media Database"),
						where=PluginDescriptor.WHERE_MENU,
						fnc=manager_menu)
