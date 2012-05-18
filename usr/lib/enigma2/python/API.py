from Tools.BoundFunction import boundFunction

def getFunctionTree(my_api, name = None):
	functions = my_api.getFunctions()
	subapis = my_api.getSubAPIs()
	resultlist = []
	for function in functions:
		item = None
		if name is None:
			item = function
		else:
			item = "%s.%s" %(name, function)
		resultlist.append(item)
	for subapi in subapis:
		subapiuri = ""
		if name is None:
			subapiuri = subapi
		else:
			subapiuri = "%s.%s" % (name, subapi)
		resultlist += getFunctionTree(my_api.call(subapi), subapiuri)
	return resultlist

def getSubAPITree(my_api, name = None):
	functions = my_api.getFunctions()
	subapis = my_api.getSubAPIs()
	resultlist = []
	if len(functions) > 0:
		resultlist = [name]
		for subapi in subapis:
			if name is None:
				subapiuri = subapi
			else:
				subapiuri = "%s.%s" % (name, subapi)
			resultlist += getSubAPITree(my_api.call(subapi), subapiuri)
	return resultlist

def registerAPIs():
	from APIs import SystemInfo, ServiceData
	modules = [SystemInfo, ServiceData]
	
	for module in modules:
		module.registerAPIs(api)

	print "APIs:", getSubAPITree(api, "api")
	print "Functions:", getFunctionTree(api, "api")

session = None

class API(object):
	def __init__(self):
		self.__calls = {}
		self.__parameters_type = {}
		self.__return_type = {}
		self.__needsSession = {}
		self.__version = None
		self.__session = None

	def __setattr__(self, name, value):
		if name in ("_%s__calls" % self.__class__.__name__, "version"):
			super.__setattr__(self, name, value)
		else:
			self.__calls[name] = value

	def __getattr__(self, name):
		call = self.__calls.get(name, None)
		return call

	def __getSub(self, matcher):
		calls = []
		for key in self.__calls.keys():
			if matcher(self.__calls[key]):
				calls.append(key)
		return calls

	def __setVersion(self, version):
		assert type(version) == int
		self.__version = version

	def __getVersion(self):
		return self.__version
	
	def setSession(self, current_session):
		global session
		session = current_session

	def getFunctions(self):
		functions = self.__getSub(lambda x: type(x) != type(self))
		functions.remove("_%s__version" % self.__class__.__name__)
		functions.remove("_%s__return_type" % self.__class__.__name__)
		functions.remove("_%s__parameters_type" % self.__class__.__name__)
		return functions

	def getSubAPIs(self):
		return self.__getSub(lambda x: type(x) == type(self))

	def add_call(self, name, call, parameters_type, return_type, needsSession = False):
		split = name.split(".")
		if len(split) > 1:
			subapiname = split[0]
			subapi = self.__calls.get(subapiname, API())
			subapi.add_call('.'.join(split[1:]), call, parameters_type, return_type, needsSession = needsSession)

			self.__calls[subapiname] = subapi
		else:
			self.__calls[name] = call
			self.__parameters_type[name] = parameters_type
			self.__return_type[name] = return_type
			self.__needsSession[name] = needsSession

	def call(self, name):
		if name is None:
			return self
		split = name.split(".")
		if len(split) > 1:
			subapi = self.__calls.get(split[0], None)
			if subapi is not None:
				return subapi.call('.'.join(split[1:]))
			return None
		else:
			call = self.__calls.get(name, None)
			if call is not None:
				if self.__needsSession.get(name, False): # subapi
					call = boundFunction(call, session)
			return call 

	version = property(__getVersion, __setVersion)

api = API()

