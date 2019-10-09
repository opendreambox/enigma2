from enigma import e_tzset
from Components.config import config
from Components.GeoIPLookup import GeoIPLookup
from Tools.Log import Log

from collections import OrderedDict
from datetime import datetime
from dateutil.zoneinfo import getzoneinfofile_stream, ZoneInfoFile
from os import environ, unlink, symlink, readlink
from Screens.Setup import Setup
from Tools import Notifications

class TimezoneIterator(object):
	def __init__(self, timezone):
		self._timezone = timezone
		self._index = -1

	def next(self):
		self._index += 1
		if self._index == 0:
			return self._timezone.name
		elif self._index == 1:
			return self._timezone.key
		raise StopIteration

class Timezone(object):
	def __init__(self, key, zinfo):
		self._key = key
		self._code = "UTC"
		self._region = "UTC"
		self._city = "UTC"
		self._offset = "UTC"
		self._render(key, zinfo)
		self._current = -1

	def _render(self, key, zinfo):
		today = datetime.now(tz=zinfo)
		self._code = today.strftime("%Z")
		vals = key.rsplit("/", 1)
		if len(vals) == 2:
			self._region, self._city = vals
			if self._region.startswith("Etc"):
				self._region = "Other"
		else:
			if vals[0] in [
				"Cuba",
				"Egypt",
				"Eire",
				"Hongkong",
				"Iceland",
				"Iran",
				"Israel",
				"Jamaica",
				"Japan",
				"Kwajalein",
				"Libya",
				"Navajo",
				"Poland",
				"Portugal",
				"Singapore",
				"Turkey",
			]:
				self._region = vals[0]
			else:
				self._region = "Other"
			self._city = vals[0]

		offset = today.strftime("%z")
		timestamp = offset[1:]
		timestamp = "%s:%s" %(timestamp[:2], timestamp[2:])
		self._offset = "GMT%s%s" %(offset[0], timestamp)

	@property
	def key(self):
		return self._key

	@property
	def code(self):
		return self._code

	@property
	def name(self):
		return "%s (%s - %s)" %(self._key, self._code, self._offset)

	@property
	def region(self):
		return self._region

	@property
	def city(self):
		return self._city

	@property
	def offset(self):
		return self._offset
	
	def __iter__(self):
		return TimezoneIterator(self)

	def __getitem__(self, item):
		if item == 0:
			return self.key
		elif item == 1:
			return self.name

	def __str__(self):
		return self.name

	def __repr__(self):
		return "~Timezone %s" %(self.name,)

class Timezones(object):
	CONFIG_VERSION = 2

	def __init__(self):
		self.timezones = []
		self._lut = {}
		self._regions = OrderedDict()
		self._defaultCountry = "en"
		self._geoIpZone = "Europe/Berlin"
		self.loadFinished = False
		self.onReady = []
		self.reload()

	def checkUpgrade(self):
		if config.misc.firstrun.value:
			return
		requiresSetup = False
		if config.timezone.version.value == 0:
			try:
				currentZone = self.getCurrentTimezone()
				Log.w(currentZone)
				if currentZone.endswith('Istanbul'):
					Log.w("Current timezone is Europe/Istanbul. User needs to verify!")
					requiresSetup = True
			except:
				pass
			config.timezone.version.value = 1
		if config.timezone.version.value == 1:
			requiresSetup = True
			config.timezone.version.value = 2
		if requiresSetup:
			Log.w("Upgraded to new timezone handling - Require setup!")
			Notifications.AddNotification(Setup, "timezone")
		config.timezone.version.save()

	def _onGeoIpData(self, data):
		if data:
			self._geoIpZone = data.timezone
			self._defaultCountry = data.country_code.lower()
		self.loadFinished = True
		for fnc in self.onReady:
			fnc()

	@property
	def regions(self):
		return list(self._regions.keys())

	@property
	def defaultRegion(self):
		return self._lut[self.defaultZone].region

	@property
	def defaultZone(self):
		return self.getCurrentTimezone()

	@property
	def defaultCountry(self):
		return self._defaultCountry

	def regionalZones(self, region):
		return self._regions.get(region, [])

	def reload(self):
		self.loadFinished = False
		GeoIPLookup(self._onGeoIpData)
		self.timezones = []
		self._lut = {}
		self._regions = OrderedDict()
		zones = ZoneInfoFile(getzoneinfofile_stream()).zones
		keys = sorted(zones.keys())
		for key in keys:
			zinfo = zones[key]
			timezone = Timezone(key, zinfo)
			region = self._regions.get(timezone.region, [])
			region.append(timezone)
			self._regions[timezone.region] = region
			self._lut[key] = timezone
			self.timezones.append(list(timezone))

	def activateTimezone(self, zone):
		Log.i(zone)
		environ['TZ'] = zone
		try:
			unlink("/etc/localtime")
		except OSError:
			pass
		try:
			symlink("/usr/share/zoneinfo/%s" %(zone,), "/etc/localtime")
		except OSError:
			pass
		e_tzset()
		config.timezone.save()

	def getTimezoneList(self):
		return [ str(x[0]) for x in self.timezones ]

	def getCurrentTimezone(self):
		t = "Europe/Berlin"
		try:
			current = readlink("/etc/localtime")
			offset = len("/usr/share/zoneinfo/")
			zone = current[offset:]
			if zone == "CET": #default link in images
				if self._geoIpZone:
					t = self._geoIpZone
			else:
				t = zone
		except:
			if self._geoIpZone:
				t = self._geoIpZone
			Log.w("No current timezone set, using fallback %s" %(t,))
		return t

	def getDefaultTimezone(self):
		# TODO return something more useful - depending on country-settings?
		t = self.getCurrentTimezone()
		if t in list(self._lut.keys()):
			return t
		return self.timezones[0][0]

timezones = Timezones()
