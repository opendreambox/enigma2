#ifndef __lib_gdi_gpixmap_h
#define __lib_gdi_gpixmap_h

#define __GPIXMAP_H_INSIDE__ 1

#include <lib/base/object.h>
#include <lib/gdi/esize.h>
#include <lib/gdi/gpixelformat.h>
#include <lib/gdi/matrix.h>
#include <lib/gdi/rgba.h>
#include <lib/gdi/scalefilter.h>
#include <lib/gdi/surface_flags.h>
#include <vector>

#undef __GPIXMAP_H_INSIDE__

class ePoint;
class eRect;
class gColor;
class gRegion;
class gSurface;

SWIG_IGNORE(gPixmap);
class gPixmap: public iObject
{
	DECLARE_REF(gPixmap);
	E_DISABLE_COPY(gPixmap)

	gRGBA m_invalidColor;
	gSurface *m_surface;
	bool m_glsl;

	void drawPixel8(const ePoint &pos, unsigned int pixel);
	void drawPixel16(const ePoint &pos, unsigned int pixel);
	void drawPixel24(const ePoint &pos, unsigned int pixel);
	void drawPixel32(const ePoint &pos, unsigned int pixel);
	void drawLine(const gRegion &clip, const ePoint &start, const ePoint &dst, unsigned int pixel, const eMatrix4x4 &matrix);

	void fillRect8(const eRect &area, unsigned int pixel);
	void fillRect16(const eRect &area, unsigned int pixel);
	void fillRect32(const eRect &area, unsigned int pixel);
	void fillRegion(const gRegion &region, unsigned int pixel, int flags, const eMatrix4x4 &matrix);

public:
#ifndef SWIG
	enum
	{
		blitAlphaTest=1,
		blitAlphaBlend=2,
		blitScale=4
	};

	gPixmap(gSurface *surface, bool takeOwnership = false);
	gPixmap(gPixelFormat fmt, unsigned int flags, const eSize &size);

	static ePtr<gPixmap> fromFile(const char *filename, gPixelFormat = gPixel::preferredFormat());
	static ePtr<gPixmap> fromFile(const char *filename, const eSize &dstSize, const eSize &aspect, gPixelFormat = gPixel::preferredFormat());

	bool isNull() const;
	gSurface *surface();
	const gSurface *surface() const;
	gPixelFormat pixelFormat() const;
	unsigned int flags() const;
	bool needClut() const;
	void drawPixel(const ePoint &pos, const gRGBA &color);
	bool glTexture(unsigned int *glHandle, unsigned int *glTarget) const;

    #if defined(D_ENABLE_ASSERTIONS)
	friend class gPixmapTest;
	static int selftest();
    #endif /* D_ENABLE_ASSERTIONS */
#endif
	virtual ~gPixmap();
	eSize size() const;

	const gRGBA &color(unsigned int index) const;
	unsigned int colorCount() const;
	std::vector<gRGBA> colorTable() const;
	void setColor(unsigned int index, const gRGBA &colorValue);
	void setColorCount(unsigned int colorCount);
	void setColorTable(const std::vector<gRGBA> &colors);
	void setScaleFilter(scalefilter_t scalefilter);

	enum ScaleMode {
		SimpleScale,
		ColorScale,
	};
	ePtr<gPixmap> scale(const eSize &size, enum ScaleMode mode = ColorScale) const;
	ePtr<gPixmap> read() const;

#ifndef SWIG
	const void *map() const;
	void *map();
	void unmap(const void *ptr) const;
	void unmap(void *ptr);
#endif

private:
	E_DECLARE_PRIVATE(gPixmap)

	friend class gDC;
	void fill(const gRegion &clip, const gColor &color, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void fill(const gRegion &clip, const gRGBA &color, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void fill(const std::vector<eRect> &rects, const ePoint &offset, const gColor &c, const gRegion &clip, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void fill(const std::vector<eRect> &rects, const ePoint &offset, const gRGBA &color, const gRegion &clip, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());

	void line(const gRegion &clip, const ePoint &start, const ePoint &end, const gColor &c, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void line(const gRegion &clip, const ePoint &start, const ePoint &end, const gRGBA &c, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	
	void blit(const gPixmap &src, const eRect &pos, const gRegion &clip, int flags, float alpha = 1.0, const eMatrix4x4 &matrix = eMatrix4x4::identity());

	void beginNativePainting();
	void endNativePainting();
	
	ePtr<gPixmap> colorScale(ePtr<gPixmap> &dst, const eSize &size) const;
	ePtr<gPixmap> simpleScale(ePtr<gPixmap> &dst, const eSize &size) const;

	void mergePalette(const gPixmap &target);
#ifdef SWIG
	gPixmap();
#endif
};
SWIG_TEMPLATE_TYPEDEF(ePtr<gPixmap>, gPixmapPtr);

#endif /* __lib_gdi_gpixmap_h */
