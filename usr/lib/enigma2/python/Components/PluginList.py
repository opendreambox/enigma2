from Components.Sources.List import List

from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE
from Tools.LoadPixmap import LoadPixmap


def PluginEntryComponent(plugin):
	if plugin.icon is None:
		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
	else:
		png = plugin.icon

	return [
		plugin,	plugin.name, plugin.description, png
	]

class PluginList(List):
	def __init__(self, list, enableWrapAround=False):
		List.__init__(self, list, enableWrapAround, item_height = 50 )
