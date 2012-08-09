def debug(cls, method, text=None):
	if text != None:
		print "[%s].%s :: %s" % (cls.__class__.__name__, method, text)
	else:
		print "[%s].%s :: called" % (cls.__class__.__name__, method)
