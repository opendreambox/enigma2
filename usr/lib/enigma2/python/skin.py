from Tools.Profile import profile
profile("LOAD:ElementTree")
import xml.etree.cElementTree
from os.path import dirname

profile("LOAD:enigma_skin")
from enigma import eSize, ePoint, gFont, eWindow, eLabel, ePixmap, eWindowStyleManager, \
	addFont, gRGB, eWindowStyleSkinned, eWindowStyleScrollbar, eListboxPythonStringContent, eListboxPythonConfigContent, eListbox
from Components.config import ConfigSubsection, ConfigText, config, ConfigBoolean
from Components.Sources.Source import ObsoleteSource
from Tools.Directories import resolveFilename, SCOPE_SKIN, SCOPE_SKIN_IMAGE, SCOPE_FONTS, SCOPE_CURRENT_SKIN, SCOPE_CONFIG, fileExists
from Tools.Import import my_import
from Tools.LoadPixmap import LoadPixmap
from Tools.Log import Log

from re import search as re_search

HAS_SKIN_USER_DISPLAY = True

colorNames = dict()
skinGlobals = dict()

def dump(x, i=0):
	print " " * i + str(x)
	try:
		for n in x.childNodes:
			dump(n, i + 1)
	except:
		None

class SkinError(Exception):
	def __init__(self, message):
		self.msg = message

	def __str__(self):
		return "{%s}: %s" % (config.skin.primary_skin.value, self.msg)

def getSkinYRes(dom):
	yres = 0
	for c in dom.findall("output"):
		id = c.attrib.get('id')
		if id:
			id = int(id)
		else:
			id = 0
		if id == 0: # framebuffer
			for res in c.findall("resolution"):
				yres = int(res.get("yres", "576"))
				break
	return yres

dom_skins = [ ]

def loadSkin(name, scope = SCOPE_SKIN):
	# read the skin
	filename = resolveFilename(scope, name)
	mpath = dirname(filename) + "/"
	dom_skins.append((mpath, xml.etree.cElementTree.parse(filename).getroot()))

# we do our best to always select the "right" value
# skins are loaded in order of priority: skin with
# highest priority is loaded last, usually the user-provided
# skin.

# currently, loadSingleSkinData (colors, bordersets etc.)
# are applied one-after-each, in order of ascending priority.
# the dom_skin will keep all screens in descending priority,
# so the first screen found will be used.

# example: loadSkin("nemesis_greenline/skin.xml")
config.skin = ConfigSubsection()
config.skin.primary_skin = ConfigText(default = "skin.xml")

profile("LoadSkin")
try:
	loadSkin('skin_user_display.xml', SCOPE_CONFIG)
except (SkinError, IOError, AssertionError), err:
	print "not loading display user skin: ", err

try:
	loadSkin('skin_user.xml', SCOPE_CONFIG)
except (SkinError, IOError, AssertionError), err:
	print "not loading user skin: ", err

try:
	loadSkin(config.skin.primary_skin.value)
except (SkinError, IOError, AssertionError), err:
	print "SKIN ERROR:", err
	print "defaulting to standard skin..."
	config.skin.primary_skin.value = 'skin.xml'
	loadSkin('skin.xml')

yres = getSkinYRes(dom_skins[-1][1])
Log.i("Skin resultion is %s" %(yres,))
if yres > 0:
	skin_default_specific = 'skin_default_%s.xml' %yres
	try:
		loadSkin(skin_default_specific)
	except (SkinError, IOError, AssertionError), err:
		Log.w("Not loading %s %s" %(skin_default_specific,err))

profile("LoadSkinDefault")
loadSkin('skin_default.xml')
profile("LoadSkinDefaultDone")


def parsePercent(val, base):
	return int(float(val.replace("%", "")) / 100.0 * base)

def evalPos(pos, wsize, ssize, scale):
	if pos == "center":
		pos = (ssize - wsize) / 2
	elif pos == "max":
		pos = ssize - wsize
	elif pos.endswith("%"):
		pos = parsePercent(pos, ssize)
	else:
		pos = int(pos) * scale[0] / scale[1]
	return int(pos)

def getParentSize(desktop, guiObject):
	parent_size = None
	if guiObject is not None:
		parent_size = guiObject.parentCsize()
		if parent_size.isEmpty() and desktop is not None:
			parent_size = desktop.size()
	else:
		parent_size = desktop.size()
	return parent_size

def translateVariable(value):
	match = re_search("{{(.*)}}", value)
	if match and len(match.groups()) == 1:
		key = match.group(1)
		val = skinGlobals.get(key, value)
		Log.i("%s => %s" %(key, val))
		return val
	return value

def parsePosition(value, scale, desktop = None, guiObject = None):
	value = translateVariable(value)
	p = value.split(',')
	x, y = p[0], p[1]
	wsize = 1, 1
	ssize = 1, 1

	size = parent_size = None
	if guiObject:
		size = guiObject.csize()
		parent_size = getParentSize(desktop, guiObject)

	if parent_size is not None and not parent_size.isEmpty():
		ssize = parent_size.width(), parent_size.height()
	if size is not None:
		wsize = size.width(), size.height()

	x = evalPos(x, wsize[0], ssize[0], scale[0])
	y = evalPos(y, wsize[1], ssize[1], scale[1])

	if len(p) == 4:
		x = x + int(p[2])
		y = y + int(p[3])

	return ePoint(x, y)

