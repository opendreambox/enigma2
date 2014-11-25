from Components.ResourceManager import resourcemanager
from UPnPCore import ManagedControlPoint

def EarlyPlugins(**kwargs):
	resourcemanager.addResource("UPnPControlPoint", ManagedControlPoint())
