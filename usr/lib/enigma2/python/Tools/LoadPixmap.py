from enigma import loadSizedImage, eSize

pixmap_cache = {}

def LoadPixmap(path, desktop = None, cached = False, size=eSize()):
	if path in pixmap_cache:
		return pixmap_cache[path]

	ptr = loadSizedImage(path, size)
	if ptr and desktop:
		desktop.makeCompatiblePixmap(ptr)

	if cached:
		pixmap_cache[path] = ptr

	return ptr
