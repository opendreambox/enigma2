from __future__ import print_function
from Components.NimManager import nimmanager

def printme(text):
	"""Test
	"""
	print(text)

def getNimCount():
	return nimmanager.getSlotCount()
	
def getNimList():
	return nimmanager.nimList()

def dreamboxModel():
	""" returns a String containing the dreambox model
	"""
	f = open("/proc/stb/info/model", "r")
	model = ''.join(f.readlines()).strip()
	if model == "":
		model = "N/A"
	return model

def registerAPIs(api):
	api.add_call("enigma2.systeminfo.test", printme, "(s)", None)
	api.add_call("enigma2.systeminfo.modelname", dreamboxModel, "()", "s")
	
	api.add_call("enigma2.systeminfo.getNimCount", getNimCount, "()", "i")
	api.add_call("enigma2.systeminfo.getNimList", getNimList, "()", "[s]")