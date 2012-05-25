#ifndef __gpixmap_h
#define __gpixmap_h

#include <pthread.h>
#include <string>
#include <vector>
#include <lib/base/object.h>
#include <lib/base/smartptr.h>
#include <lib/base/elock.h>
#include <lib/gdi/erect.h>
#include <lib/gdi/fb.h>

class QBrush;
class QColor;
class QImage;
typedef unsigned int QRgb;

class gRGB
{
public:
	unsigned char b, g, r, a;
	gRGB(int r, int g, int b, int a=0): b(b), g(g), r(r), a(a)
	{
	}
	gRGB(unsigned int val): b(val&0xFF), g((val>>8)&0xFF), r((val>>16)&0xFF), a((val>>24)&0xFF)		// ARGB
	{
	}
	gRGB(): b(0), g(0), r(0), a(0)
	{
	}

#if defined(HAVE_QT) && !defined(SWIG)
	gRGB(const QBrush &);
	gRGB(const QColor &);
	operator QBrush() const;
	operator QColor() const;
	operator QRgb() const;
#endif

	unsigned int argb() const
	{
		return (a<<24)|(r<<16)|(g<<8)|b;
	}

	void operator=(unsigned int val)
	{
		b = val&0xFF;
		g = (val>>8)&0xFF;
		r = (val>>16)&0xFF;
		a = (val>>24)&0xFF;
	}
	bool operator < (const gRGB &c) const
	{
		if (b < c.b)
			return 1;
		if (b == c.b)
		{
			if (g < c.g)
				return 1;
			if (g == c.g)
			{
				if (r < c.r)
					return 1;
				if (r == c.r)
					return a < c.a;
			}
		}
		return 0;
	}
	bool operator==(const gRGB &c) const
	{
		return (b == c.b) && (g == c.g) && (r == c.r) && (a == c.a);
	}
};

#ifndef SWIG
struct gColor
{
	int color;
	gColor(int color): color(color)
	{
	}
	gColor(): color(0)
	{
	}
	operator int() const { return color; }
	bool operator==(const gColor &o) const { return o.color==color; }
};

class gPalette
{
	friend class gDC;
	friend class gDirectFBDC;
	friend class gFBDC;
	friend class gSDLDC;
	friend class gPainter;
	friend class gPixmap;

	std::vector<gRGB> m_colorTable;

	void setColorCount(int colorCount)
	{
		if (colorCount >= 0)
			m_colorTable.resize(colorCount);
	}

	void setColor(int index, const gRGB &colorValue)
	{
		if ((index >= 0) && (index < colorCount()))
			m_colorTable[index] = colorValue;
	}

	void setColorTable(const std::vector<gRGB> &colors)
	{
		m_colorTable = colors;
	}

public:
	gPalette()
	{
	}

	gPalette(const gPalette &p) :
		m_colorTable(p.m_colorTable)
	{
	}

	gColor findColor(const gRGB &rgb) const;

	gRGB color(int index) const
	{
		if ((index >= 0) && (index < colorCount()))
			return m_colorTable[index];

		return gRGB();
	}

	int colorCount() const
	{
		return m_colorTable.size();
	}

	std::vector<gRGB> colorTable() const
	{
		return m_colorTable;
	}
};

struct gLookup
{
	int size;
	gColor *lookup;
	gLookup(int size, const gPalette &pal, const gRGB &start, const gRGB &end);
	gLookup();
	~gLookup() { delete [] lookup; }
	void build(int size, const gPalette &pal, const gRGB &start, const gRGB &end);
};

typedef enum
{
    ARGB, ABGR, RGBA, BGRA, INDEXED
} colorformat_t;

typedef enum
{
    DISABLED, BILINEAR, ANISOTROPIC,
    SHARP, SHARPER, BLURRY, ANTI_FLUTTER,
    ANTI_FLUTTER_BLURRY, ANTI_FLUTTER_SHARP
} scalefilter_t;
#endif

#ifndef SWIG
struct gSurface
{
	colorformat_t colorformat;
	bool premult;	// premultiplied alpha
	scalefilter_t scalefilter;

	int type;
	int x, y, bpp, bypp, stride;
	gPalette clut;

	void *data;
	int data_phys;
	int offset; // only for backbuffers

	gSurface();
	gSurface(eSize size, int bpp, int accel, bool premult = false);
	~gSurface();
};
#endif

class gRegion;

SWIG_IGNORE(gPixmap);
class gPixmap: public iObject
{
	DECLARE_REF(gPixmap);
	E_DISABLE_COPY(gPixmap)

	eSize m_scale_size;
public:
#ifndef SWIG
	enum
	{
		blitAlphaTest=1,
		blitAlphaBlend=2,
		blitScale=4
	};

	gPixmap(gSurface *surface);
	gPixmap(eSize, int bpp, int accel = 0, bool premult = false);

#if defined(HAVE_QT) && !defined(SWIG)
	gPixmap(const char *filename, const char *format = 0);
	QImage &toQImage();
#endif

	bool isNull() const;
	gSurface *surface;
	int final;

	inline bool needClut() const { return surface && surface->bpp <= 8; }
#endif
	virtual ~gPixmap();
	eSize size() const { return eSize(surface->x, surface->y); }
	const eSize &scaleSize() const { return m_scale_size; }

	gRGB color(int index) const;
	int colorCount() const;
	std::vector<gRGB> colorTable() const;
	void setColor(int index, const gRGB &colorValue);
	void setColorCount(int colorCount);
	void setColorTable(const std::vector<gRGB> &colors);
	void setColorFormat(colorformat_t colorformat);
	void setScaleFilter(scalefilter_t scalefilter);
	void setScaleSize(const eSize &size) { m_scale_size = size; }

private:
	E_DECLARE_PRIVATE(gPixmap)

	friend class gDC;
	void fill(const gRegion &clip, const gColor &color);
	void fill(const gRegion &clip, const gRGB &color);
	
	void blit(const gPixmap &src, const eRect &pos, const gRegion &clip, int flags=0);
	
	void mergePalette(const gPixmap &target);
	void line(const gRegion &clip, ePoint start, ePoint end, gColor color);
#ifdef SWIG
	gPixmap();
#endif
};
SWIG_TEMPLATE_TYPEDEF(ePtr<gPixmap>, gPixmapPtr);

#endif