def parseSize(value, scale, desktop = None, guiObject = None):
	value = translateVariable(value)
	x, y = value.split(',')
	if guiObject is not None:
		parent_size = getParentSize(desktop, guiObject)
		#width aliases
		if x.endswith("%"):
			x = parsePercent(x, parent_size.width())
		elif x == "fill_parent":
			x = parent_size.width()
		#height aliases
		if y.endswith("%"):
			y = parsePercent(y, parent_size.height())
		elif y == "fill_parent":
			y = parent_size.height()
	return eSize(int(x) * scale[0][0] / scale[0][1], int(y) * scale[1][0] / scale[1][1])

def parseFont(str, scale):
	name, size = str.split(';')
	return gFont(name, int(size) * scale[0][0] / scale[0][1])

def parseColor(str):
	if str[0] != '#':
		try:
			return colorNames[str]
		except:
			raise SkinError("color '%s' must be #aarrggbb or valid named color" % (str))
	return gRGB(int(str[1:], 0x10))

def parseValue(str):
	try:
		return int(str)
	except:
		raise SkinError("value '%s' is not integer" % (str))

def collectAttributes(skinAttributes, node, skin_path_prefix=None, ignore=[]):
	# walk all attributes
	for a in node.items():
		#print a
		attrib = a[0]
		value = a[1]

		if attrib in ("pixmap", "pointer", "seek_pointer", "progress_pointer", "backgroundPixmap", "selectionPixmap", "scrollbarSliderPicture", "scrollbarSliderBackgroundPicture", "scrollbarValuePicture"):
			value = resolveFilename(SCOPE_SKIN_IMAGE, value, path_prefix=skin_path_prefix)

		if attrib not in ignore:
			skinAttributes.append((attrib, value.encode("utf-8")))

def loadPixmap(path, desktop, size=eSize()):
	cached = False
	option = path.find("#")
	if option != -1:
		options = path[option+1:].split(',')
		path = path[:option]
		cached = "cached" in options
	ptr = LoadPixmap(path, desktop, cached, size=size)
	if ptr is None:
		raise SkinError("pixmap file %s not found!" % (path))
	return ptr

