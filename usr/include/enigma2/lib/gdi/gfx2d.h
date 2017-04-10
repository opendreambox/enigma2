#ifndef LIB_GDI_GFX2D_H
#define LIB_GDI_GFX2D_H

#include <lib/base/object.h>
#include <lib/gdi/surface.h>

class eRect;

SWIG_IGNORE(gGfx2dContext);
class gGfx2dContext : public iObject
{
	DECLARE_REF(gGfx2dContext);
	E_DISABLE_COPY(gGfx2dContext);

	bool m_valid;

protected:
	gSurface *m_dst;
	unsigned int m_flags;

	void setValid()
	{
		m_valid = true;
	}

public:
	gGfx2dContext(gSurface *dst, unsigned int flags) :
		m_valid(false),
		m_dst(dst),
		m_flags(flags)
	{
	}

	virtual ~gGfx2dContext() = 0;

	bool valid()
	{
		return m_valid;
	}
};

SWIG_IGNORE(gGfx2dBlitContext);
class gGfx2dBlitContext : public gGfx2dContext
{
	DECLARE_REF(gGfx2dBlitContext);
	E_DISABLE_COPY(gGfx2dBlitContext);

protected:
	const gSurface::BlitParams &m_params;

public:
	gGfx2dBlitContext(gSurface *dst, const gSurface::BlitParams &p, unsigned int flags) :
		gGfx2dContext(dst, flags),
		m_params(p)
	{
	}

	virtual ~gGfx2dBlitContext()
	{
	}

	virtual bool blit(const eRect &dstArea, const eRect &srcArea) = 0;
};

SWIG_IGNORE(gGfx2dFillContext);
class gGfx2dFillContext : public gGfx2dContext
{
	DECLARE_REF(gGfx2dFillContext);
	E_DISABLE_COPY(gGfx2dFillContext);

protected:
	const gSurface::FillParams &m_params;

public:
	gGfx2dFillContext(gSurface *dst, const gSurface::FillParams &p, unsigned int flags) :
		gGfx2dContext(dst, flags),
		m_params(p)
	{
	}

	virtual ~gGfx2dFillContext()
	{
	}

	virtual bool fill(const eRect &dstArea) = 0;
};

SWIG_IGNORE(iGfx2d);
class iGfx2d
{
public:
	virtual ~iGfx2d()
	{
	}

	virtual ePtr<gGfx2dBlitContext> createBlitContext(gSurface *dst, const gSurface::BlitParams &p, unsigned int flags) = 0;
	virtual ePtr<gGfx2dFillContext> createFillContext(gSurface *dst, const gSurface::FillParams &p, unsigned int flags) = 0;

	/* Is it possible to blend using both source alpha and
	   constant alpha in a single step? */
	virtual bool hasCombinedAlphaBlend() const
	{
		return false;
	}
};

#endif /* LIB_GDI_GFX2D_H */
