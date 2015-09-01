from enigma import eMediaDatabase

from twisted.web import resource, server
from base64 import b64decode

class CoverRoot(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)
		self.noResource = resource.NoResource(message=_("Nothing there!"))
		self._children = {}

	def render(self, request):
		return self.noResource.render(request)

	def getChildWithDefault(self, path, request):
		child = self._children.get(path, None)
		if not child:
			child = CoverResource(path)
			self._children[path] = child
		return child

class CoverResource(resource.Resource):
	def __init__(self, path):
		resource.Resource.__init__(self)
		self.noResource = resource.NoResource(message=_("Nothing there!"))
		self._path = path
		self._db = eMediaDatabase.getInstance()

	def render(self, request):
		res = self._db.getCoverArtData(int(self._path))
		if res and not res.error():
			data = res.data()
			if data:
				data = str(data[0].get("data", ""))
				cover = b64decode(data)
				request.setHeader("Content-Type", "image/jpg")
				request.setHeader("Content-Length", len(cover))
				request.setHeader("Connection", "close")
				request.setHeader("Content-Language", "de-DE,en-US;q=0.7,en;q=0.3")
				request.write(cover)
				request.finish()
				return server.NOT_DONE_YET

		return self.noResource.render(request)