def applySingleAttribute(guiObject, desktop, attrib, value, scale = ((1,1),(1,1))):
	# and set attributes
	try:
		if attrib == 'position':
			guiObject.move(parsePosition(value, scale, desktop, guiObject))
		elif attrib == 'size':
			guiObject.resize(parseSize(value, scale, desktop, guiObject))
		elif attrib == 'title':
			guiObject.setTitle(_(value))
		elif attrib == 'text':
			guiObject.setText(_(value))
		elif attrib == 'font':
			guiObject.setFont(parseFont(value, scale))
		elif attrib == 'zPosition':
			guiObject.setZPosition(int(value))
		elif attrib == 'itemHeight':
			guiObject.setItemHeight(int(value))
		elif attrib == 'itemWidth':
			guiObject.setItemWidth(int(value))
		elif attrib == 'mode':
			mode = {'vertical' : eListbox.layoutVertical,
					'grid' : eListbox.layoutGrid,
					'horizontal' : eListbox.layoutHorizontal
				}[value]
			guiObject.setMode(mode)
		elif attrib == 'margin':
			leftRight, topBottom = [int(x) for x in value.split(",")]
			guiObject.setMargin(ePoint(leftRight, topBottom))
		elif attrib == 'selectionZoom':
			guiObject.setSelectionZoom(float(value))
		elif attrib in ("pixmap", "backgroundPixmap", "selectionPixmap", "scrollbarSliderPicture", "scrollbarSliderBackgroundPicture", "scrollbarValuePicture"):
			if attrib == "pixmap" and value.endswith("svg"):
				ptr = loadPixmap(value, desktop, guiObject.size())
			else:
				try:
					ptr = loadPixmap(value, desktop) # this should already have been filename-resolved.
				except SkinError:
					s = value.split('/')
					if attrib == "pixmap" and len(s) > 2 and s[-2] == 'menu' and s[-1].endswith("png"):
						Log.w("Please fix the skin... try .svg now");
						value2 = value[:-3]
						value2 += 'svg'
						ptr = loadPixmap(value2, desktop, guiObject.size())
					else:
						raise
			if attrib == "pixmap":
				guiObject.setPixmap(ptr)
			elif attrib == "backgroundPixmap":
				guiObject.setBackgroundPicture(ptr)
			elif attrib == "selectionPixmap":
				guiObject.setSelectionPicture(ptr)
			elif attrib == "scrollbarSliderPicture":
				guiObject.setScrollbarSliderPicture(ptr)
			elif attrib == "scrollbarSliderBackgroundPicture":
				guiObject.setScrollbarSliderBackgroundPicture(ptr)
			elif attrib == "scrollbarValuePicture":
				guiObject.setScrollbarValuePicture(ptr)
			# guiObject.setPixmapFromFile(value)
		elif attrib in ("alphatest", "blend"): # used by ePixmap
			guiObject.setAlphatest(
				{ "on": 1,
				  "off": 0,
				  "blend": 2,
				}[value])
		elif attrib == "scale":
			value = {
				"off" :  ePixmap.SCALE_TYPE_NONE,
				"none" :  ePixmap.SCALE_TYPE_NONE,
				"on" :  ePixmap.SCALE_TYPE_ASPECT,
				"aspect" : ePixmap.SCALE_TYPE_ASPECT,
				"center" : ePixmap.SCALE_TYPE_CENTER,
				"width" : ePixmap.SCALE_TYPE_WIDTH,
				"height" : ePixmap.SCALE_TYPE_HEIGHT,
				"stretch" : ePixmap.SCALE_TYPE_STRETCH,
				"fill" : ePixmap.SCALE_TYPE_FILL,
			}.get(value, ePixmap.SCALE_TYPE_ASPECT)
			guiObject.setScale(value)
		elif attrib == "orientation": # used by eSlider
			try:
				guiObject.setOrientation(*
					{ "orVertical": (guiObject.orVertical, False),
						"orTopToBottom": (guiObject.orVertical, False),
						"orBottomToTop": (guiObject.orVertical, True),
						"orHorizontal": (guiObject.orHorizontal, False),
						"orLeftToRight": (guiObject.orHorizontal, False),
						"orRightToLeft": (guiObject.orHorizontal, True),
					}[value])
			except KeyError:
				print "oprientation must be either orVertical or orHorizontal!"
		elif attrib == "valign":
			try:
				guiObject.setVAlign(
					{ "top": guiObject.alignTop,
						"center": guiObject.alignCenter,
						"bottom": guiObject.alignBottom,
						"centerOrBottom" : guiObject.alignCenterOrBottom
					}[value])
			except KeyError:
				print "valign must be either top, center, bottom or centerOrBottom!"
		elif attrib == "halign":
			try:
				guiObject.setHAlign(
					{ "left": guiObject.alignLeft,
						"center": guiObject.alignCenter,
						"right": guiObject.alignRight,
						"block": guiObject.alignBlock,
						"centerOrRight": guiObject.alignCenterOrRight
					}[value])
			except KeyError:
				print "halign must be either left, center, right, block or centerOrRight!"
		elif attrib == "flags":
			flags = value.split(',')
			for f in flags:
				try:
					fv = eWindow.__dict__[f]
					guiObject.setFlag(fv)
				except KeyError:
					print "illegal flag %s!" % f
		elif attrib == "padding":
			guiObject.setPadding(parsePosition(value, scale))
		elif attrib in ("radius", "cornerRadius"):
			guiObject.setCornerRadius(int(value))
		elif attrib == "gradient":
			values = value.split(',')
			direction = {
				"horizontal" : ePixmap.GRADIENT_HORIZONTAL,
				"vertical" : ePixmap.GRADIENT_VERTICAL,
				"horizontalCentered" : ePixmap.GRADIENT_HORIZONTAL_CENTERED,
				"verticalCentered" : ePixmap.GRADIENT_VERTICAL_CENTERED,
			}.get(values[2], ePixmap.GRADIENT_VERTICAL)
			guiObject.setGradient(parseColor(values[0]), parseColor(values[1]), direction)
		elif attrib == "backgroundColor":
			guiObject.setBackgroundColor(parseColor(value))
		elif attrib == "backgroundColorSelected":
			guiObject.setBackgroundColorSelected(parseColor(value))
		elif attrib == "foregroundColor":
			guiObject.setForegroundColor(parseColor(value))
		elif attrib == "foregroundColorSelected":
			guiObject.setForegroundColorSelected(parseColor(value))
		elif attrib == "shadowColor":
			guiObject.setShadowColor(parseColor(value))
		elif attrib == "selectionDisabled":
			guiObject.setSelectionEnable(0)
		elif attrib == "transparent":
			guiObject.setTransparent(int(value))
		elif attrib == "borderColor":
			guiObject.setBorderColor(parseColor(value))
		elif attrib == "borderWidth":
			guiObject.setBorderWidth(int(value))
		elif attrib == "scrollbarSliderBorderWidth":
			guiObject.setScrollbarSliderBorderWidth(int(value))
		elif attrib == "scrollbarWidth":
			guiObject.setScrollbarWidth(int(value))
		elif attrib == "scrollbarBackgroundPixmapTopHeight":
			guiObject.setScrollbarBackgroundPixmapTopHeight(int(value))
		elif attrib == "scrollbarBackgroundPixmapBottomHeight":
			guiObject.setScrollbarBackgroundPixmapBottomHeight(int(value))
		elif attrib == "scrollbarValuePixmapTopHeight":
			guiObject.setScrollbarValuePixmapTopHeight(int(value))
		elif attrib == "scrollbarValuePixmapBottomHeight":
			guiObject.setScrollbarValuePixmapBottomHeight(int(value))
		elif attrib == "scrollbarMode":
			guiObject.setScrollbarMode(
				{ "showOnDemand": guiObject.showOnDemand,
					"showAlways": guiObject.showAlways,
					"showNever": guiObject.showNever
				}[value])
		elif attrib == "enableWrapAround":
			guiObject.setWrapAround(True)
		elif attrib == "backlogMode":
			guiObject.setBacklogMode(True)
		elif attrib == "pointer" or attrib == "seek_pointer" or attrib == "progress_pointer":
			(name, pos) = value.split(':')
			pos = parsePosition(pos, scale)
			ptr = loadPixmap(name, desktop)
			guiObject.setPointer({"pointer": 0, "seek_pointer": 1, "progress_pointer": 2}[attrib], ptr, pos)
		elif attrib == 'shadowOffset':
			guiObject.setShadowOffset(parsePosition(value, scale))
		elif attrib == 'noWrap':
			guiObject.setNoWrap(1)
		elif attrib == 'id':
			pass
		else:
			print "WARNING!!!!: unsupported skin attribute " + attrib + "=" + value
	except int:
