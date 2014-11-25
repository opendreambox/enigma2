#ifndef __lib_base_macros_h__
#define __lib_base_macros_h__

#ifndef ARRAY_SIZE
#define ARRAY_SIZE(x)	(sizeof(x) / sizeof(*(x)))
#endif

#define E_UNUSED(x)	(void)x;

#endif /* __lib_base_macros_h__ */
