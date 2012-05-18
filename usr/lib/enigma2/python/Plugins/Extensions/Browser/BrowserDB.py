from Tools.Directories import SCOPE_CONFIG, resolveFilename
from Callable import Callable
import sqlite3

import os.path as os_path
from time import time
from datetime import datetime, timedelta
from email.Utils import mktime_tz, parsedate_tz

from Cookie import SmartCookie, CookieError

from OpenSSL.crypto import load_certificate, FILETYPE_PEM

class Bookmark:
	def __init__(self, id = -1, name = "", url = "", group = 0):
		self.id = id
		self.name = name
		self.url = url
		self.group = group

	def __str__(self):
		return "Bookmark::%s|%s|%s" %(self.id, self.name, self.url)

class Group:
	def __init__(self, id = -1, name = "", parent = 0):
		self.id = id
		self.name = name
		self.parent = parent

class HistoryItem:
	def __init__(self, id = -1, timestamp = None, title = None, url = None):
		self.id = id
		if timestamp == None:
			self.timestamp = time()
		else:
			self.timestamp = float(timestamp)
		self.title = title
		self.url = url

	def __str__(self):
		return "HistoryItem::%s|%s|%s|%s" %(self.id, self.timestamp, self.title, self.url)

class Certificate:
	def __init__(self, id = -1, host = None, pem = None):
		self.id = id
		self.host = host
		self.pem = pem
		self.cert = load_certificate(FILETYPE_PEM, self.pem)

	def notBefore(self):
		return self.crtParseASN1Time(self.cert.get_notBefore())

	def notAfter(self):
		return self.crtParseASN1Time(self.cert.get_notAfter())

	def crtParseASN1Time(self, date):
		dateTime = date[:14]
		additional = date[14:]
		res = datetime.strptime(dateTime, "%Y%m%d%H%M%S")
		if additional != "Z":
			if len(additional) == 5:
				h = int(additional[1:3])
				m = int(additional[3:5])
				delta = timedelta(hours = h, minutes = m)
				if additional.startswith("+"):
					res = res + delta
				elif additional.startswith("-"):
					res = res - delta
		return res

	def __str__(self):
		return "Certificate::id=%s|host=%s|serial=%s|SHA1digest=%s issued by %s, not valid before %s or after %s" %(
				self.id, self.host, self.cert.get_serial_number(), self.cert.digest("sha1"), self.cert.get_issuer().commonName, self.notBefore(), self.notAfter()
			)

class Cookie:
	def __init__(self, key, domain, path, raw, expires, convertDate = False):
		self.key = key
		self.domain = domain
		self.path = path

		self.expires = self.cookieDate2Ts(expires) if convertDate else expires
		self.raw = raw

	@staticmethod
	def fromRawString(raw):
		try:
			sc = SmartCookie(raw)
			for key, cookie in sc.items():
				try:
					return Cookie(key, cookie['domain'], cookie['path'], raw, cookie['expires'], True)
				except:
					return None
		except CookieError as e:
			print e
			return None

	def cookieDate2Ts(self, cd):
		#Sat, 02-Nov-2013 11:33:51 GMT
		if cd.strip() != "" and cd != None:
			return mktime_tz(parsedate_tz(cd.strip()))
		return long(0)

	def __str__(self):
		return "Cookie::key=%s|domain=%s|path=%s|expires=%s" %(self.key, self.domain, self.path, self.expires)

class IterCookies:
	def __init__(self, cookies):
		self.list = cookies

	def __iter__(self):
		return self

	def next(self):
		if len(self.list) == 0:
			raise StopIteration
		else:
			cookie = self.list.pop(0)
			return (cookie.key, cookie.domain, cookie.path, cookie.raw, cookie.expires)