# AttributeError:
		print "widget %s (%s) doesn't support attribute %s!" % ("", guiObject.__class__.__name__, attrib)

def applyAllAttributes(guiObject, desktop, attributes, scale, skipZPosition=False):
	size_key = 'size'
	pos_key = 'position'
	zpos_key = 'zPosition'
	pixmap_key = 'pixmap'
	background_key = 'backgroundColor'
	roundedlabel_key = 'roundedlabelColor'

	size_val = pos_val = pixmap_val = background_val = None
	for (attrib, value) in attributes:
		if attrib == pos_key:
			pos_val = value
		elif attrib == size_key:
			size_val = value
		#SVG's really should be scaled at load-time and not by the GPU, so we handle that exception
		elif attrib == pixmap_key and value.endswith("svg"):
			pixmap_val = value
		elif attrib == background_key:
			if not background_val: #prioritize roundedlabelColor so merlin stuff keeps working
				background_val = value
		elif attrib == roundedlabel_key:
			background_val = value
		elif skipZPosition and attrib == zpos_key:
			pass
		else:
			applySingleAttribute(guiObject, desktop, attrib, value, scale)

	if background_val is not None:
		applySingleAttribute(guiObject, desktop, background_key, background_val, scale)
	#relative positioning only works if we have the sized the widget before positioning
	if size_val is not None:
		applySingleAttribute(guiObject, desktop, size_key, size_val, scale)
	if pos_val is not None:
		applySingleAttribute(guiObject, desktop, pos_key, pos_val, scale)
	if pixmap_val is not None:
		applySingleAttribute(guiObject, desktop, pixmap_key, pixmap_val, scale)

