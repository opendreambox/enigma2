from Components.config import config
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

from Tools.Log import Log
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_SKIN

class RemoteControlSelection(Screen):
	SKIN_DEFAULT = "skin_default"

	skin = """
		<screen name="RemoteControlSelection" position="center,80" size="420,610" title="RemoteControlSelection" >
			<widget name="rc" pixmap="skin_default/rc0.png" position="20,10" size="380,500" alphatest="on"/>
			<widget name="color_hint" position="10,520" size="400,50" font="Regular;18" halign="center" valign="center" backgroundColor="background" transparent="0" />
			<widget name="ok" position="10,580" size="400,24" font="Regular;22" halign="center" valign="center" backgroundColor="background" transparent="0" />
		</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["color_hint"] = Label(_("Some Remotes may exist in other Colors"))
		self["ok"] = Label(_("Press OK to apply"))

		self._pixmap = Pixmap()
		self["rc"] = self._pixmap

		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions"],
			{
				"ok": self._ok,
				"cancel": self._cancel,
				"right": self._next,
				"left": self._prev,
			})

		self._pixmaps = []
		for i in (0, 1, 2, 3):
			self._pixmaps.append(
				LoadPixmap(
					resolveFilename(SCOPE_SKIN, "skin_default/rc%s.png" % (i))
				)
			)

		self._index = -1
		self.onFirstExecBegin.append(self._firstExecBegin)

	def _firstExecBegin(self):
		self.setTitle(_("Select your Remote"))
		self.setCurrentPixmap(config.misc.rcused.value)

	def _ok(self):
		config.misc.rcused.value = self._index
		config.misc.rcused.save()
		Log.i("RC is now set to Model %s" %(config.misc.rcused.value))
		self.close()

	def _cancel(self):
		self.close()

	def setCurrentPixmap(self, index):
		if index > 3:
			index = 0
		if index < 0:
			index = 3
		self._index = index
		self._pixmap.setPixmap(self._pixmaps[index])

	def _next(self):
		self._pixmap.setShowHideAnimation("slide_right_to_left")
		self.setCurrentPixmap(self._index + 1)

	def _prev(self):
		self._pixmap.setShowHideAnimation("slide_left_to_right")
		self.setCurrentPixmap(self._index - 1)

def remoteControlSelectionRun(session, **kwargs):
	session.open(RemoteControlSelection)

def remoteControlSelectionMenu(menuid, **kwargs):
	if menuid == "devices":
		return [(_("Remote Control Selection"), remoteControlSelectionRun, "rcu_selection", None)]
	else:
		return []

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Remote Control Selection"), description=_("Select the remote you're using"), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=remoteControlSelectionMenu)
