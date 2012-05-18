import sys
from enigma import ePythonOutput

class EnigmaOutput:
	def write(self, data):
		if isinstance(data, unicode):
			data = data.encode("UTF-8")
		ePythonOutput(data)

	def isatty(self):
		return False

	def flush(self):
		pass

sys.stdout = sys.stderr = EnigmaOutput()
