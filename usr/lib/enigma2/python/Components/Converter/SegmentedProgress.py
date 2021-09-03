from __future__ import division
from Components.Converter.Converter import Converter
from Components.Element import cached

class SegmentedProgress(Converter, object):
	def __init__(self, segments):
		Converter.__init__(self, segments)
		self._segments = int(segments)

	@cached
	def getValue(self):
		r = self.source.range
		v = self.source.value
		increment = r / self._segments
		for i in range(0, self._segments+1):
			value = increment * i
			if value >= v:
				return int(value)

	value = property(getValue)

	@cached
	def getRange(self):
		return self.source.range

	range = property(getRange)