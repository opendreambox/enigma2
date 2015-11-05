class ResourceManager:
	def __init__(self):
		self.resourceList = {}
		
	def addResource(self, name, resource):
		print "[ResourceManager] adding:", name
		self.resourceList[name] = resource
		#print "resources:", self.resourceList
		
		
	def getResource(self, name, default = None):
		if not self.hasResource(name):
			return default
		return self.resourceList[name]
	
	def hasResource(self, name):
		return self.resourceList.has_key(name)
	
	def removeResource(self, name):
		if self.hasResource(name):
			del self.resourceList[name]
		
resourcemanager = ResourceManager()