def loadSingleSkinData(desktop, skin, path_prefix):
	"""loads skin data like colors, windowstyle etc."""
	assert skin.tag == "skin", "root element in skin must be 'skin'!"

	#print "***SKIN: ", path_prefix

	for c in skin.findall("output"):
		id = c.attrib.get('id')
		if id:
			id = int(id)
		else:
			id = 0
		if id == 0: # framebuffer
			for res in c.findall("resolution"):
				xres = int(res.get("xres", "720"))
				yres = int(res.get("yres", "576"))
				bpp = int(res.get("bpp", "32"))
				from enigma import gMainDC
				gMainDC.getInstance().setResolution(xres, yres, bpp)
				desktop.resize(eSize(xres, yres))
				break

	for c in skin.findall("colors"):
		for color in c.findall("color"):
			get_attr = color.attrib.get
			name = get_attr("name")
			color = get_attr("value")
			if name and color:
				colorNames[name] = parseColor(color)
				#print "Color:", name, color
			else:
				raise SkinError("need color and name, got %s %s" % (name, color))

	for c in skin.findall("listboxcontent"):
		for offset in c.findall("offset"):
			get_attr = offset.attrib.get
			name = get_attr("name")
			value = get_attr("value")
			if name and value:
				if name == "left":
					eListboxPythonStringContent.setLeftOffset(parseValue(value))
				elif name == "right":
					eListboxPythonStringContent.setRightOffset(parseValue(value))
				else:
					raise SkinError("got listboxcontent offset '%s'' but 'left' or 'right' is allowed only" % name)
		for font in c.findall("font"):
			get_attr = font.attrib.get
			name = get_attr("name")
			font = get_attr("font")
			if name and font:
				if name == "string":
					eListboxPythonStringContent.setFont(parseFont(font, ((1,1),(1,1))))
				elif name == "config_description":
					eListboxPythonConfigContent.setDescriptionFont(parseFont(font, ((1,1),(1,1))))
				elif name == "config_value":
					eListboxPythonConfigContent.setValueFont(parseFont(font, ((1,1),(1,1))))
				else:
					raise SkinError("got listboxcontent font '%s' but 'string', 'config_description' or 'config_value' is allowed only" % name)
		for value in c.findall("value"):
			get_attr = value.attrib.get
			name = get_attr("name")
			value = get_attr("value")
			if name and value:
				if name == "string_item_height":
					eListboxPythonStringContent.setItemHeight(parseValue(value))
				elif name == "config_item_height":
					eListboxPythonConfigContent.setItemHeight(parseValue(value))
				else:
					raise SkinError("got listboxcontent value '%s' but 'string_item_height' or 'config_item_height' is allowed only" % name)
		for cfgpm in c.findall("config"):
			onPath =  cfgpm.attrib.get("onPixmap")
			if not fileExists(onPath):
				onPath = resolveFilename(SCOPE_CURRENT_SKIN, onPath)
			offPath =  cfgpm.attrib.get("offPixmap")
			if not fileExists(offPath):
				offPath = resolveFilename(SCOPE_CURRENT_SKIN, offPath)
			pixmapSize = cfgpm.attrib.get("size")
			if pixmapSize:
				pixmapSize = parseSize(pixmapSize, ((1,1),(1,1)))
			else:
				pixmapSize = eSize()
			ConfigBoolean.setOnOffPixmaps(loadPixmap(onPath, desktop, pixmapSize), loadPixmap(offPath, desktop, pixmapSize))
	for c in skin.findall("fonts"):
		for font in c.findall("font"):
			get_attr = font.attrib.get
			filename = get_attr("filename", "<NONAME>")
			name = get_attr("name", "Regular")
			scale = get_attr("scale")
			if scale:
				scale = int(scale)
			else:
				scale = 100
			is_replacement = get_attr("replacement") and True or False
			resolved_font = resolveFilename(SCOPE_FONTS, filename, path_prefix=path_prefix)
			if not fileExists(resolved_font): #when font is not available look at current skin path
				skin_path = resolveFilename(SCOPE_CURRENT_SKIN, filename)
				if fileExists(skin_path):
					resolved_font = skin_path
			addFont(resolved_font, name, scale, is_replacement)
			#print "Font: ", resolved_font, name, scale, is_replacement

	for c in skin.findall("subtitles"):
		from enigma import eSubtitleWidget
		scale = ((1,1),(1,1))
		for substyle in c.findall("sub"):
			get_attr = substyle.attrib.get
			font = parseFont(get_attr("font"), scale)
			col = get_attr("foregroundColor")
			if col:
				foregroundColor = parseColor(col)
				haveColor = 1
			else:
				foregroundColor = gRGB(0xFFFFFF)
				haveColor = 0
			col = get_attr("shadowColor")
			if col:
				shadowColor = parseColor(col)
			else:
				shadowColor = gRGB(0)
			shadowOffset = parsePosition(get_attr("shadowOffset"), scale)
			face = eSubtitleWidget.__dict__[get_attr("name")]
			eSubtitleWidget.setFontStyle(face, font, haveColor, foregroundColor, shadowColor, shadowOffset)

	for windowstyle in skin.findall("windowstyle"):
		style = eWindowStyleSkinned()
		id = windowstyle.attrib.get("id")
		if id:
			id = int(id)
		else:
			id = 0
		#print "windowstyle:", id

		# defaults
		font = gFont("Regular", 20)
		offset = eSize(20, 5)

		for title in windowstyle.findall("title"):
			get_attr = title.attrib.get
			offset = parseSize(get_attr("offset"), ((1,1),(1,1)))
			font = parseFont(get_attr("font"), ((1,1),(1,1)))

		style.setTitleFont(font);
		style.setTitleOffset(offset)
		#print "  ", font, offset

		for borderset in windowstyle.findall("borderset"):
			bsName = str(borderset.attrib.get("name"))
			for pixmap in borderset.findall("pixmap"):
				get_attr = pixmap.attrib.get
				bpName = get_attr("pos")
				if "filename" in pixmap.attrib:
					filename = get_attr("filename")
					if filename and bpName:
						png = loadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, filename, path_prefix=path_prefix), desktop)
						style.setPixmap(eWindowStyleSkinned.__dict__[bsName], eWindowStyleSkinned.__dict__[bpName], png)
				elif "color" in pixmap.attrib:
					color = parseColor(get_attr("color"))
					size = int(get_attr("size"))
					Log.w("%s: %s @ %s" %(bpName, color.argb(), size))
					style.setColorBorder(eWindowStyleSkinned.__dict__[bsName], eWindowStyleSkinned.__dict__[bpName], color, size)

		for color in windowstyle.findall("color"):
			get_attr = color.attrib.get
			colorType = get_attr("name")
			color = parseColor(get_attr("color"))
			try:
				style.setColor(eWindowStyleSkinned.__dict__["col" + colorType], color)
			except:
				raise SkinError("Unknown color %s" % (colorType))

		for listfont in windowstyle.findall("listfont"):
			get_attr = listfont.attrib.get
			fontType = get_attr("type")
			fontSize = int(get_attr("size"))
			fontFace = get_attr("font")
			try:
				Log.i("########### ADDING %s: %s" %(fontType, fontSize))
				style.setListFont(eWindowStyleSkinned.__dict__["listFont" + fontType], fontSize, fontFace)
			except:
				raise SkinError("Unknown listFont %s" % (fontType))

		x = eWindowStyleManager.getInstance()
		x.setStyle(id, style)

	for windowstylescrollbar in skin.findall("windowstylescrollbar"):
		style = eWindowStyleScrollbar()
		id = windowstylescrollbar.attrib.get("id")
		if id:
			id = int(id)
		else:
			id = 4
		for value in windowstylescrollbar.findall("value"):
			get_attr = value.attrib.get
			vType = get_attr("name")
			v = get_attr("value")
			if vType in ("BackgroundPixmapTopHeight", "BackgroundPixmapBeginSize"):
				style.setBackgroundPixmapTopHeight(int(v))
			elif vType in ("BackgroundPixmapBottomHeight", "BackgroundPixmapEndSize"):
				style.setBackgroundPixmapBottomHeight(int(v))
			elif vType in ("ValuePixmapTopHeight", "ValuePixmapBeginSize"):
				style.setValuePixmapTopHeight(int(v))
			elif vType in ("ValuePixmapBottomHeight", "ValuePixmapEndSize"):
				style.setValuePixmapBottomHeight(int(v))
			elif vType == "ScrollbarWidth":
				style.setScrollbarWidth(int(v))
			elif vType == "ScrollbarBorderWidth":
				style.setScrollbarBorderWidth(int(v))
		for pixmap in windowstylescrollbar.findall("pixmap"):
			get_attr = pixmap.attrib.get
			vType = get_attr("name")
			filename = get_attr("filename")
			if filename:
				if vType == "BackgroundPixmap":
					png = loadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, filename, path_prefix=path_prefix), desktop)
					style.setBackgroundPixmap(png)
				elif vType == "ValuePixmap":
					png = loadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, filename, path_prefix=path_prefix), desktop)
					style.setValuePixmap(png)
		x = eWindowStyleManager.getInstance()
		x.setStyle(id, style)

	for g in skin.findall("globals"):
		for value in g.findall("value"):
			Log.i("Global skin value : %s" %(value.attrib,))
			skinGlobals[value.attrib["name"]] = value.attrib["value"]

	for components in skin.findall("components"):
		for component in components.findall("component"):
			componentSizes.apply(component.attrib)
			for template in component.findall("template"):
				componentSizes.addTemplate(component.attrib, template.text)

	for l in skin.findall("layouts"):
		for layout in l.findall("layout"):
			layouts.apply(layout)

