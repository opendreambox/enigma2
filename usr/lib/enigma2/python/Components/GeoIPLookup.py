from argparse import Namespace
from json import loads as json_loads
from twisted.web.client import getPage
import six

"""
This returns a native python object derived from the following JSON data (converted using argparse.Namespace)
{
   "city":"Simbach am Inn",
   "postal_code":"84359",
   "continent_code":"EU",
   "country_code":"DE",
   "country_name":"Germany",
   "timezone":"Europe\/Berlin",
   "longitude":13.0231,
   "latitude":48.2655
}
"""

class GeoIPLookup(object):
	URL = "https://reichholf.net/geoip/geoip.php"
	cachedData = None
	def __init__(self, callback=None, ip=None, useCache=True):
		self._useCache = useCache
		if callback:
			self.lookup(callback)

	def lookup(self, callback):
		if self._useCache and self.cachedData:
			self._onLookupData(self.cachedData, callback)
			return
		url = six.ensure_binary(self.URL)
		keywords = {'callback':callback}
		getPage(url).addCallbacks(self._onLookupData, self._onLookupError, callbackKeywords=keywords, errbackKeywords=keywords)

	def _onLookupData(self, response, callback=None):
		try:
			geoipdata = json_loads(response)
			for key, value in six.iteritems(geoipdata):
				geoipdata[key] = str(value)
			geoipdata = Namespace(**geoipdata)
			self.cachedData = geoipdata
			callback(geoipdata)
		except:
			callback(None)

	def _onLookupError(self, error, callback=None):
		callback(None)
