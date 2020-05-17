from __future__ import absolute_import
from Components.ResourceManager import resourcemanager

from .VideoWizard import VideoWizard

def EarlyPlugins(**kwargs):
	resourcemanager.addResource("videomode.videowizard", VideoWizard)
