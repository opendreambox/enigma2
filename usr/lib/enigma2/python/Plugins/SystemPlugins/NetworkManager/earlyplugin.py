from __future__ import absolute_import
from Components.config import config
from Components.ResourceManager import resourcemanager

from .NetworkWizard import NetworkWizardNew

def EarlyPlugins(**kwargs):
	if config.misc.firstrun.value:
		NetworkWizardNew.firstRun = True
		NetworkWizardNew.checkNetwork = True
	resourcemanager.addResource("NetworkWizard.NetworkWizardNew", NetworkWizardNew)
