#if !defined(__GPIXMAP_H_INSIDE__) && !defined(__SURFACE_H_INSIDE__) && !defined(__ENIGMA_PYTHON_I_INSIDE__)
#error "lib/gdi/scalefilter.h should not be included directly!"
#endif

#ifndef __lib_gdi_scalefilter_h
#define __lib_gdi_scalefilter_h

typedef enum
{
    DISABLED, BILINEAR, ANISOTROPIC,
    SHARP, SHARPER, BLURRY, ANTI_FLUTTER,
    ANTI_FLUTTER_BLURRY, ANTI_FLUTTER_SHARP
} scalefilter_t;

#endif /* __lib_gdi_scalefilter_h */
