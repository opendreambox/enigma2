# -*- coding: utf-8 -*-
from enigma import IrKey

from Tools.Directories import pathExists
from Tools.Log import Log

from collections import OrderedDict
import json
import os


class InputDeviceIRDatabase(object):
	IRDB = "%s/%s" %(os.path.dirname(__file__), "irdb.json")

	KEY_MAP = {
		'KEY_UP' : IrKey.CODE_UP,
		'KEY_DOWN' : IrKey.CODE_DOWN,
		'KEY_LEFT' : IrKey.CODE_LEFT,
		'KEY_RIGHT' : IrKey.CODE_RIGHT,
		'KEY_SELECT' : IrKey.CODE_OK,
		'KEY_OK' : IrKey.CODE_OK,
		'KEY_PREVIOUS' : IrKey.CODE_PREVIOUSSONG,
		'KEY_NEXT' : IrKey.CODE_NEXSONG,
		'KEY_REWIND' : IrKey.CODE_REWIND,
		'KEY_FASTFORWARD' : IrKey.CODE_FASTFORWARD,
		'KEY_MODE' : IrKey.CODE_MODE,
		'KEY_AUDIO' : IrKey.CODE_AUDIO,
		'KEY_PVR' : IrKey.CODE_VIDEO,
		'KEY_TEXT' : IrKey.CODE_TEXT,
		'KEY_POWER' : IrKey.CODE_POWER,
		'KEY_VOLUMEUP' : IrKey.CODE_VOLUMEUP,
		'KEY_VOLUMEDOWN' : IrKey.CODE_VOLUMEDOWN,
		'KEY_MUTE' : IrKey.CODE_MUTE,
		'KEY_CHANNELUP' : IrKey.CODE_CHANNELUP,
		'KEY_CHANNELDOWN' : IrKey.CODE_CHANNELDOWN,
		'KEY_PLAY' : IrKey.CODE_PLAY,
		'KEY_RECORD' : IrKey.CODE_RECORD,
		'KEY_STOP' : IrKey.CODE_STOP,
		'KEY_MENU' : IrKey.CODE_MENU,
		'KEY_ESC' : IrKey.CODE_EXIT,
		'KEY_EXIT' : IrKey.CODE_EXIT,
		'KEY_RED' : IrKey.CODE_RED,
		'KEY_GREEN' : IrKey.CODE_GREEN,
		'KEY_YELLOW' : IrKey.CODE_YELLOW,
		'KEY_BLUE' : IrKey.CODE_BLUE,
		'KEY_INFO' : IrKey.CODE_INFO,
		'KEY_EPG' : IrKey.CODE_INFO,
		'KEY_0' : IrKey.CODE_0,
		'KEY_1' : IrKey.CODE_1,
		'KEY_2' : IrKey.CODE_2,
		'KEY_3' : IrKey.CODE_3,
		'KEY_4' : IrKey.CODE_4,
		'KEY_5' : IrKey.CODE_5,
		'KEY_6' : IrKey.CODE_6,
		'KEY_7' : IrKey.CODE_7,
		'KEY_8' : IrKey.CODE_8,
		'KEY_9' : IrKey.CODE_9,
	}

	KNOWN_KEYS = KEY_MAP.keys()

	@property
	def data(self):
		return self._irdb

	def __init__(self):
		self._irdb = {}
		self.reload()

	def reload(self):
		try:
			if pathExists(self.IRDB):
				jsonstr=open(self.IRDB,'r').read()
			if jsonstr:
				self._irdb = OrderedDict( sorted(json.loads(jsonstr).items()) )
				return
		except Exception as e:
			Log.w(e)
		self._irdb = {}

	def mapKey(self, key):
		keycode = self.KEY_MAP.get(key, None)
		if not keycode:
			Log.w("Unknown keycode for key! %s" %(key))
		return keycode

irdb = InputDeviceIRDatabase()
