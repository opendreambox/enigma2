#ifndef __lib_gdi_gpixmap_h
#define __lib_gdi_gpixmap_h

#define __GPIXMAP_H_INSIDE__ 1

#include <lib/base/object.h>
#include <lib/gdi/esize.h>
#include <lib/gdi/gfx2d.h>
#include <lib/gdi/gpixelformat.h>
#include <lib/gdi/matrix.h>
#include <lib/gdi/rgba.h>
#include <lib/gdi/scalefilter.h>
#include <lib/gdi/surface_flags.h>
#include <vector>

#undef __GPIXMAP_H_INSIDE__

class ePoint;
class eRect;
struct gColor;
class gRegion;
class gSurface;

SWIG_IGNORE(gPixmap);
class gPixmap: public iObject, iGfx2d
{
	DECLARE_REF(gPixmap);
	E_DISABLE_COPY(gPixmap)

	gRGBA m_invalidColor;
	gSurface *m_surface;

	void drawPixel8(void *mem, unsigned int stride, const ePoint &pos, unsigned int pixel);
	void drawPixel16(void *mem, unsigned int stride, const ePoint &pos, unsigned int pixel);
	void drawPixel24(void *mem, unsigned int stride, const ePoint &pos, unsigned int pixel);
	void drawPixel32(void *mem, unsigned int stride, const ePoint &pos, unsigned int pixel);
	void drawLine(const gRegion &clip, const ePoint &start, const ePoint &dst, unsigned int pixel, const eMatrix4x4 &matrix);

public:
#ifndef SWIG
	enum
	{
		blitAlphaTest=1,
		blitAlphaBlend=2,
		blitScale=4,
		blitDestinationColorPlusZero=8,
		blitOnePlusOne=16,
		blitSourceAlphaPlusOne=32,
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
	/* See surface_flags.h */
	const void *map(unsigned int flags, unsigned int *stride) const;
	void *map(unsigned int flags, unsigned int *stride);
	void unmap(const void *ptr) const;
	void unmap(void *ptr);

	unsigned int width() const;
	unsigned int height() const;
	unsigned int stride() const;

	/* beginNativePainting and endNativePainting may only be called from inside the gRC thread */
	bool beginNativePainting();
	void endNativePainting();
#endif

private:
	E_DECLARE_PRIVATE(gPixmap)

	friend class gDC;
	friend class gLCDDC;
	friend class gSyncPainter;
	void fill(const gRegion &clip, const gColor &color, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void fill(const gRegion &clip, const gRGBA &color, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void fill(const std::vector<eRect> &rects, const ePoint &offset, const gColor &c, const gRegion &clip, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void fill(const std::vector<eRect> &rects, const ePoint &offset, const gRGBA &color, const gRegion &clip, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());

	void line(const gRegion &clip, const ePoint &start, const ePoint &end, const gColor &c, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	void line(const gRegion &clip, const ePoint &start, const ePoint &end, const gRGBA &c, int flags, const eMatrix4x4 &matrix = eMatrix4x4::identity());
	
	void blit(const gPixmap &src, const eRect &pos, const gRegion &clip, int flags, float alpha = 1.0, const eMatrix4x4 &matrix = eMatrix4x4::identity());

	ePtr<gPixmap> colorScale(ePtr<gPixmap> &dst, const eSize &size) const;
	ePtr<gPixmap> simpleScale(ePtr<gPixmap> &dst, const eSize &size) const;

	void mergePalette(const gPixmap &target);
#ifdef SWIG
	gPixmap();
#endif

	virtual ePtr<gGfx2dBlitContext> createBlitContext(gSurface *dst, const gSurface::BlitParams &p, unsigned int flags);
	virtual ePtr<gGfx2dFillContext> createFillContext(gSurface *dst, const gSurface::FillParams &p, unsigned int flags);
};
SWIG_TEMPLATE_TYPEDEF(ePtr<gPixmap>, gPixmapPtr);

#endif /* __lib_gdi_gpixmap_h */
