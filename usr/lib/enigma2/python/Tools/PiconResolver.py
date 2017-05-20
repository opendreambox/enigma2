class PiconResolver(object):
	@staticmethod
	def getPngName(ref, nameCache, findPicon):
		x = ref.split(':')
		if len(x) < 11: # skip invalid service references
			return ""
		# DVB-T(2)
		if x[0] == 1 and (x[6] & 0xFFFF0000) == 0xEEEE0000:
			x[6] = 0xEEEE0000
		del x[x[10] and 11 or 10:] # remove name and empty path
		x[1]='0' #replace flags field
		name = '_'.join(x).strip('_')
		pngname = nameCache.get(name, "")
		if pngname == "":
			pngname = findPicon(name)
			if pngname == "":
				# lookup without path
				pngname = findPicon('_'.join(x[:10]))
				if pngname == "" and x[0] == '4097':
					# lookup 1_* instead of 4097_*
					pngname = findPicon('1_'+'_'.join(x[1:10]))
					if pngname == "": # no picon for service found
						pngname = nameCache.get("default", "")
						if pngname == "": # no default yet in cache..
							pngname = findPicon("picon_default")
							if pngname != "":
								nameCache["default"] = pngname
		if pngname != "":
			nameCache[name] = pngname
		return pngname