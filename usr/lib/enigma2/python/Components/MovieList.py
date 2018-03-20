from GUIComponent import GUIComponent
from Tools.FuzzyDate import FuzzyTime
from ServiceReference import ServiceReference
from Components.TemplatedMultiContentComponent import TemplatedMultiContentComponent
from Components.config import config

from skin import componentSizes

from enigma import eListbox, iServiceInformation, eServiceReference, eServiceCenter

class MovieList(TemplatedMultiContentComponent):
	SORT_ALPHANUMERIC = 1
	SORT_RECORDED = 2

	LISTTYPE_ORIGINAL = 1
	LISTTYPE_COMPACT_DESCRIPTION = 2
	LISTTYPE_COMPACT = 3
	LISTTYPE_MINIMAL = 4

	LIST_STYLES = {
		LISTTYPE_ORIGINAL : "default",
		LISTTYPE_COMPACT_DESCRIPTION : "compact_description",
		LISTTYPE_COMPACT : "compact",
		LISTTYPE_MINIMAL : "minimal"
	}

	HIDE_DESCRIPTION = 1
	SHOW_DESCRIPTION = 2

	COMPONENT_ID = componentSizes.MOVIE_LIST

	default_template = """{"templates":
		{
			"default" : (75, [
				MultiContentEntryText(pos=(0, 0), size=(width-182, 30), font=0, flags=RT_HALIGN_LEFT, text=1),
				MultiContentEntryText(pos=(width-180, 0), size=(180, 30), font=3, flags=RT_HALIGN_RIGHT, text=2),
				MultiContentEntryText(pos=(200, 50), size=(200, 20), font=2, flags=RT_HALIGN_LEFT, text=3),
				MultiContentEntryText(pos=(0, 30), size=(width, 20), font=2, flags=RT_HALIGN_LEFT, text=4),
				MultiContentEntryText(pos=(0, 50), size=(200, 20), font=2, flags=RT_HALIGN_LEFT, text=5),
				MultiContentEntryText(pos=(width-200, 50), size=(198, 20), font=2, flags=RT_HALIGN_RIGHT, text=6),
			]),
			"compact_description" : (37, [
				MultiContentEntryText(pos=(0, 0), size=(width-120, 20), font=1, flags=RT_HALIGN_LEFT, text=1),
				MultiContentEntryText(pos=(0, 20), size=(width-212, 17), font=4, flags=RT_HALIGN_LEFT, text=2),
				MultiContentEntryText(pos=(width-120, 6), size=(120, 20), font=4, flags=RT_HALIGN_RIGHT, text=3),
				MultiContentEntryText(pos=(width-212, 20), size=(154, 17), font=4, flags=RT_HALIGN_RIGHT, text=4),
				MultiContentEntryText(pos=(width-58, 20), size=(58, 20), font=4, flags=RT_HALIGN_RIGHT, text=5),
			]),
			"compact" : (37, [
				MultiContentEntryText(pos=(0, 0), size=(width-77, 20), font=1, flags=RT_HALIGN_LEFT, text=1),
				MultiContentEntryText(pos=(width-200, 20), size=(200, 17), font=4, flags=RT_HALIGN_RIGHT, text=2),
				MultiContentEntryText(pos=(200, 20), size=(200, 17), font=4, flags=RT_HALIGN_LEFT, text=3),
				MultiContentEntryText(pos=(0, 20), size=(200, 17), font=4, flags=RT_HALIGN_LEFT, text=4),
				MultiContentEntryText(pos=(width-75, 0), size=(75, 20), font=1, flags=RT_HALIGN_RIGHT, text=5),
			]),
			"minimal" : (25, [
				MultiContentEntryText(pos=(0, 0), size=(width-146, 20), font=1, flags=RT_HALIGN_LEFT, text=1),
				MultiContentEntryText(pos=(width-145, 4), size=(145, 20), font=3, flags=RT_HALIGN_RIGHT, text=2),
			])
		},
		"fonts" : [gFont("Regular", 22), gFont("Regular", 20), gFont("Regular", 18), gFont("Regular", 16), gFont("Regular", 14)]
	}"""

	def __init__(self, root, list_type=None, sort_type=None, descr_state=None):
		TemplatedMultiContentComponent.__init__(self)
		self.list = []

		self.descr_state = descr_state or self.HIDE_DESCRIPTION
		self.sort_type = sort_type or self.SORT_RECORDED
		self.setListType(list_type or self.LISTTYPE_ORIGINAL)
		self.tags = set()
		if root is not None:
			self.reload(root)

		self.l.setBuildFunc(self.buildMovieListEntry)
		self.onSelectionChanged = [ ]

	def applySkin(self, desktop, parent):
		GUIComponent.applySkin(self, desktop, parent)
		self.applyTemplate(additional_locals={"width" : self.l.getItemSize().width()-30})

	def redrawList(self):
		pass

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def setListType(self, type):
		self.list_type = type
		self.setTemplate(self.LIST_STYLES[type])

	def setDescriptionState(self, val):
		self.descr_state = val

	def setSortType(self, type):
		self.sort_type = type

	# | name of movie              |
	#
	def buildMovieListEntry(self, serviceref, info, begin, len):
		if serviceref.flags & eServiceReference.mustDescent:
			return None

		if len <= 0: #recalc len when not already done
			cur_idx = self.l.getCurrentSelectionIndex()
			x = self.list[cur_idx]
			if config.usage.load_length_of_movies_in_moviellist.value:
				len = x[1].getLength(x[0]) #recalc the movie length...
			else:
				len = 0 #dont recalc movielist to speedup loading the list
			self.list[cur_idx] = (x[0], x[1], x[2], len) #update entry in list... so next time we don't need to recalc
		
		if len > 0:
			len = "%d:%02d" % (len / 60, len % 60)
		else:
			len = ""
		
		res = [ None ]
		
		txt = info.getName(serviceref)
		service = ServiceReference(info.getInfoString(serviceref, iServiceInformation.sServiceref))
		description = info.getInfoString(serviceref, iServiceInformation.sDescription)
		tags = info.getInfoString(serviceref, iServiceInformation.sTags)
		servicename = ""
		if service is not None:
			servicename = service.getServiceName()

		begin_string = ""
		if begin > 0:
			t = FuzzyTime(begin)
			begin_string = t[0] + ", " + t[1]
		
		if self.list_type == MovieList.LISTTYPE_ORIGINAL:
			res.extend((txt, tags, servicename, description, begin_string, len))
		elif self.list_type == MovieList.LISTTYPE_COMPACT_DESCRIPTION:
			res.extend((txt, description, begin_string, servicename, len))
		elif self.list_type == MovieList.LISTTYPE_COMPACT:
			res.extend((txt, tags, servicename, begin_string, len))
		else:
			assert(self.list_type == MovieList.LISTTYPE_MINIMAL)
			if self.descr_state == MovieList.SHOW_DESCRIPTION:
				res.extend((txt, begin_string))
			else:
				res.extend((txt, len))
		
		return res

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and l[0] and l[1] and l[1].getEvent(l[0])

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def reload(self, root = None, filter_tags = None):
		if root is not None:
			self.load(root, filter_tags)
		else:
			self.load(self.root, filter_tags)
		self.l.setList(self.list)

	def removeService(self, service):
		for l in self.list[:]:
			if l[0] == service:
				self.list.remove(l)
		self.l.setList(self.list)

	def __len__(self):
		return len(self.list)

	def load(self, root, filter_tags):
		# this lists our root service, then building a 
		# nice list
		
		self.list = [ ]
		self.serviceHandler = eServiceCenter.getInstance()
		
		self.root = root
		list = self.serviceHandler.list(root)
		if list is None:
			print "listing of movies failed"
			list = [ ]	
			return
		tags = set()
		
		while 1:
			serviceref = list.getNext()
			if not serviceref.valid():
				break
			if serviceref.flags & eServiceReference.mustDescent:
				continue
		
			info = self.serviceHandler.info(serviceref)
			if info is None:
				continue
			begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
		
			# convert space-seperated list of tags into a set
			this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
			if this_tags == ['']:
				this_tags = []
			this_tags = set(this_tags)
			tags |= this_tags
		
			# filter_tags is either None (which means no filter at all), or 
			# a set. In this case, all elements of filter_tags must be present,
			# otherwise the entry will be dropped.			
			if filter_tags is not None and not this_tags.issuperset(filter_tags):
				continue
		
			self.list.append((serviceref, info, begin, -1))
		
		if self.sort_type == MovieList.SORT_ALPHANUMERIC:
			self.list.sort(key=self.buildAlphaNumericSortKey)
		else:
			# sort: key is 'begin'
			self.list.sort(key=lambda x: -x[2])
		
		# finally, store a list of all tags which were found. these can be presented
		# to the user to filter the list
		self.tags = tags

	def buildAlphaNumericSortKey(self, x):
		ref = x[0]
		info = self.serviceHandler.info(ref)
		name = info and info.getName(ref)
		return (name and name.lower() or "", -x[2])

	def moveTo(self, serviceref):
		count = 0
		for x in self.list:
			if x[0] == serviceref:
				self.instance.moveSelectionTo(count)
				return True
			count += 1
		return False
	
	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)
