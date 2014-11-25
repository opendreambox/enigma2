#if !defined(__GPIXMAP_H_INSIDE__) && !defined(__SURFACE_H_INSIDE__)
#error "lib/gdi/surface_flags.h should not be included directly!"
#endif

#ifndef __lib_gdi_surface_flags_h
#define __lib_gdi_surface_flags_h

#if !defined(SWIG)

#define GSURFACE_PREMULT	(1 << 0)
#define GSURFACE_ACCEL		(1 << 1)
#define GSURFACE_MAPPED		(1 << 2)
#define GSURFACE_WINDOW		(1 << 3)
#define GSURFACE_GL_PIXMAP	(1 << 4)
#define GSURFACE_GL_FRAMEBUFFER	(1 << 5)

#endif /* !SWIG */

#endif /* __lib_gdi_surface_flags_h */
