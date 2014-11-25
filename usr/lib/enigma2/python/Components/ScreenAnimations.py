from enigma import getDesktop, eSize, ePoint, eMatrix4x4, eFloatAnimation, ePointAnimation, eSizeAnimation, eMatrixAnimation, eLinearInterpolator, eAcclerateInterpolator, eDecelerateInterpolator, eOvershootInterpolator, eBounceInterpolator, eWindowAnimationManager, eWindowAnimationSet
from Tools.Directories import resolveFilename, fileExists, SCOPE_SKIN
from Tools.Log import Log
import xml.etree.cElementTree as ET

class ScreenAnimations(object):
	def __init__(self):
		self._desktopSize = getDesktop(0).size()

	def loadDefault(self):
		animset = eWindowAnimationSet.create()
		animset.setKey(eWindowAnimationManager.KEY_DISABLED)
		animset.setName(_("Disable Animations"))
		eWindowAnimationManager.setAnimationSet(animset)
		f = resolveFilename(SCOPE_SKIN, "animations.xml")
		if fileExists(f):
			self.fromXML(filesource=f)

	def fromXML(self, filesource=None, xml=None):
		if filesource:
			root = ET.parse(filesource).getroot()
		else:
			root = ET.fromstring(xml)
		for animation in root:
			try:
				attrib = animation.attrib
				key = attrib["key"]
				name = _(attrib.get("title", key))
				internal = "internal" in attrib
				duration = int(attrib.get("duration", 0))
				alpha = pos = size = matrix = 0
				alpha_hide = pos_hide = size_hide = rotate_hide = 0

				for item in animation:
					if item.tag == "alpha":
						alpha = self._buildFloatAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "position":
						pos = self._buildPointAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "size":
						size = self._buildSizeAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "rotate":
						matrix = self._buildMatrixAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "alpha_hide":
						alpha_hide = self._buildFloatAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "position_hide":
						pos_hide = self._buildPointAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "size_hide":
						size_hide = self._buildSizeAnimation(item, duration, self._buildInterpolator(attrib))
					elif item.tag == "rotate_hide":
						rotate_hide = self._buildMatrixAnimation(item, duration, self._buildInterpolator(attrib))

				if alpha or pos or size or matrix or alpha_hide or pos_hide or size_hide or rotate_hide:
					animset = eWindowAnimationSet.create()
					animset.setKey(key)
					animset.setName(name)
					animset.setInternal(internal)
					if alpha:
						animset.setAlpha(alpha)
					if pos:
						animset.setPos(pos)
					if size:
						animset.setSize(size)
					if matrix:
						animset.setMatrix(matrix)
					if alpha_hide:
						animset.setAlphaReverse(alpha_hide)
					if pos_hide:
						animset.setPosReverse(pos_hide)
					if size_hide:
						animset.setSizeReverse(size_hide)
					if rotate_hide:
						animset.setMatrixReverse(rotate_hide)
					eWindowAnimationManager.setAnimationSet(animset)

			except Exception as ex:
				Log.w("FAILED to parse an xml defined animation! %s: %s\n%s" %(animation.tag, animation.attrib, ex))

#eLinearInterpolator()
#eAcclerateInterpolator(float factor)
#eDecelerateInterpolator(float factor)
#eOvershootInterpolator(float tension = 2.0)
#eBounceInterpolator()
	def _buildInterpolator(self, attrib):
		interpolator = eLinearInterpolator.create() #boring linear is the default
		key = attrib.get("interpolate", "linear")
		if key == "accelerate":
			if "factor" in attrib:
				interpolator = eAcclerateInterpolator.create( float(attrib["factor"]) )
			else:
				interpolator = eAcclerateInterpolator.create()
		elif key == "decelerate":
			if "factor" in attrib:
				interpolator = eDecelerateInterpolator.create( float(attrib["factor"]) )
			else:
				interpolator = eDecelerateInterpolator.create()
		elif key == "overshoot":
			if "tension" in attrib:
				interpolator = eOvershootInterpolator.create( float(attrib["tension"]) )
			else:
				interpolator = eOvershootInterpolator.create()
		elif key == "bounce":
			interpolator = eBounceInterpolator.create()

		return interpolator

#eFloatAnimation(int64_t duration, float from, float to, bool reversed = false, ePtr<eProgressInterpolator> interpolator=0)
	def _buildFloatAnimation(self, item, duration, interpolator=0):
		attrs = item.attrib
		if "interpolate" in attrs:
			interpolator = self._buildInterpolator(attrs)
		isReverse = item.tag == "alpha_hide"
		fromValue = float(attrs["val"])
		toValue = 1.0
		if isReverse:
			return eFloatAnimation.create(duration, toValue, fromValue, False, interpolator)
		else:
			return eFloatAnimation.create(duration, fromValue, toValue, False, interpolator)

#ePointAnimation(int64_t duration, ePoint from, ePoint to, bool reversed = false, ePtr<eProgressInterpolator> interpolator=0, bool isReverse=false, bool animateX=true, bool animateY=true)
	def _buildPointAnimation(self, item, duration, interpolator=0):
		attrs = item.attrib
		if "interpolate" in attrs:
			interpolator = self._buildInterpolator(attrs)
		isReverse = item.tag == "position_hide"
		animateX = "animateX" in attrs
		animateY = "animateY" in attrs
		if not animateX and not animateY:
			animateX = animateY = True

		value = float(attrs["val"])
		x = int( self._desktopSize.width() * value )
		y = int( self._desktopSize.height() * value )

		if(isReverse):
			fromPos = ePoint()
			toPos = ePoint(x,y)
		else:
			fromPos = ePoint(x,y)
			toPos = ePoint()
		return ePointAnimation.create(duration, fromPos, toPos, False, interpolator, isReverse, animateX, animateY)

#eSizeAnimation(int64_t duration, eSize from, eSize to, bool reversed = false, ePtr<eProgressInterpolator> interpolator=0)
	def _buildSizeAnimation(self, item, duration, interpolator=0):
		attrs = item.attrib
		if "interpolate" in attrs:
			interpolator = self._buildInterpolator(attrs)
		isReverse = item.tag == "size_hide"
		animateW = "animateW" in attrs
		animateH = "animateH" in attrs
		centered = "centered" in attrs
		if not animateW and not animateH:
			animateW = animateH = True
		w, h = attrs["val"].split(",")
		w, h = int(w), int(h)
		fromSize = eSize(w,h)
		toSize = eSize()
		return eSizeAnimation.create(duration, fromSize, toSize, False, interpolator, isReverse, animateW, animateH, centered)

#eMatrixAnimation(int64_t duration, eMatrix4x4 from, eMatrix4x4 to, bool reversed = false, ePtr<eProgressInterpolator> interpolator=0)
	def _buildMatrixAnimation(self, item, duration, interpolator=0):
		attrs = item.attrib
		if "interpolate" in attrs:
			interpolator = self._buildInterpolator(attrs)
		x,y,z = float(attrs.get("x", "0")), float(attrs.get("y", "0")), float(attrs.get("z", "0"))
		fromMatrix = eMatrix4x4.rotateX(x) * eMatrix4x4.rotateY(y)#z axis rotation is currently not suported * eMatrix4x4.rotateZ(z)
		toMatrix = eMatrix4x4.identity()
		return eMatrixAnimation.create(duration, fromMatrix, toMatrix, False, interpolator)