def loadSkinData(desktop):
	skins = dom_skins[:]
	skins.reverse()
	for (path, dom_skin) in skins:
		loadSingleSkinData(desktop, dom_skin, path)

def lookupScreen(name, style_id):
	for (path, skin) in dom_skins:
		# first, find the corresponding screen element
		for x in skin.findall("screen"):
			if x.attrib.get('name', '') == name:
				screen_style_id = x.attrib.get('id', '-1')
				if screen_style_id == '-1' and name.find('ummary') > 0:
					screen_style_id = '1'
				if (style_id != 2 and int(screen_style_id) == -1) or int(screen_style_id) == style_id:
					return x, path
	return None, None

class WidgetGroup():
	def __init__(self, screen):
		self.children = []
		self._screen = screen
		self.visible = 1

	def append(self, child):
		self.children.append(child)

	def hide(self):
		self.visible = 0
		for child in self.children:
			if isinstance(child, additionalWidget):
				child.instance.hide()
			elif isinstance(child, basestring):
				self._screen[child].hide()
			else:
				child.hide()

	def show(self):
		self.visible = 1
		for child in self.children:
			if isinstance(child, additionalWidget):
				child.instance.show()
			elif isinstance(child, basestring):
				self._screen[child].show()
			else:
				child.show()

	def execBegin(self):
		pass

	def execEnd(self):
		pass

	def destroy(self):
		pass

class additionalWidget:
	pass

class Layouts():
	def __init__(self):
		self.layouts = {}

	def __getitem__(self, key):
		return key in self.layouts and self.layouts[key] or {}

	def apply(self, node):
		get_attr = node.attrib.get
		key = get_attr("name")
		filename = get_attr("filename")
		if filename:
			xml_filename = resolveFilename(SCOPE_SKIN_IMAGE, filename)
			node = xml.etree.cElementTree.parse(xml_filename).getroot()
		self.layouts[key] = node.getchildren()

layouts = Layouts()

class ComponentSizes():
	CONFIG_LIST = "ConfigList"
	CHOICELIST = "ChoiceList"
	FILE_LIST = "FileList"
	MULTI_FILE_SELECT_LIST = "MultiFileSelectList"
	HELP_MENU_LIST = "HelpMenuList"
	PARENTAL_CONTROL_LIST = "ParentalControlList"
	SELECTION_LIST = "SelectionList"
	SERVICE_LIST = "ServiceList"
	SERVICE_INFO_LIST = "ServiceInfoList"
	TIMER_LIST = "TimerList"
	MOVIE_LIST = "MovieList"
	NIM_SETUP = "NimSetup"
	TIMELINE_TEXT = "TimelineText"
	MENU_PIXMAP = "MenuPixmap"
	ITEM_HEIGHT = "itemHeight"
	ITEM_WIDTH = "itemWidth"
	TEMPLATE = "template"
	TEXT_X = "textX"
	TEXT_Y = "textY"
	TEXT_WIDTH = "textWidth"
	TEXT_HEIGHT = "textHeight"
	PIXMAP_X = "pixmapX"
	PIXMAP_Y = "pixmapY"
	PIXMAP_WIDTH = "pixmapWidth"
	PIXMAP_HEIGHT = "pixmapHeight"

	def __init__(self, style_id = 0):
		self.components = {}

	def apply(self, attribs):
		values = {}
		key = None
		for a in attribs.items():
			if a[0] == "type":
				key = a[1]
			else:
				values[a[0]] = int(a[1])
		if key:
			self.components[key] = values

	def addTemplate(self, attribs, template):
		key = attribs.get("type", None)
		if key:
			self.components[key][self.TEMPLATE] = template.strip()

	def __getitem__(self, component_id):
		return component_id in self.components and self.components[component_id] or {}

	def itemHeight(self, component_id, default=None):
		val = component_id in self.components and self.components[component_id].get(self.ITEM_HEIGHT, default) or default
		if not val:
			val = 30 #30 is quite random, I went for a small value because that would probably fit most of the time
			Log.w("No itemWidth set for %s and default is %s falling back to %s") %(component_id, str(default), val)
		return val

	def itemWidth(self, component_id, default=None):
		val = component_id in self.components and self.components[component_id].get(self.ITEM_WIDTH, default) or default
		if not val:
			val = 30 #30 is quite random, I went for a small value because that would probably fit most of the time
			Log.w("No itemWidth set for %s and default is %s falling back to %s") %(component_id, str(default), val)
		return val

	def template(self, component_id):
		return component_id in self.components and self.components[component_id].get(self.TEMPLATE, None) or None

