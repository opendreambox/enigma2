from enigma import eListboxPythonStringContent, eTimer, eRCInput, getPrevAsciiCode

from Components.ActionMap import ActionMap, NumberActionMap
from Components.MenuList import MenuList
from Tools.Log import Log

from MediaBrowser import MediaBrowser, MediaBrowserList
from MediaCore import MediaCore, mediaCore

ITEM_KEY_TITLE = "__item_title"

class MediaBrowserSearchList(MenuList, MediaBrowserList):
	def __init__(self, type):
		MenuList.__init__(self, [], True, eListboxPythonStringContent)
		MediaBrowserList.__init__(self, type)

	def onParentShow(self):
		self._onShow()

	def onParentClose(self):
		self._onClose()

	def isValidType(self, item):
		return True

	def _onShow(self):
		Log.i("Subclass of MediaBrowserList has no implementation of _onShow")

	def _onClose(self):
		Log.i("Subclass of MediaBrowserList has no implementation of _onClose")

	def canDescend(self):
		return False

	def descend(self):
		pass

	def getSelectedItem(self):
		item = self.l.getCurrentSelection()
		if item is None:
			return None
		return item[1]

	def getItemName(self, item=None):
		if item is None:
			item = self.getSelectedItem()
		return item[0].getName()

	def getServiceRef(self, item=None):
		if item is None:
			item = self.getSelectedItem()[0]
		return item

	def getMeta(self, item):
		if item is None:
			item = self.getSelectedItem()[1]
		if item is None or len(item) < 2:
			return None
		return item[1]

	def search(self, needle):
		items = mediaCore.search(self._type, needle)
		self.setList(items)

from Components.Input import Input
class EnhancedInput(Input):
	def __init__(self, text="", maxSize=False, visible_width=False, type=Input.TEXT):
		Input.__init__(self, text, maxSize, visible_width, type)

	def markAll(self):
		self.allmarked = True
		self.update()

	def markNone(self):
		self.setMarkedPos(-1)

	def clear(self):
		self.setText("")

class MediaBrowserSearch(MediaBrowser):
	FEATURE_FILTER_TYPE = True
	FEATURE_ADD_FOLDER = False
	FEATURE_SEARCH = False
	TITLE = _("Search")

	skin = """
		<screen name="MediaBrowserSearch" position="center,120" size="820,520" title="Search">
		    <eLabel text="Search with 0-9 :" position="10,5" size="190,25" font="Regular;22" backgroundColor="#1f771f"/>
			<widget name="needle" position="200,5" size="610,25" font="Regular;22" halign="left" backgroundColor="#1f771f"/>
			<widget name="list" position="10,40" size="800,390" scrollbarMode="showOnDemand"/>
			<widget name="status" position="10,450" size="800,20" font="Regular;18" halign="left" foregroundColors="white,white,white" backgroundColors="background,#1f771f,#9f1313"/>
			<ePixmap pixmap="skin_default/buttons/button_off.png" zPosition="1" position="10,490" size="20,20" alphatest="on"/>
			<widget source="button_green" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_green.png" position="10,490" size="20,20" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="add" position="40, 480" size="200, 40" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center">
			</widget>
			<ePixmap pixmap="skin_default/buttons/button_off.png" zPosition="1" position="240,490" size="20,20" alphatest="on" />
			<widget source="button_blue" zPosition="2" render="Pixmap" pixmap="skin_default/buttons/button_blue.png" position="240,490" size="20,20" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="add_and_play" position="270, 480" size="400, 40" foregroundColor="white" backgroundColor="background" font="Regular;18" transparent="1" halign="left" valign="center"/>
		</screen>"""
	

	def __init__(self, session, type=type, player=None):
		MediaBrowser.__init__(self, session, type=type, player=player)
		self["needle"] = EnhancedInput()
		self.skinName = "MediaBrowserSearch"
		self._setList(MediaBrowserSearchList(type=type))

		self["numberactions"] = NumberActionMap(["NumberActions"],
		{
			"1": self._keyNumberGlobal,
			"2": self._keyNumberGlobal,
			"3": self._keyNumberGlobal,
			"4": self._keyNumberGlobal,
			"5": self._keyNumberGlobal,
			"6": self._keyNumberGlobal,
			"7": self._keyNumberGlobal,
			"8": self._keyNumberGlobal,
			"9": self._keyNumberGlobal,
			"0": self._keyNumberGlobal
		})

		self["inputactions"] = ActionMap(["InputActions"], {
			"backspace": self._actionBackspace,
			"delete": self._actionDelete,
			"ascii": self._actionAscii,
		})

		self._keyboardMode = eRCInput.getInstance().getKeyboardMode()
		eRCInput.getInstance().setKeyboardMode(eRCInput.kmAscii)
		self.__searchTimer = eTimer()
		self.__searchTimer_conn = self.__searchTimer.timeout.connect(self._onSearchTimeout)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		eRCInput.getInstance().setKeyboardMode(self._keyboardMode)

	def _onSearchInputChanged(self):
		self.__searchTimer.startLongTimer(1)

	def _actionAscii(self):
		self["needle"].handleAscii(getPrevAsciiCode())
		self._onSearchInputChanged()

	def _keyNumberGlobal(self, number):
		self["needle"].number(number)
		self._onSearchInputChanged()

	def _actionBackspace(self):
		self["needle"].deleteBackward()
		self._onSearchInputChanged()

	def _actionDelete(self):
		self["needle"].delete()
		self._onSearchInputChanged()

	def _onSearchTimeout(self):
		needle = "%" + self["needle"].getText() + "%"
		if needle:
			self._list.search(needle)

mediaCore.registerBrowser(MediaBrowserSearch, _("Search"), MediaCore.TYPE_AUDIO)
