from Components.Input import Input

class EnhancedInput(Input):
	def __init__(self, text="", maxSize = False, visible_width = False, type = Input.TEXT):
		Input.__init__(self, text, maxSize, visible_width, type)
		
	def markAll(self):
		self.allmarked = True
		self.update()
	
	def markNone(self):
		self.setMarkedPos(-1)
		
	def clear(self):
		self.setText("")