class BrowserDB:
	TABLE_VERSION = "__version"
	TABLE_BM = "bookmarks"
	TABLE_BM_GROUPS = "bookmark_groups"
	TABLE_HISTORY = "history"
	TABLE_CERTS = "certificates"
	TABLE_COOKIES = "cookies"

	DB_VERSION = 1

	FIELD_ID = "id"
	FIELD_VERSION_V = "version"
	FIELD_BM_GROUP_NAME = "name"
	FIELD_BM_GROUP_PARENT = "parent"
	FIELD_BM_NAME = "name"
	FIELD_BM_URL = "url"
	FIELD_BM_GROUPID = "groupid"
	FIELD_HIS_TS = "timestamp"
	FIELD_HIS_TITLE = "title"
	FIELD_HIS_URL = "url"
	FIELD_CERT_HOST = "host"
	FIELD_CERT_PEM = "pem"
	FIELD_COOKIE_KEY = "key"
	FIELD_COOKIE_DOMAIN = "domain"
	FIELD_COOKIE_PATH = "path"
	FIELD_COOKIE_EXPIRES = "expires"
	FIELD_COOKIE_RAW = "raw"

	SQL_CREATE_VERSION_T = "CREATE TABLE %s (%s INTEGER)" %(TABLE_VERSION, FIELD_VERSION_V)
	SQL_CREATE_BM_T = "CREATE TABLE %s (%s INTEGER PRIMARY KEY, %s TEXT, %s TEXT, %s INTEGER DEFAULT -1 NOT NULL)" %(TABLE_BM, FIELD_ID, FIELD_BM_NAME, FIELD_BM_URL, FIELD_BM_GROUPID)
	SQL_CREATE_BM_GROUPS_T = "CREATE TABLE %s (%s INTEGER PRIMARY KEY, %s INTEGER DEFAULT 0 NOT NULL, %s TEXT)" %(TABLE_BM_GROUPS, FIELD_ID, FIELD_BM_GROUP_PARENT, FIELD_BM_GROUP_NAME)
	SQL_CREATE_HISTORY_T = "CREATE TABLE %s (%s INTEGER PRIMARY KEY, %s REAL, %s TEXT, %s TEXT)" %(TABLE_HISTORY, FIELD_ID, FIELD_HIS_TS, FIELD_HIS_TITLE, FIELD_HIS_URL)
	SQL_CREATE_CERT_T = "CREATE TABLE %s (%s INTEGER PRIMARY KEY, %s TEXT, %s TEXT)" %(TABLE_CERTS, FIELD_ID, FIELD_CERT_HOST, FIELD_CERT_PEM)
	SQL_CREATE_COOKIE_T = "CREATE TABLE %(table)s( %(key)s TEXT, %(domain)s TEXT, %(path)s TEXT, %(raw)s TEXT, %(expires)s REAL, PRIMARY KEY(%(key)s, %(domain)s, %(path)s) )" %{
			'table' : TABLE_COOKIES, 'key' : FIELD_COOKIE_KEY, 'domain' : FIELD_COOKIE_DOMAIN, 'path': FIELD_COOKIE_PATH, 'raw' : FIELD_COOKIE_RAW, 'expires' : FIELD_COOKIE_EXPIRES }
	SQL_SET_VERSION = "INSERT INTO " + TABLE_VERSION + " (" + FIELD_VERSION_V + ") values (?)"

	CERT_OK = 0
	CERT_UNKOWN = 1
	CERT_CHANGED = 2

	__instance = None
	def getInstance():
		instance = None
		try:
			instance = BrowserDB()
		except BrowserDB, d:
			instance = d

		return instance
	getInstance = Callable(getInstance)

	def __init__(self):
		if BrowserDB.__instance != None:
			raise BrowserDB.__instance
		BrowserDB.__instance = self

		self.__dbfile = "%swebbrowser.db" %( resolveFilename(SCOPE_CONFIG) )
		self.__conn = None
		self.__connect()

	def __connect(self):
		if not os_path.exists(self.__dbfile):
			self.__conn = sqlite3.connect(self.__dbfile)
			self.__createDB()
		else:
			self.__conn = sqlite3.connect(self.__dbfile)
			self.__checkDbVersion()
		self.__conn.text_factory = str

	def __createDB(self):
		c = self.__conn.cursor()
		print "[BrowserDB].__initDB :: Creating Database Tables"
		c.execute(BrowserDB.SQL_CREATE_VERSION_T)
		c.execute(BrowserDB.SQL_CREATE_BM_T)
		c.execute(BrowserDB.SQL_CREATE_BM_GROUPS_T)
		c.execute(BrowserDB.SQL_CREATE_HISTORY_T)
		c.execute(BrowserDB.SQL_CREATE_CERT_T)
		c.execute(BrowserDB.SQL_CREATE_COOKIE_T)

		print BrowserDB.SQL_SET_VERSION
		c.execute(BrowserDB.SQL_SET_VERSION, (str(BrowserDB.DB_VERSION)))

		print "[BrowserDB].__initDB :: Adding default bookmarks"
		list = [ Bookmark(-1, "Dream Multimedia TV", "http://www.dream-multimedia-tv.de/"),
				Bookmark(-1, "Dream Multimedia TV - Forum", "http://www.dream-multimedia-tv.de/board/"),
				Bookmark(-1, "Twitter", "http://www.twitter.com"),
				Bookmark(-1, "Google", "http://www.google.com"),
				Bookmark(-1, "Facebook", "http://www.facebook.com"),
		]
		self.setBookmarks(list)

		self.__conn.commit()
		c.close()
		print "[BrowserDB].__initDB :: Database Tables Initialized"

	def __checkDbVersion(self):
		pass #TODO implement version Check

	def __upgradeDB(self, fv):
		pass #TODO implement Updates

	def getBookmarks(self, needle = None):
		c = self.__conn.cursor()
		bookmarks = []
		if needle is None or needle == "":
			bookmarks = self.__getBookmarks(c)
		else:
			bookmarks = self.__filterBookmarks(c, needle)
		c.close()
		return bookmarks

	def setBookmarks(self, bookmarks):
		c = self.__conn.cursor()
		for bm in bookmarks:
			self.setBookmark(bm, c)
		c.close()

	def setBookmark(self, bm, cursor = None):
		c = None
		if cursor is None:
			c = self.__conn.cursor()
		else:
			c = cursor

		if bm.id == -1:
			self.__addBookmark(bm, c)
		else:
			self.__updateBookmark(bm, c)

		if cursor is None:
			c.close()

	def deleteBookmark(self, bm):
		c = self.__conn.cursor()
		self.__deleteBookmark(bm, c)
		c.close()

	def __getBookmarks(self, cursor):
		sql = "SELECT * FROM %s ORDER BY %s ASC" %(BrowserDB.TABLE_BM, BrowserDB.FIELD_BM_NAME)
		cursor.execute(sql)
		return self.__assignBookmarks(cursor)

	def __filterBookmarks(self, cursor, needle):
		needle = "%" + needle + "%"
		sql = "SELECT * FROM %(table)s WHERE %(name)s LIKE ? ORDER BY %(name)s ASC" %{"table" : BrowserDB.TABLE_BM, "name" : BrowserDB.FIELD_BM_NAME}
		cursor.execute(sql, [needle])
		return self.__assignBookmarks(cursor)

	def __assignBookmarks(self, cursor):
		bookmarks = []
		for item in cursor:
			bookmarks.append( Bookmark(int(item[0]), str(item[1]), str(item[2]), str(item[3])) )
		return bookmarks

	def __addBookmark(self, bm, cursor):
		sql = "INSERT INTO %s (%s, %s, %s, %s) values (NULL, ?, ?, ?)" %(
			BrowserDB.TABLE_BM,
			BrowserDB.FIELD_ID,
			BrowserDB.FIELD_BM_NAME,
			BrowserDB.FIELD_BM_URL,
			BrowserDB.FIELD_BM_GROUPID
		)
		print sql
		cursor.execute(sql, (bm.name, bm.url, bm.group))
		self.__conn.commit()

	def __updateBookmark(self, bm, cursor):
		sql = "UPDATE %s SET %s=?, %s=?, %s=? WHERE %s=?" %(
			BrowserDB.TABLE_BM,
			BrowserDB.FIELD_BM_NAME,
			BrowserDB.FIELD_BM_URL,
			BrowserDB.FIELD_BM_GROUPID,
			BrowserDB.FIELD_ID
		)
		print sql
		cursor.execute(sql, (bm.name, bm.url, bm.group, str(bm.id)) )
		self.__conn.commit()

	def __deleteBookmark(self, bm, cursor):
		sql = "DELETE FROM %s WHERE %s=?" %(BrowserDB.TABLE_BM, BrowserDB.FIELD_ID)
		print sql
		cursor.execute(sql, (str(bm.id)) )
		self.__conn.commit()

	def getHistory(self, needle = None):
		items = []
		c = self.__conn.cursor()
		if needle is None or needle == "":
			items = self.__getHistory(c)
		else:
			items = self.__filterHistory(c, needle)
		c.close()

		return items

	def __getHistory(self, cursor):
		sql = "SELECT * FROM %s ORDER BY %s DESC" %(BrowserDB.TABLE_HISTORY, BrowserDB.FIELD_HIS_TS)
		cursor.execute(sql)
		return self.__assignHistory(cursor)

	def __filterHistory(self, cursor, needle):
		needle = "%" + needle + "%"
		sql = "SELECT * FROM %(table)s WHERE %(title)s LIKE ? ORDER BY %(ts)s DESC" %{"table" : BrowserDB.TABLE_HISTORY, "title" : BrowserDB.FIELD_HIS_TITLE, "ts" : BrowserDB.FIELD_HIS_TS}
		cursor.execute(sql, [needle])
		return self.__assignHistory(cursor)

	def __assignHistory(self, cursor):
		items = []
		for item in cursor:
			items.append( HistoryItem(int(item[0]), str(item[1]), str(item[2]), str(item[3])) )
		return items

	def addToHistory(self, hi, cursor = None):
		c = None
		if cursor is None:
			c = self.__conn.cursor()
		else:
			c = cursor
		self.__addHistoryItem(hi, c)

		if cursor is None:
			c.close()

	def clearHistory(self):
		c = self.__conn.cursor()
		self.__clearHistory(c)
		c.close()

	def __clearHistory(self, cursor):
		sql = "DELETE FROM %s" %(BrowserDB.TABLE_HISTORY)
		cursor.execute(sql)
		self.__conn.commit()

	def __addHistoryItem(self, hi, cursor):
		sql = "INSERT INTO %s (%s, %s, %s, %s) values (NULL, ?, ?, ?)" %(
			BrowserDB.TABLE_HISTORY,
			BrowserDB.FIELD_ID,
			BrowserDB.FIELD_HIS_TS,
			BrowserDB.FIELD_HIS_TITLE,
			BrowserDB.FIELD_HIS_URL,
		)
		print sql
		cursor.execute(sql, (str(hi.timestamp), hi.title, hi.url))
		self.__conn.commit()

	def suggsetUrls(self, needle):
		c = self.__conn.cursor()
		return self.__suggestUrls(c, needle)
		c.close()

	def __suggestUrls(self, cursor, needle):
		needle = "%" + needle + "%"
		sql = "SELECT DISTINCT %(url)s FROM %(table)s WHERE %(url)s LIKE ? ORDER BY %(url)s ASC"

		urls = []
		sqlBM = sql %{"url" : BrowserDB.FIELD_BM_URL, "table" : BrowserDB.TABLE_BM}
		print sqlBM
		urls = self.__execUrlSearch(cursor, sqlBM, needle, urls)

		sqlHis = sql %{"url" : BrowserDB.FIELD_HIS_URL, "table" : BrowserDB.TABLE_HISTORY}
		print sqlHis
		urls = self.__execUrlSearch(cursor, sqlHis, needle, urls)

		self.__conn.commit()
		#remove duplicates
		d = {}
		for x in urls:
			d[x] = 1
		urls = list(d.keys())
		return urls

	def __execUrlSearch(self, cursor, sql, needle, list):
		print "needle=%s" %needle
		cursor.execute(sql, [needle])
		for item in cursor:
			list.append(str(item[0]))
		return list

	def addCert(self, cert):
		c = self.__conn.cursor()
		sql = "INSERT INTO %s (%s, %s, %s) values (NULL, ?, ?)" %(
			BrowserDB.TABLE_CERTS,
			BrowserDB.FIELD_ID,
			BrowserDB.FIELD_CERT_HOST,
			BrowserDB.FIELD_CERT_PEM
		)
		print sql
		c.execute(sql, (cert.host, cert.pem))
		self.__conn.commit()
		c.close()

	def checkCert(self, cert):
		c = self.__conn.cursor()
		#First check if the given host + cert are in the exception list
		sql = "SELECT %s FROM %s WHERE %s LIKE ? AND %s LIKE ? LIMIT 1" %(
			BrowserDB.FIELD_ID,
			BrowserDB.TABLE_CERTS,
			BrowserDB.FIELD_CERT_HOST,
			BrowserDB.FIELD_CERT_PEM
		)

		c.execute(sql, (cert.host, cert.pem))
		for item in c:
			c.close()
			return BrowserDB.CERT_OK

		#Check if there is any other known "exceptional" cert for the given host, if so - BE CAREFUL!
		sql = "SELECT %s FROM %s WHERE %s LIKE ? AND %s NOT LIKE ? LIMIT 1" %(
			BrowserDB.FIELD_ID,
			BrowserDB.TABLE_CERTS,
			BrowserDB.FIELD_CERT_HOST,
			BrowserDB.FIELD_CERT_PEM
		)
		c.execute(sql, (cert.host, cert.pem))
		for item in c:
			c.close()
			return BrowserDB.CERT_CHANGED

		c.close()
		return self.CERT_UNKOWN

	def getCerts(self):
		items = []
		c = self.__conn.cursor()
		items = self.__getCerts(c)
		c.close()
		return items

	def __getCerts(self, cursor):
		sql = "SELECT * FROM %s ORDER BY %s DESC" %(BrowserDB.TABLE_CERTS, BrowserDB.FIELD_CERT_HOST)
		cursor.execute(sql)
		return self.__assignCerts(cursor)

	def __assignCerts(self, cursor):
		certs = []
		for item in cursor:
			certs.append( Certificate(item[0], item[1], item[2]) )
		return certs

	def deleteCert(self, cert):
		c = self.__conn.cursor()
		self.__deleteCert(cert, c)
		c.close()

	def __deleteCert(self, cert, cursor):
		sql = "DELETE FROM %s WHERE %s=?" %(BrowserDB.TABLE_CERTS, BrowserDB.FIELD_ID)
		print sql
		cursor.execute(sql, (str(cert.id)) )
		self.__conn.commit()

	def getCookies(self):
		cookies = []
		c = self.__conn.cursor()
		cookies = self.__getCookies(c)
		c.close()
		return cookies

	def __getCookies(self, cursor):
		sql = "SELECT * FROM %s ORDER BY %s ASC" %(BrowserDB.TABLE_COOKIES, BrowserDB.FIELD_COOKIE_DOMAIN)
		cursor.execute(sql)
		return self.__assignCookies(cursor)

	def __assignCookies(self, cursor):
		cookies = []
		for c in cursor:
			cookies.append(Cookie(c[0], c[1], c[2], c[3], c[4]))
		return cookies

	def persistCookies(self, cookies):
		c = self.__conn.cursor()
		self.__persistCookies(cookies, c)
		c.close()

	def __persistCookies(self, cookies, cursor = None):
		sql = "REPLACE INTO %s (%s, %s, %s, %s, %s) values ( ?, ?, ?, ?, ? )" %(
			BrowserDB.TABLE_COOKIES,
			BrowserDB.FIELD_COOKIE_KEY,
			BrowserDB.FIELD_COOKIE_DOMAIN,
			BrowserDB.FIELD_COOKIE_PATH,
			BrowserDB.FIELD_COOKIE_RAW,
			BrowserDB.FIELD_COOKIE_EXPIRES)
		print sql
		sqlDel = "DELETE FROM %(table)s WHERE %(expires)s > 0 and %(expires)s < ?" %{ 'table' : BrowserDB.TABLE_COOKIES, 'expires' : BrowserDB.FIELD_COOKIE_EXPIRES }
		print sqlDel
		c = None
		if cursor is None:
			c = self.__conn.cursor()
		else:
			c = cursor

		c.executemany(sql, IterCookies(cookies))
		self.__conn.commit()

		c.execute(sqlDel, [str(time())])
		self.__conn.commit()

		if cursor is None:
			c.close()

	def deleteAllCookies(self):
		c = self.__conn.cursor()
		self.__deleteAllCookies(c)
		c.close()

	def __deleteAllCookies(self, cursor):
		sql = "DELETE FROM %s" %(BrowserDB.TABLE_COOKIES)
		cursor = self.__conn.cursor()
		cursor.execute(sql)
		self.__conn.commit()
		cursor.close()

	def deleteCookie(self, cookie):
		c = self.__conn.cursor()
		self.__deleteCookie(cookie, c)
		c.close()

	def __deleteCookie(self, cookie, cursor):
		sql = "DELETE FROM %s WHERE %s like ? AND %s like ? AND %s like ?" %(BrowserDB.TABLE_COOKIES, BrowserDB.FIELD_COOKIE_KEY, BrowserDB.FIELD_COOKIE_DOMAIN, BrowserDB.FIELD_COOKIE_PATH)
		cursor = self.__conn.cursor()
		cursor.execute(sql, (cookie.key, cookie.domain, cookie.path))
		self.__conn.commit()
		cursor.close()


