from re import compile

class PiconResolver(object):
	partnerbox = compile('1:0:[0-9a-fA-F]+:[1-9a-fA-F]+[0-9a-fA-F]*:[1-9a-fA-F]+[0-9a-fA-F]*:[1-9a-fA-F]+[0-9a-fA-F]*:[1-9a-fA-F]+[0-9a-fA-F]*:[0-9a-fA-F]+:[0-9a-fA-F]+:[0-9a-fA-F]+:http')
	@staticmethod
	def getPiconName(ref):
		pos = ref.rfind(':')
		pos2 = ref.rfind(':', 0, pos)
		if pos - pos2 == 1 or PiconResolver.partnerbox.match(ref) is not None or ref.startswith("4097"):
			basename = ref[:pos2].replace(':', '_')
		else:
			basename = ref[:pos].replace(':', '_')
		if basename.startswith("4097"):
			basename = "1%s" %(basename[4:])
		return basename

	@staticmethod
	def getPngName(ref, nameCache, findPicon):
		name = PiconResolver.getPiconName(ref)
		pngname = nameCache.get(name, "")
		if pngname == "":
			pngname = findPicon(name)
			if pngname != "":
				nameCache[name] = pngname
			else: # no picon for service found
				pngname = nameCache.get("default", "")
				if pngname == "": # no default yet in cache..
					pngname = findPicon("picon_default")
					if pngname != "":
						nameCache["default"] = pngname
		return pngname