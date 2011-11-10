from Components.ResourceManager import resourcemanager

class EarlyTestClass:
	def __init__(self):
		print "[TestPlugin] starting EarlyTestClass"

	def testmsg(self):
		print "[TestPlugin] testmsg called"

def EarlyPlugins(**kwargs):
	resourcemanager.addResource("EarlyTest", EarlyTestClass())
	