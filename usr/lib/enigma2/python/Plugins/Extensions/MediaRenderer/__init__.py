from Components.config import config, ConfigOnOff, ConfigText, ConfigSubsection
from Tools.HardwareInfo import HardwareInfo

config.plugins.mediarenderer = ConfigSubsection()
config.plugins.mediarenderer.enabled = ConfigOnOff(default=True)
config.plugins.mediarenderer.name = ConfigText(default="%s" %(HardwareInfo().get_device_name()), fixed_size = False)
config.plugins.mediarenderer.uuid = ConfigText(default="", fixed_size = False)
