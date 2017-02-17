from Components.ResourceManager import resourcemanager

from VideoWizard import VideoWizard

def EarlyPlugins(**kwargs):
	resourcemanager.addResource("videomode.videowizard", VideoWizard)
