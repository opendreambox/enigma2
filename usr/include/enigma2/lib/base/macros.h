#ifndef __lib_base_macros_h__
#define __lib_base_macros_h__

#ifndef ARRAY_SIZE
#define ARRAY_SIZE(x)	(sizeof(x) / sizeof(*(x)))
#endif

#define E_UNUSED(x)	(void)x;

/* hint to the compiler for better optimization */
#ifndef likely
    #define likely(x) __builtin_expect(!!(x), 1)
#endif

#ifndef unlikely
    #define unlikely(x) __builtin_expect(!!(x), 0)
#endif

#endif /* __lib_base_macros_h__ */
