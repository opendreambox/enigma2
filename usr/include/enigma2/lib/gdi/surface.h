#ifndef __lib_gdi_surface_h
#define __lib_gdi_surface_h

#if !defined(SWIG)

#define __SURFACE_H_INSIDE__ 1

#include <lib/gdi/esize.h>
#include <lib/gdi/palette.h>
#include <lib/gdi/surface_flags.h>

#undef __SURFACE_H_INSIDE__

class gSurface
{
	gPixelFormat m_pixelFormat;
	unsigned int m_flags;
	int m_type;
	unsigned long m_phys_addr;
	bool m_valid;

public:
	int scalefilter;

	unsigned int x, y, bypp, stride;
	gPalette clut;

	void *data;
	int offset; // y-offset, only for backbuffers
	void *priv; // for accelerators

	gSurface(gPixelFormat pixelFormat, unsigned int flags);
	static gSurface *create(gPixelFormat pixelFormat, unsigned int flags, const eSize &size);
	~gSurface();

	gPixelFormat pixelFormat() const { return m_pixelFormat; }
	unsigned int flags() const { return m_flags; }
	unsigned int bpp() const { return gPixel::bitsPerPixel(m_pixelFormat); }
	bool needClut() const { return gPixel::isIndexed(m_pixelFormat); }
	eSize size() const { return eSize(x, y); }
	unsigned long physAddr() const { return m_phys_addr; }
	void setData(const eSize &size, unsigned int stride, void *data, unsigned long phys_addr = 0);
	bool valid() const { return m_valid; }
	unsigned int alignment() const;
	bool glTexture(unsigned int *glHandle, unsigned int *glTarget) const;
	void flushCache(const eRect &rect);
};

#endif /* !SWIG */

#endif /* __lib_gdi_surface_h */
