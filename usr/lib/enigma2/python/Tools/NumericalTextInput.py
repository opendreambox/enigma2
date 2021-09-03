# -*- coding: UTF-8 -*-
from enigma import eTimer
from Components.Language import language

class NumericalTextInput:
	def __init__(self, nextFunc=None, handleTimeout = True, search = False):
		self.mapping = []
		self.lang = language.getLanguage()
		self.useableChars=None
		self.nextFunction=nextFunc

		if handleTimeout:
			self.timer = eTimer()
			self.timer_conn = self.timer.timeout.connect(self.timeout)
		else:
			self.timer_conn = None
			self.timer = None
		self.lastKey = -1
		self.pos = -1

		if search:
			if isinstance(search, basestring):
				self.mapping.append (unicode(search)+u"0") # 0
			else:
				self.mapping.append (u"%_0") # 1
			self.mapping.append (u" 1") # 1
			self.mapping.append (u"abc2") # 2
			self.mapping.append (u"def3") # 3
			self.mapping.append (u"ghi4") # 4
			self.mapping.append (u"jkl5") # 5
			self.mapping.append (u"mno6") # 6
			self.mapping.append (u"pqrs7") # 7
			self.mapping.append (u"tuv8") # 8
			self.mapping.append (u"wxyz9") # 9
			return

		if self.lang == 'de_DE':
			self.mapping.append (u"0,?!&@=*'+\"()$~") # 0
			self.mapping.append (u" 1.:/-_#") # 1
			self.mapping.append (u"abcä2ABCÄ") # 2
			self.mapping.append (u"def3DEF") # 3
			self.mapping.append (u"ghi4GHI") # 4
			self.mapping.append (u"jkl5JKL") # 5
			self.mapping.append (u"mnoö6MNOÖ") # 6
			self.mapping.append (u"pqrsß7PQRSß") # 7
			self.mapping.append (u"tuvü8TUVÜ") # 8
			self.mapping.append (u"wxyz9WXYZ") # 9
		elif self.lang == 'es_ES':
			self.mapping.append (u"0,?!&@=*'+\"()$~") # 0
			self.mapping.append (u" 1.:/-_#") # 1
			self.mapping.append (u"abcáà2ABCÁÀ") # 2
			self.mapping.append (u"deéèf3DEFÉÈ") # 3
			self.mapping.append (u"ghiíì4GHIÍÌ") # 4
			self.mapping.append (u"jkl5JKL") # 5
			self.mapping.append (u"mnñoóò6MNÑOÓÒ") # 6
			self.mapping.append (u"pqrs7PQRS") # 7
			self.mapping.append (u"tuvúù8TUVÚÙ") # 8
			self.mapping.append (u"wxyz9WXYZ") # 9
		if self.lang in ('sv_SE', 'fi_FI'):
			self.mapping.append (u"0,?!&@=*'+\"()$~") # 0
			self.mapping.append (u" 1.:/-_#") # 1
			self.mapping.append (u"abcåä2ABCÅÄ") # 2
			self.mapping.append (u"defé3DEFÉ") # 3
			self.mapping.append (u"ghi4GHI") # 4
			self.mapping.append (u"jkl5JKL") # 5
			self.mapping.append (u"mnoö6MNOÖ") # 6
			self.mapping.append (u"pqrs7PQRS") # 7
			self.mapping.append (u"tuv8TUV") # 8
			self.mapping.append (u"wxyz9WXYZ") # 9
		elif self.lang in ('cs_CZ', 'sk_SK'):
			self.mapping.append (u"0,?'+\"()@$!=&*") # 0
			self.mapping.append (u" 1.:/-_#") # 1
			self.mapping.append (u"abc2áäčABCÁÄČ") # 2
			self.mapping.append (u"def3ďéěDEFĎÉĚ") # 3
			self.mapping.append (u"ghi4íGHIÍ") # 4
			self.mapping.append (u"jkl5ľĺJKLĽĹ") # 5
			self.mapping.append (u"mno6ňóöôMNOŇÓÖÔ") # 6
			self.mapping.append (u"pqrs7řŕšPQRSŘŔŠ") # 7
			self.mapping.append (u"tuv8ťúůüTUVŤÚŮÜ") # 8
			self.mapping.append (u"wxyz9ýžWXYZÝŽ") # 9
		elif self.lang == 'ru_RU':
			self.mapping.append (u"0,?!&@=*'+\"()$~") # 0
			self.mapping.append (u" 1.:/-_#") # 1
			self.mapping.append (u"abc2ABCабвгАБВГ") # 2
			self.mapping.append (u"def3DEFдежзДЕЖЗ") # 3
			self.mapping.append (u"ghi4GHIийклИЙКЛ") # 4
			self.mapping.append (u"jkl5JKLмнопМНОП") # 5
			self.mapping.append (u"mno6MNOрстуРСТУ") # 6
			self.mapping.append (u"pqrs7PQRSфхцчФХЦЧ") # 7
			self.mapping.append (u"tuv8TUVшщъыШЩЪЫ") # 8
			self.mapping.append (u"wxyz9WXYZьэюяЬЭЮЯ") # 9
		else:
			self.mapping.append (u"0,?!&@=*'+\"()$~") # 0
			self.mapping.append (u" 1.:/-_#") # 1
			self.mapping.append (u"abc2ABC") # 2
			self.mapping.append (u"def3DEF") # 3
			self.mapping.append (u"ghi4GHI") # 4
			self.mapping.append (u"jkl5JKL") # 5
			self.mapping.append (u"mno6MNO") # 6
			self.mapping.append (u"pqrs7PQRS") # 7
			self.mapping.append (u"tuv8TUV") # 8
			self.mapping.append (u"wxyz9WXYZ") # 9

	def setUseableChars(self, useable):
		self.useableChars = unicode(useable)
		

	def getKey(self, num):
		cnt=0
		if self.lastKey != num:
			if self.lastKey != -1:
				self.nextChar()
			self.lastKey = num
			self.pos = -1
		if self.timer is not None:
			self.timer.start(1000, True)
		while True:
			self.pos += 1
			if len(self.mapping[num]) <= self.pos:
				self.pos = 0
			if self.useableChars:
				pos = self.useableChars.find(self.mapping[num][self.pos])
				if pos == -1:
					cnt += 1
					if cnt < len(self.mapping[num]):
						continue
					else:
						return None
			break
		return self.mapping[num][self.pos]

	def nextKey(self):
		if self.timer is not None:
			self.timer.stop()
		self.lastKey = -1

	def nextChar(self):
		self.nextKey()
		if self.nextFunction:
			self.nextFunction()

	def timeout(self):
		if self.lastKey != -1:
			self.nextChar()

class NumericalHexInput(NumericalTextInput):
	def __init__(self, nextFunc=None, handleTimeout=True):
		NumericalTextInput.__init__(self, nextFunc=nextFunc, handleTimeout=handleTimeout, search=False)
		self.mapping = []
		self.mapping.append (u"0:") # 0
		self.mapping.append (u"1a") # 1
		self.mapping.append (u"2b") # 2
		self.mapping.append (u"3c") # 3
		self.mapping.append (u"4d") # 4
		self.mapping.append (u"5e") # 5
		self.mapping.append (u"6f") # 6
		self.mapping.append (u"7") # 7
		self.mapping.append (u"8") # 8
		self.mapping.append (u"9") # 9
		self.setUseableChars('0123456789:abcdef')
