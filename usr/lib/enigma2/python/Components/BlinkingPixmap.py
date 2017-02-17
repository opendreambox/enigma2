from Pixmap import PixmapConditional
from ConditionalWidget import BlinkingWidgetConditional


class BlinkingPixmapConditional(BlinkingWidgetConditional, PixmapConditional):
	def __init__(self):
		BlinkingWidgetConditional.__init__(self)
		PixmapConditional.__init__(self)
