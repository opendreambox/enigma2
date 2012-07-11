from enigma import loadImage

pixmap_cache = {}

def LoadPixmap(path, desktop = None, cached = False):
	if path in pixmap_cache:
		return pixmap_cache[path]

	ptr = loadImage(path)
	if ptr and desktop:
		desktop.makeCompatiblePixmap(ptr)

	if cached:
		pixmap_cache[path] = ptr

	return ptr