componentSizes = ComponentSizes()

def readSkin(screen, skin, names, desktop):
	if not isinstance(names, list):
		names = [names]

	name = "<embedded-in-'%s'>" % screen.__class__.__name__

	style_id = desktop.getStyleID();

	# try all skins, first existing one have priority
	for n in names:
		myscreen, path = lookupScreen(n, style_id)
		if myscreen is not None:
			# use this name for debug output
			name = n
			break

	# otherwise try embedded skin
	if myscreen is None:
		myscreen = getattr(screen, "parsedSkin", None)

	# try uncompiled embedded skin
	if myscreen is None and getattr(screen, "skin", None):
		print "Looking for embedded skin"
		skin_tuple = screen.skin
		if not isinstance(skin_tuple, tuple):
			skin_tuple = (skin_tuple,)
		for sskin in skin_tuple:
			parsedSkin = xml.etree.cElementTree.fromstring(sskin)
			screen_style_id = parsedSkin.attrib.get('id', '-1')
			if (style_id != 2 and int(screen_style_id) == -1) or int(screen_style_id) == style_id:
				myscreen = screen.parsedSkin = parsedSkin
				break

	#assert myscreen is not None, "no skin for screen '" + repr(names) + "' found!"
	if myscreen is None:
		print "No skin to read..."
		emptySkin = "<screen></screen>"
		myscreen = screen.parsedSkin = xml.etree.cElementTree.fromstring(emptySkin)

	screen.skinAttributes = [ ]

	skin_path_prefix = getattr(screen, "skin_path", path)

	for widget in myscreen.getchildren():
		if widget.tag == "layout":
			get_attr = widget.attrib.get
			for layout in layouts[get_attr('name')]:
				myscreen.append(layout)
			myscreen.remove(widget)

	collectAttributes(screen.skinAttributes, myscreen, skin_path_prefix, ignore=["name"])

	screen.additionalWidgets = [ ]
	screen.renderer = [ ]

	visited_components = set()

	# now walk all widgets
	parseWidgets(name, myscreen, screen, skin_path_prefix, visited_components)

	from Components.GUIComponent import GUIComponent
	nonvisited_components = [x for x in set(screen.keys()) - visited_components if isinstance(x, GUIComponent)]
	assert not nonvisited_components, "the following components in %s don't have a skin entry: %s" % (name, ', '.join(nonvisited_components))

def parseWidgets(name, node, screen, skin_path_prefix, visited_components, group=None):
	for widget in node.getchildren():
		w_tag = widget.tag

		if w_tag == "group":
			gname = widget.attrib.get('name')
			assert(gname) not in screen.keys(), "element with name %s already exists in %s!" % (gname, screen.skinName)
			inner_group = WidgetGroup(screen)
			screen[gname] = inner_group
			if group is not None:
				group.append(inner_group)
			visited_components.add(gname)
			parseWidgets(name, widget, screen, skin_path_prefix, visited_components, inner_group)
			continue

		if w_tag == "widget":
			parseWidget(name, widget, screen, skin_path_prefix, visited_components, group)
			continue

		if w_tag == "applet":
			try:
				codeText = widget.text.strip()
			except:
				codeText = ""

			#print "Found code:"
			#print codeText
			widgetType = widget.attrib.get('type')

			code = compile(codeText, "skin applet", "exec")

			if widgetType == "onLayoutFinish":
				screen.onLayoutFinish.append(code)
				#print "onLayoutFinish = ", codeText
			else:
				raise SkinError("applet type '%s' unknown!" % widgetType)
				#print "applet type '%s' unknown!" % type

			continue

		w = additionalWidget()

		if w_tag == "eLabel":
			w.widget = eLabel
		elif w_tag == "ePixmap":
			w.widget = ePixmap
		else:
			raise SkinError("unsupported stuff : %s" % w_tag)
			#print "unsupported stuff : %s" % widget.tag

		w.skinAttributes = [ ]
		collectAttributes(w.skinAttributes, widget, skin_path_prefix, ignore=['name'])

		if group is not None:
			group.append(w)

		# applyAttributes(guiObject, widget, desktop)
		# guiObject.thisown = 0
		screen.additionalWidgets.append(w)

