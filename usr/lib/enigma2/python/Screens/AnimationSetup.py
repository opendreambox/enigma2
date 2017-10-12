from enigma import eWindowAnimationManager, getDesktop
from Components.config import config, ConfigInteger, ConfigOnOff, ConfigText, getConfigListEntry
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.HardwareInfo import HardwareInfo

config.osd.window_animation = ConfigOnOff(default=True)
config.osd.window_animation_default = ConfigText(default="simple_fade")
config.osd.widget_animation = ConfigOnOff(default=False)
config.osd.widget_animation_display = ConfigOnOff(default=False)
config.osd.widget_animation_duration = ConfigInteger(default=400, limits=(50,1000))

class AnimationSetup(Screen):
	skin = """
		<screen name="AnimationSetup" position="center,120" size="820,520" title="Animation Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="list" position="10,60" size="800,390" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<eLabel position="10,480" size="800,1" backgroundColor="grey" />
			<widget name="selected_info" position="10,488" size="800,25" font="Regular;22" halign="center" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["list"] = MenuList([], enableWrapAround=True)
		
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("Extended"))
		self["key_blue"] = Label(_("Preview"))
		self["selected_info"] = Label(_("* current animation"))

		self["SetupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"save": self._ok,
			"cancel": self.close,
			"ok" : self._ok,
			"blue": self._preview,
			"yellow": self._extended,
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

	def _extended(self):
		self.session.open(ExtendedAnimationsSetup)

class ExtendedAnimationsSetup(Screen, ConfigListScreen):
	DEVICES_TO_ANIMATE = ["dm900", "dm920"]

	def __init__(self, session, windowTitle=_("Extend Animations Configuration")):
		Screen.__init__(self, session, windowTitle=windowTitle)
		ConfigListScreen.__init__(self, [], session=session, on_change=self._onChange)

		self.skinName = "Setup"

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["actions"] = NumberActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}, -2)

		self._dsk_osd = getDesktop(0)
		if HardwareInfo().get_device_name() in self.DEVICES_TO_ANIMATE:
			self._dsk_dsp = getDesktop(1)
		else:
			self._dsk_dsp = None
		self._createSetup()

	def _onChange(self):
		self._createSetup()

	def saveAll(self):
		ConfigListScreen.saveAll(self)
		self._dsk_osd.setWidgetAnimationsEnabled(config.osd.widget_animation.value)
		if self._dsk_dsp:
			self._dsk_dsp.setWidgetAnimationsEnabled(config.osd.widget_animation_display.value)
		eWindowAnimationManager.setWidgetDefault()

	def _createSetup(self):
		entries = [
			getConfigListEntry(_("OSD")),
			getConfigListEntry(_("OSD cross-fading for text and pictures)"), config.osd.widget_animation),
		]
		if self._dsk_dsp:
			entries.extend([
				getConfigListEntry(("Display")),
				getConfigListEntry(_("Display cross-fading for text and pictures"), config.osd.widget_animation_display),
			])
		if config.osd.widget_animation.value or config.osd.widget_animation_display.value:
			entries.extend([
				getConfigListEntry(_("General Settings")),
				getConfigListEntry(_("Cross-fading duration"), config.osd.widget_animation_duration),
			])
		self["config"].list = entries
