from enigma import eEPGCache
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, fileExists, SCOPE_CONFIG
from Tools.Log import Log

import os, unittest

class TestEpgCache(unittest.TestCase):
	session = None
	def test_save(self):
		self.addCleanup(self.cleanup_save)
		testdb = "__test.db"
		self.oldfile = config.misc.epgcache_filename.value
		config.misc.epgcache_filename.value = resolveFilename(SCOPE_CONFIG, testdb)
		self._remove_db()
		print "saving to %s... " % (config.misc.epgcache_filename.value),
		config.misc.epgcache_filename.save()
		eEPGCache.getInstance().save()

	def cleanup_save(self):
		config.misc.epgcache_filename.value = self.oldfile

	def _remove_db(self):
		if fileExists(config.misc.epgcache_filename.value):
			print "Removing old test result...",
			os.remove(config.misc.epgcache_filename.value)


def runTests(*args, **kwargs):
	Log.w("Running EPG Cache unit tests")
	suite = unittest.TestLoader().loadTestsFromTestCase(TestEpgCache)
	unittest.TextTestRunner(verbosity=2).run(suite)

def Plugins(**kwargs):
	return [ PluginDescriptor(name="EPGCacheTest", description=_("EPGCache Test"), where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=runTests) ]
