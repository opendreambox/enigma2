from __future__ import absolute_import
from Components.Pixmap import PixmapConditional
from Components.ConditionalWidget import BlinkingWidgetConditional


class BlinkingPixmapConditional(BlinkingWidgetConditional, PixmapConditional):
	def __init__(self):
		BlinkingWidgetConditional.__init__(self)
		PixmapConditional.__init__(self)
