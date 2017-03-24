#ifndef __lib_gdi_surface_h
#define __lib_gdi_surface_h

#if !defined(SWIG)

#define __SURFACE_H_INSIDE__ 1

#include <lib/gdi/erect.h>
#include <lib/gdi/esize.h>
#include <lib/gdi/palette.h>
#include <lib/gdi/surface_flags.h>
#include <map>

#undef __SURFACE_H_INSIDE__

class gSurface
{
	gPixelFormat m_pixelFormat;
	unsigned int m_flags;
	int m_type;
	unsigned long m_phys_addr;
	bool m_valid;
	int m_fd;
	unsigned long m_offset;
	std::map<void *, std::pair<unsigned long, unsigned long> > m_maps;

	void *map(unsigned int flags, unsigned int *pstride, unsigned long offset, unsigned long len);
	void unmap(void *mem, unsigned long offset, unsigned long len);
	unsigned long paletteOffset() const;
	unsigned long paletteLength() const;
	unsigned long totalLength() const;

public:
	int scalefilter;

	unsigned int x, y, bypp, stride;
	gPalette clut;

	void *data;
	void *priv; // for accelerators

	gSurface(gPixelFormat pixelFormat, unsigned int flags);
	static gSurface *create(gPixelFormat pixelFormat, unsigned int flags, const eSize &size);
	~gSurface();

	gPixelFormat pixelFormat() const { return m_pixelFormat; }
	void setPixelFormat(gPixelFormat fmt);
	unsigned int flags() const { return m_flags; }
	unsigned int bpp() const { return gPixel::bitsPerPixel(m_pixelFormat); }
	bool needClut() const { return gPixel::isIndexed(m_pixelFormat); }
	eSize size() const { return eSize(x, y); }
	unsigned long physAddr() const { return m_phys_addr; }
	unsigned long palettePhysAddr() const;
	void setData(const eSize &size, unsigned int stride, void *data, unsigned long phys_addr = 0, int fd = -1, size_t offset = 0);
	bool valid() const { return m_valid; }
	unsigned int alignment() const;
	bool glTexture(unsigned int *glHandle, unsigned int *glTarget) const;
	void flushCache(const eRect &rect=eRect());
	int fd() const;
	unsigned long offset() const;
	unsigned long length() const;

	/* See surface_flags.h */
	void *map(unsigned int flags, unsigned int *stride);
	void *mapPalette(unsigned int flags, unsigned int *size);
	const void *map(unsigned int flags, unsigned int *stride) const;
	void unmap(void *mem);
	void unmap(const void *mem) const;
};

#endif /* !SWIG */

#endif /* __lib_gdi_surface_h */
