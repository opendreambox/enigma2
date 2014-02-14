from Converter import Converter
from time import localtime, strftime
from Components.Element import cached

class ClockToText(Converter, object):
	DEFAULT = 0
	WITH_SECONDS = 1
	IN_MINUTES = 2
	DATE = 3
	FORMAT = 4
	AS_LENGTH = 5
	TIMESTAMP = 6
	
	# add: date, date as string, weekday, ... 
	# (whatever you need!)
	
	def __init__(self, type):
		Converter.__init__(self, type)
		if type == "WithSeconds":
			self.type = self.WITH_SECONDS
		elif type == "InMinutes":
			self.type = self.IN_MINUTES
		elif type == "Date":
			self.type = self.DATE
		elif type == "AsLength":
			self.type = self.AS_LENGTH
		elif type == "Timestamp":	
			self.type = self.TIMESTAMP
		elif str(type).find("Format") != -1:
			self.type = self.FORMAT
			self.fmt_string = type[7:]
		else:
			self.type = self.DEFAULT
		self.short_day = { "Mon": _("Mon"), "Tue": _("Tue"), "Wed": _("Wed"), "Thu": _("Thu"), "Fri": _("Fri"), "Sat": _("Sat"), "Sun": _("Sun") }
		self.full_day = { "Monday": _("Monday"), "Tuesday": _("Tuesday"), "Wednesday": _("Wednesday"), "Thursday": _("Thursday"), "Friday": _("Friday"), "Saturday": _("Saturday"), "Sunday": _("Sunday") }
		self.short_month = { "Jan": _("Jan"), "Feb": _("Feb"), "Mar": _("Mar"), "Apr": _("Apr"), "May": _("May"), "Jun": _("Jun"), "Jul": _("Jul"), "Aug": _("Aug"), "Sep": _("Sep"), "Oct": _("Oct"), "Nov": _("Nov"), "Dec": _("Dec") }
		self.full_month = { "January": _("January"), "February": _("February"), "March": _("March"), "April": _("April"), "May": _("May"), "June": _("June"), "July": _("July"), "August": _("August"), "September": _("September"), "October": _("October"), "November": _("November"), "December": _("December") }

	@cached
	def getText(self):
		time = self.source.time
		if time is None:
			return ""

		# handle durations
		if self.type == self.IN_MINUTES:
			return "%d min" % (time / 60)
		elif self.type == self.AS_LENGTH:
			return "%d:%02d" % (time / 60, time % 60)
		elif self.type == self.TIMESTAMP:
			return str(time)
		
		t = localtime(time)
		
		if self.type == self.WITH_SECONDS:
			return "%2d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
		elif self.type == self.DEFAULT:
			return "%02d:%02d" % (t.tm_hour, t.tm_min)
		elif self.type == self.DATE:
			line = strftime("%A %B")
			line = line.split(" ")
			fDay = self.full_day[line[0]]
			fMonth = self.full_month[line[1]]
			return "%s %s %s" % (fDay, fMonth, strftime("%d, %Y", t))

		elif self.type == self.FORMAT:
			spos = self.fmt_string.find('%')
			if spos > -1:
				s1 = self.fmt_string[:spos]
				s2 = strftime(self.fmt_string[spos:], t)
				shortDay = self.fmt_string.find('%a')
				fullDay = self.fmt_string.find('%A')
				shortMonth = self.fmt_string.find('%b')
				fullMonth = self.fmt_string.find('%B')
				line = str(s1+s2)
				if shortDay > -1:
					replaces = self.short_day
					# http://stackoverflow.com/questions/6116978/python-replace-multiple-strings
					line = reduce(lambda inline, outline: inline.replace(*outline), replaces.iteritems(), line)
				if fullDay > -1:
					replaces = self.full_day
					line = reduce(lambda inline, outline: inline.replace(*outline), replaces.iteritems(), line)
				if shortMonth > -1:
					replaces = self.short_month
					line = reduce(lambda inline, outline: inline.replace(*outline), replaces.iteritems(), line)
				if fullMonth > -1:
					replaces = self.full_month
					line = reduce(lambda inline, outline: inline.replace(*outline), replaces.iteritems(), line)
				return line
			else:
				return strftime(self.fmt_string, t)

		else:
			return "???"

	text = property(getText)
