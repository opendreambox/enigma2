from enigma import eWindowAnimationManager
from Components.config import config, ConfigText
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

config.osd.window_animation_default = ConfigText(default="simple_fade")

class AnimationSetup(Screen):
	skin = """
		<screen name="AnimationSetup" position="center,center" size="580,500" title="Animation Setup">

			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />

			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			
			<widget name="list" position="10,50" size="560,405" scrollbarMode="showOnDemand"/>
			<widget name="selected_info" position="10,460" zPosition="1" size="560,40" font="Regular;20" valign="center" transparent="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["list"] = MenuList([], enableWrapAround=True)
		
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_blue"] = Label(_("Preview"))
		self["selected_info"] = Label(_("* current animation"))

		self["SetupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"save": self._ok,
			"cancel": self.close,
			"ok" : self._ok,
			"blue": self._preview
		}, -3)
		self.reload()

	def reload(self):
		animations = eWindowAnimationManager.getAnimations()
		l = []
		for key, name in animations.iteritems():
			if key == config.osd.window_animation_default.value:
				name = "* %s" %(name)
			l.append( (name, key) )
		self["list"].setList(l)

	def _getCurrent(self):
		return self["list"].getCurrent()

	def _ok(self):
		current = self._getCurrent()
		if current:
			key = current[1]
			config.osd.window_animation_default.value = key
			config.osd.window_animation_default.save()
			eWindowAnimationManager.setDefault(key)
		self.close()

	def _preview(self):
		current = self._getCurrent()
		if current:
			self.session.open(MessageBox, current[0], MessageBox.TYPE_INFO, timeout=3, custom_animation=current[1])
		