def parseWidget(name, widget, screen, skin_path_prefix, visited_components, group):
	get_attr = widget.attrib.get
	# ok, we either have 1:1-mapped widgets ('old style'), or 1:n-mapped
	# widgets (source->renderer).
	wname = get_attr('name')
	wsource = get_attr('source')

	if wname is None and wsource is None:
		print "widget has no name and no source!"
		return

	if wname:
		# print "Widget name=", wname
		visited_components.add(wname)

		# get corresponding 'gui' object
		try:
			attributes = screen[wname].skinAttributes = [ ]
			if group is not None:
				group.append(wname)
		except:
			raise SkinError("component with name '" + wname + "' was not found in skin of screen '" + name + "'!")
			# print "WARNING: component with name '" + wname + "' was not found in skin of screen '" + name + "'!"

# 			assert screen[wname] is not Source

		# and collect attributes for this
		collectAttributes(attributes, widget, skin_path_prefix, ignore=['name'])
	elif wsource and not screen.ignoreSource(wsource):
		# get corresponding source
		# print "Widget source=", wsource

		while True:  # until we found a non-obsolete source

			# parse our current "wsource", which might specifiy a "related screen" before the dot,
			# for example to reference a parent, global or session-global screen.
			scr = screen

			# resolve all path components
			path = wsource.split('.')
			while len(path) > 1:
				scr = screen.getRelatedScreen(path[0])
				if scr is None:
					# print wsource
					# print name
					raise SkinError("specified related screen '" + wsource + "' was not found in screen '" + name + "'!")
				path = path[1:]

			# resolve the source.
			source = scr.get(path[0])
			if isinstance(source, ObsoleteSource):
				# however, if we found an "obsolete source", issue warning, and resolve the real source.
				print "WARNING: SKIN '%s' USES OBSOLETE SOURCE '%s', USE '%s' INSTEAD!" % (name, wsource, source.new_source)
				print "OBSOLETE SOURCE WILL BE REMOVED %s, PLEASE UPDATE!" % (source.removal_date)
				if source.description:
					print source.description

				wsource = source.new_source
			else:
				# otherwise, use that source.
				break

		if source is None:
			raise SkinError("source '" + wsource + "' was not found in screen '" + name + "'!")

		tmp = get_attr('render').split(',')
		wrender = tmp[0]
		if tmp > 1:
			wrender_args = tmp[1:]
		else:
			wrender_args = tuple()

		if not wrender:
			raise SkinError("you must define a renderer with render= for source '%s'" % (wsource))

		for converter in widget.findall("convert"):
			ctype = converter.get('type')
			assert ctype, "'convert'-tag needs a 'type'-attribute"
			# print "Converter:", ctype
			try:
				parms = converter.text.strip()
			except:
				parms = ""
			# print "Params:", parms
			converter_class = my_import('.'.join(("Components", "Converter", ctype))).__dict__.get(ctype)

			c = None

			for i in source.downstream_elements:
				if isinstance(i, converter_class) and i.converter_arguments == parms:
					c = i

			if c is None:
				print "allocating new converter!"
				c = converter_class(parms)
				c.connect(source)
			else:
				print "reused converter!"
				hasattr(c, "reuse") and c.reuse()

			source = c

		renderer_class = my_import('.'.join(("Components", "Renderer", wrender))).__dict__.get(wrender)

		renderer = renderer_class(*wrender_args)  # instantiate renderer

		renderer.connect(source)  # connect to source
		attributes = renderer.skinAttributes = [ ]
		collectAttributes(attributes, widget, skin_path_prefix, ignore=['render', 'source'])

		screen.renderer.append(renderer)
		if group is not None:
			group.append(renderer)

class TemplatedColors():
	def __init__(self, style_id = 0):
		x = eWindowStyleManager.getInstance()
		style = x.getStyle(style_id)
		self.colors = {}
		for color_name in ("Background", "LabelForeground", "ListboxForeground", "ListboxSelectedForeground", "ListboxBackground", "ListboxSelectedBackground", "ListboxMarkedForeground", "ListboxMarkedAndSelectedForeground", "ListboxMarkedBackground", "ListboxMarkedAndSelectedBackground", "WindowTitleForeground", "WindowTitleBackground"):
			color = gRGB(0)
			style.getColor(eWindowStyleSkinned.__dict__["col"+color_name], color)
			self.colors[color_name] = color

	def __getitem__(self, color_name):
		return color_name in self.colors and self.colors[color_name] or gRGB(0)

class TemplatedListFonts():
	KEYBOARD = "Keyboard"
	BIGGER = "Bigger"
	BIG = "Big"
	MEDIUM = "Medium"
	SMALL = "Small"
	SMALLER = "Smaller"

	def __init__(self, style_id = 0):
		x = eWindowStyleManager.getInstance()
		style = x.getStyle(style_id)
		self.sizes = {}
		self.faces = {}
		for font_id in (self.BIGGER, self.BIG, self.MEDIUM, self.SMALL, self.SMALLER):
			size = int(style.getListFontSize(eWindowStyleSkinned.__dict__["listFont" + font_id]))
			face = style.getListFontFace(eWindowStyleSkinned.__dict__["listFont" + font_id])
			Log.i("%s: %s, %s" %(font_id, size, face))
			self.sizes[font_id] = size
			self.faces[font_id] = face

	def size(self, font_id, default=20):
		return font_id in self.sizes and self.sizes[font_id] or default

	def face(self, font_id, default="Regular"):
		return font_id in self.faces and self.faces[font_id] or default
