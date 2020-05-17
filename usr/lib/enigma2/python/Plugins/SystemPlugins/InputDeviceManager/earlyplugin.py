from __future__ import absolute_import
from Components.config import config
from Components.ResourceManager import resourcemanager

from .InputDeviceWizard import InputDeviceWizardBase



def EarlyPlugins(**kwargs):
	if config.misc.firstrun.value:
		InputDeviceWizardBase.firstRun = True
		InputDeviceWizardBase.checkConnectedDevice = True
	resourcemanager.addResource("InputDeviceWizard.InputDeviceWizardBase", InputDeviceWizardBase)
