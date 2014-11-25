from Plugins.Plugin import PluginDescriptor
from twisted.web import resource
from API import api, getFunctionTree, getSubAPITree
import json, traceback

class APIRoot(resource.Resource):
	def render(self, request):
		return json.dumps({ "methods": {
				"/call" : "Call any api function",
				"/getSubAPITree" : "Get a tree of SubAPIs",
				"/getFunctionTree" : "Get the function-tree of a SubAPI",
			}})

class APIJSONResource(resource.Resource):
	def render_POST(self, request):
		body = self._getRequestBody(request)
		try:
			request.setHeader('Content-Type','application/json;charset=UTF-8')
			return self.render_JSON(json.loads(body))
		except Exception as e:
			return self._error(e)
	
	def _getRequestBody(self, request):
		try:
			body = request.content.getvalue()
		except:
			body = request.content.read()
		if not body:
			body = "{}"
		return body
	
	def render_JSON(self, j):
		return json.dumps({})
	
	def _error(self, message, id=None, data=None):
		return json.dumps({"error": {"code": -1, "message" : str(message), "data": data}})
	
	def _result(self, data, id=None):
		return json.dumps({"result": data, "id" : id , "error" : None})

class APICallResource(APIJSONResource):
	def render_JSON(self, j):
		method = j.get("method", None)
		if not method:
			return self._error("mandatory parameter 'method' not given")

		call = api.call(method)
		data = call(*j.get("params", []), **j.get("namedparams", {}))
		return self._result(data=data, id=j.get("id", None))

class APIgetSubAPITreeResource(APIJSONResource):
	def render_JSON(self, j):
		return self.getSubAPITree(id=j.get("id", None), **j.get("namedparams", {}))

	def getSubAPITree(self, id=None, name="api"):
		return self._result( data=getSubAPITree(api, name=name), id=id)

class APIgetFunctionTree(APIJSONResource):
	def render_JSON(self, j):
		return self.getFunctionTree(id=j.get("id", None), **j.get("namedparams", {}))

	def getFunctionTree(self, id=None, name="api"):
		return self._result( data=getFunctionTree(api, name=name), id=id )

def sessionstart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		
		try:
			from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
			root = APIRoot()
			root.putChild("call", APICallResource())
			root.putChild("getSubAPITree", APIgetSubAPITreeResource())
			root.putChild("getFunctionTree", APIgetFunctionTree())
			addExternalChild(("api", root, "JSON-RPC API", api.version, False))
		except Exception as e:
			print "--------------------- JSON WEB API !!!NOT!!! AVAILABLE!\n%s" %e

def Plugins(**kwargs):
	return [ PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart) ]
