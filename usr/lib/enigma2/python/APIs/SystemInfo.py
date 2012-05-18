def printme(text):
	"""Test
	"""
        print text

def registerAPIs(api):
	api.add_call("enigma2.systeminfo.test", printme, "(s)", None)