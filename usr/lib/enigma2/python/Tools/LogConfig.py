LOG_TYPE_DEBUG = "D/ "
LOG_TYPE_INFO = "I/ "
LOG_TYPE_WARNING = "W/ "
LOG_TYPE_ERROR = "E/ "

LOG_LEVEL_ERROR = 0
LOG_LEVEL_WARNING = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_DEBUG = 3

class LogConfig(object):
	_initialized = False

	@staticmethod
	def init():
		if LogConfig._initialized:
			return
		else:
			from Components.config import config, ConfigSubsection, ConfigOnOff, ConfigSelection, ConfigInteger
			config.log = ConfigSubsection()
			config.log.level = ConfigSelection(
				choices={ LOG_TYPE_INFO : "INFO", LOG_TYPE_WARNING : "WARNING", LOG_TYPE_ERROR : "ERROR" }, default=LOG_TYPE_INFO)
			config.log.verbose = ConfigOnOff(default=False)
			config.log.colored = ConfigOnOff(default=True)
			LogConfig._initialized = True

	@staticmethod
	def level():
		return config.log.level.value

	@staticmethod
	def verbose():
		return config.log.verbose.value

	@staticmethod
	def colored():
		return config.log.colored.value
